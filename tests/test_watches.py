from src.watches import WATCHES, get_watch


def test_dune_buggy_watch_configured():
    watch = get_watch("dune-buggy")
    assert watch is not None
    assert watch.label == "Dune Buggy"
    assert watch.include_dealer_sources is False
    assert watch.bat_include_completed is True
    urls = [url for url, _needle in watch.bat_pages]
    assert "https://bringatrailer.com/volkswagen/rail-dune-buggy/" in urls
    assert "https://bringatrailer.com/meyers-manx/manx/" in urls


def test_watches_include_core_models():
    ids = {w.id for w in WATCHES}
    assert {"honda-s2000", "porsche-cayman", "dune-buggy"} <= ids
