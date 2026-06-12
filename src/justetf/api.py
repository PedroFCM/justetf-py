"""High-level convenience API composing ISIN resolution and data fetching."""

import logging
from dataclasses import dataclass
from typing import cast

from . import _client, _profile
from ._countries import Country
from ._info import ETFInfo, _fetch_info
from ._isin import ticker_to_isin
from ._sectors import Sector, sector_allocation

logger = logging.getLogger("justetf")


@dataclass
class ETF:
    """Full ETF data: sectors, countries, and metadata."""

    isin: str
    sectors: list[Sector]
    countries: list[Country]
    info: ETFInfo


def etf_sectors(ticker: str) -> list[Sector]:
    """Resolve a ticker to its ISIN and return sector weights.

    Never raises; failures are logged to the ``justetf`` logger.

    Args:
        ticker: ETF ticker with optional exchange suffix (e.g. ``WEBN.DE``).

    Returns:
        List of ``{"name": str, "percentage": float}`` dicts, or ``[]`` on any failure.
    """
    try:
        isin = ticker_to_isin(ticker)
        if not isin:
            logger.warning("etf_sectors(%r): no ISIN match", ticker)
            return []
        return sector_allocation(isin)
    except Exception:
        logger.warning("etf_sectors(%r) failed", ticker, exc_info=True)
        return []


def get_etf(ticker: str) -> ETF:
    """Resolve a ticker and fetch full ETF data (sectors, countries, metadata).

    The profile page is fetched at most once per call and shared across the
    sector, country, and metadata parsers (cached pieces skip it entirely).

    Args:
        ticker: ETF ticker with optional exchange suffix (e.g. ``WEBN.DE``).

    Returns:
        ``ETF`` dataclass populated with sectors, countries, and info.

    Raises:
        ValueError: If no ISIN is found for the ticker, or if a justETF
            markup change breaks name/percentage parsing.
        requests.HTTPError: On a non-2xx response from justETF.
    """
    isin = ticker_to_isin(ticker)
    if not isin:
        raise ValueError(f"No ISIN found for ticker {ticker!r}")

    with _client.new_session() as s:
        page_html: str | None = None

        def page() -> str:
            nonlocal page_html
            if page_html is None:
                page_html = _profile.fetch_page(s, isin)
            return page_html

        return ETF(
            isin=isin,
            sectors=cast(list[Sector], _profile.allocation(isin, "sectors", session=s, page=page)),
            countries=cast(
                list[Country], _profile.allocation(isin, "countries", session=s, page=page)
            ),
            info=_fetch_info(isin, page=page),
        )


def portfolio_sectors(weights: dict[str, float]) -> list[Sector]:
    """Return weighted blended sector allocation for a portfolio of ETFs.

    Weights are normalized before blending, so they need not sum to 1.
    Tickers with a non-positive weight or no sector data are skipped with a
    logged warning, and their weight is redistributed across the rest.

    Args:
        weights: Mapping from ticker to portfolio weight
            (e.g. ``{"WEBN.DE": 0.6, "CSPX.L": 0.4}``).

    Returns:
        List of ``{"name": str, "percentage": float}`` dicts sorted by
        descending weight.  Returns ``[]`` if no sector data is available
        for any ticker.
    """
    fetched: list[tuple[float, list[Sector]]] = []
    for ticker, w in weights.items():
        if w <= 0:
            logger.warning("portfolio_sectors: skipping %r (non-positive weight %r)", ticker, w)
            continue
        sectors = etf_sectors(ticker)
        if not sectors:
            logger.warning("portfolio_sectors: skipping %r (no sector data)", ticker)
            continue
        fetched.append((w, sectors))

    if not fetched:
        return []

    total_w = sum(w for w, _ in fetched)
    blended: dict[str, float] = {}
    for w, sectors in fetched:
        norm = w / total_w
        for s in sectors:
            blended[s["name"]] = blended.get(s["name"], 0.0) + norm * s["percentage"]

    result: list[Sector] = [{"name": name, "percentage": pct} for name, pct in blended.items()]
    result.sort(key=lambda s: s["percentage"], reverse=True)
    return result
