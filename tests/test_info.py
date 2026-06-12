import pytest
import responses as rsps_lib

from justetf import etf_info

PROFILE_URL = "https://www.justetf.com/en/etf-profile.html"
ISIN = "IE0003XJA0J9"

_PROFILE_FULL = """
<html><body>
  <h1 data-testid="etf-profile-header_etf-name">Amundi Prime All Country World UCITS ETF Acc</h1>
  <div class="val bold" data-testid="etf-profile-header_fund-size-value-wrapper">
    <span> EUR 1,890 </span> m
    <span data-testid="etf-profile-header_fund-size-indicator"></span>
  </div>
  <span data-testid="tl_etf-basics_value_ter">0.07% p.a.</span>
  <span data-testid="tl_etf-basics_value_replication">Physical</span>
  <span data-testid="tl_etf-basics_value_domicile-country">Ireland</span>
  <span data-testid="tl_etf-basics_value_distribution-policy">Accumulating</span>
</body></html>
"""

_PROFILE_MISSING_FIELDS = """
<html><body>
  <h1 data-testid="etf-profile-header_etf-name">Minimal ETF</h1>
</body></html>
"""


@rsps_lib.activate
def test_parse_full_info():
    rsps_lib.add(rsps_lib.GET, PROFILE_URL, body=_PROFILE_FULL)
    result = etf_info(ISIN)
    assert result["name"] == "Amundi Prime All Country World UCITS ETF Acc"
    assert result["ter"] == 0.07
    assert result["fund_size_meur"] == 1890.0
    assert result["replication"] == "Physical"
    assert result["domicile"] == "Ireland"
    assert result["distribution"] == "Accumulating"


@rsps_lib.activate
def test_missing_optional_fields_are_none():
    rsps_lib.add(rsps_lib.GET, PROFILE_URL, body=_PROFILE_MISSING_FIELDS)
    result = etf_info(ISIN)
    assert result["name"] == "Minimal ETF"
    assert result["ter"] is None
    assert result["fund_size_meur"] is None
    assert result["replication"] is None


@rsps_lib.activate
def test_partial_parse_is_not_cached():
    rsps_lib.add(rsps_lib.GET, PROFILE_URL, body=_PROFILE_MISSING_FIELDS)
    assert etf_info(ISIN)["ter"] is None
    assert etf_info(ISIN)["ter"] is None
    # Name parsed but other fields missing: stays retryable, not cached.
    assert len(rsps_lib.calls) == 2


@rsps_lib.activate
def test_name_entities_are_unescaped():
    body = '<h1 data-testid="etf-profile-header_etf-name">iShares Core S&amp;P 500 UCITS ETF</h1>'
    rsps_lib.add(rsps_lib.GET, PROFILE_URL, body=body)
    assert etf_info(ISIN)["name"] == "iShares Core S&P 500 UCITS ETF"


def test_fund_size_units():
    from justetf._info import _parse_fund_size_meur

    html = '<div data-testid="x_fund-size-value-wrapper"><span> EUR 2.1 </span> bn'
    assert _parse_fund_size_meur(html) == 2100.0
    # Unknown unit must not be silently treated as millions.
    assert _parse_fund_size_meur(html.replace("bn", "k")) is None


@rsps_lib.activate
def test_empty_name_not_cached():
    rsps_lib.add(rsps_lib.GET, PROFILE_URL, body="<html><body></body></html>")
    result = etf_info(ISIN)
    assert result["name"] == ""
    result2 = etf_info(ISIN)
    assert result2["name"] == ""
    assert len(rsps_lib.calls) == 2


@pytest.mark.live
def test_webn_info_live():
    result = etf_info("IE0003XJA0J9")
    assert result["name"] != ""
    assert result["ter"] is not None
    assert result["ter"] < 1.0
    assert result["domicile"] is not None
