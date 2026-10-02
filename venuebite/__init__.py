from pathlib import Path
import os
import secrets

from flask import Flask, render_template, request
from dotenv import load_dotenv

from venuebite.providers.mapbox_provider import MapboxLocationProvider, public_token
from venuebite.services.geography_service import GeographyService
from venuebite.services.mock_data_service import MockLocationDataService


def create_app(config=None, *, data_provider=None, location_provider=None):
    root = Path(__file__).resolve().parent.parent
    if not (config and config.get("TESTING")):
        load_dotenv(root / ".env", override=False)
    app = Flask(
        __name__,
        template_folder=str(root / "templates"),
        static_folder=str(root / "static"),
    )
    app.config.from_mapping(
        MAX_CONTENT_LENGTH=16 * 1024,
        SECRET_KEY=os.environ.get("SECRET_KEY") or secrets.token_urlsafe(32),
        MAPBOX_ACCESS_TOKEN=os.environ.get("MAPBOX_ACCESS_TOKEN", ""),
        MAPBOX_SEARCH_COUNTRIES=os.environ.get("MAPBOX_SEARCH_COUNTRIES", ""),
        MAPBOX_REQUEST_ORIGIN=os.environ.get("MAPBOX_REQUEST_ORIGIN", ""),
    )
    if config:
        app.config.update(config)
    if app.testing and "MAPBOX_ACCESS_TOKEN" not in (config or {}):
        app.config["MAPBOX_ACCESS_TOKEN"] = ""

    app.extensions["location_data_provider"] = (
        data_provider if data_provider is not None else MockLocationDataService()
    )
    geographic_provider = location_provider if location_provider is not None else MapboxLocationProvider(
        app.config["MAPBOX_ACCESS_TOKEN"],
        countries=app.config["MAPBOX_SEARCH_COUNTRIES"],
        request_origin=app.config["MAPBOX_REQUEST_ORIGIN"],
    )
    app.extensions["geography_service"] = GeographyService(geographic_provider, app.config["SECRET_KEY"])

    @app.context_processor
    def geography_context():
        return {
            "geography_enabled": geographic_provider.enabled,
            "map_enabled": bool(public_token(app.config["MAPBOX_ACCESS_TOKEN"])),
            "map_configuration_message": geographic_provider.configuration_message,
        }

    from venuebite.routes import bp

    app.register_blueprint(bp)

    @app.errorhandler(413)
    def request_too_large(error):
        return render_template(
            "index.html", values={}, errors={},
            page_error="This request is too large. Please submit a shorter location and restaurant concept.",
        ), 413

    @app.errorhandler(500)
    def unexpected_error(error):
        return render_template(
            "index.html", values={}, errors={},
            page_error="We couldn't complete this analysis. Please try again.",
        ), 500

    @app.after_request
    def response_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'self' https://api.mapbox.com/mapbox-gl-js/ 'wasm-unsafe-eval'; "
            "style-src 'self' https://api.mapbox.com/mapbox-gl-js/ 'unsafe-inline'; "
            "img-src 'self' data: blob: https://api.mapbox.com; font-src 'self'; "
            "connect-src 'self' https://api.mapbox.com https://events.mapbox.com https://*.tiles.mapbox.com; "
            "worker-src 'self' blob:; child-src blob:; object-src 'none'; "
            "base-uri 'self'; form-action 'self'; frame-ancestors 'none'"
        )
        if request.method == "POST" or request.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store"
        return response

    return app
