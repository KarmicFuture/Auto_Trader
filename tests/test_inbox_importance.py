from datetime import datetime, timezone

from src.inbox.importance import filter_important, score_message
from src.inbox.models import Message


def make_message(**overrides):
    defaults = dict(
        source="gmail",
        conversation="Lunch plans",
        sender="friend@example.com",
        text="Want to grab lunch sometime next month?",
        timestamp=datetime(2026, 8, 3, 12, 0, tzinfo=timezone.utc),
    )
    defaults.update(overrides)
    return Message(**defaults)


def test_urgent_message_scores_high():
    msg = make_message(
        conversation="URGENT: server down",
        text="Please respond ASAP, this is critical and needs action today.",
    )
    scored = score_message(msg)
    assert scored.score >= 4
    assert "urgent language" in scored.reasons


def test_vip_sender_boosts_score():
    cfg = {"vip_senders": ["boss@company.com"]}
    msg = make_message(sender="Big Boss <boss@company.com>", text="Quick question for you?")
    scored = score_message(msg, cfg)
    assert "VIP sender" in scored.reasons
    assert scored.score >= 4


def test_custom_keyword_matches():
    cfg = {"keywords": ["s2000"]}
    msg = make_message(text="Saw a clean S2000 at the meet, you interested?")
    scored = score_message(msg, cfg)
    assert "watched keyword" in scored.reasons


def test_newsletter_is_penalized():
    msg = make_message(
        sender="Deals <no-reply@shop.example.com>",
        conversation="FLASH SALE 50% off today only!!!",
        text="Unsubscribe at any time. View this email in your browser.",
    )
    scored = score_message(msg)
    assert scored.score < 3


def test_muted_sender_never_alerts():
    cfg = {"muted_senders": ["spammy"], "min_importance": 1}
    msg = make_message(sender="spammy@example.com", text="URGENT deadline call me ASAP")
    scored = score_message(msg, cfg)
    assert scored.score == 0
    assert scored.reasons == ["muted"]


def test_discord_mention_and_dm_boost():
    msg = make_message(
        source="discord",
        conversation="#general",
        sender="teammate",
        text="hey can you look at this?",
        extra={"mentions_me": True, "is_dm": False},
    )
    scored = score_message(msg)
    assert "you were mentioned" in scored.reasons
    assert scored.score >= 4


def test_filter_important_sorts_and_thresholds():
    important = make_message(
        text="URGENT: need you to confirm payment of $500 by end of day"
    )
    boring = make_message(text="ok cool")
    result = filter_important([boring, important], {"min_importance": 3})
    assert len(result) == 1
    assert result[0].message is important


def test_score_clamped_to_ten():
    cfg = {"vip_senders": ["boss"], "keywords": ["merger"]}
    msg = make_message(
        sender="boss",
        text=(
            "URGENT merger deadline today — can you confirm the $2M wire "
            "transfer before our meeting? Call me ASAP."
        ),
        extra={"mentions_me": True, "is_dm": True},
    )
    scored = score_message(msg, cfg)
    assert scored.score == 10
