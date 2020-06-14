"""Sentiment scoring with VADER + TextBlob ensemble.

VADER is rule-based, tuned for social-media slang and emojis. TextBlob is a
lexicon + naive bayes thing. Each disagrees on borderline cases. Take a
weighted average and call it good.
"""
from textblob import TextBlob
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

_vader = SentimentIntensityAnalyzer()

# weights from configs/default.yaml; not loaded here to keep this pure
DEFAULT_VADER_WEIGHT = 0.6
DEFAULT_TEXTBLOB_WEIGHT = 0.4


def score_vader(text):
    """VADER compound score in [-1, 1]."""
    return _vader.polarity_scores(text)["compound"]


def score_textblob(text):
    """TextBlob polarity in [-1, 1]."""
    return TextBlob(text).sentiment.polarity


def score(text, vader_weight=DEFAULT_VADER_WEIGHT, textblob_weight=DEFAULT_TEXTBLOB_WEIGHT):
    """Return (combined, vader, textblob) tuple."""
    v = score_vader(text)
    t = score_textblob(text)
    total = vader_weight + textblob_weight
    combined = (vader_weight * v + textblob_weight * t) / total
    return combined, v, t


def label(s):
    if s >= 0.05:
        return "positive"
    if s <= -0.05:
        return "negative"
    return "neutral"
