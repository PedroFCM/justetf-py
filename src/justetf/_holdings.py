"""Top-holdings scraping from the justETF profile page.

The profile page embeds the top constituent positions inline (the "Top 10
holdings" table). Unlike sectors and countries there is no AJAX "load more"
link, so every row is already present on the single profile-page GET.

Each row carries the holding name, its ISIN (encoded in the stock-profile
``href``), and the portfolio weight. ``get_etf`` reuses the shared page so
holdings cost no extra request.
"""

import re
from html import unescape
from typing import TypedDict, cast

from . import _cache, _client, _profile

# ISIN sits in the stock-profile href; the full name is in the title attribute.
_NAME_RE = re.compile(
    r'tl_etf-holdings_top-holdings_link_name"\s+href="/en/stock-profiles/([^"]+)"\s+title="([^"]*)"'
)
_PCT_RE = re.compile(r'tl_etf-holdings_top-holdings_value_percentage"[^>]*>([^<]+)<')


class Holding(TypedDict):
    """A single ETF constituent position."""

    name: str
    isin: str
    percentage: float  # portfolio weight, e.g. ``4.84`` for "4.84%"


def _parse(html: str) -> list[Holding]:
    """Extract holding rows from profile-page HTML.

    Args:
        html: Raw profile-page HTML containing justETF testid attributes.

    Returns:
        List of ``{"name": str, "isin": str, "percentage": float}`` dicts.

    Raises:
        ValueError: If name and percentage counts differ (markup change),
            rather than silently mispairing them.
    """
    rows = _NAME_RE.findall(html)
    pcts = _PCT_RE.findall(html)
    return [
        {"name": unescape(name), "isin": isin, "percentage": float(pct.rstrip("%"))}
        for (isin, name), pct in zip(rows, pcts, strict=True)
    ]


def _fetch_holdings(isin: str, page: _profile.PageLoader | None = None) -> list[Holding]:
    """Fetch and cache top holdings, optionally reusing an already-fetched page."""
    cached = _cache.get(f"top-holdings:{isin}")
    if cached is not None:
        return cast(list[Holding], cached)

    if page is not None:
        html = page()
    else:
        with _client.new_session() as s:
            html = _profile.fetch_page(s, isin)

    items = _parse(html)
    # An empty parse means missing data or a markup change — keep it retryable.
    if items:
        _cache.set(f"top-holdings:{isin}", items, _profile.TTL_DAY)
    return items


def top_holdings(isin: str) -> list[Holding]:
    """Fetch the top constituent holdings for an ETF by ISIN.

    Args:
        isin: A valid ISIN (e.g. ``IE0003XJA0J9``).

    Returns:
        List of ``{"name": str, "isin": str, "percentage": float}`` dicts
        ordered by weight (descending). Empty if no holdings are published.
    """
    return _fetch_holdings(isin)
