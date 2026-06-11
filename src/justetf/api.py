"""High-level convenience API composing ISIN resolution and sector fetching."""

import logging

from ._isin import ticker_to_isin
from ._sectors import Sector, sector_allocation

logger = logging.getLogger("justetf")


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
