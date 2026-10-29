"""Command-line entry: index, status, query."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import config, db, indexer, retriever


def _cmd_index(args) -> int:
    corpus = Path(args.corpus)
    if not corpus.is_dir():
        print(f"error: corpus dir not found: {corpus}", file=sys.stderr)
        return 2
    conn = db.connect(args.db)
    stats = indexer.index_corpus(conn, corpus)
    conn.close()
    print(json.dumps(stats, indent=2))
    return 0


def _cmd_status(args) -> int:
    if not Path(args.db).exists():
        print(f"error: DB not found at {args.db}; run `index` first", file=sys.stderr)
        return 2
    conn = db.connect(args.db)
    docs = indexer.list_documents(conn)
    for d in docs:
        d["fingerprints"] = indexer.fingerprint_count(conn, d["id"])
    print(json.dumps({
        "db_path": str(args.db),
        "document_count": len(docs),
        "documents": docs,
        "disclaimer": config.DISCLAIMER,
    }, indent=2))
    conn.close()
    return 0


def _cmd_query(args) -> int:
    if not Path(args.db).exists():
        print(f"error: DB not found at {args.db}; run `index` first", file=sys.stderr)
        return 2
    conn = db.connect(args.db)
    result = retriever.query_file(conn, Path(args.file))
    conn.close()
    result["disclaimer"] = config.DISCLAIMER
    print(json.dumps(result, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="plagiarism", description="Offline similarity analyzer (45% build).")
    p.add_argument("--db", default=str(config.DB_PATH), help="SQLite path (default: data/plagiarism.db)")
    sub = p.add_subparsers(dest="cmd", required=True)

    pi = sub.add_parser("index", help="Index a corpus directory into the DB")
    pi.add_argument("--corpus", default=str(config.CORPUS_DIR))
    pi.set_defaults(func=_cmd_index)

    ps = sub.add_parser("status", help="Show indexed documents")
    ps.set_defaults(func=_cmd_status)

    pq = sub.add_parser("query", help="Find candidate source docs for a file")
    pq.add_argument("--file", required=True)
    pq.set_defaults(func=_cmd_query)
    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())