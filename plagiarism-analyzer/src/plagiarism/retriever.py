"""Given query fingerprints, find candidate source documents in the DB."""
from __future__ import annotations

from collections import defaultdict

from . import alignment, config, fingerprints, preprocessing, winnowing


def candidates(conn, query_fps: list[winnowing.Fingerprint]) -> dict[int, list[dict]]:
    """Return {doc_id: [{fp_hash, token_start, token_end}, ...]} of shared fingerprints."""
    if not query_fps:
        return {}
    hashes = list({fp.hash for fp in query_fps})
    placeholders = ",".join("?" * len(hashes))
    rows = conn.execute(
        f"SELECT doc_id, fp_hash, token_start, token_end "
        f"FROM fingerprints WHERE fp_hash IN ({placeholders})",
        hashes,
    ).fetchall()

    grouped: dict[int, list[dict]] = defaultdict(list)
    for r in rows:
        grouped[r["doc_id"]].append({
            "fp_hash": r["fp_hash"],
            "token_start": r["token_start"],
            "token_end": r["token_end"],
        })
    return dict(grouped)


def fingerprint_text(text: str, k: int = config.K, w: int = config.WINNOW_W):
    """Convenience: text -> tokens -> k-grams -> winnowed fingerprints."""
    tokens = preprocessing.tokenize(text)
    grams = fingerprints.build(tokens, k=k)
    return winnowing.select(grams, w=w)


def query_file(conn, path) -> dict:
    """High-level: read file, fingerprint, retrieve, align, rank candidates."""
    from . import io_utils
    text = io_utils.read_text(path)
    tokens = preprocessing.tokenize(text)
    fps = winnowing.select(fingerprints.build(tokens))
    grouped = candidates(conn, fps)

    ranked = []
    for doc_id, hits in grouped.items():
        row = conn.execute("SELECT path FROM documents WHERE id = ?", (doc_id,)).fetchone()

        # Align shared fingerprints into contiguous passages
        spans = alignment.align_matches(fps, hits)

        # Merge covered token positions and compute coverage
        covered = set()
        for s in spans:
            for w in range(s.query_start, s.query_end + 1):
                covered.add(w)
        coverage = (len(covered) / len(tokens) * 100.0) if tokens else 0.0

        ranked.append({
            "doc_id": doc_id,
            "path": row["path"] if row else None,
            "shared_fingerprints": len(hits),
            "coverage_percent": round(coverage, 1),
            "matched_spans": [
                {"query": [s.query_start, s.query_end],
                 "source": [s.source_start, s.source_end]}
                for s in spans
            ],
        })

    ranked.sort(key=lambda r: r["coverage_percent"], reverse=True)
    return {
        "query_path": str(path),
        "query_fingerprints": len(fps),
        "candidates": ranked,
    }
