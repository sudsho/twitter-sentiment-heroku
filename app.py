"""Flask app for the sentiment dashboard."""
import os

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template

from src.store import store

load_dotenv()

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/tweets")
def api_tweets():
    n = int(request_arg("n", 50))
    items = store.recent(n=n)
    return jsonify({"count": len(items), "tweets": items})


@app.route("/healthz")
def healthz():
    return "ok"


def request_arg(name, default):
    from flask import request
    return request.args.get(name, default)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port, debug=True)
