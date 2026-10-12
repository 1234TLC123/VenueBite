from copy import deepcopy
from dataclasses import replace
from decimal import Decimal
import json
import sqlite3

import pytest
from werkzeug.datastructures import MultiDict

from venuebite import create_app
from venuebite.providers.zoning_provider import ZoningLookup, ZoningRecord
from venuebite.regulatory import PROJECT_FIELDS
from venuebite.services.analysis_service import AnalysisService
from venuebite.services.saved_site_service import SaveError, build_snapshot, form_context
from venuebite.snapshots import SnapshotError, encode_snapshot
from test_demographic_integration import Geography, CensusGeography, Census, Pois
from test_occupancy import TERMS, candidate
from test_regulatory import Zoning, STAMP
from test_saved_sites import Inputs
from test_site_intelligence import LOCATION, PARCEL, Parcels


@pytest.fixture
def regulatory_workspace(tmp_path):
    providers = Geography(), CensusGeography(), Census(), Pois(), Parcels(*[(PARCEL,)] * 40), Zoning()
    providers[0].location = LOCATION
    config = {"TESTING": True, "SECRET_KEY": "regulatory-test-secret", "DATABASE": str(tmp_path / "regulatory.db")}
    return configured(config, providers), providers, config


def configured(config, providers):
    geo, tract, census, pois, parcels, zoning = providers
    return create_app(config, location_provider=geo, census_geo_provider=tract, demographic_provider=census,
                      poi_provider=pois, site_provider=parcels, zoning_provider=zoning)


def values(app, *, occupancy=False):
    return form_context({"location": LOCATION.display_name, "concept": "Indian Restaurant", "radius_miles": "3",
        "latitude": LOCATION.latitude, "longitude": LOCATION.longitude,
        "selection_token": app.extensions["geography_service"].sign(LOCATION),
        "regulatory_type": "full_service", "regulatory_alcohol": "yes", "regulatory_outdoor_seating": "yes",
        "regulatory_drive_through": "no", **(TERMS if occupancy else {})})


def analysis(app, *, regulatory=True, occupancy=False):
    return AnalysisService(app.extensions["location_data_provider"], app.extensions["competition_service"],
        app.extensions["demographic_service"], app.extensions["site_intelligence_service"],
        app.extensions["regulatory_service"] if regulatory else None).analyze(
        LOCATION.display_name, "Indian Restaurant", geographic_location=LOCATION,
        candidate_property=candidate() if occupancy else None, regulatory_project=values(app))


def stored(app, *, regulatory=True, occupancy=False, name="Regulatory candidate"):
    snapshot = build_snapshot(analysis(app, regulatory=regulatory, occupancy=occupancy), LOCATION, values(app, occupancy=occupancy))
    snapshot["location"]["label"] = "User-entered Denver candidate"
    return app.extensions["saved_site_service"].repository.insert(name, snapshot)[0]


def save_form(app, client, *, occupancy=False):
    inputs = values(app, occupancy=occupancy)
    response = client.post("/", data=inputs)
    assert response.status_code == 200 and "Official use review required" in response.text
    hidden = Inputs(response.text).values
    return {**inputs, **{key: hidden[key] for key in ("snapshot_token", "csrf_token")},
            "display_name": "Regulatory candidate", "location_label": "User-entered Denver candidate"}


@pytest.mark.parametrize("status", ["identified", "unsupported", "unavailable", "ambiguous", "no_match"])
@pytest.mark.parametrize("occupancy", [False, True])
def test_regulatory_never_changes_score_coverage_trace_or_explanations(regulatory_workspace, status, occupancy):
    app, providers, _ = regulatory_workspace
    baseline = analysis(app, regulatory=False, occupancy=occupancy)
    providers[-1].result = ZoningLookup(status, STAMP, "City and County of Denver", "08031",
        ZoningRecord("PUD-99", code_family=1959) if status == "identified" else None)
    result = analysis(app, occupancy=occupancy)
    for field in ("score", "coverage", "scoring_trace", "explanations", "provenance", "occupancy"):
        assert getattr(result, field) == getattr(baseline, field)
    assert result.coverage.percent == (90 if occupancy else 80)
    assert [f.weight for f in result.score.factors] == [.3, .3, .2, .2]


