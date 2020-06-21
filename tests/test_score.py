from src.score import score, score_vader, score_textblob, label


def test_label_thresholds():
    assert label(0.5) == "positive"
    assert label(-0.5) == "negative"
    assert label(0.0) == "neutral"
    assert label(0.04) == "neutral"
    assert label(-0.04) == "neutral"


def test_vader_positive():
    s = score_vader("I love this so much, absolutely amazing!")
    assert s > 0.5


def test_vader_negative():
    s = score_vader("This is terrible. I hate it.")
    assert s < -0.3


def test_textblob_runs():
    s = score_textblob("Great product, would recommend.")
    assert -1.0 <= s <= 1.0


def test_score_ensemble_returns_three_values():
    combined, v, t = score("happy day, all good")
    assert combined > 0
    assert -1.0 <= v <= 1.0
    assert -1.0 <= t <= 1.0


def test_empty_text_does_not_crash():
    combined, v, t = score("")
    assert combined == 0 or abs(combined) < 0.01
