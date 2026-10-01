from dataclasses import replace

import pytest

from venuebite import create_app
from venuebite.services import DataProviderError
from venuebite.services.mock_data_service import MockLocationDataService


VALID_FORM = {"location": "Aurora, CO", "concept": "Congolese Restaurant"}


def test_home_page_contains_post_form_and_empty_workspace(client):
    response = client.get("/")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert 'method="post"' in html
    assert 'name="location"' in html
    assert 'name="concept"' in html
    assert "Awaiting analysis" in html
    assert "Demo data only" in html
    assert "Coming soon" in html


def test_successful_analysis_renders_all_mvp_sections(client):
    response = client.post("/", data=VALID_FORM)
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    for text in [
        "Aurora, CO", "Congolese Restaurant", "72.5", "Promising opportunity",
        "Population", "Income", "Rent", "Competition", "Location context",
        "Live map data will be added later", "Area insights", "Nearby competition",
        "Sample Kitchen 01", "Strengths", "Risks", "Demo data only",
        "fictional", "same sample dataset", "not scientifically validated",
    ]:
        assert text in html


@pytest.mark.parametrize("data, message", [
    ({"location": "", "concept": "Cafe"}, "Enter a location."),
    ({"location": "  \t\n", "concept": "Cafe"}, "Enter a location."),
    ({"concept": "Cafe"}, "Enter a location."),
    ({"location": "Denver"}, "Enter a restaurant concept."),
    ({"location": "Denver", "concept": "   "}, "Enter a restaurant concept."),
    ({"location": "x" * 201, "concept": "Cafe"}, "200 characters or fewer"),
    ({"location": "Denver", "concept": "x" * 121}, "120 characters or fewer"),
    ({"location": "Denver\x00", "concept": "Cafe"}, "unsupported control characters"),
])
def test_server_validation(client, data, message):
    response = client.post("/", data=data)
    assert response.status_code == 400
    assert message in response.get_data(as_text=True)
    assert b"Awaiting analysis" in response.data
    assert b"72.5" not in response.data


def test_blank_submission_reports_both_errors(client):
    response = client.post("/", data={})
    assert response.status_code == 400
    assert b"Enter a location." in response.data
    assert b"Enter a restaurant concept." in response.data


def test_validation_preserves_other_field(client):
    response = client.post("/", data={"location": "", "concept": "Congolese Restaurant"})
    assert b'value="Congolese Restaurant"' in response.data
    assert b'aria-invalid="true"' in response.data


def test_duplicate_field_is_rejected(client):
    response = client.post("/", data={"location": ["Denver", "Aurora"], "concept": "Cafe"})
    assert response.status_code == 400
    assert b"Submit one location at a time." in response.data


def test_whitespace_is_normalized(client):
    response = client.post("/", data={"location": "  Aurora,   CO  ", "concept": "  Congolese   Restaurant "})
    assert response.status_code == 200
    assert b'value="Aurora, CO"' in response.data
    assert b'value="Congolese Restaurant"' in response.data


def test_html_input_is_escaped_in_results_and_form(client):
    attack = '<script>alert("xss")</script>'
    response = client.post("/", data={"location": attack, "concept": attack})
    assert response.status_code == 200
    assert attack.encode() not in response.data
    assert b"&lt;script&gt;" in response.data


def test_html_input_is_escaped_in_validation_response(client):
    response = client.post("/", data={"location": '"><img src=x onerror=alert(1)>', "concept": ""})
    assert response.status_code == 400
    assert b"<img src=x" not in response.data
    assert b"&lt;img" in response.data


def test_another_location_can_be_analyzed_without_old_results(client):
    client.post("/", data=VALID_FORM)
    response = client.post("/", data={"location": "Denver, CO", "concept": "Cafe & Bakery"})
    assert response.status_code == 200
    assert b"Denver, CO" in response.data
    assert b'value="Aurora, CO"' not in response.data
    assert b"<h2>Aurora, CO</h2>" not in response.data
    assert b"Cafe &amp; Bakery" in response.data


def test_query_string_does_not_run_analysis(client):
    response = client.get("/?location=Denver&concept=Cafe")
    assert response.status_code == 200
    assert b"Awaiting analysis" in response.data
    assert b"72.5" not in response.data


def test_replaceable_provider_is_used_by_analysis():
    class TestProvider:
        def get_location_data(self, location, concept):
            data = MockLocationDataService().get_location_data(location, concept)
            return replace(data, factor_scores={"population": 100, "income": 100, "rent": 100, "competition": 100})

    app = create_app({"TESTING": True}, data_provider=TestProvider())
    response = app.test_client().post("/", data=VALID_FORM)
    assert response.status_code == 200
    assert b"100.0" in response.data
    assert b"Strong opportunity" in response.data
    assert b"No factors fall below the risk threshold." in response.data


def test_provider_failure_is_useful_and_preserves_inputs():
    class FailingProvider:
        def get_location_data(self, location, concept):
            raise DataProviderError("private upstream details")

    app = create_app({"TESTING": True}, data_provider=FailingProvider())
    response = app.test_client().post("/", data=VALID_FORM)
    assert response.status_code == 503
    assert b"temporarily unavailable" in response.data
    assert b'value="Aurora, CO"' in response.data
    assert b"private upstream details" not in response.data


def test_unexpected_errors_do_not_expose_internal_details():
    class BrokenProvider:
        def get_location_data(self, location, concept):
            raise RuntimeError("private implementation details")

    app = create_app({"TESTING": True, "PROPAGATE_EXCEPTIONS": False}, data_provider=BrokenProvider())
    response = app.test_client().post("/", data=VALID_FORM)
    assert response.status_code == 500
    assert b"Please try again" in response.data
    assert b"private implementation details" not in response.data
    assert b"Traceback" not in response.data


def test_oversized_request_has_safe_error_page(client):
    response = client.post("/", data={"location": "x" * 17000, "concept": "Cafe"})
    assert response.status_code == 413
    assert b"request is too large" in response.data


def test_security_headers_and_no_session_cookie(client):
    response = client.post("/", data=VALID_FORM)
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert "default-src 'self'" in response.headers["Content-Security-Policy"]
    assert "form-action 'self'" in response.headers["Content-Security-Policy"]
    assert "Set-Cookie" not in response.headers


@pytest.mark.parametrize("path, mime", [
    ("/static/css/style.css", "text/css"),
    ("/static/js/main.js", "javascript"),
    ("/static/icons/map-pin.svg", "image/svg+xml"),
])
def test_static_assets_are_served(client, path, mime):
    response = client.get(path)
    assert response.status_code == 200
    assert mime in response.content_type
