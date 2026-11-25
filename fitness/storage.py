import csv
import io
import json
import logging
import sqlite3
from dataclasses import asdict
from pathlib import Path

from .config import DATA_FILE, DATABASE_FILE, FIELDS
from .models import Session
from .validation import validate

logger = logging.getLogger(__name__)


class Store:
    """SQLite session repository with JSON migration and CSV import support."""

    def __init__(self, path=None):
        self.path = Path(path) if path is not None else DATABASE_FILE
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()
        self._migrate_legacy_json()
        self.sessions = []
        self.load()

    def _connect(self):
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _initialize(self):
        with self._connect() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY,
                    date TEXT NOT NULL,
                    activity TEXT NOT NULL,
                    duration_min REAL NOT NULL CHECK(duration_min BETWEEN 1 AND 600),
                    distance_km REAL NOT NULL CHECK(distance_km BETWEEN 0 AND 200),
                    calories REAL NOT NULL CHECK(calories BETWEEN 0 AND 5000),
                    notes TEXT NOT NULL DEFAULT ''
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_sessions_date ON sessions(date)")
        logger.info("SQLite storage initialized at %s", self.path)

    def _migrate_legacy_json(self):
        legacy = DATA_FILE
        if self.path.exists() and self.path.stat().st_size > 0:
            return
        if not legacy.exists():
            return
        try:
            rows = json.loads(legacy.read_text(encoding="utf-8"))
            with self._connect() as conn:
                for row in rows:
                    clean = {key: row.get(key, "") for key in FIELDS}
                    conn.execute(
                        "INSERT OR IGNORE INTO sessions "
                        "(id,date,activity,duration_min,distance_km,calories,notes) "
                        "VALUES (:id,:date,:activity,:duration_min,:distance_km,:calories,:notes)",
                        clean,
                    )
            logger.info("Migrated %d legacy JSON records", len(rows))
        except (OSError, json.JSONDecodeError, TypeError, sqlite3.Error):
            logger.exception("Legacy JSON migration failed; original JSON retained")

    def load(self):
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT id,date,activity,duration_min,distance_km,calories,notes "
                "FROM sessions ORDER BY id"
            ).fetchall()
        self.sessions = [Session(**dict(row)) for row in rows]
        return self.sessions

    def save(self):
        """Persist the current in-memory collection atomically."""
        with self._connect() as conn:
            conn.execute("BEGIN")
            conn.execute("DELETE FROM sessions")
            conn.executemany(
                "INSERT INTO sessions "
                "(id,date,activity,duration_min,distance_km,calories,notes) "
                "VALUES (:id,:date,:activity,:duration_min,:distance_km,:calories,:notes)",
                [asdict(s) for s in self.sessions],
            )
        logger.info("Saved %d session records", len(self.sessions))

    def next_id(self):
        with self._connect() as conn:
            value = conn.execute("SELECT COALESCE(MAX(id), 0) + 1 FROM sessions").fetchone()[0]
        return int(value)

    def add(self, **values):
        session = Session(id=self.next_id(), **values)
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO sessions "
                "(id,date,activity,duration_min,distance_km,calories,notes) "
                "VALUES (?,?,?,?,?,?,?)",
                (session.id, session.date, session.activity, session.duration_min,
                 session.distance_km, session.calories, session.notes),
            )
        self.sessions.append(session)
        logger.info("Added session id=%s activity=%s", session.id, session.activity)
        return session

    def delete(self, ids):
        ids = {int(value) for value in ids}
        if not ids:
            return
        with self._connect() as conn:
            conn.executemany("DELETE FROM sessions WHERE id=?", [(value,) for value in ids])
        self.sessions = [s for s in self.sessions if s.id not in ids]
        logger.info("Deleted %d session(s)", len(ids))

    def import_csv(self, text):
        """Bulk import. Returns (imported_count, list_of_error_strings)."""
        ok, errors = 0, []
        reader = csv.DictReader(io.StringIO(text))
        required = {"date", "activity", "duration_min"}
        if not reader.fieldnames or not required.issubset(reader.fieldnames):
            return 0, [f"Header must contain at least: {', '.join(sorted(required))}"]
        for row_number, row in enumerate(reader, start=2):
            values, error = validate(
                row.get("date"), (row.get("activity") or "").strip().title(),
                row.get("duration_min"), row.get("distance_km"),
                row.get("calories"), row.get("notes"),
            )
            if error:
                errors.append(f"Row {row_number}: {error}")
                logger.warning("CSV import rejected row %d: %s", row_number, error)
                continue
            self.add(**values)
            ok += 1
        logger.info("CSV import completed: imported=%d rejected=%d", ok, len(errors))
        return ok, errors
