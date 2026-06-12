"""Ticker-to-ISIN resolution via the justETF screener JSON endpoint.

The screener exposes a Wicket-powered DataTable that accepts a ``query`` parameter.
Two requests are made on a fresh session:

1. GET the screener page to obtain the Wicket page-state counter and session cookies.
2. POST to the DataTable endpoint with the bare ticker as the query string.

The response is JSON with a ``data`` array of ETF rows. When multiple rows are
returned (e.g. fuzzy matches), the row whose ``ticker`` field matches exactly is
preferred; otherwise the first row is taken (justETF ranks the best match first).
"""

import logging
import re

from . import _cache, _client

logger = logging.getLogger("justetf")

_SEARCH_URL = "https://www.justetf.com/en/search.html"
_COUNTER_RE = re.compile(
    r"(\d+)-1\.0-container-tabsContentContainer-tabsContentRepeater"
    r"-1-container-content-etfsTablePanel"
)
_TTL_ISIN = 30 * 24 * 3600  # 30 days
_TTL_MISS = 24 * 3600  # 1 day for tickers with no match
_MISS = ""  # cached sentinel for negative results (None means "not cached")


def _strip_suffix(yahoo_ticker: str) -> str:
    """Strip the exchange suffix from a Yahoo Finance ticker.

    Args:
        yahoo_ticker: Ticker string such as ``WEBN.DE`` or ``CSPX.L``.

    Returns:
        Bare ticker in uppercase, e.g. ``WEBN``.
    """
    return re.sub(r"\.[A-Z]+$", "", yahoo_ticker.upper())


def ticker_to_isin(yahoo_ticker: str) -> str | None:
    """Resolve a Yahoo Finance ticker to its ISIN via the justETF screener.

    Args:
        yahoo_ticker: Ticker with optional exchange suffix (e.g. ``WEBN.DE``).

    Returns:
        ISIN string, or ``None`` if no match is found.
    """
    base = _strip_suffix(yahoo_ticker)
    cached = _cache.get(f"isin:{base}")
    if isinstance(cached, str):
        return cached or None

    with _client.new_session() as s:
        resp = s.get(_SEARCH_URL, params={"search": "ETFS"}, timeout=_client.TIMEOUT)
        resp.raise_for_status()

        m = _COUNTER_RE.search(resp.text)
        counter = m.group(1) if m else "0"

        endpoint = (
            f"{_SEARCH_URL}?{counter}-1.0-container-tabsContentContainer"
            f"-tabsContentRepeater-1-container-content-etfsTablePanel"
            f"=&search=ETFS&_wicket=1"
        )
        etf_params = f"search=ETF&productGroup=epg-longOnly&ls=any&query={base}"
        data = {
            "draw": 1,
            "start": 0,
            "length": -1,
            "lang": "en",
            "country": "DE",
            "universeType": "private",
            "defaultCurrency": "EUR",
            "etfsParams": etf_params,
        }
        resp = s.post(endpoint, data=data, timeout=_client.TIMEOUT)
        resp.raise_for_status()

    rows = resp.json().get("data", [])
    if not rows:
        _cache.set(f"isin:{base}", _MISS, _TTL_MISS)
        return None

    # Prefer an exact ticker match; otherwise trust justETF's ranking (first row).
    row = next((r for r in rows if r.get("ticker") == base), rows[0])
    isin = row.get("isin")
    if not isin:
        # Schema drift: row exists but carries no ISIN. Do not cache; retryable.
        logger.warning("ticker_to_isin(%r): screener row missing 'isin' field", base)
        return None
    _cache.set(f"isin:{base}", isin, _TTL_ISIN)
    return isin
