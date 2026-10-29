from plagiarism.preprocessing import tokenize


def test_empty():
    assert tokenize("") == []


def test_whitespace_only():
    assert tokenize("   \n\t ") == []


def test_offsets_point_into_original():
    text = "Hello, World!"
    toks = tokenize(text)
    assert [t.text for t in toks] == ["hello", "world"]
    assert text[toks[0].start:toks[0].end] == "Hello"
    assert text[toks[1].start:toks[1].end] == "World"


def test_punctuation_and_case():
    toks = tokenize("The cat's toy.")
    assert [t.text for t in toks] == ["the", "cat", "s", "toy"]


def test_unicode():
    toks = tokenize("café déjà vu")
    assert [t.text for t in toks] == ["café", "déjà", "vu"]


def test_index_sequence():
    toks = tokenize("a b c d")
    assert [t.index for t in toks] == [0, 1, 2, 3]