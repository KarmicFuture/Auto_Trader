from src.sources.carmax import (
    _facet_has_model,
    _model_matches,
    _model_paths,
    _to_listing,
)
from src.watches import get_watch


def test_model_paths_include_718_cayman():
    assert _model_paths("cayman") == ("cayman", "718-cayman")
    assert _model_paths("s2000") == ("s2000",)


def test_model_matches_718_cayman():
    assert _model_matches("718 Cayman", wanted="Cayman")
    assert _model_matches("Cayman", wanted="Cayman")
    assert not _model_matches("Cayenne", wanted="Cayman")
    assert not _model_matches("Civic", wanted="S2000")


def test_facet_has_model_detects_make_only_fallback():
    make_only = [
        {
            "category": "make",
            "name": "make",
            "value": "honda",
            "display": "Honda",
        }
    ]
    assert not _facet_has_model(make_only, model_slug="s2000")

    with_model = [
        {"name": "make", "value": "porsche", "display": "Porsche"},
        {"name": "model", "value": "cayman", "display": "Cayman"},
    ]
    assert _facet_has_model(with_model, model_slug="cayman")

    modern = [
        {"name": "make", "value": "porsche", "display": "Porsche"},
        {"name": "model", "value": "718-cayman", "display": "718 Cayman"},
    ]
    assert _facet_has_model(modern, model_slug="cayman")


def test_to_listing_carmax():
    watch = get_watch("porsche-cayman")
    assert watch is not None
    listing = _to_listing(
        {
            "stockNumber": 28398760,
            "year": 2016,
            "make": "Porsche",
            "model": "Cayman",
            "trim": "Black Edition",
            "basePrice": 45998.0,
            "mileage": 46061,
            "storeCity": "San Diego",
            "stateAbbreviation": "CA",
            "state": "California",
            "storeName": "Kearny Mesa",
            "heroImageUrl": "https://img2.carmax.com/assets/28398760/hero.jpg",
        },
        watch=watch,
    )
    assert listing is not None
    assert listing.source == "carmax"
    assert listing.id == "28398760"
    assert listing.url == "https://www.carmax.com/car/28398760"
    assert listing.price == 45998
    assert listing.mileage == 46061
    assert listing.location == "San Diego, CA"
    assert listing.notes == "Kearny Mesa"
    assert "Black Edition" in listing.title
