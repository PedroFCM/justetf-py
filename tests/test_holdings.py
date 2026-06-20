import pytest
import responses as rsps_lib

from justetf import top_holdings
from justetf._holdings import _parse

PROFILE_URL = "https://www.justetf.com/en/etf-profile.html"
ISIN = "IE0003XJA0J9"


def _row(isin: str, name: str, pct: str) -> str:
    return (
        f'<tr data-testid="etf-holdings_top-holdings_row">'
        f'<td><a data-testid="tl_etf-holdings_top-holdings_link_name" '
        f'href="/en/stock-profiles/{isin}" title="{name}"><span>{name}</span></a></td>'
        f'<td><span data-testid="tl_etf-holdings_top-holdings_value_percentage">{pct}</span></td>'
        f"</tr>"
    )


_PROFILE = f"""
<html><body>
  <table data-testid="etf-holdings_top-holdings_table"><tbody>
    {_row("US67066G1040", "NVIDIA Corp.", "4.84%")}
    {_row("US0378331005", "Apple", "4.09%")}
    {_row("US5949181045", "Microsoft", "3.17%")}
  </tbody></table>
</body></html>
"""


@rsps_lib.activate
def test_top_holdings_parses_rows():
    rsps_lib.add(rsps_lib.GET, PROFILE_URL, body=_PROFILE)
    result = top_holdings(ISIN)
    assert result == [
        {"name": "NVIDIA Corp.", "isin": "US67066G1040", "percentage": 4.84},
        {"name": "Apple", "isin": "US0378331005", "percentage": 4.09},
        {"name": "Microsoft", "isin": "US5949181045", "percentage": 3.17},
    ]


def test_name_entities_are_unescaped():
    html = _row("FR0000120271", "LVMH Moët &amp; Chandon", "1.50%")
    assert _parse(html) == [
        {"name": "LVMH Moët & Chandon", "isin": "FR0000120271", "percentage": 1.5}
    ]


def test_mismatched_counts_raise():
    # A name with no matching percentage row signals a markup change.
    html = (
        '<a data-testid="tl_etf-holdings_top-holdings_link_name" '
        'href="/en/stock-profiles/US67066G1040" title="NVIDIA Corp."><span>x</span></a>'
    )
    with pytest.raises(ValueError):
        _parse(html)


@rsps_lib.activate
def test_empty_parse_is_not_cached():
    rsps_lib.add(rsps_lib.GET, PROFILE_URL, body="<html><body></body></html>")
    assert top_holdings(ISIN) == []
    assert top_holdings(ISIN) == []
    # Second call must hit the network again, not a cached empty list.
    assert len(rsps_lib.calls) == 2


@pytest.mark.live
def test_webn_top_holdings_live():
    result = top_holdings("IE0003XJA0J9")
    assert len(result) >= 5
    assert all(h["isin"] and h["name"] and h["percentage"] > 0 for h in result)
