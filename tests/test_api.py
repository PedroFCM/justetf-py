import pytest
import responses as rsps_lib

from justetf import api as api_mod
from justetf import get_etf, portfolio_sectors

PROFILE_URL = "https://www.justetf.com/en/etf-profile.html"
ISIN = "IE0003XJA0J9"

_PROFILE = """
<html><body>
  <h1 data-testid="etf-profile-header_etf-name">Amundi Prime All Country World UCITS ETF Acc</h1>
  <div class="val bold" data-testid="etf-profile-header_fund-size-value-wrapper">
    <span> EUR 1,890 </span> m
  </div>
  <span data-testid="tl_etf-basics_value_ter">0.07% p.a.</span>
  <span data-testid="tl_etf-basics_value_replication">Physical</span>
  <span data-testid="tl_etf-basics_value_domicile-country">Ireland</span>
  <span data-testid="tl_etf-basics_value_distribution-policy">Accumulating</span>
  <span data-testid="tl_etf-holdings_sectors_value_name">Technology</span>
  <span data-testid="tl_etf-holdings_sectors_value_percentage">27.32%</span>
  <span data-testid="tl_etf-holdings_countries_value_name">United States</span>
  <span data-testid="tl_etf-holdings_countries_value_percentage">64.12%</span>
</body></html>
"""


@rsps_lib.activate
def test_get_etf_fetches_profile_once(monkeypatch):
    monkeypatch.setattr(api_mod, "ticker_to_isin", lambda t: ISIN)
    rsps_lib.add(rsps_lib.GET, PROFILE_URL, body=_PROFILE)
    etf = get_etf("WEBN.DE")
    assert etf.isin == ISIN
    assert etf.sectors == [{"name": "Technology", "percentage": 27.32}]
    assert etf.countries == [{"name": "United States", "percentage": 64.12}]
    assert etf.info["name"] == "Amundi Prime All Country World UCITS ETF Acc"
    assert etf.info["ter"] == 0.07
    assert etf.info["fund_size"] == 1890.0
    assert etf.info["fund_size_currency"] == "EUR"
    # Sectors, countries, and info share a single profile-page fetch.
    assert len(rsps_lib.calls) == 1


def test_get_etf_unknown_ticker_raises(monkeypatch):
    monkeypatch.setattr(api_mod, "ticker_to_isin", lambda t: None)
    with pytest.raises(ValueError, match="NOPE"):
        get_etf("NOPE")


def test_portfolio_sectors_blends(monkeypatch):
    data = {
        "AAA": [{"name": "Tech", "percentage": 50.0}, {"name": "Health", "percentage": 50.0}],
        "BBB": [{"name": "Tech", "percentage": 100.0}],
    }
    monkeypatch.setattr(api_mod, "etf_sectors", lambda t: data[t])
    result = portfolio_sectors({"AAA": 0.5, "BBB": 0.5})
    assert result == [
        {"name": "Tech", "percentage": 75.0},
        {"name": "Health", "percentage": 25.0},
    ]


def test_portfolio_sectors_normalizes_weights(monkeypatch):
    monkeypatch.setattr(api_mod, "etf_sectors", lambda t: [{"name": "Tech", "percentage": 100.0}])
    result = portfolio_sectors({"AAA": 2.0, "BBB": 6.0})
    assert result == [{"name": "Tech", "percentage": 100.0}]


def test_portfolio_sectors_skips_tickers_without_data(monkeypatch):
    data = {"AAA": [{"name": "Tech", "percentage": 100.0}], "BAD": []}
    monkeypatch.setattr(api_mod, "etf_sectors", lambda t: data[t])
    result = portfolio_sectors({"AAA": 0.25, "BAD": 0.75})
    assert result == [{"name": "Tech", "percentage": 100.0}]


def test_portfolio_sectors_zero_weights_do_not_divide_by_zero(monkeypatch):
    fetched_tickers = []

    def fake_etf_sectors(ticker):
        fetched_tickers.append(ticker)
        return [{"name": "Tech", "percentage": 100.0}]

    monkeypatch.setattr(api_mod, "etf_sectors", fake_etf_sectors)
    assert portfolio_sectors({"AAA": 0.0, "BBB": -1.0}) == []
    # Non-positive weights are skipped before any fetch happens.
    assert fetched_tickers == []


def test_portfolio_sectors_empty_weights():
    assert portfolio_sectors({}) == []
