"""Same-origin JSON transport only; all analysis and AI logic lives in services."""

import hmac
import secrets
import re

from flask import Blueprint, current_app, jsonify, request, session
from werkzeug.exceptions import RequestEntityTooLarge

from venuebite.ai import AIError, unique_json

bp = Blueprint("ai", __name__)


def ai_session():
    if "ai_csrf" not in session:
        session["ai_csrf"] = secrets.token_urlsafe(32)
    return session["ai_csrf"]


@bp.post("/api/ai/chat")
def chat():
    try:
        request.max_content_length = 32 * 1024
        expected, received = session.get("ai_csrf", ""), request.headers.get("X-CSRF-Token", "")
        if not expected or not re.fullmatch(r"[A-Za-z0-9_-]{43}", received) or not hmac.compare_digest(expected, received) or request.headers.get("Sec-Fetch-Site") == "cross-site":
            raise AIError("invalid_session", "This analyst session expired. Reload the analysis.", 403)
        if request.mimetype != "application/json":
            raise AIError("invalid_request", "Submit a JSON analyst question.", 400)
        try:
            payload = unique_json(request.get_data(as_text=True), 32 * 1024)
        except AIError:
            raise AIError("invalid_request", "Submit a valid JSON analyst question.", 400) from None
        return jsonify(current_app.extensions["ai_analyst_service"].chat(payload, expected, current_hash=session.get("ai_current_hash", "")))
    except RequestEntityTooLarge:
        return jsonify(error="This analyst request is too large. Reset the conversation.", code="request_too_large"), 413
    except AIError as error:
        return jsonify(error=str(error), code=error.code), error.status
