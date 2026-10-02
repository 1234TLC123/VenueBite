from flask import Blueprint, current_app, jsonify, render_template, request

from venuebite.providers.location_provider import LocationError, validate_identifier, validate_query, validate_session
from venuebite.providers.mapbox_provider import public_token
from venuebite.services import DataProviderError
from venuebite.services.analysis_service import AnalysisService
from venuebite.distance import ALLOWED_RADIUS_MILES

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
    radius = request.form.get("radius_miles", str(current_app.config["COMPETITION_RADIUS_MILES"]))
    if len(request.form.getlist("radius_miles")) > 1 or radius not in {str(value) for value in ALLOWED_RADIUS_MILES}:
        errors["radius_miles"] = "Choose a 1, 3, or 5 mile radius."
        radius = str(current_app.config["COMPETITION_RADIUS_MILES"])
    values["radius_miles"] = radius
    geography = current_app.extensions["geography_service"]
    geographic_location = None
    token = request.form.get("selection_token", "")
    if token:
        try:
            restored = geography.read_selection(token)
            if restored.display_name == values.get("location"):
                geographic_location = restored
                values.update(selection_token=token, latitude=restored.latitude, longitude=restored.longitude)
        except LocationError:
            pass
    if errors:
        return render_template("index.html", values=values, errors=errors, geographic_location=geographic_location), 400

    try:
        geographic_location = geography.resolve_form(request.form, values)
    except LocationError as error:
        errors["location"] = str(error)
        for field in ("selection_token", "latitude", "longitude"):
            values.pop(field, None)
        return render_template("index.html", values=values, errors=errors, geography_error=True), error.status
    if geographic_location:
        values.update(
            location=geographic_location.display_name,
            selection_token=geography.sign(geographic_location),
            latitude=geographic_location.latitude,
            longitude=geographic_location.longitude,
        )

    service = AnalysisService(
        current_app.extensions["location_data_provider"], current_app.extensions["competition_service"],
        current_app.extensions["demographic_service"],
    )
    try:
        report = service.analyze(
            values["location"], values["concept"],
            geographic_location=geographic_location if request.form.get("demo_only") != "1" else None,
            radius_miles=int(radius),
        )
    except DataProviderError:
        current_app.logger.exception("Location data provider failed")
        return render_template(
            "index.html", values=values, errors={}, geographic_location=geographic_location,
            page_error="Location data is temporarily unavailable. Please try again.",
        ), 503

    competition_payload = report.competition.map_payload(geographic_location, values["concept"]) if report.competition else None
    return render_template("results.html", values=values, errors={}, report=report, geographic_location=geographic_location, competition_payload=competition_payload)


@bp.get("/api/map-config")
def map_config():
    provider = current_app.extensions["geography_service"].provider
    token = public_token(current_app.config["MAPBOX_ACCESS_TOKEN"])
    return jsonify(
        enabled=bool(token), search_enabled=provider.enabled,
        access_token=token,
        message=provider.configuration_message if not token else "",
    )


@bp.get("/api/locations/suggestions")
def location_suggestions():
    try:
        if any(len(request.args.getlist(field)) != 1 for field in ("q", "session_token")):
            raise LocationError("Provide one location query and search session.", code="invalid_query", status=400)
        query = validate_query(request.args.get("q"))
        session = validate_session(request.args.get("session_token"))
        provider = current_app.extensions["geography_service"].provider
        suggestions, attribution = provider.suggest(query, session)
        return jsonify(suggestions=[item.to_dict() for item in suggestions], attribution=attribution)
    except LocationError as error:
        return jsonify(error=str(error), code=error.code), error.status


@bp.post("/api/locations/retrieve")
def retrieve_location():
    try:
        payload = request.get_json(silent=True)
        if not isinstance(payload, dict):
            raise LocationError("Submit a valid location selection.", code="invalid_selection", status=400)
        identifier = validate_identifier(payload.get("provider_id"))
        session = validate_session(payload.get("session_token"))
        geography = current_app.extensions["geography_service"]
        location = geography.provider.retrieve(identifier, session)
        return jsonify(location=location.to_dict(), selection_token=geography.sign(location))
    except LocationError as error:
        return jsonify(error=str(error), code=error.code), error.status
