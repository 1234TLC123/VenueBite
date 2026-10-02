from pathlib import Path
import os
import secrets

from flask import Flask, render_template, request
from dotenv import load_dotenv

from venuebite.providers.mapbox_provider import MapboxLocationProvider, public_token
from venuebite.providers.mapbox_poi_provider import MapboxPoiProvider
from venuebite.providers.census_provider import CensusGeoProvider, CensusDemographicProvider
from venuebite.providers.regrid_provider import RegridProvider, fallback_radius, request_timeout
from venuebite.distance import ALLOWED_RADIUS_MILES, DEFAULT_RADIUS_MILES
from venuebite.services.competition_service import CompetitionService
from venuebite.services.demographic_service import DemographicService
from venuebite.services.geography_service import GeographyService
from venuebite.services.mock_data_service import MockLocationDataService
from venuebite.services.site_intelligence_service import SiteIntelligenceService


def create_app(config=None, *, data_provider=None, location_provider=None, poi_provider=None,
               census_geo_provider=None, demographic_provider=None, site_provider=None):
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
        MAPBOX_HTTP_TIMEOUT_SECONDS=os.environ.get("MAPBOX_HTTP_TIMEOUT_SECONDS", 6),
        COMPETITION_RADIUS_MILES=os.environ.get("COMPETITION_RADIUS_MILES", DEFAULT_RADIUS_MILES),
        CENSUS_API_KEY=os.environ.get("CENSUS_API_KEY", ""),
        CENSUS_HTTP_TIMEOUT_SECONDS=os.environ.get("CENSUS_HTTP_TIMEOUT_SECONDS", 8),
        REGRID_API_TOKEN=os.environ.get("REGRID_API_TOKEN", ""),
        REGRID_HTTP_TIMEOUT_SECONDS=os.environ.get("REGRID_HTTP_TIMEOUT_SECONDS", 8),
        REGRID_FALLBACK_RADIUS_METERS=os.environ.get("REGRID_FALLBACK_RADIUS_METERS", 25),
    )
    if config:
        app.config.update(config)
    if app.testing and "MAPBOX_ACCESS_TOKEN" not in (config or {}):
        app.config["MAPBOX_ACCESS_TOKEN"] = ""
    if app.testing and "CENSUS_API_KEY" not in (config or {}):
        app.config["CENSUS_API_KEY"] = ""
    if app.testing and "REGRID_API_TOKEN" not in (config or {}):
        app.config["REGRID_API_TOKEN"] = ""
    app.config["REGRID_HTTP_TIMEOUT_SECONDS"] = request_timeout(app.config["REGRID_HTTP_TIMEOUT_SECONDS"])
    app.config["REGRID_FALLBACK_RADIUS_METERS"] = fallback_radius(app.config["REGRID_FALLBACK_RADIUS_METERS"])
    try:
        default_radius = int(str(app.config["COMPETITION_RADIUS_MILES"]))
    except (ValueError, TypeError):
        default_radius = DEFAULT_RADIUS_MILES
    app.config["COMPETITION_RADIUS_MILES"] = default_radius if default_radius in ALLOWED_RADIUS_MILES else DEFAULT_RADIUS_MILES

    app.extensions["location_data_provider"] = (
        data_provider if data_provider is not None else MockLocationDataService()
    )
    geographic_provider = location_provider if location_provider is not None else MapboxLocationProvider(
        app.config["MAPBOX_ACCESS_TOKEN"],
        countries=app.config["MAPBOX_SEARCH_COUNTRIES"],
        request_origin=app.config["MAPBOX_REQUEST_ORIGIN"],
        timeout=app.config["MAPBOX_HTTP_TIMEOUT_SECONDS"],
    )
    app.extensions["geography_service"] = GeographyService(geographic_provider, app.config["SECRET_KEY"])
    restaurant_provider = poi_provider if poi_provider is not None else MapboxPoiProvider(
        app.config["MAPBOX_ACCESS_TOKEN"], countries=app.config["MAPBOX_SEARCH_COUNTRIES"],
        request_origin=app.config["MAPBOX_REQUEST_ORIGIN"], timeout=app.config["MAPBOX_HTTP_TIMEOUT_SECONDS"],
    )
    app.extensions["competition_service"] = CompetitionService(restaurant_provider)
    app.extensions["demographic_service"] = DemographicService(
        census_geo_provider if census_geo_provider is not None else CensusGeoProvider(app.config["CENSUS_HTTP_TIMEOUT_SECONDS"]),
        demographic_provider if demographic_provider is not None else CensusDemographicProvider(
            app.config["CENSUS_API_KEY"], timeout=app.config["CENSUS_HTTP_TIMEOUT_SECONDS"],
        ),
    )
    app.extensions["site_intelligence_service"] = SiteIntelligenceService(
        site_provider if site_provider is not None else RegridProvider(
            app.config["REGRID_API_TOKEN"], timeout=app.config["REGRID_HTTP_TIMEOUT_SECONDS"],
        ),
        fallback_radius_meters=app.config["REGRID_FALLBACK_RADIUS_METERS"],
    )

    @app.context_processor
    def geography_context():
        return {
            "geography_enabled": geographic_provider.enabled,
            "map_enabled": bool(public_token(app.config["MAPBOX_ACCESS_TOKEN"])),
            "map_configuration_message": geographic_provider.configuration_message,
            "default_radius_miles": app.config["COMPETITION_RADIUS_MILES"],
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
