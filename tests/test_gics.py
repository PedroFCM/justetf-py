import pytest

from justetf import GICS_SECTORS, normalize_sector


def test_gics_sectors_count():
    assert len(GICS_SECTORS) == 11


def test_gics_sectors_contains_canonical_names():
    assert "Information Technology" in GICS_SECTORS
    assert "Health Care" in GICS_SECTORS
    assert "Communication Services" in GICS_SECTORS
    assert "Consumer Discretionary" in GICS_SECTORS
    assert "Consumer Staples" in GICS_SECTORS


@pytest.mark.parametrize(
    "alias, canonical",
    [
        ("Technology", "Information Technology"),
        ("Financial Services", "Financials"),
        ("Consumer Cyclical", "Consumer Discretionary"),
        ("Consumer Defensive", "Consumer Staples"),
        ("Healthcare", "Health Care"),
        ("Basic Materials", "Materials"),
        ("Telecommunication Services", "Communication Services"),
    ],
)
def test_normalize_maps_known_aliases(alias, canonical):
    assert normalize_sector(alias) == canonical


def test_normalize_passes_through_canonical_names():
    for sector in GICS_SECTORS:
        assert normalize_sector(sector) == sector


def test_normalize_passes_through_unknown_name():
    assert normalize_sector("Other") == "Other"
    assert normalize_sector("unknown sector") == "unknown sector"
