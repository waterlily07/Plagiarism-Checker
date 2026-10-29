from plagiarism import config


def test_defaults():
    assert config.K == 5
    assert config.WINNOW_W == 4
    assert config.HASH_DIGEST_BYTES == 8
    assert "not" in config.DISCLAIMER.lower() or "does not" in config.DISCLAIMER.lower()