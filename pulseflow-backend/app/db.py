"""SQLite storage. Only alerts are stored. Transcripts are never persisted (privacy by design)."""
import json
import sqlite3
import time
from contextlib import contextmanager

from . import config

SCHEMA = """
CREATE TABLE IF NOT EXISTS alerts(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  kind TEXT NOT NULL,
  severity TEXT NOT NULL,
  message TEXT NOT NULL,
  payload TEXT,
  status TEXT NOT NULL DEFAULT 'new',
  created_at REAL NOT NULL
);
"""


@contextmanager
def connect():
    c = sqlite3.connect(config.DB_PATH)
    c.row_factory = sqlite3.Row
    try:
        c.executescript(SCHEMA)
        yield c
        c.commit()
    finally:
        c.close()


def _row(r):
    d = dict(r)
    d["payload"] = json.loads(d["payload"]) if d.get("payload") else None
    return d


def add_alert(kind, severity, message, payload=None):
    data = json.dumps(payload, ensure_ascii=False) if payload is not None else None
    with connect() as c:
        cur = c.execute(
            "INSERT INTO alerts(kind,severity,message,payload,status,created_at) VALUES(?,?,?,?,'new',?)",
            (kind, severity, message, data, time.time()),
        )
        return _row(c.execute("SELECT * FROM alerts WHERE id=?", (cur.lastrowid,)).fetchone())


def list_alerts(limit=50):
    with connect() as c:
        rows = c.execute("SELECT * FROM alerts ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
        return [_row(r) for r in rows]


def recent_alert_exists(kind, within_seconds):
    with connect() as c:
        r = c.execute(
            "SELECT 1 FROM alerts WHERE kind=? AND created_at>? LIMIT 1",
            (kind, time.time() - within_seconds),
        ).fetchone()
        return r is not None


def set_alert_status(alert_id, status):
    with connect() as c:
        return c.execute("UPDATE alerts SET status=? WHERE id=?", (status, alert_id)).rowcount > 0
