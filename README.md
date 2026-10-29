# Plagiarism Similarity Analyzer

An offline plagiarism similarity tool. Fingerprints documents with
**5-word k-grams**, uses the **winnowing algorithm** to keep a sparse
fingerprint set, stores them in **SQLite**, and — given a query file —
retrieves candidate sources, aligns matching passages, and reports
**coverage percentages** with highlighted spans.

> **Disclaimer:** This tool measures *textual similarity* against an
> indexed corpus. It does NOT determine plagiarism, intent, or
> originality. Results are evidence for human review.

## What works

- Preprocessing that preserves character offsets for every token
- 5-word k-gram fingerprinting with reproducible signed-64-bit `blake2b` hashes
- Winnowing (k=5, window w=4)
- SQLite schema, idempotent indexing, cascade deletes
- Candidate retrieval with **passage alignment** and **coverage percentage**
- CLI: `index`, `status`, `query`
- Flask upload UI with highlighted matched passages
- 27 unit tests, all passing

## Setup

    python -m venv .venv
    .\.venv\Scripts\Activate.ps1     # Windows
    # source .venv/bin/activate      # Linux/macOS
    pip install -r requirements.txt
    pip install -e .

## Commands

    pytest

    python -m plagiarism index --corpus data/corpus
    python -m plagiarism status
    python -m plagiarism query --file data/corpus/sample_a.txt

    flask --app plagiarism.web.app run --debug

## Populating the corpus

`scripts/fetch_corpus.py` downloads 10 public-domain books from Project
Gutenberg into `data/corpus/`. Standard library only.

    python scripts\fetch_corpus.py
    python -m plagiarism index --corpus data/corpus

## Algorithm summary

1. **Tokenize** text, keeping each word's char offset in the original.
2. **Fingerprint**: slide a 5-word window, join, hash with
   `blake2b(digest_size=8)`, reinterpret as a signed 64-bit int so it
   fits SQLite INTEGER.
3. **Winnow**: over each window of 4 consecutive hashes pick the minimum;
   if its position changes, record it as a fingerprint.
4. **Index**: store `(doc_id, fp_hash, token_start, token_end)` in SQLite.
5. **Retrieve**: look up fingerprints via `WHERE fp_hash IN (...)`.
6. **Align**: group consecutive matching fingerprints into contiguous
   passages.
7. **Score**: coverage % = tokens covered by matched spans ÷ total tokens.