def test_route_shows_official_evidence_alongside_prior_features(regulatory_workspace):
    app, providers, _ = regulatory_workspace
    response = app.test_client().post("/", data=values(app, occupancy=True))
    assert response.status_code == 200
    for text in ('data-regulatory-status="use_review_required"', 'id="regulatory-heading"', "D-CV", "Denver Zoning Code",
                 "Restaurant-use permission not yet verified", "Verified official fact", "Needs official confirmation",
                 "Government guidance", "User supplied", "$9,450.00", 'data-competition=', 'data-initial-location=', 'data-site-status="exact"'):
        assert text in response.text
    assert not providers[0].calls and len(providers[-1].calls) == 1
    assert response.headers["Cache-Control"] == "no-store"


def test_failure_is_local_and_sanitized(regulatory_workspace, caplog):
    app, providers, _ = regulatory_workspace
    providers[-1].result = RuntimeError("synthetic-private-provider-body")
    response = app.test_client().post("/", data=values(app))
    assert response.status_code == 200 and 'data-regulatory-status="unavailable"' in response.text
    assert 'data-census-status="available"' in response.text and 'data-competition=' in response.text
    assert 'data-site-status="exact"' in response.text
    assert "synthetic-private" not in response.text + caplog.text


@pytest.mark.parametrize("field", PROJECT_FIELDS)
@pytest.mark.parametrize("duplicate", [False, True])
def test_invalid_project_form_precedes_every_provider(regulatory_workspace, field, duplicate):
    app, providers, _ = regulatory_workspace
    form = MultiDict(values(app))
    if duplicate: form.add(field, "yes")
    else: form[field] = "<script>"
    response = app.test_client().post("/", data=form)
    assert response.status_code == 400 and "Choose one supported project option" in response.text
    assert all(not p.calls for p in providers)


def test_get_and_explicit_demo_never_request_zoning(regulatory_workspace):
    app, providers, _ = regulatory_workspace
    client = app.test_client()
    assert client.get("/").status_code == 200
    response = client.post("/", data={**values(app), "demo_only": "1"})
    assert response.status_code == 200 and 'data-regulatory-status="unknown"' in response.text
    assert not providers[-1].calls


@pytest.mark.parametrize("field", PROJECT_FIELDS)
def test_project_edit_rejects_stale_save(regulatory_workspace, field):
    app = regulatory_workspace[0]
    form = values(app)
    service = app.extensions["saved_site_service"]
    token = service.prepare(analysis(app), LOCATION, form)
    changed = "quick_service" if field == "regulatory_type" else "no" if form[field] == "yes" else "yes"
    with pytest.raises(SaveError, match="stale"):
        service.save(token, "Candidate", {**form, field: changed}, location_label="Denver")
    assert not service.list().sites


def test_saved_snapshot_persists_normalized_regulatory_and_partial_occupancy(regulatory_workspace):
    app = regulatory_workspace[0]
    client = app.test_client()
    form = save_form(app, client, occupancy=True)
    response = client.post("/saved", data=form)
    assert response.status_code == 303
    site = app.extensions["saved_site_service"].list().sites[0]
    snapshot = site.snapshot
    assert snapshot["snapshot_version"] == 3 and snapshot["regulatory"]["retrieved_at"] == STAMP
    assert snapshot["regulatory"]["project"]["alcohol"] == "yes"
    assert Decimal(snapshot["occupancy"]["monthly_known_total"]) == Decimal("9450")
    assert snapshot["coverage"]["percent"] == 90 and snapshot["factors"][2]["status"] == "partial"
    encoded = encode_snapshot(snapshot)
    for forbidden in ('"coordinates"', '"latitude"', '"longitude"', '"geometry"', '"features"', '"mapbox_id"',
                      "test.site", "Live Indian kitchen", "regulatory-test-secret", LOCATION.display_name):
        assert forbidden not in encoded
    assert "Retrieved" in client.get(response.location).text
    prefill = app.extensions["saved_site_service"].prefill(site)
    assert all(prefill.get(key, "") == "" for key in ("selection_token", "latitude", "longitude"))
    assert prefill["regulatory_alcohol"] == "yes"


