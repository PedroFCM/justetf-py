import pytest
import responses as rsps_lib

from justetf import ticker_to_isin

SEARCH_URL = "https://www.justetf.com/en/search.html"

_SEARCH_HTML = (
    '<html><body id="0-1.0-container-tabsContentContainer'
    '-tabsContentRepeater-1-container-content-etfsTablePanel"></body></html>'
)
_WEBN_JSON = {
    "data": [{"isin": "IE0003XJA0J9", "ticker": "WEBN", "name": "Amundi Prime All Country World"}]
}
_CSPX_JSON = {
    "data": [
        {"isin": "IE00B5BMR087", "ticker": "SXR8", "name": "iShares Core S&P 500"},
        {"isin": "IE00B52MJY50", "ticker": "SXR1", "name": "iShares Core MSCI Pacific"},
    ]
}


@rsps_lib.activate
def test_webn_exact_match():
    rsps_lib.add(rsps_lib.GET, SEARCH_URL, body=_SEARCH_HTML)
    rsps_lib.add(rsps_lib.POST, SEARCH_URL, json=_WEBN_JSON)
    assert ticker_to_isin("WEBN.DE") == "IE0003XJA0J9"


@rsps_lib.activate
def test_cspx_falls_back_to_first_row():
    rsps_lib.add(rsps_lib.GET, SEARCH_URL, body=_SEARCH_HTML)
    rsps_lib.add(rsps_lib.POST, SEARCH_URL, json=_CSPX_JSON)
    # No row has ticker == "CSPX", so first row wins
    assert ticker_to_isin("CSPX.L") == "IE00B5BMR087"


@rsps_lib.activate
def test_unknown_ticker_returns_none():
    rsps_lib.add(rsps_lib.GET, SEARCH_URL, body=_SEARCH_HTML)
    rsps_lib.add(rsps_lib.POST, SEARCH_URL, json={"data": []})
    assert ticker_to_isin("ZZZZ.XX") is None


@rsps_lib.activate
def test_negative_result_is_cached():
    rsps_lib.add(rsps_lib.GET, SEARCH_URL, body=_SEARCH_HTML)
    rsps_lib.add(rsps_lib.POST, SEARCH_URL, json={"data": []})
    assert ticker_to_isin("ZZZZ.XX") is None
    assert ticker_to_isin("ZZZZ.XX") is None
    # Second lookup must be served from the negative cache (one GET + one POST total)
    assert len(rsps_lib.calls) == 2


@pytest.mark.live
def test_webn_live():
    assert ticker_to_isin("WEBN.DE") == "IE0003XJA0J9"
