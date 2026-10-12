"""Session-bound temporary context; saved references are always reloaded server-side."""

from hashlib import sha256
import hmac
import json

from itsdangerous import URLSafeTimedSerializer, BadData

from venuebite.ai import AIError, CONTEXT_VERSION, CONTEXT_MAX_AGE, MAX_CONTEXT_BYTES, STARTERS, COMPARE_STARTERS, credential_guard
from venuebite.services.ai_evidence import EvidenceRegistry
from venuebite.services.saved_site_service import build_snapshot, SaveError
from venuebite.snapshots import encode_snapshot, SnapshotError
from venuebite.db import PersistenceError


def digest(snapshot):
    return sha256(encode_snapshot(snapshot).encode("utf-8")).hexdigest()


def model_context(context):
    """Deduplicate provenance/limitations; source URLs are exclusively server-rendered."""
    origins, limits, entries = [], [], {}
    for identifier, item in context["evidence"].items():
        origin = {"source": item["source"], "date": item["date"]}
        if origin not in origins:
            origins.append(origin)
        if item["limitation"] not in limits:
            limits.append(item["limitation"])
        entries[identifier] = {key: item[key] for key in ("label", "value", "units", "status")}
        entries[identifier].update(origin_index=origins.index(origin), limitation_index=limits.index(item["limitation"]))
    result = {**context, "evidence": entries, "origins": origins, "evidence_limitations": limits}
    if len(json.dumps(result, ensure_ascii=False, separators=(",", ":")).encode("utf-8")) > MAX_CONTEXT_BYTES:
        raise AIError("context_too_large", "This context is too large for the analyst.", 400)
    return result


class AIContextBuilder:
    def __init__(self, saved, comparison, secret, *, sensitive_values=()):
        self.saved, self.comparison = saved, comparison
        self.serializer = URLSafeTimedSerializer(secret, salt="venuebite-ai-context-v1")
        self.sensitive_values = sensitive_values

    def build(self, snapshots, kind, labels, comparison=None):
        registry = EvidenceRegistry()
        for index, snapshot in enumerate(snapshots, 1):
            registry.site(snapshot, f"s{index}")
        if kind == "compare":
            registry.comparisons(snapshots)
            if comparison:
                for kind_name, items in (("highlight", comparison.highlights), ("warning", comparison.warnings)):
                    for index, value in enumerate(items, 1):
                        registry.add(f"compare.{kind_name}.{index}", f"Deterministic comparison {kind_name}", value,
                                     limitation="Historical stored model comparison, not an automatic recommendation or fresh market evidence.")
        context = {"version": CONTEXT_VERSION, "kind": kind, "sites": [
            {"slot": f"s{index}", "label": label[:140], "historical": kind != "current"}
            for index, label in enumerate(labels, 1)
        ], "evidence": registry.entries,
            "comparison_highlights": list(comparison.highlights) if comparison else [],
            "comparison_warnings": list(comparison.warnings) if comparison else [],
        }
        credential_guard(context, self.sensitive_values)
        if len(json.dumps(context, ensure_ascii=False, allow_nan=False).encode("utf-8")) > 3 * MAX_CONTEXT_BYTES:
            raise AIError("context_too_large", "This context is too large for the analyst.", 400)
        return context

    def current(self, report, location, values, session_token):
        snapshot = build_snapshot(report, location, values, allow_unresolved=True)
        context = self.build([snapshot], "current", ["Current analysis"])
        return self._sign({"kind": "current", "context": context}, session_token)

    def saved_site(self, site, session_token):
        return self._sign({"kind": "saved", "ids": [site.id], "digests": [digest(site.snapshot)]}, session_token)

    def compare(self, comparison, session_token):
        return self._sign({"kind": "compare", "ids": [s.id for s in comparison.sites],
                           "digests": [digest(s.snapshot) for s in comparison.sites]}, session_token)

    def _sign(self, payload, session_token):
        token = self.serializer.dumps({"version": CONTEXT_VERSION, "session": sha256(session_token.encode()).hexdigest(), **payload})
        if len(token) > 20000:
            raise AIError("context_too_large", "This context is too large for the analyst.", 400)
        return token

    def resolve(self, token, session_token):
        try:
            if not isinstance(token, str) or len(token) > 20000:
                raise ValueError
            payload = self.serializer.loads(token, max_age=CONTEXT_MAX_AGE)
            if payload.get("version") != CONTEXT_VERSION or not hmac.compare_digest(payload["session"], sha256(session_token.encode()).hexdigest()):
                raise ValueError
            kind = payload["kind"]
            if kind == "current" and set(payload) == {"version", "session", "kind", "context"}:
                context = payload["context"]
                if context["kind"] != kind:
                    raise ValueError
                credential_guard(context, self.sensitive_values)
                return context
            if kind not in {"saved", "compare"} or set(payload) != {"version", "session", "kind", "ids", "digests"}:
                raise ValueError
            if kind == "compare":
                comparison = self.comparison.compare(payload["ids"])
                sites = comparison.sites
            else:
                if len(payload["ids"]) != 1:
                    raise ValueError
                comparison = None
                site = self.saved.get(payload["ids"][0])
                if site is None:
                    raise ValueError
                sites = (site,)
            if [digest(s.snapshot) for s in sites] != payload["digests"]:
                raise ValueError
            return self.build([s.snapshot for s in sites], kind, [s.display_name for s in sites], comparison)
        except AIError:
            raise
        except (BadData, ValueError, TypeError, KeyError, AttributeError, SaveError, SnapshotError, PersistenceError):
            raise AIError("stale_context", "This analysis context expired or changed. Reload or analyze again.", 409) from None


def analyst_view(token, kind, label, enabled):
    return {"token": token, "kind": kind, "label": label, "enabled": enabled,
            "starters": COMPARE_STARTERS if kind == "compare" else STARTERS}
