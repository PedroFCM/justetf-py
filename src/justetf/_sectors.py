"""Sector allocation fetching via the justETF ETF profile page.

The profile page embeds only the top few sectors inline. The full breakdown is
loaded via a Wicket AJAX call whose URL is present in the page HTML whenever
more than the initial set of sectors exist. Two requests are made:

1. GET the profile page to capture session cookies and locate the AJAX URL.
2. GET the AJAX endpoint (with Wicket headers) to retrieve the full sector list.

For ETFs with very few sectors (e.g. single-commodity funds), the profile page
already contains all rows and the AJAX call is skipped.
"""

import re
from html import unescape
from typing import TypedDict, cast

from . import _cache, _client

_PROFILE_URL = "https://www.justetf.com/en/etf-profile.html"
_TTL_SECTORS = 24 * 3600  # 24 hours

_NAME_RE = re.compile(r'tl_etf-holdings_sectors_value_name"[^>]*>([^<]+)<')
_PCT_RE = re.compile(r'tl_etf-holdings_sectors_value_percentage"[^>]*>([^<]+)<')
_MORE_RE = re.compile(r'"(/en/etf-profile\.html\?[^"]*loadMoreSectors[^"]*)"')


class Sector(TypedDict):
    """A single sector weight entry."""

    name: str
    percentage: float


def _parse_sectors(html: str) -> list[Sector]:
    """Extract sector name/percentage pairs from an HTML or XML fragment.

    Args:
        html: Raw HTML or XML string containing justETF sector testid attributes.

    Returns:
        List of ``{"name": str, "percentage": float}`` dicts.

    Raises:
        ValueError: If name and percentage counts differ (markup change),
            rather than silently mispairing them.
    """
    names = _NAME_RE.findall(html)
    pcts = _PCT_RE.findall(html)
    return [
        {"name": name, "percentage": float(pct.rstrip("%"))}
        for name, pct in zip(names, pcts, strict=True)
    ]


def sector_allocation(isin: str) -> list[Sector]:
    """Fetch sector allocation for an ETF by ISIN.

    Args:
        isin: A valid ISIN (e.g. ``IE0003XJA0J9``).

    Returns:
        List of ``{"name": str, "percentage": float}`` dicts ordered by weight.
    """
    cached = _cache.get(f"sectors:{isin}")
    if cached is not None:
        return cast(list[Sector], cached)

    with _client.new_session() as s:
        resp = s.get(_PROFILE_URL, params={"isin": isin}, timeout=15)
        resp.raise_for_status()
        page = resp.text

        m = _MORE_RE.search(page)
        if m:
            # The href comes from HTML, so its ampersands are escaped as &amp;
            ajax_url = f"https://www.justetf.com{unescape(m.group(1))}"
            resp = s.get(
                ajax_url,
                headers={
                    "Wicket-Ajax": "true",
                    "Wicket-Ajax-BaseURL": f"etf-profile.html?isin={isin}",
                },
                timeout=15,
            )
            resp.raise_for_status()
            sectors = _parse_sectors(resp.text)
        else:
            sectors = _parse_sectors(page)

    # An empty parse means missing data or a markup change — keep it retryable.
    if sectors:
        _cache.set(f"sectors:{isin}", sectors, _TTL_SECTORS)
    return sectors
