from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Watch:
    """A make/model the board tracks nationwide."""

    id: str
    label: str
    make: str
    model: str
    make_slug: str
    model_slug: str
    bat_url: str
    bat_title_needle: str
    autotrader_make: str
    autotrader_model: str
    year_min: int
    year_max: int


WATCHES: tuple[Watch, ...] = (
    Watch(
        id="honda-s2000",
        label="Honda S2000",
        make="Honda",
        model="S2000",
        make_slug="honda",
        model_slug="s2000",
        bat_url="https://bringatrailer.com/honda/s2000/",
        bat_title_needle="s2000",
        autotrader_make="HONDA",
        autotrader_model="S2000",
        year_min=1999,
        year_max=2009,
    ),
    Watch(
        id="porsche-cayman",
        label="Porsche Cayman",
        make="Porsche",
        model="Cayman",
        make_slug="porsche",
        model_slug="cayman",
        bat_url="https://bringatrailer.com/porsche/cayman/",
        bat_title_needle="cayman",
        autotrader_make="PORSCHE",
        autotrader_model="CAYMAN",
        year_min=2006,
        year_max=2026,
    ),
)


def get_watch(watch_id: str) -> Watch | None:
    for watch in WATCHES:
        if watch.id == watch_id:
            return watch
    return None
