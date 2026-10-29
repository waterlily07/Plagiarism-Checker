from plagiarism import db


def test_connect_creates_schema(tmp_path):
    p = tmp_path / "t.db"
    conn = db.connect(p)
    tables = {r["name"] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'")}
    assert {"documents", "fingerprints"} <= tables
    conn.close()


def test_is_initialized(tmp_path):
    p = tmp_path / "t.db"
    assert not db.is_initialized(p)
    db.connect(p).close()
    assert db.is_initialized(p)


def test_connect_is_idempotent(tmp_path):
    p = tmp_path / "t.db"
    db.connect(p).close()
    db.connect(p).close()  # must not raise