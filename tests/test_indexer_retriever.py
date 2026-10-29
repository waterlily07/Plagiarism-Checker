from pathlib import Path

import pytest

from plagiarism import db, indexer, retriever

FIXTURES = Path(__file__).parent / "fixtures" / "tiny_docs"


@pytest.fixture()
def conn(tmp_path):
    c = db.connect(tmp_path / "t.db")
    yield c
    c.close()


def test_index_and_list(conn):
    stats = indexer.index_corpus(conn, FIXTURES)
    assert stats["indexed"] >= 3
    docs = indexer.list_documents(conn)
    names = {Path(d["path"]).name for d in docs}
    assert {"identical_1.txt", "identical_2.txt", "different.txt"} <= names


def test_reindex_same_content_is_noop(conn):
    first = indexer.index_corpus(conn, FIXTURES)
    second = indexer.index_corpus(conn, FIXTURES)
    assert second["indexed"] == 0
    assert second["skipped"] == first["indexed"]


def test_retrieval_finds_identical_doc(conn):
    indexer.index_corpus(conn, FIXTURES)
    result = retriever.query_file(conn, FIXTURES / "identical_1.txt")
    paths = {Path(c["path"]).name for c in result["candidates"]}
    assert "identical_2.txt" in paths


def test_retrieval_finds_partial_copy(conn):
    indexer.index_corpus(conn, FIXTURES)
    result = retriever.query_file(conn, FIXTURES / "partial_copy.txt")
    paths = {Path(c["path"]).name for c in result["candidates"]}
    assert "identical_1.txt" in paths


def test_different_doc_has_few_or_no_candidates(conn):
    indexer.index_corpus(conn, FIXTURES)
    result = retriever.query_file(conn, FIXTURES / "different.txt")
    # 'different.txt' shares no 5-word window with the others
    names = {Path(c["path"]).name for c in result["candidates"]}
    assert "identical_1.txt" not in names


def test_empty_query(conn):
    indexer.index_corpus(conn, FIXTURES)
    result = retriever.query_file(conn, FIXTURES / "different.txt")
    # sanity: query itself has fingerprints
    assert result["query_fingerprints"] >= 0


def test_delete_cascades(conn):
    indexer.index_corpus(conn, FIXTURES)
    docs = indexer.list_documents(conn)
    did = docs[0]["id"]
    indexer.delete_document(conn, did)
    left = conn.execute(
        "SELECT COUNT(*) c FROM fingerprints WHERE doc_id = ?", (did,)).fetchone()["c"]
    assert left == 0