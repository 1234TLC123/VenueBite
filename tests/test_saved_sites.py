from copy import deepcopy
from datetime import datetime, timezone
from decimal import Decimal
from html.parser import HTMLParser
import json
import sqlite3

import pytest
from werkzeug.datastructures import MultiDict

from venuebite import create_app
from venuebite.db import Database, PersistenceError, SCHEMA
from venuebite.repositories.saved_site_repository import SavedSiteRepository
from venuebite.services.analysis_service import AnalysisService
from venuebite.services.saved_site_service import SaveError, build_snapshot, form_context
from venuebite.snapshots import SnapshotError, decode_snapshot, encode_snapshot
from venuebite.providers.demographic_provider import CensusError
from venuebite.providers.poi_provider import PoiError
from venuebite.providers.site_provider import SiteError
from test_demographic_integration import Geography, CensusGeography, Census, Pois
from test_occupancy import TERMS, candidate
from test_site_intelligence import LOCATION, PARCEL, Parcels


class Inputs(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.values = {}
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "input" and attrs.get("name"):
            self.values[attrs["name"]] = attrs.get("value", "")


@pytest.fixture
def saved_workspace(tmp_path):
    geo, tract, census, pois, parcels = Geography(), CensusGeography(), Census(), Pois(), Parcels(*[(PARCEL,)] * 20)
    geo.location = LOCATION
    app = create_app({"TESTING": True, "DATABASE": str(tmp_path / "saved.db"), "SECRET_KEY": "test-save-secret"},
                     location_provider=geo, census_geo_provider=tract, demographic_provider=census, poi_provider=pois, site_provider=parcels)
    return app, app.test_client(), (geo, tract, census, pois, parcels)


def completed(workspace, *, occupancy=False):
    app = workspace[0]
    values = form_context({"location": LOCATION.display_name, "concept": "Indian Restaurant", "radius_miles": "3",
                          "latitude": LOCATION.latitude, "longitude": LOCATION.longitude,
                          "selection_token": app.extensions["geography_service"].sign(LOCATION), **(TERMS if occupancy else {})})
    report = AnalysisService(app.extensions["location_data_provider"], app.extensions["competition_service"],
                             app.extensions["demographic_service"], app.extensions["site_intelligence_service"]).analyze(
        LOCATION.display_name, values["concept"], geographic_location=LOCATION, candidate_property=candidate() if occupancy else None)
    return values, report


def stored(workspace, name="Candidate", *, occupancy=False, changes=None):
    app = workspace[0]
    values, report = completed(workspace, occupancy=occupancy)
    snapshot = build_snapshot(report, LOCATION, values)
    snapshot["location"]["label"] = "Denver, Colorado"
    if changes:
        changes(snapshot)
    return app.extensions["saved_site_service"].repository.insert(name, snapshot)[0]


def save_form(workspace, *, occupancy=False):
    app, client = workspace[:2]
    response = client.post("/", data={"location": LOCATION.display_name, "concept": "Indian Restaurant", "radius_miles": "3",
        "selection_token": app.extensions["geography_service"].sign(LOCATION), **(TERMS if occupancy else {})})
    assert response.status_code == 200
    fields = Inputs(response.get_data(as_text=True)).values
    assert fields["snapshot_token"]
    return {**form_context(fields), **(TERMS if occupancy else {}), "snapshot_token": fields["snapshot_token"], "csrf_token": fields["csrf_token"],
            "display_name": "Denver candidate", "location_label": "Denver, Colorado"}


def test_repository_crud_order_idempotency_and_reconstruction(saved_workspace):
    service = saved_workspace[0].extensions["saved_site_service"]
    assert not service.list().sites
    a, b = stored(saved_workspace, "A"), stored(saved_workspace, "B")
    assert [s.id for s in service.list().sites] == [b.id, a.id]
    duplicate, created = service.repository.insert("Repeat", a.snapshot)
    assert duplicate == a and not created
    fresh = SavedSiteRepository(Database(service.repository.database.path))
    fresh.database.initialize()
    fresh.database.initialize()
    assert fresh.get(a.id) == a and len(fresh.list().sites) == 2
    assert fresh.delete(a.id) and not fresh.delete(a.id) and fresh.get(a.id) is None
    assert fresh.get(9999) is None


def test_completed_save_no_search_box_storage_and_exact_outputs(saved_workspace):
    app = saved_workspace[0]
    values, report = completed(saved_workspace, occupancy=True)
    service = app.extensions["saved_site_service"]
    token = service.prepare(report, LOCATION, values)
    site, created = service.save(token, "  Café - Candidate  ", values, location_label="  Denver, Colorado  ")
    assert created and site.display_name == "Café - Candidate"
    snapshot = site.snapshot
    assert snapshot["location"]["label"] == "Denver, Colorado"
    assert snapshot["snapshot_version"] == 2
    assert snapshot["score"]["value"] == report.score.overall_score
    assert snapshot["coverage"]["percent"] == 90
    assert snapshot["score"]["model_version"] == "2.0"
    assert [f["weight"] for f in snapshot["factors"]] == [.3, .3, .2, .2]
    assert snapshot["factors"][2]["status"] == "partial"
    assert snapshot["factors"][2]["contribution"] == pytest.approx(13.2)
    assert Decimal(snapshot["occupancy"]["monthly_known_total"]) == Decimal("9450")
    assert Decimal(snapshot["occupancy"]["monthly_base"]).quantize(Decimal(".01")) == Decimal("7466.67")
    assert Decimal(snapshot["occupancy"]["monthly_additional"]).quantize(Decimal(".01")) == Decimal("1983.33")
    assert Decimal(snapshot["occupancy"]["budget_utilization"]) == Decimal("94.5")
    assert snapshot["occupancy"]["property_address"] == ""
    assert snapshot["demographics"]["geoid"] and snapshot["demographics"]["vintage"] == 2024
    assert datetime.fromisoformat(snapshot["analysis"]["timestamp"]).tzinfo is not None
    serialized = encode_snapshot(snapshot)
    for forbidden in (LOCATION.display_name, LOCATION.provider_id if hasattr(LOCATION, "provider_id") else "test.site", "Live Indian kitchen", '"latitude"', '"longitude"', '"coordinates"', '"geometry"', '"features"'):
        assert forbidden not in serialized
    with service.repository.database.connection() as conn:
        columns = [r[1] for r in conn.execute("PRAGMA table_info(saved_sites)")]
        assert "latitude" not in columns and "longitude" not in columns


@pytest.mark.parametrize("field", ["location", "concept", "radius_miles", "latitude", "longitude", "selection_token", *TERMS, "property_address", "source_url", "source_label", "occupancy_notes"])
def test_every_analysis_input_change_rejects_stale_save(saved_workspace, field):
    app = saved_workspace[0]
    values, report = completed(saved_workspace)
    service = app.extensions["saved_site_service"]
    token = service.prepare(report, LOCATION, values)
    with pytest.raises(SaveError, match="stale"):
        service.save(token, "Candidate", {**values, field: values[field] + "changed"}, location_label="Denver")
    assert not service.list().sites


@pytest.mark.parametrize("name", ["", "  ", "x" * 141, "bad\x00name", "bad\nname"])
def test_name_validation(saved_workspace, name):
    values, report = completed(saved_workspace)
    service = saved_workspace[0].extensions["saved_site_service"]
    with pytest.raises(SaveError):
        service.save(service.prepare(report, LOCATION, values), name, values, location_label="Denver")


@pytest.mark.parametrize("label", ["", "   ", "x" * 201, "bad\x00label"])
def test_owned_location_label_required(saved_workspace, label):
    values, report = completed(saved_workspace)
    service = saved_workspace[0].extensions["saved_site_service"]
    with pytest.raises(SaveError):
        service.save(service.prepare(report, LOCATION, values), "Name", values, location_label=label)


@pytest.mark.parametrize("site_id", ["0", "-1", "1.0", "1 OR 1=1", "1; DROP TABLE saved_sites", "99999999999999999999999", "", True])
def test_invalid_ids_cannot_change_storage(saved_workspace, site_id):
    service = saved_workspace[0].extensions["saved_site_service"]
    site = stored(saved_workspace)
    for action in (service.get, service.delete):
        with pytest.raises(SaveError):
            action(site_id)
    assert service.get(site.id) == site


@pytest.mark.parametrize("mutate", [lambda s: s.update(raw_payload={}), lambda s: s["location"].update(latitude=39),
    lambda s: s["competition"].update(restaurants=[]), lambda s: s["score"].update(value=float("nan")),
    lambda s: s["factors"][0].update(score=True), lambda s: s.update(snapshot_version=999),
    lambda s: s["site"].update(source_url="javascript:alert(1)"), lambda s: s["occupancy"].update(monthly_known_total="Infinity"),
    lambda s: s["location"].update(provider="Mapbox"), lambda s: s["analysis"].update(timestamp="2026-10-07"),
    lambda s: s["factors"].pop(), lambda s: s["explanations"].update(risks=[{"raw": "response"}])])
def test_malformed_or_disallowed_snapshot_rejected(saved_workspace, mutate):
    snapshot = deepcopy(stored(saved_workspace).snapshot)
    mutate(snapshot)
    with pytest.raises(SnapshotError):
        encode_snapshot(snapshot)


@pytest.mark.parametrize("value", ["null", "[]", "{bad", '{"a":1,"a":2}', "x" * 70000, "NaN"], ids=["null", "array", "broken", "duplicate", "oversized", "nan"])
def test_unsafe_json_rejected(value):
    with pytest.raises(SnapshotError):
        decode_snapshot(value)


def test_corrupt_record_omitted_not_deleted(saved_workspace):
    service = saved_workspace[0].extensions["saved_site_service"]
    site = stored(saved_workspace)
    with service.repository.database.connection() as conn:
        conn.execute("UPDATE saved_sites SET snapshot_json = ? WHERE id = ?", ("{broken", site.id))
    assert service.list().unreadable_count == 1
    assert saved_workspace[1].get(f"/saved/{site.id}").status_code == 422
    assert service.delete(site.id)


@pytest.mark.parametrize("count", [2, 3, 4])
def test_comparison_count_order_no_mutation_and_render(saved_workspace, count):
    sites = [stored(saved_workspace, f"Candidate {i}") for i in range(count)]
    ids = [s.id for s in reversed(sites)]
    before = [deepcopy(s.snapshot) for s in sites]
    comparison = saved_workspace[0].extensions["comparison_service"].compare(ids)
    assert [s.id for s in comparison.sites] == ids
    assert [s.snapshot for s in sites] == before
    assert comparison.highlights and "tie for" in comparison.highlights[0]
    assert "choose" not in " ".join(comparison.highlights).lower()
    response = saved_workspace[1].get("/compare", query_string=MultiDict([("site_id", str(i)) for i in ids]))
    assert response.status_code == 200
    assert 'scope="row"' in response.text and 'data-comparison-evidence="real"' in response.text


@pytest.mark.parametrize("ids", [[], [1], [1, 2, 3, 4, 5], [1, 1], [1, "bad"], [1, 9999]])
def test_invalid_comparison(saved_workspace, ids):
    stored(saved_workspace)
    with pytest.raises(SaveError):
        saved_workspace[0].extensions["comparison_service"].compare(ids)


def test_evidence_missing_zero_and_partial_comparison(saved_workspace):
    a = stored(saved_workspace, "Partial", occupancy=True)
    def changes(s):
        s["demographics"]["population"] = None
        s["demographics"]["income"] = 0
        s["competition"]["nearest_direct_meters"] = None
        s["site"].update(status="not_found", area_acres=None, parcel_id="", parcel_number="")
    b = stored(saved_workspace, "Demo", changes=changes)
    comparison = saved_workspace[0].extensions["comparison_service"].compare([a.id, b.id])
    assert "Highest stored score" not in comparison.badges[a.id]
    assert "Highest Data Coverage" in comparison.badges[a.id]
    assert "not equally supported" in " ".join(comparison.highlights)
    rows = comparison.sections[0]["rows"]
    assert rows[0]["values"][1] == "Unavailable" and rows[1]["values"][1] == "$0.00"
    assert next(row for row in comparison.sections[-1]["rows"] if row["label"] == "Known monthly occupancy")["values"][1] == "Unknown total"


def test_occupancy_highlight_only_comparable_terms(saved_workspace):
    a = stored(saved_workspace, "A", occupancy=True)
    b = stored(saved_workspace, "B", occupancy=True, changes=lambda s: s["occupancy"].update(space_size_sqft="2800.0", monthly_known_total="10000"))
    result = saved_workspace[0].extensions["comparison_service"].compare([b.id, a.id])
    assert "Lowest known occupancy" in result.badges[a.id]
    c = stored(saved_workspace, "C", occupancy=True, changes=lambda s: s["occupancy"].update(space_size_sqft="3000"))
    result = saved_workspace[0].extensions["comparison_service"].compare([a.id, c.id])
    assert all("Lowest known occupancy" not in b for b in result.badges.values())


def test_model_context_and_evidence_rank_gates(saved_workspace):
    a = stored(saved_workspace, "A")
    b = stored(saved_workspace, "B", changes=lambda s: s["score"].update(model_version="future"))
    result = saved_workspace[0].extensions["comparison_service"].compare([a.id, b.id])
    assert all("Highest Data Coverage" not in badges for badges in result.badges.values())
    c = stored(saved_workspace, "C", changes=lambda s: s["analysis"].update(radius_miles=5))
    result = saved_workspace[0].extensions["comparison_service"].compare([a.id, c.id])
    assert all("Strongest competition factor" not in badges for badges in result.badges.values())


def test_save_routes_duplicate_and_html_sql_escaping(saved_workspace):
    client = saved_workspace[1]
    fields = save_form(saved_workspace, occupancy=True)
    fields["display_name"] = '<script>alert("x")</script>; DROP TABLE saved_sites;--'
    first = client.post("/saved", data=fields)
    assert first.status_code == 303
    second = client.post("/saved", data=fields)
    assert second.location == first.location
    html = client.get(first.location).text
    assert '<script>alert("x")</script>' not in html and "&lt;script&gt;" in html
    assert "SAVED SNAPSHOT" in html and "$9,450.00" in html and "Not retained" in html
    assert len(saved_workspace[0].extensions["saved_site_service"].list().sites) == 1


@pytest.mark.parametrize("change", [{"csrf_token": "bad"}, {"snapshot_token": "invalid"}, {"display_name": ""},
    {"location_label": ""}, {"concept": "Pizza"}])
def test_save_route_invalid(saved_workspace, change):
    fields = save_form(saved_workspace)
    assert saved_workspace[1].post("/saved", data={**fields, **change}).status_code == 400
    assert not saved_workspace[0].extensions["saved_site_service"].list().sites


def test_duplicate_fields_rejected(saved_workspace):
    fields = MultiDict(save_form(saved_workspace))
    fields.add("location_label", "Other")
    assert saved_workspace[1].post("/saved", data=fields).status_code == 400


def test_delete_confirmation_csrf_post_and_missing_selected(saved_workspace):
    service, client = saved_workspace[0].extensions["saved_site_service"], saved_workspace[1]
    a, b = stored(saved_workspace, "A"), stored(saved_workspace, "B")
    assert client.get(f"/saved/{a.id}/delete").status_code == 405
    assert client.post(f"/saved/{a.id}/delete", data={"confirm": "delete"}).status_code == 400
    form = Inputs(client.get(f"/saved/{a.id}/delete-confirmation").text).values
    assert service.get(a.id)
    assert client.post(f"/saved/{a.id}/delete", data=form).status_code == 303
    assert service.get(a.id) is None
    assert client.post(f"/saved/{a.id}/delete", data=form).status_code == 303
    assert client.get(f"/compare?site_id={a.id}&site_id={b.id}").status_code == 400
    assert client.get(f"/saved/{a.id}").status_code == 404
    assert client.get(f"/saved/{a.id}/delete-confirmation").status_code == 303


def test_no_provider_calls_browsing_reanalysis_or_mutations(saved_workspace):
    app, client, providers = saved_workspace
    form = save_form(saved_workspace)
    counts = [len(p.calls) for p in providers]
    a = client.post("/saved", data=form)
    b = stored(saved_workspace, "Second")
    counts = [len(p.calls) for p in providers]
    for path in ("/saved", a.location, f"/saved/{b.id}", f"/compare?site_id=1&site_id={b.id}", "/?saved_id=1"):
        response = client.get(path)
        assert response.status_code == 200
        if path.startswith(("/saved", "/compare")):
            assert "mapbox-gl.js" not in response.text and "data-initial-location=" not in response.text
        else:
            fields = Inputs(response.text).values
            assert fields["selection_token"] == "" and fields["latitude"] == "" and fields["longitude"] == ""
    assert [len(p.calls) for p in providers] == counts
    form = Inputs(client.get(f"/saved/{b.id}/delete-confirmation").text).values
    client.post(f"/saved/{b.id}/delete", data=form)
    assert [len(p.calls) for p in providers] == counts


def test_empty_single_and_invalid_routes(saved_workspace):
    client = saved_workspace[1]
    assert "No saved sites" in client.get("/saved").text
    assert client.get("/compare").status_code == 200
    stored(saved_workspace)
    assert "two" in client.get("/compare").text.lower()
    assert client.get("/saved/bad").status_code == 400
    assert client.get("/compare?site_id=1").status_code == 400
    assert client.get("/?saved_id=1&saved_id=2").status_code == 400


def test_database_errors_are_sanitized_and_temp_database_default(tmp_path):
    blocked = tmp_path / "file"
    blocked.touch()
    app = create_app({"TESTING": True, "DATABASE": str(blocked / "saved.db")})
    for path in ("/saved", "/saved/1", "/compare"):
        response = app.test_client().get(path)
        assert response.status_code == 503 and str(blocked) not in response.text and "Traceback" not in response.text
    assert app.test_cli_runner().invoke(args=["init-db"]).exit_code == 1
    isolated = create_app({"TESTING": True})
    assert "venuebite-test-" in isolated.config["DATABASE"]
    assert isolated.test_cli_runner().invoke(args=["init-db"]).exit_code == 0


def test_expired_tampered_and_secret_snapshots(saved_workspace, monkeypatch):
    values, report = completed(saved_workspace)
    service = saved_workspace[0].extensions["saved_site_service"]
    token = service.prepare(report, LOCATION, values)
    for invalid in ("", token + "tamper"):
        with pytest.raises(SaveError):
            service.save(invalid, "Name", values, location_label="Denver")
    monkeypatch.setattr("venuebite.services.saved_site_service.SAVE_TOKEN_AGE_SECONDS", -1)
    with pytest.raises(SaveError):
        service.save(token, "Name", values, location_label="Denver")
    with pytest.raises(SaveError, match="credential"):
        service.save(token, "test-save-secret", values, location_label="Denver")


def test_legacy_schema_migration_preserves_outputs_and_scrubs_geography(saved_workspace, tmp_path):
    old = deepcopy(stored(saved_workspace).snapshot)
    old.update(snapshot_version=1)
    old["location"] = {"label": LOCATION.display_name, "latitude": LOCATION.latitude, "longitude": LOCATION.longitude,
                       "provider": "Mapbox", "place_type": "address", "city": "", "region": "Colorado", "country": "us"}
    old["occupancy"]["property_address"] = LOCATION.display_name
    path = tmp_path / "legacy.db"
    conn = sqlite3.connect(path)
    conn.execute(SCHEMA.replace("restaurant_concept TEXT", "latitude REAL NOT NULL, longitude REAL NOT NULL, restaurant_concept TEXT"))
    conn.execute("PRAGMA user_version = 1")
    conn.execute("INSERT INTO saved_sites VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (7, old["analysis"]["id"], "User candidate", old["location"]["label"], LOCATION.latitude, LOCATION.longitude,
         old["analysis"]["concept"], 3, old["score"]["value"], old["score"]["classification"], "2.0", 80,
         old["coverage"]["label"], old["analysis"]["timestamp"], datetime.now(timezone.utc).isoformat(), 1, json.dumps(old)))
    conn.commit()
    conn.close()
    repo = SavedSiteRepository(Database(path))
    repo.database.initialize()
    repo.database.initialize()
    migrated = repo.get(7)
    assert migrated.display_name == "User candidate" and migrated.snapshot["score"] == old["score"]
    assert migrated.snapshot["factors"] == old["factors"] and migrated.snapshot["location"]["label"] == "Saved candidate"
    assert migrated.snapshot["occupancy"]["property_address"] == ""
    assert LOCATION.display_name.encode() not in path.read_bytes()


