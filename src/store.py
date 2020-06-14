"""In-memory ring buffer for incoming tweets.

Threads (the tweepy stream worker, Flask request handlers) all share this
single buffer module-level. Good enough for one dyno; not safe across dynos.
"""
import threading
import time
from collections import deque


class TweetStore(object):
    def __init__(self, maxlen=200):
        self._buf = deque(maxlen=maxlen)
        self._lock = threading.Lock()

    def add(self, tweet):
        # tweet is expected to be a dict with at least: id, text, created_at, score
        tweet.setdefault("received_at", time.time())
        with self._lock:
            self._buf.append(tweet)

    def recent(self, n=None):
        with self._lock:
            items = list(self._buf)
        if n is None:
            return items
        return items[-n:]

    def since(self, seconds):
        cutoff = time.time() - seconds
        with self._lock:
            return [t for t in self._buf if t.get("received_at", 0) >= cutoff]

    def __len__(self):
        with self._lock:
            return len(self._buf)


# module-level singleton; imported by app.py and stream.py
store = TweetStore(maxlen=200)
