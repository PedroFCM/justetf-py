import pytest
import responses as rsps_lib

from justetf import country_allocation

PROFILE_URL = "https://www.justetf.com/en/etf-profile.html"
AJAX_URL = (
    "https://www.justetf.com/en/etf-profile.html"
    "?0-1.0-holdingsSection-countries-loadMoreCountries&isin=IE0003XJA0J9&_wicket=1"
)
ISIN = "IE0003XJA0J9"

_PROFILE_WITH_MORE = """
<html><body>
  <a href="/en/etf-profile.html?0-1.0-holdingsSection-countries-loadMoreCountries&amp;isin=IE0003XJA0J9&amp;_wicket=1">more</a>
  <span data-testid="tl_etf-holdings_countries_value_name">United States</span>
  <span data-testid="tl_etf-holdings_countries_value_percentage">64.12%</span>
</body></html>
"""  # noqa: E501

_AJAX_RESPONSE = """
<ajax-response>
  <span data-testid="tl_etf-holdings_countries_value_name">United States</span>
  <span data-testid="tl_etf-holdings_countries_value_percentage">64.12%</span>
  <span data-testid="tl_etf-holdings_countries_value_name">Japan</span>
  <span data-testid="tl_etf-holdings_countries_value_percentage">5.81%</span>
  <span data-testid="tl_etf-holdings_countries_value_name">Other</span>
  <span data-testid="tl_etf-holdings_countries_value_percentage">30.07%</span>
</ajax-response>
"""

_PROFILE_NO_MORE = """
<html><body>
  <span data-testid="tl_etf-holdings_countries_value_name">Germany</span>
  <span data-testid="tl_etf-holdings_countries_value_percentage">100.00%</span>
</body></html>
"""


@rsps_lib.activate
def test_full_breakdown_via_ajax():
    rsps_lib.add(rsps_lib.GET, PROFILE_URL, body=_PROFILE_WITH_MORE)
    rsps_lib.add(rsps_lib.GET, AJAX_URL, body=_AJAX_RESPONSE)
    result = country_allocation(ISIN)
    assert len(result) == 3
    assert result[0] == {"name": "United States", "percentage": 64.12}
    assert abs(sum(r["percentage"] for r in result) - 100.0) < 0.01


@rsps_lib.activate
def test_embedded_rows_when_no_ajax():
    rsps_lib.add(rsps_lib.GET, PROFILE_URL, body=_PROFILE_NO_MORE)
    result = country_allocation("IE00B7KMNP07")
    assert result == [{"name": "Germany", "percentage": 100.0}]


@rsps_lib.activate
def test_empty_parse_is_not_cached():
    rsps_lib.add(rsps_lib.GET, PROFILE_URL, body="<html><body></body></html>")
    assert country_allocation(ISIN) == []
    assert country_allocation(ISIN) == []
    assert len(rsps_lib.calls) == 2


@rsps_lib.activate
def test_country_name_entities_are_unescaped():
    body = """
    <html><body>
      <span data-testid="tl_etf-holdings_countries_value_name">Trinidad &amp; Tobago</span>
      <span data-testid="tl_etf-holdings_countries_value_percentage">1.00%</span>
    </body></html>
    """
    rsps_lib.add(rsps_lib.GET, PROFILE_URL, body=body)
    assert country_allocation(ISIN) == [{"name": "Trinidad & Tobago", "percentage": 1.0}]


@pytest.mark.live
def test_webn_countries_live():
    result = country_allocation("IE0003XJA0J9")
    assert len(result) > 5
    total = sum(r["percentage"] for r in result)
    assert abs(total - 100.0) < 0.5
