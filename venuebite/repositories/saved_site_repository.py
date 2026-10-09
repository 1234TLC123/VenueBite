"""Parameterized queries and normalized, validated snapshot serialization."""

from datetime import datetime, timezone

from venuebite.snapshots import SavedSite, SavedSiteList, SnapshotError, decode_snapshot, encode_snapshot, utc_timestamp


class SavedSiteRepository:
    def __init__(self, database):
        self.database = database

    def _record(self, row):
        snapshot = decode_snapshot(row["snapshot_json"])
        expected = {
            "analysis_id": snapshot["analysis"]["id"], "location_label": snapshot["location"]["label"],
            "restaurant_concept": snapshot["analysis"]["concept"], "search_radius_miles": snapshot["analysis"]["radius_miles"],
            "opportunity_score": snapshot["score"]["value"], "opportunity_classification": snapshot["score"]["classification"],
            "score_model_version": snapshot["score"]["model_version"], "data_coverage": snapshot["coverage"]["percent"],
            "coverage_label": snapshot["coverage"]["label"], "analysis_timestamp": snapshot["analysis"]["timestamp"],
            "snapshot_version": snapshot["snapshot_version"],
        }
        if any(row[key] != value for key, value in expected.items()):
            raise SnapshotError()
        utc_timestamp(row["created_at"])
        return SavedSite(row["id"], row["display_name"], row["created_at"], snapshot)

    def insert(self, display_name, snapshot):
        serialized = encode_snapshot(snapshot)
        location, analysis, score, coverage = (snapshot[key] for key in ("location", "analysis", "score", "coverage"))
        values = (analysis["id"], display_name, location["label"],
                  analysis["concept"], analysis["radius_miles"], score["value"], score["classification"],
                  score["model_version"], coverage["percent"], coverage["label"], analysis["timestamp"],
                  datetime.now(timezone.utc).isoformat(), snapshot["snapshot_version"], serialized)
        with self.database.connection() as connection:
            cursor = connection.execute("""
                INSERT INTO saved_sites (analysis_id, display_name, location_label,
                    restaurant_concept, search_radius_miles, opportunity_score, opportunity_classification,
                    score_model_version, data_coverage, coverage_label, analysis_timestamp, created_at,
                    snapshot_version, snapshot_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(analysis_id) DO NOTHING
            """, values)
            created = cursor.rowcount == 1
            row = connection.execute("SELECT * FROM saved_sites WHERE analysis_id = ?", (analysis["id"],)).fetchone()
        return self._record(row), created

    def get(self, site_id):
        with self.database.connection() as connection:
            row = connection.execute("SELECT * FROM saved_sites WHERE id = ?", (site_id,)).fetchone()
        return self._record(row) if row is not None else None

    def list(self):
        with self.database.connection() as connection:
            rows = connection.execute("SELECT * FROM saved_sites ORDER BY created_at DESC, id DESC").fetchall()
        sites, unreadable = [], 0
        for row in rows:
            try:
                sites.append(self._record(row))
            except SnapshotError:
                unreadable += 1
        return SavedSiteList(tuple(sites), unreadable)

    def delete(self, site_id):
        with self.database.connection() as connection:
            return connection.execute("DELETE FROM saved_sites WHERE id = ?", (site_id,)).rowcount == 1
