"""Read a corpus directory, fingerprint each file, write to SQLite."""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from . import config, db, fingerprints, io_utils, preprocessing, winnowing


def index_corpus(conn, corpus_dir: Path, k: int = config.K, w: int = config.WINNOW_W) -> dict:
    """Index every *.txt file in `corpus_dir`. Idempotent on path+content."""
    stats = {"indexed": 0, "skipped": 0, "empty": 0}
    for path in sorted(corpus_dir.glob("*.txt")):
        text = io_utils.read_text(path)
        sha = io_utils.sha256_of(text)

        existing = conn.execute(
            "SELECT id, sha256 FROM documents WHERE path = ?", (str(path),)
        ).fetchone()
        if existing is not None:
            if existing["sha256"] == sha:
                stats["skipped"] += 1
                continue
            # Content changed on disk: drop old fingerprints, re-index below.
            conn.execute("DELETE FROM documents WHERE id = ?", (existing["id"],))

        tokens = preprocessing.tokenize(text)
        if not tokens:
            stats["empty"] += 1
            continue

        grams = fingerprints.build(tokens, k=k)
        fps = winnowing.select(grams, w=w)

        now = datetime.now(timezone.utc).isoformat(timespec="seconds")
        cur = conn.execute(
            "INSERT INTO documents (path, sha256, word_count, char_count, indexed_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (str(path), sha, len(tokens), len(text), now),
        )
        doc_id = cur.lastrowid

        if fps:
            conn.executemany(
                "INSERT OR IGNORE INTO fingerprints "
                "(doc_id, fp_hash, token_start, token_end) VALUES (?, ?, ?, ?)",
                [(doc_id, fp.hash, fp.token_start, fp.token_end) for fp in fps],
            )
        stats["indexed"] += 1

    conn.commit()
    return stats


def delete_document(conn, doc_id: int) -> None:
    conn.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
    conn.commit()


def list_documents(conn) -> list[dict]:
    rows = conn.execute(
        "SELECT id, path, word_count, char_count, indexed_at FROM documents ORDER BY id"
    ).fetchall()
    return [dict(r) for r in rows]


def fingerprint_count(conn, doc_id: int) -> int:
    row = conn.execute(
        "SELECT COUNT(*) AS c FROM fingerprints WHERE doc_id = ?", (doc_id,)
    ).fetchone()
    return int(row["c"])