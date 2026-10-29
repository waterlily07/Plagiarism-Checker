"""Tokenize text into words while preserving each word's position
in the ORIGINAL text. This is what makes later highlighting possible."""
from __future__ import annotations

import re
from dataclasses import dataclass

_WORD_RE = re.compile(r"\w+", flags=re.UNICODE)


@dataclass(frozen=True)
class Token:
    index: int      # position in the token stream
    text: str       # normalized (lowercased) word
    start: int      # char offset in original text (inclusive)
    end: int        # char offset in original text (exclusive)


def tokenize(text: str) -> list[Token]:
    """Return tokens with char offsets into `text`.

    Lowercases for comparison but keeps offsets pointing into the
    original string so we can slice `text[start:end]` later.
    """
    if not text:
        return []
    tokens: list[Token] = []
    for i, m in enumerate(_WORD_RE.finditer(text)):
        tokens.append(Token(index=i, text=m.group(0).lower(), start=m.start(), end=m.end()))
    return tokens


def join_words(tokens: list[Token]) -> str:
    """Convenience for tests / debugging: normalized word sequence."""
    return " ".join(t.text for t in tokens)