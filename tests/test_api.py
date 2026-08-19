"""Tests for the Flask JSON API, using the in-process test client (no network)."""
import app as flask_app


def client():
    return flask_app.app.test_client()


def test_healthz():
    r = client().get("/healthz")
    assert r.status_code == 200
    assert r.data == b"ok"


def test_score_endpoint_positive():
    r = client().post("/api/score", json={"text": "I love this, absolutely amazing!"})
    assert r.status_code == 200
    body = r.get_json()
    assert body["label"] == "positive"
    assert body["score"] > 0


def test_score_endpoint_negative():
    r = client().post("/api/score", json={"text": "This is terrible, I hate it."})
    body = r.get_json()
    assert body["label"] == "negative"
    assert body["score"] < 0


def test_score_endpoint_returns_valid_label():
    r = client().post("/api/score", json={"text": "just some words here"})
    body = r.get_json()
    assert body["label"] in {"positive", "negative", "neutral"}


def test_score_endpoint_accepts_form():
    r = client().post("/api/score", data={"text": "wonderful, so happy!"})
    body = r.get_json()
    assert body["label"] == "positive"


def test_tweets_endpoint_returns_json():
    r = client().get("/api/tweets")
    assert r.status_code == 200
    body = r.get_json()
    assert "tweets" in body and "count" in body


def test_summary_endpoint_has_windows():
    r = client().get("/api/sentiment-summary")
    body = r.get_json()
    assert "windows" in body
    assert "total_in_buffer" in body
