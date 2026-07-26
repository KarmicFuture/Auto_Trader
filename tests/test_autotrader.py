from src.sources.autotrader import _to_listing


def test_autotrader_to_listing():
    item = {
        "id": 123456,
        "year": 2003,
        "make": "Honda",
        "model": "S2000",
        "title": "2003 Honda S2000",
        "pricingDetail": {"salePrice": 27500},
        "specifications": {"mileage": {"value": "61,200", "label": "miles"}},
        "owner": {"city": "Austin", "state": "TX", "name": "Example Motors"},
        "images": [{"src": "https://example.com/s2k.jpg"}],
    }
    listing = _to_listing(item)
    assert listing is not None
    assert listing.source == "autotrader"
    assert listing.id == "123456"
    assert listing.price == 27500
    assert listing.mileage == 61200
    assert listing.location == "Austin, TX"
    assert "listingId=123456" in listing.url
