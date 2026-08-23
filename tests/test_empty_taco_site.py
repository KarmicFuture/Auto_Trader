from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "empty-taco"


def test_empty_taco_site_files_exist():
    for name in ("index.html", "styles.css", "script.js", "favicon.svg"):
        assert (SITE / name).is_file()


def test_promo_page_covers_booking_menu_story_and_merch():
    html = (SITE / "index.html").read_text()
    assert "Empty Taco" in html
    assert "Schedule us to your place" in html
    assert 'id="booking-form"' in html
    assert "$3.00" in html
    assert "$5.00" in html
    assert "chips" in html.lower()
    assert "fix a bad day" in html.lower()
    assert "implement fun" in html.lower() or "put fun" in html.lower()
    assert 'id="merch"' in html
    assert "NO TACOS tee" in html
    assert "Ybor" in html
    assert 'id="send"' in html
    assert "$20" in html
    assert "Send a hot dog to a friend" in html
    assert 'id="send-form"' in html


def test_booking_script_builds_a_mailto():
    js = (SITE / "script.js").read_text()
    assert "mailto:" in js
    assert "book@emptytaco.com" in js
    assert "classic: 3" in js
    assert "combo: 5" in js