def test_unknown_schema_is_not_recreated(tmp_path):
    path = tmp_path / "future.db"
    with sqlite3.connect(path) as conn:
        conn.execute("CREATE TABLE keep_me (value TEXT)")
        conn.execute("INSERT INTO keep_me VALUES ('preserve')")
        conn.execute("PRAGMA user_version = 999")
    with pytest.raises(PersistenceError):
        Database(path).initialize()
    with sqlite3.connect(path) as conn:
        assert conn.execute("SELECT value FROM keep_me").fetchone()[0] == "preserve"


def test_v2_response_attribution_migration_preserves_every_fact(saved_workspace):
    service = saved_workspace[0].extensions["saved_site_service"]
    site = stored(saved_workspace)
    old = deepcopy(site.snapshot)
    old["competition"]["attribution"] = "temporary-search-response-attribution"
    with sqlite3.connect(service.repository.database.path) as conn:
        conn.execute("UPDATE saved_sites SET snapshot_json = ? WHERE id = ?", (json.dumps(old), site.id))
        conn.execute("PRAGMA user_version = 2")
    service.repository.database.initialize()
    assert service.get(site.id) == site
    assert b"temporary-search-response-attribution" not in service.repository.database.path.read_bytes()


def test_snapshot_date_normalizes_timezone(saved_workspace):
    assert "18:00 UTC" in saved_workspace[0].jinja_env.filters["snapshot_date"]("2026-10-07T12:00:00-06:00")


