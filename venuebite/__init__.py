from pathlib import Path

from flask import Flask, render_template

from venuebite.services.mock_data_service import MockLocationDataService


def create_app(config=None, *, data_provider=None):
    root = Path(__file__).resolve().parent.parent
    app = Flask(
        __name__,
        template_folder=str(root / "templates"),
        static_folder=str(root / "static"),
    )
    app.config.from_mapping(MAX_CONTENT_LENGTH=16 * 1024)
    if config:
        app.config.update(config)

    app.extensions["location_data_provider"] = (
        data_provider if data_provider is not None else MockLocationDataService()
    )

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
        response.headers["Referrer-Policy"] = "same-origin"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'self'; style-src 'self'; "
            "img-src 'self'; font-src 'self'; object-src 'none'; "
            "base-uri 'self'; form-action 'self'; frame-ancestors 'none'"
        )
        return response

    return app
