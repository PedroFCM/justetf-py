"""Shared scraping helpers for the justETF ETF profile page.

Sector and country allocations use identical markup; only the ``data-testid``
prefix and the "load more" AJAX link differ by kind, so one parameterized
scraper serves both:

1. GET the profile page to capture session cookies and locate the AJAX URL.
2. GET the AJAX endpoint (with Wicket headers) to retrieve the full list.

For ETFs with very few entries (e.g. single-commodity funds), the profile page
already contains all rows and the AJAX call is skipped.

``get_etf`` shares a single profile fetch across sectors, countries, and
metadata by passing a ``PageLoader`` callback.

The public ``sector_allocation`` / ``country_allocation`` wrappers and the
``Sector`` / ``Country`` types live here too, since both are thin specialisations
of the same parameterized scraper.
"""

import re
from collections.abc import Callable
from html import unescape
from typing import Literal, NamedTuple, TypedDict, cast

import requests

from . import _cache, _client

PROFILE_URL = "https://www.justetf.com/en/etf-profile.html"
TTL_DAY = 24 * 3600

# The two breakdown kinds the profile page exposes; a typo becomes a type error.
Kind = Literal["sectors", "countries"]

# Returns the profile page HTML, fetching it at most once across calls.
PageLoader = Callable[[], str]


class _KindRes(NamedTuple):
    """Compiled regexes for one breakdown kind."""

    name: re.Pattern[str]
    pct: re.Pattern[str]
    more: re.Pattern[str]  # "load more" AJAX link, absent on few-entry ETFs


_RES = {
    kind: _KindRes(
        name=re.compile(rf'tl_etf-holdings_{kind}_value_name"[^>]*>([^<]+)<'),
        pct=re.compile(rf'tl_etf-holdings_{kind}_value_percentage"[^>]*>([^<]+)<'),
        more=re.compile(rf'"(/en/etf-profile\.html\?[^"]*loadMore{kind.capitalize()}[^"]*)"'),
    )
    for kind in ("sectors", "countries")
}


class Allocation(TypedDict):
    """A single name/percentage breakdown entry (sector or country)."""

    name: str
    percentage: float


# Sector and country breakdowns share the same shape; the distinct public names
# document intent at call sites without duplicating the type.
Sector = Allocation
Country = Allocation


def fetch_page(session: requests.Session, isin: str) -> str:
    """Fetch the ETF profile page HTML, saving session cookies.

    Args:
        session: Open session from ``_client.new_session()``.
        isin: A valid ISIN (e.g. ``IE0003XJA0J9``).

    Returns:
        Profile page HTML.
    """
    resp = session.get(PROFILE_URL, params={"isin": isin}, timeout=_client.TIMEOUT)
    resp.raise_for_status()
    return resp.text


def _parse(html: str, kind: Kind) -> list[Allocation]:
    """Extract name/percentage pairs from an HTML or XML fragment.

    Args:
        html: Raw HTML or XML string containing justETF testid attributes.
        kind: ``"sectors"`` or ``"countries"``.

    Returns:
        List of ``{"name": str, "percentage": float}`` dicts.

    Raises:
        ValueError: If name and percentage counts differ (markup change),
            rather than silently mispairing them.
    """
    res = _RES[kind]
    names = res.name.findall(html)
    pcts = res.pct.findall(html)
    return [
        {"name": unescape(name), "percentage": float(pct.rstrip("%"))}
        for name, pct in zip(names, pcts, strict=True)
    ]


def _from_page(session: requests.Session, page: str, isin: str, kind: Kind) -> list[Allocation]:
    """Parse a kind's full breakdown from a profile page, following its AJAX link if present."""
    m = _RES[kind].more.search(page)
    if not m:
        # Few-entry ETFs embed all rows inline; no AJAX link exists.
        return _parse(page, kind)

    # The href comes from HTML, so its ampersands are escaped as &amp;
    ajax_url = f"https://www.justetf.com{unescape(m.group(1))}"
    resp = session.get(
        ajax_url,
        headers={
            "Wicket-Ajax": "true",
            "Wicket-Ajax-BaseURL": f"etf-profile.html?isin={isin}",
        },
        timeout=_client.TIMEOUT,
    )
    resp.raise_for_status()
    return _parse(resp.text, kind)


def allocation(
    isin: str,
    kind: Kind,
    session: requests.Session | None = None,
    page: PageLoader | None = None,
) -> list[Allocation]:
    """Fetch a name/percentage breakdown for an ETF by ISIN, with caching.

    Args:
        isin: A valid ISIN (e.g. ``IE0003XJA0J9``).
        kind: ``"sectors"`` or ``"countries"``.
        session: Open session to reuse; must be given together with ``page``.
        page: Loader returning already-fetched profile page HTML.

    Returns:
        List of ``{"name": str, "percentage": float}`` dicts ordered by weight.

    Raises:
        ValueError: If only one of ``session`` and ``page`` is given.
    """
    if (session is None) != (page is None):
        raise ValueError("session and page must be given together")

    cached = _cache.get(f"{kind}:{isin}")
    if cached is not None:
        return cast(list[Allocation], cached)

    if session is not None and page is not None:
        items = _from_page(session, page(), isin, kind)
    else:
        with _client.new_session() as s:
            items = _from_page(s, fetch_page(s, isin), isin, kind)

    # An empty parse means missing data or a markup change — keep it retryable.
    if items:
        _cache.set(f"{kind}:{isin}", items, TTL_DAY)
    return items


def sector_allocation(isin: str) -> list[Sector]:
    """Fetch sector allocation for an ETF by ISIN.

    Args:
        isin: A valid ISIN (e.g. ``IE0003XJA0J9``).

    Returns:
        List of ``{"name": str, "percentage": float}`` dicts ordered by weight.
    """
    return allocation(isin, "sectors")


def country_allocation(isin: str) -> list[Country]:
    """Fetch country allocation for an ETF by ISIN.

    Args:
        isin: A valid ISIN (e.g. ``IE0003XJA0J9``).

    Returns:
        List of ``{"name": str, "percentage": float}`` dicts ordered by weight.
    """
    return allocation(isin, "countries")
