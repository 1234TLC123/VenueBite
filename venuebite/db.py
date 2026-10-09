"""Small, non-destructive SQLite boundary for local saved analyses."""

from contextlib import contextmanager
import logging
from pathlib import Path
import sqlite3
from venuebite.snapshots import SnapshotError, encode_snapshot, migrate_legacy_snapshot, migrate_source_note


SCHEMA_VERSION = 3
logger = logging.getLogger(__name__)
SCHEMA = """
CREATE TABLE IF NOT EXISTS saved_sites (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    analysis_id TEXT NOT NULL UNIQUE,
    display_name TEXT NOT NULL CHECK(length(display_name) BETWEEN 1 AND 140),
    location_label TEXT NOT NULL,
    restaurant_concept TEXT NOT NULL,
    search_radius_miles INTEGER NOT NULL CHECK(search_radius_miles IN (1, 3, 5)),
    opportunity_score REAL NOT NULL CHECK(opportunity_score BETWEEN 0 AND 100),
    opportunity_classification TEXT NOT NULL,
    score_model_version TEXT NOT NULL,
    data_coverage REAL NOT NULL CHECK(data_coverage BETWEEN 0 AND 100),
    coverage_label TEXT NOT NULL,
    analysis_timestamp TEXT NOT NULL,
    created_at TEXT NOT NULL,
    snapshot_version INTEGER NOT NULL,
    snapshot_json TEXT NOT NULL
);
"""
INDEX = "CREATE INDEX IF NOT EXISTS saved_sites_created ON saved_sites(created_at DESC, id DESC)"


class PersistenceError(Exception):
    def __init__(self):
        super().__init__("Saved Sites is temporarily unavailable. Please try again.")


class Database:
    def __init__(self, path):
        self.path = Path(path)

    @contextmanager
    def connection(self):
        connection = None
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            connection = sqlite3.connect(self.path, timeout=5)
            connection.row_factory = sqlite3.Row
            connection.execute("PRAGMA secure_delete = ON")
            version = connection.execute("PRAGMA user_version").fetchone()[0]
            if version not in (0, 1, 2, SCHEMA_VERSION):
                raise PersistenceError()
            if version == 1:
                self._migrate(connection)
                connection.execute("VACUUM")
            elif version == 2:
                self._migrate_source_note(connection)
                connection.execute("VACUUM")
            with connection:
                connection.execute(SCHEMA)
                connection.execute(INDEX)
                connection.execute("PRAGMA user_version = 3")
            with connection:
                yield connection
        except (OSError, sqlite3.Error):
            logger.warning("Saved-site storage unavailable; database operation failed")
            raise PersistenceError() from None
        finally:
            if connection is not None:
                connection.close()

    def initialize(self):
        with self.connection():
            pass

    def _migrate(self, connection):
        try:
            # Transactionally replace only the schema; preserve every saved analysis.
            connection.execute("BEGIN IMMEDIATE")
            rows = connection.execute("SELECT * FROM saved_sites").fetchall()
            connection.execute("ALTER TABLE saved_sites RENAME TO saved_sites_v1")
            connection.execute("DROP INDEX IF EXISTS saved_sites_created")
            connection.execute(SCHEMA)
            for row in rows:
                snapshot = migrate_legacy_snapshot(row["snapshot_json"])
                connection.execute("""INSERT INTO saved_sites (id, analysis_id, display_name, location_label,
                    restaurant_concept, search_radius_miles, opportunity_score, opportunity_classification,
                    score_model_version, data_coverage, coverage_label, analysis_timestamp, created_at,
                    snapshot_version, snapshot_json) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (row["id"], row["analysis_id"], row["display_name"], snapshot["location"]["label"],
                     row["restaurant_concept"], row["search_radius_miles"], row["opportunity_score"], row["opportunity_classification"],
                     row["score_model_version"], row["data_coverage"], row["coverage_label"], row["analysis_timestamp"], row["created_at"],
                     snapshot["snapshot_version"], encode_snapshot(snapshot)))
            connection.execute("DROP TABLE saved_sites_v1")
            connection.execute(INDEX)
            connection.execute("PRAGMA user_version = 3")
            connection.commit()
        except (sqlite3.Error, SnapshotError):
            connection.rollback()
            logger.warning("Saved-site schema migration could not be completed; existing records preserved")
            raise PersistenceError() from None

    def _migrate_source_note(self, connection):
        try:
            with connection:
                for row in connection.execute("SELECT id, snapshot_json FROM saved_sites").fetchall():
                    snapshot = migrate_source_note(row["snapshot_json"])
                    connection.execute("UPDATE saved_sites SET snapshot_json = ? WHERE id = ?", (encode_snapshot(snapshot), row["id"]))
                connection.execute("PRAGMA user_version = 3")
        except (ValueError, TypeError, KeyError, sqlite3.Error):
            logger.warning("Saved-site metadata migration failed; existing records preserved")
            raise PersistenceError() from None
