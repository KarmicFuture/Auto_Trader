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
    # Extra BaT category pages as (url, title_needle) pairs.
    extra_bat_pages: tuple[tuple[str, str], ...] = ()
    # Cars.com / Autotrader make-model search (not useful for kit/specialty cars).
    include_dealer_sources: bool = True
    # Include recent BaT results (useful when live specialty inventory is thin).
    bat_include_completed: bool = False

    @property
    def bat_pages(self) -> tuple[tuple[str, str], ...]:
        return ((self.bat_url, self.bat_title_needle),) + self.extra_bat_pages


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
    Watch(
        id="dune-buggy",
        label="Dune Buggy",
        make="Volkswagen",
        model="Dune Buggy",
        make_slug="volkswagen",
        model_slug="buggy",
        bat_url="https://bringatrailer.com/volkswagen/rail-dune-buggy/",
        bat_title_needle="buggy",
        autotrader_make="",
        autotrader_model="",
        year_min=1955,
        year_max=2026,
        extra_bat_pages=(
            ("https://bringatrailer.com/meyers-manx/manx/", "manx"),
        ),
        include_dealer_sources=False,
        bat_include_completed=True,
    ),
)


def get_watch(watch_id: str) -> Watch | None:
    for watch in WATCHES:
        if watch.id == watch_id:
            return watch
    return None
