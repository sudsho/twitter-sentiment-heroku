# twitter-sentiment-heroku

Real-time Twitter sentiment dashboard. Streams tweets matching a keyword via
tweepy, scores them with VADER + TextBlob, and shows the rolling sentiment in a
small Flask web UI. Deployable to Heroku.

## Why

Quarantine boredom side project. Wanted to see how the public mood around a
keyword (`covid`, a brand name, a politician, a TV show) shifts in real time.
Easiest way to learn the Twitter streaming API at the same time.

## What it does

- A background worker opens a tweepy filter stream against a list of
  keywords (configurable in `configs/default.yaml`).
- Each incoming tweet gets scored by two sentiment models:
  - VADER (`vaderSentiment`) — rule-based, tuned for social media slang.
  - TextBlob — naive Bayes-ish polarity.
  - The app reports both individually and a simple average.
- The last N tweets sit in an in-memory ring buffer (default N=200).
- A tiny Flask app reads the buffer and serves:
  - `/` — HTML dashboard with the latest tweets and a moving-average chart.
  - `/api/tweets` — JSON dump of recent tweets + scores.
  - `/api/sentiment-summary` — 1, 5, 15-minute moving averages.
- The dashboard auto-refreshes every 5 seconds via a small JS poller.

## Stack

- Python 3.8
- Flask 1.1
- tweepy 3.8 (Twitter API v1.1, before the rebrand)
- vaderSentiment 3.3.2
- TextBlob 0.15
- gunicorn for the web dyno
- Heroku (Procfile + runtime.txt)

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
cp .env.example .env
# edit .env with your Twitter API keys
```

Run web + worker locally in two terminals:

```bash
# terminal 1
python -m src.stream
# terminal 2
gunicorn app:app
```

Then open http://localhost:8000.

## Deploy to Heroku

```bash
heroku create my-twitter-sentiment
heroku config:set TWITTER_CONSUMER_KEY=...
heroku config:set TWITTER_CONSUMER_SECRET=...
heroku config:set TWITTER_ACCESS_TOKEN=...
heroku config:set TWITTER_ACCESS_SECRET=...
heroku config:set TRACK_KEYWORDS="python,flask,covid"
git push heroku main
heroku ps:scale web=1 worker=1
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
pytest -v
```

Tests cover the scoring functions and the ring buffer. The streaming layer is
not unit-tested (it talks to the live Twitter API).

## Layout

```
.
├── app.py                # Flask entrypoint
├── src/
│   ├── stream.py         # tweepy stream listener
│   ├── score.py          # VADER + TextBlob ensemble
│   └── store.py          # in-memory ring buffer
├── templates/
│   └── index.html        # dashboard
├── static/
│   └── chart.js          # moving-average chart
├── configs/
│   └── default.yaml
├── tests/
│   ├── test_score.py
│   └── test_store.py
├── Procfile
├── runtime.txt
├── requirements.txt
└── .env.example
```

## License

MIT.
