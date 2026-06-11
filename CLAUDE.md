# justetf-py — Claude Code Guide

## What this is

A minimal Python client for fetching per-sector allocation data from justETF.
Resolves ETF tickers to ISINs and returns sector weights as a list of `{name, percentage}` dicts.

## How to run

```bash
uv sync
uv run pytest                        # unit tests (mocked)
uv run pytest -m live                # live network tests against justetf.com
uv run python -c "from justetf import etf_sectors; print(etf_sectors('WEBN'))"
```

## Architecture

```
src/justetf/
  __init__.py    # re-exports only: Sector, ticker_to_isin, sector_allocation, etf_sectors
  api.py         # etf_sectors() — composes _isin + _sectors; logs failures to "justetf" logger
  _client.py     # new_session() factory — fresh requests.Session per lookup (browser UA)
  _isin.py       # ticker → ISIN via justETF screener JSON endpoint
  _sectors.py    # ISIN → sector list via profile page + Wicket AJAX; Sector TypedDict
  _cache.py      # disk cache at ~/.cache/justetf-py/ (JSON files, TTL-based, atomic writes)
  py.typed       # PEP 561 marker
tests/
  conftest.py    # autouse fixture redirects _cache._CACHE_DIR to tmp_path
  test_isin.py
  test_sectors.py
```

## justETF endpoints

### Ticker → ISIN (two requests, same session)

1. GET `https://www.justetf.com/en/search.html?search=ETFS`
   Parse Wicket counter from:
   `(\d+)-1\.0-container-tabsContentContainer-tabsContentRepeater-1-container-content-etfsTablePanel`
   (always `0` on a fresh session — parse it anyway for robustness).

2. POST `https://www.justetf.com/en/search.html?{counter}-1.0-container-tabsContentContainer-tabsContentRepeater-1-container-content-etfsTablePanel=&search=ETFS&_wicket=1`
   Form data: `draw=1&start=0&length=-1&lang=en&country=DE&universeType=private&defaultCurrency=EUR&etfsParams=search%3DETF%26productGroup%3Depg-longOnly%26ls%3Dany%26query%3D{TICKER}`
   Response: JSON `{"data": [{"isin": "...", "ticker": "...", "name": "..."}, ...]}`.

   Disambiguation: prefer exact `ticker` match; otherwise take first row (justETF ranks
   best match first).

### ISIN → sectors (two requests, same session)

1. GET `https://www.justetf.com/en/etf-profile.html?isin={ISIN}` — saves session cookies.
   - If page contains `loadMoreSectors`: that URL is the AJAX endpoint (full breakdown).
   - If absent: embedded rows are already complete (few-sector ETFs).

2. GET `https://www.justetf.com/en{loadMoreSectors_path}` with headers:
   `Wicket-Ajax: true`, `Wicket-Ajax-BaseURL: etf-profile.html?isin={ISIN}`
   Parse `data-testid="tl_etf-holdings_sectors_value_name"` and `_percentage` from the XML.

Browser User-Agent required on all requests. `Accept-Language: en` for English sector names.

## Caching

- `~/.cache/justetf-py/{sha1(key)}.json` — `{"expires": <unix_ts>, "data": ...}`
- ISIN lookups: 30-day TTL. Negative results (no match) cached as `""` with 1-day TTL.
- Sector data: 24-hour TTL. Empty parses are never cached (keeps markup breakage retryable).
- Writes are atomic (temp file + `os.replace`).

## After every change

```bash
uv run --group dev ruff check . --fix
uv run --group dev ruff format .
```

## Docstring style

Use Google-style docstrings without type annotations (types live in signatures only).

```python
def ticker_to_isin(yahoo_ticker: str) -> str | None:
    """Resolve a Yahoo Finance ticker to its ISIN via the justETF screener.

    Args:
        yahoo_ticker: Ticker with optional exchange suffix (e.g. ``WEBN.DE``).

    Returns:
        ISIN string, or ``None`` if no match is found.
    """
```

## Key conventions

- `etf_sectors()` must never raise — catch all exceptions, log to the `justetf` logger, return `[]`.
- No pandas, no BeautifulSoup — `requests` + `re` only. HTML-unescape URLs extracted from hrefs.
- Sector results are `list[Sector]` (TypedDict); `zip(..., strict=True)` so markup drift raises
  instead of mispairing names and percentages.
- Tests use `responses` library for HTTP mocking; live tests are marked `@pytest.mark.live`
  and excluded by default via `addopts = "-m 'not live'"`.
