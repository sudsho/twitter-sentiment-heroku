"""Offline smoke test for the Twitter sentiment app.

Runs with NO network and NO Twitter API access. It proves the two things that
matter:

1. The VADER + TextBlob sentiment scorer works. We evaluate it on a small
   bundled, hand-labeled toy tweet set (positive / negative / neutral) and print
   the accuracy against those labels. There is no model training here: the
   scorer is a rule-based ensemble, so "accuracy" means how well the ensemble's
   labels match the toy ground truth.

2. The Flask app boots in-process (via the test client) and the on-demand
   predict endpoint (POST /api/score) returns a valid label. We also feed the
   scored tweets into the shared store and exercise the dashboard JSON APIs.

The live Twitter stream (src/stream.py, tweepy) is never imported, so no
credentials or network are needed. TextBlob's polarity uses a bundled lexicon,
so there is no nltk corpora download either. If TextBlob is not installed the
scorer degrades to VADER-only automatically.

Run:  python scripts/smoke.py   (or: make smoke)
"""
import os
import sys
import time

# Make sure the repo root is importable when run as `python scripts/smoke.py`.
_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

# Belt-and-braces: keep the smoke fully offline even if some dependency tried to
# phone home. Point any Twitter creds at obvious dummies so nothing real is used.
os.environ.setdefault("DOTENV_PATH", "/nonexistent-smoke.env")
os.environ.setdefault("TWITTER_CONSUMER_KEY", "smoke-dummy")
os.environ.setdefault("TWITTER_CONSUMER_SECRET", "smoke-dummy")
os.environ.setdefault("TWITTER_ACCESS_TOKEN", "smoke-dummy")
os.environ.setdefault("TWITTER_ACCESS_SECRET", "smoke-dummy")

from src.score import label, score  # noqa: E402
from src.store import store  # noqa: E402

# Small bundled, hand-labeled toy tweet set. Synthetic (not from the Twitter
# API), so the smoke needs no network. Clear-cut examples chosen so a rule-based
# scorer should get them right.
TOY_TWEETS = [
    # positive
    ("Absolutely loving the new update, works like a charm!", "positive"),
    ("Best customer service ever, so happy right now :)", "positive"),
    ("This movie was fantastic, I really enjoyed every minute", "positive"),
    ("Great job team, super proud of what we shipped today", "positive"),
    ("What a beautiful sunny morning, feeling grateful", "positive"),
    ("I highly recommend this, it made my day", "positive"),
    # negative
    ("This is the worst experience I have ever had, so frustrating", "negative"),
    ("I hate how buggy this app is, it keeps crashing", "negative"),
    ("Terrible service, waited two hours and got nothing", "negative"),
    ("So disappointed, the product broke on day one", "negative"),
    ("Awful traffic today, completely ruined my morning", "negative"),
    ("I am furious, they cancelled my order without telling me", "negative"),
    # neutral
    ("The meeting is scheduled for 3pm on Tuesday", "neutral"),
    ("I bought some groceries and then went home", "neutral"),
    ("The train departs from platform 4 at noon", "neutral"),
    ("Here is the quarterly report you asked for", "neutral"),
    ("It is currently 20 degrees outside", "neutral"),
    ("The document has twelve pages in total", "neutral"),
]


def evaluate_scorer():
    """Score the toy set, print per-example results and overall accuracy."""
    print("=" * 68)
    print("1) Evaluating the VADER + TextBlob scorer on the toy tweet set")
    print("=" * 68)
    correct = 0
    for text, gold in TOY_TWEETS:
        combined, v, t = score(text)
        pred = label(combined)
        ok = pred == gold
        correct += ok
        mark = "ok " if ok else "XX "
        print("  {} gold={:<8} pred={:<8} score={:+.3f}  {}".format(
            mark, gold, pred, combined, text[:46]))
    acc = correct / len(TOY_TWEETS)
    print("-" * 68)
    print("  accuracy: {}/{} = {:.1%}".format(correct, len(TOY_TWEETS), acc))
    print()
    return acc


def exercise_flask():
    """Boot the Flask app in-process and hit the predict + dashboard APIs."""
    print("=" * 68)
    print("2) Booting Flask in-process and exercising the predict endpoint")
    print("=" * 68)
    import app as flask_app

    client = flask_app.app.test_client()

    # health check
    r = client.get("/healthz")
    assert r.status_code == 200 and r.data == b"ok", "healthz failed"
    print("  GET  /healthz -> 200 ok")

    # predict endpoint: POST a sample tweet, assert a valid label comes back
    valid = {"positive", "negative", "neutral"}
    samples = [
        ("I love this, absolutely amazing!", "positive"),
        ("This is terrible, I hate it.", "negative"),
        ("The meeting is scheduled for 3pm on Tuesday", "neutral"),
    ]
    for text, expected in samples:
        r = client.post("/api/score", json={"text": text})
        assert r.status_code == 200, "/api/score status {}".format(r.status_code)
        body = r.get_json()
        assert body["label"] in valid, "invalid label: {}".format(body["label"])
        assert body["label"] == expected, (
            "expected {} for {!r}, got {}".format(expected, text, body["label"]))
        print("  POST /api/score {!r:<38} -> {} ({:+.3f})".format(
            text[:34], body["label"], body["score"]))

    # feed the scored toy tweets into the shared store, like the worker would,
    # then check the dashboard JSON endpoints read them back.
    now = time.time()
    for i, (text, _gold) in enumerate(TOY_TWEETS):
        combined, v, t = score(text)
        store.add({
            "id": str(i),
            "text": text,
            "user": "smoke",
            "created_at": "now",
            "score": combined,
            "vader": v,
            "textblob": t,
            "label": label(combined),
            "received_at": now,
        })

    r = client.get("/api/tweets?n=5")
    tweets = r.get_json()
    assert tweets["count"] == 5, "expected 5 recent tweets, got {}".format(tweets["count"])
    assert all(x["label"] in valid for x in tweets["tweets"]), "bad label in /api/tweets"
    print("  GET  /api/tweets?n=5 -> count={}".format(tweets["count"]))

    r = client.get("/api/sentiment-summary")
    summary = r.get_json()
    assert "windows" in summary and summary["total_in_buffer"] >= len(TOY_TWEETS)
    win = summary["windows"][0]
    print("  GET  /api/sentiment-summary -> total_in_buffer={} "
          "window[0]: pos={} neg={} neu={}".format(
              summary["total_in_buffer"], win["positive"],
              win["negative"], win["neutral"]))
    print()


def main():
    acc = evaluate_scorer()
    exercise_flask()

    # a rule-based ensemble on clear-cut toy tweets should be comfortably right;
    # keep the bar honest but non-trivial so a broken scorer fails the smoke.
    assert acc >= 0.75, "scorer accuracy too low: {:.1%}".format(acc)

    print("=" * 68)
    print("SMOKE PASSED  (offline, no Twitter API)")
    print("=" * 68)


if __name__ == "__main__":
    main()
