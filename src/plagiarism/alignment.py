"""Align shared fingerprints into contiguous matching passages."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MatchedSpan:
    query_start: int
    query_end: int
    source_start: int
    source_end: int
    fingerprint_count: int


def align_matches(query_fps, source_hits) -> list[MatchedSpan]:
    """
    Given query fingerprints and DB hits from one source document,
    group consecutive matches into contiguous passages.
    """
    if not query_fps or not source_hits:
        return []

    # Map source hash -> list of token_start positions in the source doc
    source_map: dict[int, list[int]] = {}
    for hit in source_hits:
        source_map.setdefault(hit["fp_hash"], []).append(hit["token_start"])

    # Build one raw match per (query position, source position) pair
    matches: list[dict] = []
    for q_fp in query_fps:
        if q_fp.hash not in source_map:
            continue
        for s_start in source_map[q_fp.hash]:
            matches.append({
                "query_start": q_fp.token_start,
                "query_end": q_fp.token_end,
                "source_start": s_start,
                "source_end": s_start + (q_fp.token_end - q_fp.token_start),
            })

    if not matches:
        return []

    # Deterministic order
    matches.sort(key=lambda m: (m["query_start"], m["source_start"]))

    # Group into contiguous spans; a match extends the current span
    # if it starts within one token of the span's end AND the source
    # offset also moved by the same amount (diagonal alignment).
    spans: list[MatchedSpan] = []
    current = dict(matches[0])
    current["fingerprint_count"] = 1

    for m in matches[1:]:
        same_diagonal = (
            (m["query_start"] - m["source_start"])
            == (current["query_start"] - current["source_start"])
        )
        touches_current = m["query_start"] <= current["query_end"] + 1

        if same_diagonal and touches_current:
            current["query_end"] = max(current["query_end"], m["query_end"])
            current["source_end"] = max(current["source_end"], m["source_end"])
            current["fingerprint_count"] += 1
        else:
            spans.append(MatchedSpan(**current))
            current = dict(m)
            current["fingerprint_count"] = 1

    spans.append(MatchedSpan(**current))
    return spans
