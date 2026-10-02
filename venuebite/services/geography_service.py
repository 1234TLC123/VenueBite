from itsdangerous import BadSignature, URLSafeTimedSerializer

from venuebite.providers.location_provider import GeographicLocation, LocationError, validate_coordinates


class GeographyService:
    def __init__(self, provider, secret_key):
        self.provider = provider
        self.serializer = URLSafeTimedSerializer(secret_key, salt="venuebite-selected-location-v1")

    def sign(self, location):
        return self.serializer.dumps(location.to_dict())

    def read_selection(self, token):
        try:
            data = self.serializer.loads(token, max_age=1800)
            return GeographicLocation(**data)
        except (BadSignature, TypeError, ValueError, LocationError):
            raise LocationError("This location selection expired or changed. Search and select it again.", code="invalid_selection", status=400) from None

    def resolve_form(self, form, values):
        for field in ("latitude", "longitude", "selection_token", "demo_only"):
            if len(form.getlist(field)) > 1:
                raise LocationError("Submit one location selection at a time.", code="invalid_selection", status=400)
        latitude, longitude = form.get("latitude", ""), form.get("longitude", "")
        coordinates = None
        if latitude or longitude:
            coordinates = validate_coordinates(latitude, longitude)
        token = form.get("selection_token", "")
        location = self.read_selection(token) if token else None
        if coordinates and not location:
            raise LocationError("Select a location suggestion before submitting coordinates.", code="invalid_selection", status=400)
        if location:
            if values["location"] != location.display_name:
                raise LocationError("The location changed. Search and select it again.", code="invalid_selection", status=400)
            if coordinates and any(abs(actual - expected) > 0.000001 for actual, expected in zip(coordinates, (location.latitude, location.longitude))):
                raise LocationError("The coordinates changed. Select the location again.", code="invalid_coordinates", status=400)
            return location
        if form.get("demo_only") == "1" or not self.provider.enabled:
            return None
        return self.provider.forward(values["location"])
