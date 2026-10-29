"""SQLite schema and connection helpers. Single source of truth for storage."""
from __future__ import annotations

import sqlite3
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS documents (
    id          INTEGER PRIMARY KEY,
    path        TEXT NOT NULL UNIQUE,
    sha256      TEXT NOT NULL,
    word_count  INTEGER NOT NULL,
    char_count  INTEGER NOT NULL,
    indexed_at  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS fingerprints (
    doc_id      INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    fp_hash     INTEGER NOT NULL,
    token_start INTEGER NOT NULL,
    token_end   INTEGER NOT NULL,
    PRIMARY KEY (doc_id, fp_hash, token_start)
);

CREATE INDEX IF NOT EXISTS idx_fp_hash ON fingerprints(fp_hash);
CREATE INDEX IF NOT EXISTS idx_fp_doc  ON fingerprints(doc_id);
"""


def connect(db_path: Path | str) -> sqlite3.Connection:
    """Open (or create) the DB, ensure schema, enable FK cascade."""
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(SCHEMA)
    return conn


def is_initialized(db_path: Path | str) -> bool:
    if not Path(db_path).exists():
        return False
    conn = sqlite3.connect(str(db_path))
    try:
        row = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='documents'"
        ).fetchone()
        return row is not None
    finally:
        conn.close()