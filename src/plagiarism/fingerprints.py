"""5-word k-grams hashed with blake2b (reproducible across runs)."""
from __future__ import annotations

import hashlib
from dataclasses import dataclass

from . import config
from .preprocessing import Token


@dataclass(frozen=True)
class KGram:
    hash: int                   # 64-bit int from blake2b
    tokens: tuple[Token, ...]   # the 5 tokens that formed this gram


def _hash_words(words: tuple[str, ...]) -> int:
    """Stable across runs; Python's built-in hash() is salted and unsuitable."""
    payload = "\x1f".join(words).encode("utf-8")
    digest = hashlib.blake2b(payload, digest_size=config.HASH_DIGEST_BYTES).digest()
    return _signed_64(digest)


def _signed_64(digest: bytes) -> int:
    """Interpret 8 bytes as a signed 64-bit int (SQLite INTEGER range)."""
    unsigned = int.from_bytes(digest, "big")
    if unsigned >= 2**63:
        unsigned -= 2**64
    return unsigned


def build(tokens: list[Token], k: int = config.K) -> list[KGram]:
    """Return all k-word grams, each with its stable hash."""
    if k <= 0:
        raise ValueError("k must be positive")
    if len(tokens) < k:
        return []
    grams: list[KGram] = []
    for i in range(len(tokens) - k + 1):
        window = tokens[i:i + k]
        h = _hash_words(tuple(t.text for t in window))
        grams.append(KGram(hash=h, tokens=tuple(window)))
    return grams