# justetf-py — Claude Code Guide

## What this is

A minimal Python client for fetching ETF data from justETF: sector and country
allocations as lists of `{name, percentage}` dicts, plus profile metadata (TER,
fund size, replication, domicile, distribution). Resolves ETF tickers to ISINs.

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
  __init__.py    # re-exports only (Sector, Country, ETFInfo, ETF, etf_sectors, get_etf, ...)
  api.py         # etf_sectors() (never raises), get_etf(), portfolio_sectors(), ETF dataclass
  _client.py     # new_session() factory — fresh requests.Session per lookup (browser UA)
  _isin.py       # ticker → ISIN via justETF screener JSON endpoint
  _profile.py    # shared profile-page scraping: fetch_page(), parameterized sector/country
                 # allocation (regexes keyed by kind), caching; PageLoader for shared fetches.
                 # Also hosts the Sector/Country types (aliases of one Allocation TypedDict)
                 # and the public sector_allocation()/country_allocation() wrappers.
  _info.py       # ETFInfo metadata (name, TER, fund size, ...) parsed from the profile page
  _cache.py      # disk cache at ~/.cache/justetf-py/ (JSON files, TTL-based, atomic writes)
  py.typed       # PEP 561 marker
tests/
  conftest.py    # autouse fixture redirects _cache._CACHE_DIR to tmp_path
  test_isin.py
  test_allocation.py  # sector_allocation + country_allocation (shared _profile scraper)
  test_info.py
  test_api.py    # get_etf (single page fetch) + portfolio_sectors (mocked etf_sectors)
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

### ISIN → sectors/countries (two requests, same session)

1. GET `https://www.justetf.com/en/etf-profile.html?isin={ISIN}` — saves session cookies.
   - If page contains `loadMoreSectors` / `loadMoreCountries`: that URL is the AJAX
     endpoint (full breakdown).
   - If absent: embedded rows are already complete (few-entry ETFs).

2. GET `https://www.justetf.com/en{loadMore_path}` with headers:
   `Wicket-Ajax: true`, `Wicket-Ajax-BaseURL: etf-profile.html?isin={ISIN}`
   Parse `data-testid="tl_etf-holdings_{sectors|countries}_value_name"` and
   `_percentage` from the XML.

### ISIN → metadata (one request)

All `ETFInfo` fields come from inline profile-page HTML (`etf-profile-header_etf-name`,
`tl_etf-basics_value_*` testids, `fund-size-value-wrapper`). `get_etf()` fetches the
profile page at most once and shares it across all three parsers via a `PageLoader`.

Browser User-Agent required on all requests. `Accept-Language: en` for English names.

## Caching

- `~/.cache/justetf-py/{sha1(key)}.json` — `{"expires": <unix_ts>, "data": ...}`
- ISIN lookups: 30-day TTL. Negative results (no match) cached as `""` with 1-day TTL.
- Sector/country data: 24-hour TTL. Empty parses are never cached (keeps markup
  breakage retryable).
- Metadata: 24-hour TTL. Cached only when every field parsed; partial parses stay retryable.
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

- `etf_sectors()` and `portfolio_sectors()` must never raise — failures are logged to the
  `justetf` logger and skipped. `get_etf()` raises (`ValueError`, `requests.HTTPError`) by design.
- No pandas, no BeautifulSoup — `requests` + `re` only. HTML-unescape URLs extracted from
  hrefs AND all text captured from HTML (names can contain `&amp;`, e.g. "S&P 500").
- Allocation results are `list[Sector]` / `list[Country]` (TypedDicts); `zip(..., strict=True)`
  so markup drift raises instead of mispairing names and percentages.
- Tests use `responses` library for HTTP mocking; live tests are marked `@pytest.mark.live`
  and excluded by default via `addopts = "-m 'not live'"`.