def test_legacy_and_current_survive_reconstruction_without_provider_calls(regulatory_workspace, monkeypatch):
    app, providers, config = regulatory_workspace
    old, new = stored(app, regulatory=False, name="Legacy"), stored(app, occupancy=True)
    old_bytes = encode_snapshot(old.snapshot)
    counts = [len(p.calls) for p in providers]
    def fail(*args, **kwargs): raise AssertionError("History must not request providers or recalculate")
    for provider in providers:
        for method in ("forward", "lookup", "fetch", "search"):
            if hasattr(provider, method): monkeypatch.setattr(provider, method, fail)
    monkeypatch.setattr(AnalysisService, "analyze", fail)
    restarted = configured(config, providers)
    client = restarted.test_client()
    for path in ("/saved", f"/saved/{old.id}", f"/saved/{new.id}", f"/compare?site_id={old.id}&site_id={new.id}", f"/?saved_id={new.id}"):
        response = client.get(path)
        assert response.status_code == 200
        if path.startswith(("/saved", "/compare")):
            assert "mapbox-gl.js" not in response.text
    comparison = restarted.extensions["comparison_service"].compare([old.id, new.id])
    rows = next(s for s in comparison.sections if s["label"] == "Zoning & regulatory feasibility")["rows"]
    assert "Not captured in this snapshot" in rows[0]["values"][0]
    assert "Official use review required" in rows[0]["values"][1]
    sources = next(row for row in rows if row["label"] == "Official GIS sources")["values"][1]
    assert "ODC_ENG_SRVCCDBOUNDARY_A" in sources and "ODC_ZONE_ZONING_A" in sources
    assert all("zoning" not in badge.lower() and "regulatory" not in badge.lower() for badges in comparison.badges.values() for badge in badges)
    assert [len(p.calls) for p in providers] == counts
    assert encode_snapshot(restarted.extensions["saved_site_service"].get(old.id).snapshot) == old_bytes
    with sqlite3.connect(config["DATABASE"]) as conn:
        assert conn.execute("PRAGMA user_version").fetchone()[0] == 3
        assert [r[0] for r in conn.execute("SELECT snapshot_version FROM saved_sites ORDER BY id")] == [2, 3]


@pytest.mark.parametrize("mutate", [lambda r: r.update(geometry={}), lambda r: r.update(raw_payload={}),
    lambda r: r["sources"][0].update(url="javascript:alert(1)"), lambda r: r["sources"][0].update(retrieved_at="bad"),
    lambda r: r["sources"][0].update(verified_at="2026-99-99"), lambda r: r.update(effective_date="today"),
    lambda r: r["project"].update(alcohol=[]), lambda r: r.update(status={})])
def test_unsafe_persisted_regulatory_is_unreadable_not_deleted(regulatory_workspace, mutate):
    app, _, config = regulatory_workspace
    site = stored(app)
    snapshot = deepcopy(site.snapshot)
    mutate(snapshot["regulatory"])
    with pytest.raises(SnapshotError): encode_snapshot(snapshot)
    with sqlite3.connect(config["DATABASE"]) as conn:
        conn.execute("UPDATE saved_sites SET snapshot_json = ? WHERE id = ?", (json.dumps(snapshot), site.id))
    assert app.test_client().get(f"/saved/{site.id}").status_code == 422
    assert app.extensions["saved_site_service"].list().unreadable_count == 1


def test_official_field_text_is_escaped_live_and_saved(regulatory_workspace):
    app, providers, _ = regulatory_workspace
    providers[-1].result = replace(providers[-1].result, record=ZoningRecord('<script>alert("x")</script>', code_family=2010))
    live = app.test_client().post("/", data=values(app)).text
    saved = app.test_client().get(f"/saved/{stored(app).id}").text
    for html in (live, saved):
        assert '<script>alert("x")</script>' not in html and "&lt;script&gt;" in html


def test_testing_defaults_disable_network_zoning():
    app = create_app({"TESTING": True})
    assert not app.extensions["regulatory_service"].provider.enabled


@pytest.mark.parametrize("status", ["unsupported", "unavailable", "ambiguous", "no_match", "unknown"])
def test_nonidentified_states_are_saved_without_becoming_negative_facts(regulatory_workspace, status):
    app, providers, _ = regulatory_workspace
    providers[-1].result = ZoningLookup(status, STAMP)
    site = stored(app)
    saved = app.extensions["saved_site_service"].get(site.id)
    assert saved.snapshot["regulatory"]["status"] == status
    assert saved.snapshot["regulatory"]["district"] == "" and saved.snapshot["regulatory"]["checklist"] == []
    assert app.test_client().get(f"/saved/{site.id}").status_code == 200
