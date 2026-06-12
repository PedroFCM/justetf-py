import pytest
import responses as rsps_lib
from requests.exceptions import ConnectionError as RequestsConnectionError

from justetf import country_allocation, etf_sectors, sector_allocation

SEARCH_URL = "https://www.justetf.com/en/search.html"
PROFILE_URL = "https://www.justetf.com/en/etf-profile.html"
ISIN = "IE0003XJA0J9"

SECTORS_AJAX_URL = (
    "https://www.justetf.com/en/etf-profile.html"
    "?0-1.0-holdingsSection-sectors-loadMoreSectors&isin=IE0003XJA0J9&_wicket=1"
)
COUNTRIES_AJAX_URL = (
    "https://www.justetf.com/en/etf-profile.html"
    "?0-1.0-holdingsSection-countries-loadMoreCountries&isin=IE0003XJA0J9&_wicket=1"
)

_SECTORS_PROFILE_WITH_MORE = """
<html><body>
  <a href="/en/etf-profile.html?0-1.0-holdingsSection-sectors-loadMoreSectors&amp;isin=IE0003XJA0J9&amp;_wicket=1">more</a>
  <span data-testid="tl_etf-holdings_sectors_value_name">Technology</span>
  <span data-testid="tl_etf-holdings_sectors_value_percentage">27.32%</span>
</body></html>
"""  # noqa: E501

_SECTORS_AJAX_RESPONSE = """
<ajax-response>
  <span data-testid="tl_etf-holdings_sectors_value_name">Technology</span>
  <span data-testid="tl_etf-holdings_sectors_value_percentage">27.32%</span>
  <span data-testid="tl_etf-holdings_sectors_value_name">Financials</span>
  <span data-testid="tl_etf-holdings_sectors_value_percentage">14.85%</span>
  <span data-testid="tl_etf-holdings_sectors_value_name">Other</span>
  <span data-testid="tl_etf-holdings_sectors_value_percentage">57.83%</span>
</ajax-response>
"""

_SECTORS_PROFILE_NO_MORE = """
<html><body>
  <span data-testid="tl_etf-holdings_sectors_value_name">Basic Materials</span>
  <span data-testid="tl_etf-holdings_sectors_value_percentage">72.93%</span>
  <span data-testid="tl_etf-holdings_sectors_value_name">Other</span>
  <span data-testid="tl_etf-holdings_sectors_value_percentage">27.07%</span>
</body></html>
"""

_COUNTRIES_PROFILE_WITH_MORE = """
<html><body>
  <a href="/en/etf-profile.html?0-1.0-holdingsSection-countries-loadMoreCountries&amp;isin=IE0003XJA0J9&amp;_wicket=1">more</a>
  <span data-testid="tl_etf-holdings_countries_value_name">United States</span>
  <span data-testid="tl_etf-holdings_countries_value_percentage">64.12%</span>
</body></html>
"""  # noqa: E501

_COUNTRIES_AJAX_RESPONSE = """
<ajax-response>
  <span data-testid="tl_etf-holdings_countries_value_name">United States</span>
  <span data-testid="tl_etf-holdings_countries_value_percentage">64.12%</span>
  <span data-testid="tl_etf-holdings_countries_value_name">Japan</span>
  <span data-testid="tl_etf-holdings_countries_value_percentage">5.81%</span>
  <span data-testid="tl_etf-holdings_countries_value_name">Other</span>
  <span data-testid="tl_etf-holdings_countries_value_percentage">30.07%</span>
</ajax-response>
"""

_COUNTRIES_PROFILE_NO_MORE = """
<html><body>
  <span data-testid="tl_etf-holdings_countries_value_name">Germany</span>
  <span data-testid="tl_etf-holdings_countries_value_percentage">100.00%</span>
</body></html>
"""


# --- sectors ---------------------------------------------------------------


@rsps_lib.activate
def test_sector_full_breakdown_via_ajax():
    rsps_lib.add(rsps_lib.GET, PROFILE_URL, body=_SECTORS_PROFILE_WITH_MORE)
    rsps_lib.add(rsps_lib.GET, SECTORS_AJAX_URL, body=_SECTORS_AJAX_RESPONSE)
    result = sector_allocation(ISIN)
    assert len(result) == 3
    assert result[0] == {"name": "Technology", "percentage": 27.32}
    assert abs(sum(r["percentage"] for r in result) - 100.0) < 0.01


@rsps_lib.activate
def test_sector_embedded_rows_when_no_ajax():
    rsps_lib.add(rsps_lib.GET, PROFILE_URL, body=_SECTORS_PROFILE_NO_MORE)
    result = sector_allocation("IE00B7KMNP07")
    assert result == [
        {"name": "Basic Materials", "percentage": 72.93},
        {"name": "Other", "percentage": 27.07},
    ]


@rsps_lib.activate
def test_etf_sectors_returns_empty_on_failure():
    rsps_lib.add(rsps_lib.GET, SEARCH_URL, body=RequestsConnectionError())
    assert etf_sectors("BADTICKER.XX") == []


@rsps_lib.activate
def test_sector_empty_parse_is_not_cached():
    rsps_lib.add(rsps_lib.GET, PROFILE_URL, body="<html><body></body></html>")
    assert sector_allocation(ISIN) == []
    assert sector_allocation(ISIN) == []
    # Second call must hit the network again, not a cached empty list
    assert len(rsps_lib.calls) == 2


@pytest.mark.live
def test_webn_sectors_live():
    result = sector_allocation("IE0003XJA0J9")
    assert len(result) > 5
    total = sum(r["percentage"] for r in result)
    assert abs(total - 100.0) < 0.5


# --- countries -------------------------------------------------------------


@rsps_lib.activate
def test_country_full_breakdown_via_ajax():
    rsps_lib.add(rsps_lib.GET, PROFILE_URL, body=_COUNTRIES_PROFILE_WITH_MORE)
    rsps_lib.add(rsps_lib.GET, COUNTRIES_AJAX_URL, body=_COUNTRIES_AJAX_RESPONSE)
    result = country_allocation(ISIN)
    assert len(result) == 3
    assert result[0] == {"name": "United States", "percentage": 64.12}
    assert abs(sum(r["percentage"] for r in result) - 100.0) < 0.01


@rsps_lib.activate
def test_country_embedded_rows_when_no_ajax():
    rsps_lib.add(rsps_lib.GET, PROFILE_URL, body=_COUNTRIES_PROFILE_NO_MORE)
    result = country_allocation("IE00B7KMNP07")
    assert result == [{"name": "Germany", "percentage": 100.0}]


@rsps_lib.activate
def test_country_empty_parse_is_not_cached():
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
