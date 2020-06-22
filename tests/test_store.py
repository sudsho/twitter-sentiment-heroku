import time

from src.store import TweetStore


def make(text, score=0.0, label="neutral"):
    return {"id": "1", "text": text, "user": "u", "created_at": "now", "score": score, "label": label}


def test_add_and_recent():
    s = TweetStore(maxlen=5)
    for i in range(3):
        s.add(make("t{}".format(i)))
    out = s.recent()
    assert len(out) == 3
    assert out[0]["text"] == "t0"


def test_ring_buffer_caps_at_maxlen():
    s = TweetStore(maxlen=3)
    for i in range(10):
        s.add(make("t{}".format(i)))
    out = s.recent()
    assert len(out) == 3
    # oldest 7 dropped
    assert out[0]["text"] == "t7"
    assert out[-1]["text"] == "t9"


def test_recent_n():
    s = TweetStore(maxlen=10)
    for i in range(8):
        s.add(make("t{}".format(i)))
    last2 = s.recent(n=2)
    assert len(last2) == 2
    assert last2[-1]["text"] == "t7"


def test_since_filters_by_time():
    s = TweetStore(maxlen=10)
    s.add(make("old"))
    # backdate it
    s._buf[-1]["received_at"] = time.time() - 600
    s.add(make("new"))
    recent = s.since(60)
    assert len(recent) == 1
    assert recent[0]["text"] == "new"


def test_len():
    s = TweetStore(maxlen=10)
    assert len(s) == 0
    s.add(make("x"))
    assert len(s) == 1
