"""Flask upload UI for the plagiarism analyzer."""
from __future__ import annotations

from flask import Flask, render_template, request

from .. import config, db, preprocessing, retriever


def create_app(db_path=None) -> Flask:
    app = Flask(__name__, template_folder="templates")
    app.config["DB_PATH"] = str(db_path or config.DB_PATH)
    app.config["DISCLAIMER"] = config.DISCLAIMER

    @app.route("/", methods=["GET"])
    def index():
        return render_template("index.html", disclaimer=config.DISCLAIMER)

    @app.route("/analyze", methods=["POST"])
    def analyze():
        text = (request.form.get("text") or "").strip()
        if not text:
            return render_template(
                "index.html",
                disclaimer=config.DISCLAIMER,
                error="Please paste some text to analyze.",
            ), 400

        tokens = preprocessing.tokenize(text)
        fps = retriever.fingerprint_text(text)

        conn = db.connect(app.config["DB_PATH"])
        try:
            grouped = retriever.candidates(conn, fps)
            sources = []
            for doc_id, hits in grouped.items():
                row = conn.execute(
                    "SELECT path FROM documents WHERE id = ?", (doc_id,)
                ).fetchone()
                if row is None:
                    continue
                from .. import alignment
                spans = alignment.align_matches(fps, hits)
                covered = set()
                for s in spans:
                    for w in range(s.query_start, s.query_end + 1):
                        covered.add(w)
                coverage = (len(covered) / len(tokens) * 100.0) if tokens else 0.0
                sources.append({
                    "path": row["path"],
                    "coverage_percent": round(coverage, 1),
                    "spans": [
                        {"q_start": s.query_start, "q_end": s.query_end}
                        for s in spans
                    ],
                })
            sources.sort(key=lambda s: s["coverage_percent"], reverse=True)
        finally:
            conn.close()

        # Build an HTML-safe highlighted version of the query text
        # by marking each token that falls inside a matched span.
        highlighted = _build_highlighted_html(text, tokens, sources)

        overall = max((s["coverage_percent"] for s in sources), default=0.0)

        return render_template(
            "result.html",
            disclaimer=config.DISCLAIMER,
            overall=overall,
            sources=sources,
            highlighted=highlighted,
            word_count=len(tokens),
        )

    return app


def _build_highlighted_html(text: str, tokens, sources) -> str:
    """Wrap every token inside any matched span with a <mark> tag.

    Colors alternate per source so a reader can see which passage came
    from which document.
    """
    from markupsafe import Markup, escape

    # Collect every (source_index, token_start, token_end) triple
    intervals = []
    for i, s in enumerate(sources):
        for sp in s["spans"]:
            intervals.append((i, sp["q_start"], sp["q_end"]))

    parts: list[Markup] = []
    cursor = 0
    palette = ["#fff3b0", "#bde0fe", "#c7f9cc", "#ffd6a5", "#d0bfff"]
    for tok in tokens:
        if tok.start < cursor:
            continue
        # Whitespace between previous token and this one
        if tok.start > cursor:
            parts.append(escape(text[cursor:tok.start]))

        # Which source(s) claim this token?
        owner = None
        for (i, s, e) in intervals:
            if s <= tok.index <= e:
                owner = i
                break

        if owner is None:
            parts.append(escape(text[tok.start:tok.end]))
        else:
            color = palette[owner % len(palette)]
            parts.append(
                Markup(
                    f'<mark style="background:{color};">'
                    f'{escape(text[tok.start:tok.end])}</mark>'
                )
            )
        cursor = tok.end

    if cursor < len(text):
        parts.append(escape(text[cursor:]))
    return Markup("".join(str(p) for p in parts))
