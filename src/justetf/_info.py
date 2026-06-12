"""ETF metadata fetching from the justETF profile page.

All fields are extracted from the inline HTML on a single GET request; no AJAX
call is needed.  Fields that cannot be parsed are ``None``.
"""

import re
from html import unescape
from typing import TypedDict, cast

from . import _cache, _client, _profile

_NAME_RE = re.compile(r'etf-profile-header_etf-name"[^>]*>([^<]+)<')
_TER_RE = re.compile(r'tl_etf-basics_value_ter"[^>]*>([^<]+)<')
_REPLICATION_RE = re.compile(r'tl_etf-basics_value_replication"[^>]*>([^<]+)<')
_DOMICILE_RE = re.compile(r'tl_etf-basics_value_domicile-country"[^>]*>([^<]+)<')
_DISTRIBUTION_RE = re.compile(r'tl_etf-basics_value_distribution-policy"[^>]*>([^<]+)<')
# Matches: <div data-testid="...fund-size-value-wrapper"> <span> EUR 1,890 </span> m
_FUND_SIZE_RE = re.compile(
    r"fund-size-value-wrapper[^>]*>\s*<span>\s*([^<]+?)\s*</span>\s*([A-Za-z]+)"
)


class ETFInfo(TypedDict):
    """ETF metadata from the justETF profile page."""

    name: str
    ter: float | None  # total expense ratio, e.g. ``0.07`` for "0.07% p.a."
    fund_size: float | None  # fund size in millions of ``fund_size_currency``
    fund_size_currency: str | None  # e.g. ``"EUR"`` (justETF default display currency)
    replication: str | None  # e.g. ``"Physical"``
    domicile: str | None  # e.g. ``"Ireland"``
    distribution: str | None  # e.g. ``"Accumulating"`` or ``"Distributing"``


def _first(pattern: re.Pattern[str], html: str) -> str | None:
    m = pattern.search(html)
    return unescape(m.group(1)).strip() if m else None


def _parse_ter(raw: str) -> float | None:
    m = re.search(r"([\d.]+)%", raw)
    return float(m.group(1)) if m else None


def _parse_fund_size(html: str) -> tuple[float | None, str | None]:
    """Extract fund size in millions plus its display currency.

    Returns:
        ``(amount_in_millions, currency)``, or ``(None, None)`` if absent or
        the unit is unknown. A missing currency prefix means EUR (site default).
    """
    m = _FUND_SIZE_RE.search(html)
    if not m:
        return None, None
    cur = re.match(r"^([A-Z]{3})\s+", m.group(1))
    currency = cur.group(1) if cur else "EUR"
    # Strip currency prefix (e.g. "EUR ") and thousands commas.
    amount_str = re.sub(r"^[A-Z]+\s+", "", m.group(1)).replace(",", "").strip()
    try:
        amount = float(amount_str)
    except ValueError:
        return None, None
    unit = m.group(2).lower()
    if unit == "m":
        return amount, currency
    if unit == "bn":
        return amount * 1000, currency
    # Unknown unit: better None than a value off by orders of magnitude.
    return None, None


def _parse_info(html: str) -> ETFInfo:
    ter_raw = _first(_TER_RE, html)
    fund_size, fund_size_currency = _parse_fund_size(html)
    return ETFInfo(
        name=_first(_NAME_RE, html) or "",
        ter=_parse_ter(ter_raw) if ter_raw else None,
        fund_size=fund_size,
        fund_size_currency=fund_size_currency,
        replication=_first(_REPLICATION_RE, html),
        domicile=_first(_DOMICILE_RE, html),
        distribution=_first(_DISTRIBUTION_RE, html),
    )


def _fetch_info(isin: str, page: _profile.PageLoader | None = None) -> ETFInfo:
    """Fetch and cache metadata, optionally reusing an already-fetched page."""
    cached = _cache.get(f"info:{isin}")
    if cached is not None:
        return cast(ETFInfo, cached)

    if page is not None:
        html = page()
    else:
        with _client.new_session() as s:
            html = _profile.fetch_page(s, isin)

    info = _parse_info(html)
    # Cache only complete parses so a single broken field stays retryable.
    if info["name"] and all(v is not None for v in info.values()):
        _cache.set(f"info:{isin}", dict(info), _profile.TTL_DAY)
    return info


def etf_info(isin: str) -> ETFInfo:
    """Fetch ETF metadata for a given ISIN.

    Args:
        isin: A valid ISIN (e.g. ``IE0003XJA0J9``).

    Returns:
        ``ETFInfo`` TypedDict; unparseable fields are ``None``.
    """
    return _fetch_info(isin)
