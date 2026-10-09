from html.parser import HTMLParser

import pytest

from test_occupancy import TERMS
from test_occupancy_integration import analyze, submit, workspace
from test_site_intelligence import PARCEL
from venuebite.providers.poi_provider import PoiError
from venuebite.providers.site_provider import SiteError


class Document(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.nodes, self.stack = [], []
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        node = {"tag": tag, "attrs": dict(attrs), "parents": tuple(self.stack), "text": ""}
        self.nodes.append(node)
        if tag not in {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}:
            self.stack.append(node)

    def handle_endtag(self, tag):
        for index in range(len(self.stack) - 1, -1, -1):
            if self.stack[index]["tag"] == tag:
                del self.stack[index:]
                break

    def handle_data(self, text):
        for node in self.stack:
            node["text"] += text

    def find(self, tag=None, **attrs):
        return [n for n in self.nodes if (tag is None or n["tag"] == tag) and all(k in n["attrs"] and n["attrs"][k] == v for k, v in attrs.items())]


@pytest.mark.parametrize("result", [False, True])
def test_primary_navigation_contains_working_workspace_links(client, result):
    response = client.post("/", data={"location": "Aurora", "concept": "Indian"}) if result else client.get("/")
    html = response.get_data(as_text=True)
    nav = Document(html).find("nav", **{"aria-label": "Main navigation"})[0]
    assert "Analyze" in nav["text"]
    assert 'href="/compare"' in html and 'href="/saved"' in html
    for text in ("Coming soon", "Saved Locations", "Find an Area"):
        assert text not in html


def test_empty_workspace_has_no_fake_metrics(client):
    doc = Document(client.get("/").get_data(as_text=True))
    assert doc.find("h2", id="empty-score-heading")
    assert not doc.find("meter") and not doc.find("circle")
    assert doc.find("div", id="location-map")
    assert doc.find("div", **{"aria-hidden": "true"})


def test_optional_terms_are_grouped_and_collapsed(client):
    doc = Document(client.get("/").get_data(as_text=True))
    assert "open" not in doc.find("details", **{"class": "occupancy-inputs"})[0]["attrs"]
    assert {n["text"].strip() for n in doc.find("legend")} == {"Space", "Lease", "Additional costs", "Business threshold", "Source"}
    assert len(doc.find("button", type="submit", **{"data-submit-button": None})) == 1


def test_dashboard_uses_original_scores_and_accessible_contributions(workspace):
    expected = analyze(workspace)
    workspace[-1].results = [(PARCEL,)]
    doc = Document(submit(workspace).get_data(as_text=True))
    assert doc.find("div", **{"class": "score-value"})[0]["text"].strip().startswith(f"{expected.score.overall_score:.1f}")
    ring = doc.find("svg", **{"aria-hidden": "true"})[0]
    assert ring["attrs"]["focusable"] == "false"
    coverage = doc.find("meter", **{"aria-label": "Real usable model data coverage, percent"})[0]
    assert float(coverage["attrs"]["value"]) == expected.coverage.percent
    for factor in expected.score.factors:
        assert float(doc.find("meter", **{"aria-label": f"{factor.label} score"})[0]["attrs"]["value"]) == factor.score
        assert doc.find(**{"data-contribution": factor.weighted_points_label})
    assert "not success probability" in doc.find("div", **{"class": "data-coverage"})[0]["text"]


def test_report_anchor_targets_exist(workspace):
    doc = Document(submit(workspace, **TERMS).get_data(as_text=True))
    nav = doc.find("nav", **{"aria-label": "Report sections"})[0]
    for link in doc.find("a"):
        if nav in link["parents"] and "hidden" not in link["attrs"]:
            assert doc.find(id=link["attrs"]["href"][1:])


@pytest.mark.parametrize("field", ["monthly_occupancy_budget", "asking_rent", "space_size_sqft"])
def test_terms_validation_expands_form_and_preserves_labels(workspace, field):
    response = submit(workspace, **{**TERMS, field: "-1"})
    assert response.status_code == 400
    doc = Document(response.get_data(as_text=True))
    assert "open" in doc.find("details", **{"class": "occupancy-inputs"})[0]["attrs"]
    assert doc.find(id=field)[0]["attrs"]["aria-invalid"] == "true"
    assert doc.find("label", **{"for": field})
    assert not doc.find(**{"data-occupancy-status": "complete"})


@pytest.mark.parametrize("budget,utilization", [("10000", "94.5%"), ("8000", "118.1%"), ("1000", "945.0%")])
def test_occupancy_gauge_keeps_actual_ratio_when_over_scale(workspace, budget, utilization):
    response = submit(workspace, **{**TERMS, "monthly_occupancy_budget": budget})
    doc = Document(response.get_data(as_text=True))
    progress = doc.find("progress")[0]
    assert utilization in progress["text"]
    assert progress["attrs"]["aria-valuetext"] == f"{utilization} of stated budget"
    assert 0 <= float(progress["attrs"]["value"]) <= float(progress["attrs"]["max"]) == 150
    assert doc.find(**{"data-factor-evidence": "partial"})
    assert "$9,450.00" in response.get_data(as_text=True)


def test_dashboard_data_is_stale_guarded(workspace):
    doc = Document(submit(workspace, **TERMS).get_data(as_text=True))
    for identifier in ("score-heading", "coverage-heading", "factor-heading", "assessment-heading", "insights-heading", "site-heading", "occupancy-heading"):
        node = doc.find(id=identifier)[0]
        assert any("data-analysis-output" in parent["attrs"] for parent in node["parents"])
    assert doc.find("section", **{"data-analysis-pending": None, "hidden": None})
    parcel_caution = doc.find(id="site-model-limitation")[0]
    assert "separate from Opportunity Score and Data Coverage" in parcel_caution["text"]
    assert not any(parent["tag"] == "details" for parent in parcel_caution["parents"])


def test_provider_failure_retains_geography_and_other_evidence(workspace):
    workspace[5].failure = PoiError("Competition unavailable")
    workspace[-1].results = [SiteError("network")]
    html = submit(workspace).get_data(as_text=True)
    doc = Document(html)
    assert doc.find("div", id="map-frame")[0]["attrs"].get("data-initial-location")
    assert doc.find(**{"data-factor-evidence": "real"})
    assert doc.find(**{"data-factor-evidence": "fallback"})
    assert "Live competition is unavailable" in html and "Site intelligence" in html


@pytest.mark.parametrize("path,mime", [
    ("/static/js/form-ui.js", "javascript"),
    ("/static/images/geospatial-field.svg", "image/svg+xml"),
])
def test_new_ui_assets_are_local_and_served(client, path, mime):
    response = client.get(path)
    assert response.status_code == 200 and mime in response.content_type
