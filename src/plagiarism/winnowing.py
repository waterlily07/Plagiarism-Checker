"""Winnowing: from a stream of k-gram hashes, pick a sparse,
position-stable set of fingerprints (Schleimer et al., 2003)."""
from __future__ import annotations

from dataclasses import dataclass

from . import config
from .fingerprints import KGram


@dataclass(frozen=True)
class Fingerprint:
    hash: int
    tokens: tuple            # tuple[Token, ...] — the source k-gram's tokens
    token_start: int         # index in token stream of the first token
    token_end: int           # index of the last token (inclusive)


def select(grams: list[KGram], w: int = config.WINNOW_W) -> list[Fingerprint]:
    """Return selected fingerprints. Ties: leftmost minimum wins, and only
    a fingerprint whose *position* changes versus the previous window is kept.
    """
    if w <= 0:
        raise ValueError("w must be positive")
    n = len(grams)
    if n == 0:
        return []
    if w > n:
        # Degenerate case: one window covering everything -> single min.
        min_idx = min(range(n), key=lambda i: (grams[i].hash, i))
        g = grams[min_idx]
        return [_to_fp(g, min_idx)]

    selected: list[Fingerprint] = []
    last_emitted_pos = -1

    for start in range(0, n - w + 1):
        window = grams[start:start + w]
        # min by (hash, absolute_position) — deterministic tie-break
        min_local = min(range(w), key=lambda j: (window[j].hash, start + j))
        abs_pos = start + min_local
        if abs_pos != last_emitted_pos:
            selected.append(_to_fp(grams[abs_pos], abs_pos))
            last_emitted_pos = abs_pos
    return selected


def _to_fp(g: KGram, pos: int) -> Fingerprint:
    return Fingerprint(
        hash=g.hash,
        tokens=g.tokens,
        token_start=g.tokens[0].index,
        token_end=g.tokens[-1].index,
    )