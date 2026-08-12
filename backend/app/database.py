"""
Thin SQLite persistence layer.

Design choice: raw sqlite3 instead of an ORM (SQLAlchemy, etc).
For a single-user, single-table-ish app like this, an ORM adds a layer of
indirection with no real payoff -- the queries are simple enough to write
and read directly, and it keeps the dependency footprint small. If this
grew multi-user / multi-table with real relations, I'd reach for SQLAlchemy
+ Alembic migrations instead of hand-rolled schema management.

Vectors are stored as JSON-encoded float lists in a TEXT column. That's fine
at this scale (see README "what breaks at scale") -- a real deployment would
use a proper vector index (pgvector, FAISS, Qdrant, etc).
"""
import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Iterator

from app.config import settings

SCHEMA = """
CREATE TABLE IF NOT EXISTS items (
    id TEXT PRIMARY KEY,
    source_type TEXT NOT NULL CHECK(source_type IN ('note', 'url')),
    source_url TEXT,
    title TEXT,
    raw_content TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS chunks (
    id TEXT PRIMARY KEY,
    item_id TEXT NOT NULL REFERENCES items(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    embedding TEXT,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_chunks_item_id ON chunks(item_id);
"""


def get_db_path() -> str:
    return settings.database_path


def init_db() -> None:
    with get_connection() as conn:
        conn.executescript(SCHEMA)
        conn.commit()


@contextmanager
def get_connection() -> Iterator[sqlite3.Connection]:
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
    finally:
        conn.close()


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def encode_embedding(vector: list[float]) -> str:
    return json.dumps(vector)


def decode_embedding(raw: str | None) -> list[float]:
    if not raw:
        return []
    return json.loads(raw)
