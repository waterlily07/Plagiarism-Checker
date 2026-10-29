import pytest

from plagiarism import fingerprints, winnowing
from plagiarism.preprocessing import tokenize


def _fp(text):
    toks = tokenize(text)
    return winnowing.select(fingerprints.build(toks, k=5), w=4)


def test_empty():
    assert _fp("") == []


def test_fewer_grams_than_window():
    # 6 words -> 2 grams; window 4 > 2 -> single min emitted
    fps = _fp("a b c d e f")
    assert len(fps) == 1


def test_positions_are_monotonic():
    text = " ".join(f"w{i}" for i in range(30))
    fps = _fp(text)
    starts = [fp.token_start for fp in fps]
    assert starts == sorted(starts)
    assert len({fp.token_start for fp in fps}) == len(fps)  # no dup positions


def test_invalid_window():
    with pytest.raises(ValueError):
        winnowing.select([], w=0)