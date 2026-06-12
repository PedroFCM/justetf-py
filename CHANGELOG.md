# Changelog

## 0.1.0 (2026-06-12)


### Features

* :sparkles: Add justetf-py 0.1.0: justETF sector allocation client  - Ticker-to-ISIN resolution via the justETF screener endpoint - Sector allocation via profile page + Wicket AJAX, with HTML-unescaped   AJAX URLs and strict name/percentage pairing - Disk cache with per-entry TTL, atomic writes, and negative-result   caching; empty parses stay retryable - Typed results (Sector TypedDict, py.typed marker) - Mocked test suite with isolated cache; live tests opt-in via -m live - PyPI-ready metadata and project tooling (ruff, pre-commit, uv) ([0e44cd2](https://github.com/PedroFCM/justetf-py/commit/0e44cd2d5e2f84b61887f50b90ea058884ba13ab))
* add country allocation, ETF metadata, and portfolio API ([6ce67d3](https://github.com/PedroFCM/justetf-py/commit/6ce67d3ea2af44af268840a6daf6cf9d23308991))
* add GICS_SECTORS constant and normalize_sector helper ([575ccf6](https://github.com/PedroFCM/justetf-py/commit/575ccf68d2b6625c303885f771a7c51fd868c092))


### Bug Fixes

* :bug: add "Telecommunication" alias for pre-2016 GICS shortening ([25b9a0b](https://github.com/PedroFCM/justetf-py/commit/25b9a0b6be331e07b33f94d9000585069dbbfb7a))
