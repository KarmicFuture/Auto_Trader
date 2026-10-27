from datetime import datetime, timedelta, timezone

from src.inbox.models import Message, ScoredMessage
from src.inbox.store import InboxSeenStore


def make_scored(message_id="abc123"):
    msg = Message(
        source="gmail",
        conversation="Test",
        sender="a@example.com",
        text="hello",
        timestamp=datetime(2026, 8, 3, tzinfo=timezone.utc),
        message_id=message_id,
    )
    return ScoredMessage(msg, 5, ["test"])


def test_inbox_store_roundtrip(tmp_path):
    path = tmp_path / "inbox_seen.json"
    store = InboxSeenStore(path)
    scored = make_scored()

    assert store.is_new(scored)
    store.mark_seen([scored])
    store.save()

    again = InboxSeenStore(path)
    assert not again.is_new(scored)
    assert again.count == 1


def test_inbox_store_prunes_old_entries(tmp_path):
    path = tmp_path / "inbox_seen.json"
    store = InboxSeenStore(path)
    old = (datetime.now(timezone.utc) - timedelta(days=60)).isoformat()
    store._seen["gmail:ancient"] = old
    store.mark_seen([make_scored("fresh")])
    store.save()

    again = InboxSeenStore(path)
    assert again.count == 1
    assert not again.is_new(make_scored("fresh"))
