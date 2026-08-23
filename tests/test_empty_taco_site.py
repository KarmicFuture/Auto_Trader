from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "empty-taco"


def test_empty_taco_site_files_exist():
    for name in ("index.html", "styles.css", "script.js", "favicon.svg"):
        assert (SITE / name).is_file()


def test_promo_page_covers_booking_menu_and_story():
    html = (SITE / "index.html").read_text()
    assert "Empty Taco" in html
    assert "Schedule us to your place" in html
    assert 'id="booking-form"' in html
    assert "Classic dog" in html
    assert "$5.00" in html
    assert "Tech people who just love a hot dog" in html
    assert "Ybor" in html


def test_booking_script_builds_a_mailto():
    js = (SITE / "script.js").read_text()
    assert "mailto:" in js
    assert "book@emptytaco.com" in js
