"""justetf-py: Python client for justETF sector allocation data.

Example:
    >>> from justetf import etf_sectors
    >>> etf_sectors("WEBN.DE")
    [{"name": "Technology", "percentage": 27.32}, ...]
"""

from ._gics import GICS_SECTORS, normalize_sector
from ._isin import ticker_to_isin
from ._sectors import Sector, sector_allocation
from .api import etf_sectors

__all__ = [
    "GICS_SECTORS",
    "Sector",
    "etf_sectors",
    "normalize_sector",
    "sector_allocation",
    "ticker_to_isin",
]
