"""SQLite persistence. One connection per operation; durable file on a mounted volume."""
import json
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

SCHEMA = """
CREATE TABLE IF NOT EXISTS schema_version (version INTEGER PRIMARY KEY);
INSERT OR IGNORE INTO schema_version VALUES (1);
CREATE TABLE IF NOT EXISTS drafts (
 id TEXT PRIMARY KEY, owner TEXT NOT NULL, name TEXT NOT NULL,
 payload TEXT NOT NULL, created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS drafts_owner ON drafts(owner, created_at);
CREATE TABLE IF NOT EXISTS onetricks_observations (
 id TEXT PRIMARY KEY, champion TEXT NOT NULL, opponent TEXT NOT NULL,
 observed_at TEXT NOT NULL, payload TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS onetricks_pair ON onetricks_observations(champion, opponent, observed_at);
"""

@contextmanager
def connection():
    path = Path(os.getenv("DATABASE_PATH", str(Path(__file__).resolve().parents[2] / ".data" / "draftwise.sqlite3")))
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, timeout=10)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=10000")
        conn.executescript(SCHEMA)
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def save_draft(owner, name, payload):
    identifier, now = str(uuid4()), datetime.now(timezone.utc).isoformat()
    with connection() as conn:
        if conn.execute("SELECT COUNT(*) FROM drafts WHERE owner=?", (owner,)).fetchone()[0] >= 50:
            raise ValueError("You have 50 saved drafts. Delete one before saving another.")
        conn.execute("INSERT INTO drafts VALUES (?,?,?,?,?)", (identifier, owner, name, json.dumps(payload), now))
    return {"id": identifier, "name": name, "draft": payload, "createdAt": now}

def list_drafts(owner):
    with connection() as conn:
        rows = conn.execute("SELECT * FROM drafts WHERE owner=? ORDER BY created_at DESC LIMIT 50", (owner,)).fetchall()
    return [{"id":r["id"], "name":r["name"], "draft":json.loads(r["payload"]), "createdAt":r["created_at"]} for r in rows]

def delete_draft(owner, identifier):
    with connection() as conn:
        return conn.execute("DELETE FROM drafts WHERE id=? AND owner=?", (identifier, owner)).rowcount > 0

def import_observations(records):
    # Validation happens before this call; the entire batch commits atomically.
    import hashlib
    with connection() as conn:
        for record in records:
            payload = json.dumps(record, sort_keys=True)
            identifier = hashlib.sha256(payload.encode()).hexdigest()
            conn.execute("INSERT OR IGNORE INTO onetricks_observations VALUES (?,?,?,?,?)", (identifier, record["champion"], record["opponent"], record["observedAt"], payload))

def observations_for(champion, opponent):
    with connection() as conn:
        rows = conn.execute("SELECT payload FROM onetricks_observations WHERE champion=? AND opponent=? ORDER BY observed_at DESC, id DESC LIMIT 20", (champion, opponent)).fetchall()
    return [json.loads(r["payload"]) for r in rows]
