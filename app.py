"""Flask app for the sentiment dashboard."""
import os

import yaml
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request

from src.score import label, score
from src.store import store

# load .env if present; on heroku the dyno sets env vars directly so missing
# .env is fine. dotenv silently does nothing if the file isn't there but we
# want to be explicit so a typo'd path is noisy.
DOTENV_PATH = os.environ.get("DOTENV_PATH", ".env")
if os.path.exists(DOTENV_PATH):
    load_dotenv(DOTENV_PATH)

app = Flask(__name__)


def _load_windows():
    try:
        with open("configs/default.yaml") as f:
            cfg = yaml.safe_load(f)
        return cfg.get("moving_avg_windows_seconds", [60, 300, 900])
    except Exception:
        return [60, 300, 900]


WINDOWS = _load_windows()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/tweets")
def api_tweets():
    n = int(request.args.get("n", 50))
    items = store.recent(n=n)
    return jsonify({"count": len(items), "tweets": items})


@app.route("/api/sentiment-summary")
def api_summary():
    out = {"windows": []}
    for w in WINDOWS:
        items = store.since(w)
        if items:
            avg = sum(t["score"] for t in items) / len(items)
            pos = sum(1 for t in items if t["label"] == "positive")
            neg = sum(1 for t in items if t["label"] == "negative")
            neu = sum(1 for t in items if t["label"] == "neutral")
        else:
            avg = 0.0
            pos = neg = neu = 0
        out["windows"].append({
            "window_seconds": w,
            "count": len(items),
            "avg_score": avg,
            "positive": pos,
            "negative": neg,
            "neutral": neu,
        })
    out["total_in_buffer"] = len(store)
    return jsonify(out)


@app.route("/api/score", methods=["POST"])
def api_score():
    """Score a single piece of text on demand.

    Accepts JSON ``{"text": "..."}`` or a form field ``text`` and returns the
    VADER + TextBlob ensemble score and a positive/negative/neutral label. This
    runs the same offline scorer the stream worker uses, so it needs no Twitter
    API access.
    """
    data = request.get_json(silent=True) or {}
    text = data.get("text")
    if text is None:
        text = request.form.get("text", "")
    combined, v, t = score(text)
    return jsonify({
        "text": text,
        "score": combined,
        "vader": v,
        "textblob": t,
        "label": label(combined),
    })


@app.route("/healthz")
def healthz():
    return "ok"


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port, debug=True)
