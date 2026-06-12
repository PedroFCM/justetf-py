"""Country allocation fetching via the justETF ETF profile page.

The fetch/parse mechanics live in ``_profile``; this module pins the
``countries`` kind and exposes the public ``Country`` type.
"""

from typing import TypedDict, cast

from . import _profile


class Country(TypedDict):
    """A single country weight entry."""

    name: str
    percentage: float


def country_allocation(isin: str) -> list[Country]:
    """Fetch country allocation for an ETF by ISIN.

    Args:
        isin: A valid ISIN (e.g. ``IE0003XJA0J9``).

    Returns:
        List of ``{"name": str, "percentage": float}`` dicts ordered by weight.
    """
    return cast(list[Country], _profile.allocation(isin, "countries"))
