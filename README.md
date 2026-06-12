# justetf-py

[![CI](https://github.com/PedroFCM/justetf-py/actions/workflows/ci.yml/badge.svg)](https://github.com/PedroFCM/justetf-py/actions/workflows/ci.yml)

Python client for fetching ETF data from [justETF](https://www.justetf.com): sector and country
allocations, fund metadata, and portfolio-level blending. Resolves ETF tickers to ISINs
automatically.

## Installation

```bash
pip install justetf-py
```

> Not yet on PyPI. Install directly from GitHub in the meantime:
> ```bash
> pip install git+https://github.com/PedroFCM/justetf-py.git
> ```

## Usage

### Full ETF data in one call

```python
from justetf import get_etf

etf = get_etf("WEBN.DE")

etf.isin                  # "IE0003XJA0J9"
etf.sectors               # [{"name": "Technology", "percentage": 27.32}, ...]
etf.countries             # [{"name": "United States", "percentage": 63.1}, ...]
etf.info["name"]          # "Amundi MSCI World UCITS ETF"
etf.info["ter"]           # 0.07
etf.info["fund_size_meur"]  # 4200.0
etf.info["replication"]   # "Physical"
etf.info["domicile"]      # "Luxembourg"
etf.info["distribution"]  # "Accumulating"
```

`get_etf()` fetches the profile page once and shares it across all three parsers.
Raises `ValueError` if the ticker is unknown, `requests.HTTPError` on network errors.

### Sector allocation only

```python
from justetf import etf_sectors

sectors = etf_sectors("WEBN.DE")
# [{"name": "Technology", "percentage": 27.32}, {"name": "Financials", "percentage": 14.85}, ...]
```

`etf_sectors()` never raises — returns `[]` on any failure. Failures are logged to the
`justetf` logger.

### Portfolio blending

```python
from justetf import portfolio_sectors

blended = portfolio_sectors({"WEBN.DE": 0.6, "CSPX.L": 0.4})
# [{"name": "Technology", "percentage": 26.1}, ...]
```

Weights are normalized before blending, so they need not sum to 1. Tickers with no sector
data are skipped with a logged warning.

### Lower-level access

```python
from justetf import ticker_to_isin, sector_allocation, country_allocation, etf_info

isin = ticker_to_isin("CSPX.L")          # "IE00B5BMR087"
sectors = sector_allocation(isin)         # list[Sector]
countries = country_allocation(isin)      # list[Country]
info = etf_info(isin)                     # ETFInfo TypedDict
```

## How it works

1. **Ticker → ISIN**: queries the justETF screener JSON endpoint (exchange suffix stripped:
   `WEBN.DE` → `WEBN`).
2. **ISIN → data**: fetches the ETF profile page, then calls the Wicket AJAX endpoint for
   full sector/country breakdowns. Metadata is parsed from the same profile page HTML.

## Caching

Results are cached on disk at `~/.cache/justetf-py/`:

| Data | TTL |
|------|-----|
| ISIN lookups | 30 days |
| Sector / country allocations | 24 hours |
| ETF metadata | 24 hours |
| Unknown-ticker misses | 1 day |

Empty parses are never cached, so transient markup failures stay retryable.

## Supported tickers

Any ETF listed on [justETF](https://www.justetf.com) — primarily European-listed ETFs
(XETRA `.DE`, London Stock Exchange `.L`, etc.). Exchange suffixes are stripped automatically,
so both `WEBN` and `WEBN.DE` work.

## Development

```bash
uv sync --group dev
uv run pytest              # mocked unit tests
uv run pytest -m live      # live tests (requires network)
uv run ruff check . --fix
uv run ruff format .
```

## License

MIT
