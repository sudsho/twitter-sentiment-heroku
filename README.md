# twitter-sentiment-heroku

Real-time Twitter sentiment dashboard. Streams tweets matching a keyword via
tweepy, scores them with VADER + TextBlob, and shows the rolling sentiment in a
small Flask web UI. Deployable to Heroku.

[![Build Status](https://travis-ci.org/sudsho/twitter-sentiment-heroku.svg?branch=main)](https://travis-ci.org/sudsho/twitter-sentiment-heroku)
[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy?template=https://github.com/sudsho/twitter-sentiment-heroku)

## Quick start (runs offline)

You do not need a Twitter account, API keys, or a network connection to try the
sentiment engine. The scorer (VADER + TextBlob) is rule-based and the Flask app
can score text on demand.

```bash
pip install vaderSentiment textblob Flask PyYAML python-dotenv
python scripts/smoke.py
```

The smoke evaluates the scorer on a small bundled, hand-labeled toy tweet set
(positive / negative / neutral), prints the accuracy, then boots the Flask app
in-process and POSTs sample tweets to the `POST /api/score` predict endpoint.
It never touches the Twitter API. Real output:

```
====================================================================
1) Evaluating the VADER + TextBlob scorer on the toy tweet set
====================================================================
  ok  gold=positive pred=positive score=+0.673  Absolutely loving the new update, works like a
  ok  gold=positive pred=positive score=+0.809  Best customer service ever, so happy right now
  ...
  ok  gold=neutral  pred=neutral  score=+0.000  The document has twelve pages in total
--------------------------------------------------------------------
  accuracy: 18/18 = 100.0%

====================================================================
2) Booting Flask in-process and exercising the predict endpoint
====================================================================
  GET  /healthz -> 200 ok
  POST /api/score 'I love this, absolutely amazing!'     -> positive (+0.767)
  POST /api/score 'This is terrible, I hate it.'         -> negative (-0.827)
  POST /api/score 'The meeting is scheduled for 3pm o'   -> neutral (+0.000)
  GET  /api/tweets?n=5 -> count=5
  GET  /api/sentiment-summary -> total_in_buffer=18 window[0]: pos=6 neg=6 neu=6

====================================================================
SMOKE PASSED  (offline, no Twitter API)
====================================================================
```

`make smoke` runs the same thing if you have `make`. Note the accuracy is over a
tiny, deliberately clear-cut toy set, so it is a sanity check on the scoring
path, not a benchmark. TextBlob's polarity uses a bundled lexicon, so there is
no `nltk` corpora download; if TextBlob is not installed the scorer falls back
to VADER only.

You can also score a single tweet over HTTP once the app is running:

```bash
curl -s -X POST localhost:8000/api/score -H "Content-Type: application/json" \
  -d '{"text": "loving this weather"}'
# {"label":"positive","score":0.6115,"text":"loving this weather","textblob":...,"vader":...}
```

## Why

Quarantine boredom side project. Wanted to see how the public mood around a
keyword (`covid`, a brand name, a politician, a TV show) shifts in real time.
Easiest way to learn the Twitter streaming API at the same time.

## What it does

- A background worker opens a tweepy filter stream against a list of
  keywords (configurable in `configs/default.yaml`).
- Each incoming tweet gets scored by two sentiment models:
  - VADER (`vaderSentiment`) - rule-based, tuned for social media slang.
  - TextBlob - naive Bayes-ish polarity.
  - Reported individually + as a weighted average.
- The last N tweets sit in an in-memory ring buffer (default N=200).
- A tiny Flask app reads the buffer and serves:
  - `/` - HTML dashboard with the latest tweets and a moving-average chart.
  - `/api/tweets` - JSON dump of recent tweets + scores.
  - `/api/sentiment-summary` - 1, 5, 15-minute moving averages.
  - `POST /api/score` - score an arbitrary piece of text on demand (returns the
    VADER + TextBlob ensemble score and a positive/negative/neutral label).
    This is the offline predict path and needs no Twitter access.
- The dashboard auto-refreshes every 5s (override with `?refresh=N`).

## Stack

- Python 3.8
- Flask 1.1
- tweepy 3.8 (Twitter API v1.1, before the rebrand)
- vaderSentiment 3.3.2
- TextBlob 0.15
- gunicorn for the web dyno
- Heroku (Procfile + runtime.txt + app.json)

## Setup

You need a Twitter developer account. Apply at
[developer.twitter.com](https://developer.twitter.com). Approval can take a few
days; they ask what you plan to build. Once approved, create an app and grab
the four keys.

Local:

```bash
git clone https://github.com/sudsho/twitter-sentiment-heroku
cd twitter-sentiment-heroku
python -m venv .venv
source .venv/bin/activate    # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
python -m textblob.download_corpora    # one time, for textblob
cp .env.example .env
# edit .env with your Twitter API keys
```

Run web + worker locally in two terminals:

```bash
# terminal 1
python -m src.stream
# terminal 2
gunicorn wsgi:app
```

Then open http://localhost:8000.

## Deploy to Heroku

Quick path: hit the Deploy button at the top of this README.

Manual:

```bash
heroku create my-twitter-sentiment
heroku config:set TWITTER_CONSUMER_KEY=...
heroku config:set TWITTER_CONSUMER_SECRET=...
heroku config:set TWITTER_ACCESS_TOKEN=...
heroku config:set TWITTER_ACCESS_SECRET=...
heroku config:set TRACK_KEYWORDS="python,flask,covid"
git push heroku main
heroku ps:scale web=1 worker=1
heroku logs --tail
```

Heroku free dyno is enough for low-volume keywords. High-volume tags
(`#trump`, `#bts`) can blow past the free tier rate limits and you may need
a hobby dyno.

## Config

Defaults live in `configs/default.yaml`:

```yaml
track_keywords:
  - python
  - flask
language: en
buffer_size: 200
moving_avg_windows_seconds: [60, 300, 900]
```

Override `TRACK_KEYWORDS` and `LANGUAGE` via env vars on Heroku.

## Tests

```bash
pytest -q
```

Real output: `18 passed`. Tests cover the scoring functions, the ring buffer,
and the Flask JSON API (including the `POST /api/score` predict endpoint, driven
by the in-process test client, no network). The live streaming layer is not
unit-tested because it talks to the Twitter API.

## Layout

```
.
├── app.py                # Flask routes
├── wsgi.py               # gunicorn entrypoint
├── src/
│   ├── stream.py         # tweepy stream listener
│   ├── score.py          # VADER + TextBlob ensemble
│   └── store.py          # in-memory ring buffer
├── templates/
│   └── index.html        # dashboard
├── static/
│   └── chart.js          # summary bars + tweet list
├── configs/
│   └── default.yaml
├── scripts/
│   └── smoke.py          # offline smoke: scorer accuracy + Flask predict path
├── tests/
│   ├── test_score.py
│   ├── test_store.py
│   └── test_api.py       # Flask JSON API incl. POST /api/score
├── Makefile              # make smoke / make test
├── Procfile
├── app.json
├── runtime.txt
├── requirements.txt
└── .env.example
```

## Known issues / things I didn't do

- In-memory store means the buffer resets on every dyno restart. Heroku
  recycles dynos every 24h. Fine for a demo. A real version would use Redis
  or Postgres.
- The web and worker dynos don't share memory, so the dashboard only sees
  tweets the *web* dyno scored. On Heroku you'd hit this. For the demo, run
  the stream from inside the same process by importing `src.stream` and
  spawning a thread on app boot. Left as an exercise (or use Redis pub/sub).
- No rate-limit handling beyond the basic 420 backoff.
- No persistent history. The 15-minute window is the longest available.

## License

MIT.
