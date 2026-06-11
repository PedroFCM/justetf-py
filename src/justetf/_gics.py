"""GICS sector constants and normalization helper."""

GICS_SECTORS: tuple[str, ...] = (
    "Energy",
    "Materials",
    "Industrials",
    "Consumer Discretionary",
    "Consumer Staples",
    "Health Care",
    "Financials",
    "Information Technology",
    "Communication Services",
    "Utilities",
    "Real Estate",
)

# Known non-canonical aliases from justETF and other data providers (e.g. Yahoo Finance).
_ALIASES: dict[str, str] = {
    # Yahoo Finance
    "Technology": "Information Technology",
    "Financial Services": "Financials",
    "Consumer Cyclical": "Consumer Discretionary",
    "Consumer Defensive": "Consumer Staples",
    "Healthcare": "Health Care",
    "Basic Materials": "Materials",
    # Pre-2016 GICS names and provider shortenings
    "Telecommunication Services": "Communication Services",
    "Telecommunication": "Communication Services",
}


def normalize_sector(name: str) -> str:
    """Map a sector name to its canonical GICS name.

    Canonical names are returned unchanged. Unknown names are also returned
    unchanged so callers can handle them without raising.

    Args:
        name: Sector label from any provider (e.g. ``"Technology"``,
            ``"Financial Services"``).

    Returns:
        Canonical GICS sector name if a mapping exists, otherwise ``name``
        as-is.
    """
    return _ALIASES.get(name, name)
