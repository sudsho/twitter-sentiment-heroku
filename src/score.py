"""Sentiment scoring with VADER. TextBlob added later."""
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

_vader = SentimentIntensityAnalyzer()


def score_vader(text):
    """Return VADER compound score in [-1, 1]."""
    return _vader.polarity_scores(text)["compound"]


def label(score):
    if score >= 0.05:
        return "positive"
    if score <= -0.05:
        return "negative"
    return "neutral"
