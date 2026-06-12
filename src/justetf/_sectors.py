"""Sector allocation fetching via the justETF ETF profile page.

The fetch/parse mechanics live in ``_profile``; this module pins the
``sectors`` kind and exposes the public ``Sector`` type.
"""

from typing import TypedDict, cast

from . import _profile


class Sector(TypedDict):
    """A single sector weight entry."""

    name: str
    percentage: float


def sector_allocation(isin: str) -> list[Sector]:
    """Fetch sector allocation for an ETF by ISIN.

    Args:
        isin: A valid ISIN (e.g. ``IE0003XJA0J9``).

    Returns:
        List of ``{"name": str, "percentage": float}`` dicts ordered by weight.
    """
    return cast(list[Sector], _profile.allocation(isin, "sectors"))
