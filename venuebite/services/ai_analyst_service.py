"""Ephemeral analyst orchestration with bounded local request/cost controls."""

from collections import OrderedDict
from hashlib import sha256
import hmac
from threading import Lock
from time import monotonic
import re

from venuebite.ai import AIError, MAX_MESSAGE, MAX_HISTORY, PROMPT_VERSION, safe_text, credential_guard
from venuebite.services.ai_response_validator import AIResponseValidator
from venuebite.services.ai_context import model_context


class RequestBudget:
    def __init__(self, *, clock=monotonic, limit=8, capacity=1024):
        self.clock, self.limit, self.capacity = clock, limit, capacity
        self.lock = Lock()
        self.sessions = OrderedDict()

    def begin(self, session, request_id):
        now = self.clock()
        with self.lock:
            for key, value in list(self.sessions.items()):
                if now - value["start"] > 60 and not value["busy"]:
                    del self.sessions[key]
            entry = self.sessions.get(session)
            if entry is None:
                if len(self.sessions) >= self.capacity:
                    raise AIError("rate_limited", "The analyst is busy. Try again in a minute.", 429)
                entry = {"start": now, "count": 0, "busy": False, "ids": set()}
                self.sessions[session] = entry
            if entry["busy"] or request_id in entry["ids"]:
                raise AIError("duplicate_request", "A question is already pending or was submitted. Send a new question.", 409)
            if entry["count"] >= self.limit:
                raise AIError("rate_limited", "Question limit reached. Try again in a minute.", 429)
            entry["busy"] = True
            entry["count"] += 1
            entry["ids"].add(request_id)

    def finish(self, session):
        with self.lock:
            if session in self.sessions:
                self.sessions[session]["busy"] = False


class AIAnalystService:
    def __init__(self, provider, contexts, *, sensitive_values=(), budget=None):
        self.provider, self.contexts = provider, contexts
        self.sensitive_values = sensitive_values
        self.validator = AIResponseValidator(sensitive_values)
        self.budget = budget or RequestBudget()

    def chat(self, payload, session, *, current_hash=None):
        if not isinstance(payload, dict) or set(payload) != {"context_token", "message", "history", "request_id"}:
            raise AIError("invalid_request", "Submit a question with the current analysis context.", 400)
        message = safe_text(payload["message"], MAX_MESSAGE)
        history = payload["history"]
        if not isinstance(history, list) or len(history) > MAX_HISTORY:
            raise AIError("invalid_history", "Reset the conversation to continue.", 400)
        recent = []
        for entry in history:
            if not isinstance(entry, dict) or set(entry) != {"role", "content"} or entry["role"] not in {"user", "assistant"}:
                raise AIError("invalid_history", "Reset the conversation to continue.", 400)
            recent.append({"role": entry["role"], "content": safe_text(entry["content"], MAX_MESSAGE)})
        request_id = payload["request_id"]
        if not isinstance(request_id, str) or not re.fullmatch(r"[a-f0-9-]{32,36}", request_id):
            raise AIError("invalid_request", "Submit one question at a time.", 400)
        credential_guard([message, recent], (*self.sensitive_values, session))
        context = self.contexts.resolve(payload["context_token"], session)
        if context["kind"] == "current" and current_hash is not None and not hmac.compare_digest(
            sha256(payload["context_token"].encode()).hexdigest(), current_hash
        ):
            raise AIError("stale_context", "A newer analysis replaced this context. Analyze again.", 409)
        if not self.provider.enabled:
            raise AIError("not_configured", "SiteWise is unavailable because the server AI provider is not configured.", 503)
        self.budget.begin(session, request_id)
        try:
            output = self.provider.answer(model_context(context), message, recent)
            answer = self.validator.validate(output, context)
            return {"version": PROMPT_VERSION, "context_kind": context["kind"], **answer}
        except AIError:
            raise
        except Exception:
            # Provider exceptions may include credentials or requests: never log their text.
            raise AIError() from None
        finally:
            self.budget.finish(session)