@pytest.mark.parametrize("failed", ["census", "competition", "parcel", "all"])
def test_provider_failure_snapshots_keep_missing_and_fallback_semantics(saved_workspace, failed):
    geo, tract, census, pois, parcels = saved_workspace[2]
    if failed in ("census", "all"):
        census.failure = CensusError("network")
    if failed in ("competition", "all"):
        pois.failure = PoiError("Network unavailable")
    if failed in ("parcel", "all"):
        parcels.results = [SiteError("network")]
    site = stored(saved_workspace)
    if failed in ("census", "all"):
        assert site.snapshot["demographics"]["population"] is None and site.snapshot["factors"][0]["status"] == "fallback"
    if failed in ("competition", "all"):
        assert site.snapshot["competition"]["observed_count"] is None and site.snapshot["factors"][3]["status"] == "fallback"
    if failed in ("parcel", "all"):
        assert site.snapshot["site"]["status"] == "unavailable" and site.snapshot["site"]["area_acres"] is None
    assert saved_workspace[1].get(f"/saved/{site.id}").status_code == 200


@pytest.mark.parametrize("action", ["insert", "delete"])
def test_failed_mutation_is_sanitized(saved_workspace, monkeypatch, action):
    service, client = saved_workspace[0].extensions["saved_site_service"], saved_workspace[1]
    def fail(*args):
        raise PersistenceError()
    if action == "insert":
        fields = save_form(saved_workspace)
        monkeypatch.setattr(service.repository, "insert", fail)
        response = client.post("/saved", data=fields)
    else:
        site = stored(saved_workspace)
        fields = Inputs(client.get(f"/saved/{site.id}/delete-confirmation").text).values
        monkeypatch.setattr(service.repository, "delete", fail)
        response = client.post(f"/saved/{site.id}/delete", data=fields)
    assert response.status_code == 503 and "Traceback" not in response.text


def test_safe_user_source_url_and_address_are_retained(saved_workspace):
    values, report = completed(saved_workspace, occupancy=True)
    values.update(property_address="User storefront", source_url="https://example.com/lease", source_label="Broker quote")
    service = saved_workspace[0].extensions["saved_site_service"]
    snapshot = build_snapshot(report, LOCATION, values)
    snapshot["occupancy"].update(source_url=values["source_url"], property_address=values["property_address"])
    site = service.repository.insert("User terms", snapshot)[0]
    html = saved_workspace[1].get(f"/saved/{site.id}").text
    assert 'href="https://example.com/lease"' in html and 'rel="noopener noreferrer"' in html
    assert site.snapshot["occupancy"]["property_address"] == "User storefront" and "User storefront" in html
