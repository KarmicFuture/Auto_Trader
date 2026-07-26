from src.sources.autotempest import _jquery_param, _parse_price, _token_for, AutoTempestClient


def test_token_matches_known_capture():
    params = {
        "make": "honda",
        "model": "s2000",
        "radius": "500",
        "originalradius": "500",
        "zip": "10001",
        "sort": "best_match",
        "sites": "cm",
        "deduplicationSites": "te|hem|cs|cv|cm|eb|ot|extended|fbm|st",
        "rpp": "50",
    }
    assert (
        _token_for(params)
        == "44022a94ef29e04ebc4b3cd2c26de8ce49971c5ba1359f9e68180ec611bd1ec3"
    )


def test_jquery_param_encodes_pipe():
    assert "deduplicationSites=te%7Chem" in _jquery_param(
        {"deduplicationSites": "te|hem"}
    )


def test_parse_price():
    assert _parse_price("$48,175") == 48175
    assert _parse_price(12000) == 12000


def test_to_listing_cars_com():
    item = {
        "id": "cm-abc",
        "externalId": "abc",
        "title": "2004 Honda S2000",
        "year": "2004",
        "price": "$48,175",
        "mileage": "52,643",
        "location": "Woodside, NY",
        "distance": 5.1,
        "url": "https://www.cars.com/vehicledetail/abc/?aff=atempest&utm_source=x",
        "dealerName": "Paragon Honda",
        "imgSource": "https://example.com/a.jpg",
    }
    listing = AutoTempestClient._to_listing(item, source_name="cars.com")
    assert listing is not None
    assert listing.source == "cars.com"
    assert listing.price == 48175
    assert listing.mileage == 52643
    assert listing.url == "https://www.cars.com/vehicledetail/abc/"
    assert "Woodside" in (listing.location or "")
