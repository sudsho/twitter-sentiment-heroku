"""tweepy filter stream worker.

Reads Twitter creds + keywords from env vars, opens a streaming connection,
and pushes scored tweets into the shared store.
"""
import logging
import os
import sys
import time

import tweepy
import yaml

from src.score import score, label
from src.store import store

log = logging.getLogger("stream")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")


def load_config(path="configs/default.yaml"):
    with open(path) as f:
        cfg = yaml.safe_load(f)
    # env override
    kw = os.environ.get("TRACK_KEYWORDS")
    if kw:
        cfg["track_keywords"] = [k.strip() for k in kw.split(",") if k.strip()]
    lang = os.environ.get("LANGUAGE")
    if lang:
        cfg["language"] = lang
    return cfg


class Listener(tweepy.StreamListener):
    def on_status(self, status):
        # skip retweets to avoid double-counting
        if hasattr(status, "retweeted_status"):
            return
        text = status.text
        combined, v, t = score(text)
        store.add({
            "id": status.id_str,
            "text": text,
            "user": status.user.screen_name,
            "created_at": status.created_at.isoformat(),
            "score": combined,
            "vader": v,
            "textblob": t,
            "label": label(combined),
        })

    def on_error(self, status_code):
        log.warning("stream error: %s", status_code)
        if status_code == 420:
            # rate limited; back off
            time.sleep(60)
        return True  # keep stream open


def build_auth():
    auth = tweepy.OAuthHandler(
        os.environ["TWITTER_CONSUMER_KEY"],
        os.environ["TWITTER_CONSUMER_SECRET"],
    )
    auth.set_access_token(
        os.environ["TWITTER_ACCESS_TOKEN"],
        os.environ["TWITTER_ACCESS_SECRET"],
    )
    return auth


def run():
    cfg = load_config()
    keywords = cfg["track_keywords"]
    log.info("tracking: %s", keywords)
    listener = Listener()
    stream = tweepy.Stream(auth=build_auth(), listener=listener)
    stream.filter(track=keywords, languages=[cfg.get("language", "en")])


if __name__ == "__main__":
    try:
        run()
    except KeyboardInterrupt:
        log.info("bye")
        sys.exit(0)
