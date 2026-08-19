"""Sentiment scoring with VADER + TextBlob ensemble.

VADER is rule-based, tuned for social-media slang and emojis. TextBlob is a
lexicon + naive bayes thing. Each disagrees on borderline cases. Take a
weighted average and call it good.
"""
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# TextBlob is optional. Its polarity uses a bundled lexicon (no network / no
# nltk corpora download), but if the package isn't installed we degrade to a
# VADER-only ensemble instead of crashing. This keeps the scorer importable in
# minimal environments (e.g. the offline smoke).
try:
    from textblob import TextBlob
    _HAS_TEXTBLOB = True
except Exception:  # pragma: no cover - exercised only when textblob is absent
    TextBlob = None
    _HAS_TEXTBLOB = False

_vader = SentimentIntensityAnalyzer()

# weights from configs/default.yaml; not loaded here to keep this pure
DEFAULT_VADER_WEIGHT = 0.6
DEFAULT_TEXTBLOB_WEIGHT = 0.4


def score_vader(text):
    """VADER compound score in [-1, 1]."""
    return _vader.polarity_scores(text)["compound"]


def score_textblob(text):
    """TextBlob polarity in [-1, 1].

    Returns 0.0 (neutral) when TextBlob is not installed so the ensemble can
    fall back to VADER-only rather than failing.
    """
    if not _HAS_TEXTBLOB:
        return 0.0
    return TextBlob(text).sentiment.polarity


def score(text, vader_weight=DEFAULT_VADER_WEIGHT, textblob_weight=DEFAULT_TEXTBLOB_WEIGHT):
    """Return (combined, vader, textblob) tuple."""
    v = score_vader(text)
    t = score_textblob(text)
    if not _HAS_TEXTBLOB:
        # VADER-only fallback: don't let a zeroed textblob term dilute the score
        return v, v, t
    total = vader_weight + textblob_weight
    combined = (vader_weight * v + textblob_weight * t) / total
    return combined, v, t


def label(s):
    if s >= 0.05:
        return "positive"
    if s <= -0.05:
        return "negative"
    return "neutral"
