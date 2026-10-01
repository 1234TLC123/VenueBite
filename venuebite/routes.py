from flask import Blueprint, current_app, render_template, request

from venuebite.services import DataProviderError
from venuebite.services.analysis_service import AnalysisService

bp = Blueprint("main", __name__)
FIELD_LIMITS = {"location": 200, "concept": 120}
FIELD_LABELS = {"location": "location", "concept": "restaurant concept"}


def validate_form(form):
    values = {}
    errors = {}
    for field, limit in FIELD_LIMITS.items():
        value = " ".join(form.get(field, "").split())
        values[field] = value[:limit]
        label = FIELD_LABELS[field]
        if not value:
            errors[field] = f"Enter a {label}."
        elif len(form.getlist(field)) > 1:
            errors[field] = f"Submit one {label} at a time."
        elif len(value) > limit:
            errors[field] = f"Keep the {label} to {limit} characters or fewer."
        elif any(ord(char) < 32 or ord(char) == 127 for char in value):
            errors[field] = f"Remove unsupported control characters from the {label}."
    return values, errors


@bp.route("/", methods=["GET", "POST"])
def home():
    if request.method == "GET":
        return render_template("index.html", values={}, errors={})

    values, errors = validate_form(request.form)
    if errors:
        return render_template("index.html", values=values, errors=errors), 400

    service = AnalysisService(current_app.extensions["location_data_provider"])
    try:
        report = service.analyze(values["location"], values["concept"])
    except DataProviderError:
        current_app.logger.exception("Location data provider failed")
        return render_template(
            "index.html", values=values, errors={},
            page_error="Location data is temporarily unavailable. Please try again.",
        ), 503

    return render_template("results.html", values=values, errors={}, report=report)
