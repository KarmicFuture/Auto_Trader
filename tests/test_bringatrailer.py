from src.sources.bringatrailer import (
    _listings_from_completed_json,
    _listings_from_live_cards,
    _parse_mileage,
    _parse_year,
)


SAMPLE_HTML = """
<html><body>
<div class="listing-card listing-card-separate"
    data-listing_id="118176273"
    data-timestamp_end="1785174120">
  <a href="https://bringatrailer.com/listing/2003-honda-s2000-223/">27k-Mile 2003 Honda S2000</a>
  <p class="listing-card-excerpt">Finished in New Formula Red. Bid $45,000</p>
  <img src="https://example.com/s2k.jpg" />
</div>
<script>
var auctionsCompletedInitialData = {"items":[{"id":1,"active":false,"title":"2005 Honda S2000","url":"https://bringatrailer.com/listing/2005-honda-s2000-1/","current_bid":25000,"excerpt":"50k miles","country_code":"US"}]};
</script>
</body></html>
"""


def test_parse_year_and_mileage():
    assert _parse_year("27k-Mile 2003 Honda S2000") == 2003
    assert _parse_mileage("27k-Mile 2003 Honda S2000") == 27000
    assert _parse_mileage("car", "has 22,500 miles now") == 22500


def test_live_cards():
    listings = _listings_from_live_cards(SAMPLE_HTML)
    assert len(listings) == 1
    assert listings[0].id == "118176273"
    assert listings[0].status == "live"
    assert "S2000" in listings[0].title
    assert listings[0].price == 45000


def test_completed_json():
    listings = _listings_from_completed_json(SAMPLE_HTML)
    assert len(listings) == 1
    assert listings[0].year == 2005
    assert listings[0].price == 25000
    assert listings[0].status == "completed"
