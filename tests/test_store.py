from src.models import Listing
from src.store import SeenStore


def test_seen_store_roundtrip(tmp_path):
    path = tmp_path / "seen.json"
    store = SeenStore(path)
    listing = Listing(
        id="1",
        source="bringatrailer",
        title="2003 Honda S2000",
        url="https://example.com/1",
        price=20000,
    )
    assert store.is_new(listing)
    store.mark_seen([listing])
    store.save()

    again = SeenStore(path)
    assert not again.is_new(listing)
    assert again.count == 1
