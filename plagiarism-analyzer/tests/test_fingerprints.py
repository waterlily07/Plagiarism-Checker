import pytest

from plagiarism import fingerprints
from plagiarism.preprocessing import tokenize


def test_empty_and_short():
    assert fingerprints.build([]) == []
    assert fingerprints.build(tokenize("only four words here")) == []


def test_kgram_count():
    toks = tokenize("a b c d e f g")
    grams = fingerprints.build(toks, k=5)
    assert len(grams) == 3  # 7 - 5 + 1


def test_hashes_are_reproducible():
    toks = tokenize("the quick brown fox jumps over")
    a = [g.hash for g in fingerprints.build(toks)]
    b = [g.hash for g in fingerprints.build(toks)]
    assert a == b


def test_hashes_fit_sqlite_signed_64():
    # SQLite INTEGER is signed 64-bit: [-2^63, 2^63 - 1].
    toks = tokenize(" ".join(f"w{i}" for i in range(200)))
    for g in fingerprints.build(toks):
        assert isinstance(g.hash, int)
        assert -(2**63) <= g.hash <= 2**63 - 1


def test_hash_differs_for_different_text():
    a = fingerprints.build(tokenize("one two three four five"))[0].hash
    b = fingerprints.build(tokenize("one two three four SIX"))[0].hash
    assert a != b


def test_invalid_k():
    with pytest.raises(ValueError):
        fingerprints.build(tokenize("a b c"), k=0)
