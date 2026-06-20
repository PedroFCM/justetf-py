"""justetf-py: Python client for justETF sector and country allocation data.

Example:
    >>> from justetf import etf_sectors, get_etf
    >>> etf_sectors("WEBN.DE")
    [{"name": "Technology", "percentage": 27.32}, ...]
    >>> etf = get_etf("WEBN.DE")
    >>> etf.info["ter"]
    0.07
"""

from importlib.metadata import version as _version

from ._gics import GICS_SECTORS, normalize_sector
from ._holdings import Holding, top_holdings
from ._info import ETFInfo, etf_info
from ._isin import ticker_to_isin
from ._profile import Country, Sector, country_allocation, sector_allocation
from .api import ETF, etf_sectors, get_etf, portfolio_sectors

__version__ = _version("justetf-py")

__all__ = [
    "Country",
    "ETF",
    "ETFInfo",
    "GICS_SECTORS",
    "Holding",
    "Sector",
    "country_allocation",
    "etf_info",
    "etf_sectors",
    "get_etf",
    "normalize_sector",
    "portfolio_sectors",
    "sector_allocation",
    "ticker_to_isin",
    "top_holdings",
]
