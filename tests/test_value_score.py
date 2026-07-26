from src.value_score import apply_value_score, estimate_fair_value, score_value
from src.models import Listing


def test_s2000_low_miles_scores_higher_than_high_ask():
    fair, _ = estimate_fair_value(
        watch_id="honda-s2000",
        title="2007 Honda S2000",
        year=2007,
        mileage=30000,
    )
    cheap = score_value(int(fair * 0.75), fair)
    rich = score_value(int(fair * 1.25), fair)
    assert cheap.value_score is not None and rich.value_score is not None
    assert cheap.value_score > rich.value_score
    assert cheap.value_label == "Great value"


def test_cayman_gt4_has_higher_fair_value_than_base():
    base, _ = estimate_fair_value(
        watch_id="porsche-cayman",
        title="2015 Porsche Cayman",
        year=2015,
        mileage=40000,
    )
    gt4, label = estimate_fair_value(
        watch_id="porsche-cayman",
        title="2016 Porsche Cayman GT4",
        year=2016,
        mileage=40000,
    )
    assert gt4 > base
    assert "GT4" in label


def test_apply_value_score_sets_fields():
    listing = Listing(
        id="1",
        source="cars.com",
        title="2004 Honda S2000",
        url="https://example.com/1",
        price=25000,
        year=2004,
        mileage=50000,
    )
    scored = apply_value_score(listing, "honda-s2000")
    assert scored.fair_value is not None
    assert scored.value_score is not None
    assert scored.value_label is not None
    assert scored.watch_id == "honda-s2000"
