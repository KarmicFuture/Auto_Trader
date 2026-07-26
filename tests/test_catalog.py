from src.catalog import _us_location
from src.models import Listing


def test_strip_distance_suffix():
    listing = Listing(
        id="1",
        source="cars.com",
        title="2004 Honda S2000",
        url="https://example.com/1",
        location="Woodside, NY (5.1 mi)",
    )
    cleaned = _us_location(listing)
    assert cleaned.location == "Woodside, NY"


def test_keep_plain_location():
    listing = Listing(
        id="1",
        source="cars.com",
        title="2004 Honda S2000",
        url="https://example.com/1",
        location="Austin, TX",
    )
    assert _us_location(listing).location == "Austin, TX"
