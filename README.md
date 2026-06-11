# justetf-py

Python client for fetching ETF sector allocation data from [justETF](https://www.justetf.com).

Resolves ETF tickers to ISINs and returns per-sector percentage weights — useful for enriching
portfolio analytics with real sector breakdowns instead of treating ETFs as a single opaque bucket.

## Installation

```bash
pip install justetf-py
```

> Not yet on PyPI. Install directly from GitHub in the meantime:
> ```bash
> pip install git+https://github.com/pedrofcmachado/justetf-py.git
> ```

## Usage

```python
from justetf import etf_sectors, ticker_to_isin, sector_allocation

# Convenience: ticker → sectors in one call
sectors = etf_sectors("WEBN.DE")
# [{"name": "Technology", "percentage": 27.32}, {"name": "Financials", "percentage": 14.85}, ...]

# Step by step
isin = ticker_to_isin("CSPX.L")          # "IE00B5BMR087"
sectors = sector_allocation(isin)
```

`etf_sectors()` never raises — it returns `[]` if the ticker is unknown or justETF is unreachable.
Failures are logged to the `justetf` logger for debugging.

Results are fully typed (`Sector` TypedDict, `py.typed` marker included). Requires Python 3.10+.

## How it works

1. **Ticker → ISIN**: queries the justETF screener JSON endpoint with the bare ticker
   (exchange suffix stripped: `WEBN.DE` → `WEBN`).
2. **ISIN → sectors**: fetches the ETF profile page, then calls the Wicket AJAX endpoint
   for the full sector breakdown.

Results are cached on disk (`~/.cache/justetf-py/`): ISINs for 30 days, sector data for
24 hours, unknown-ticker misses for 24 hours. Empty sector parses are never cached, so
transient failures stay retryable.

## Supported tickers

Any ETF listed on [justETF](https://www.justetf.com) — primarily European-listed ETFs
(e.g. XETRA `.DE`, London Stock Exchange `.L`). Exchange suffixes are stripped automatically,
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
