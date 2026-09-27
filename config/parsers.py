"""Parser tiers a user can choose.

The tier is the user setting. The method is fixed here and is the same
for every user. fast, medium, and slow are the only tiers.
"""

PARSER_TIERS: dict[str, str] = {
    "fast": "pymupdf4llm",
    "medium": "docling",
    "slow": "marker",
}

DEFAULT_PARSER_TIER = "medium"


def method_for(tier: str) -> str:
    """Return the parser method configured for a tier.

    Raises:
        ValueError: The tier is not one of the configured keys.
    """
    try:
        return PARSER_TIERS[tier]
    except KeyError:
        known = ", ".join(PARSER_TIERS)
        raise ValueError(
            f"Parser tier '{tier}' is not configured. Choose one of: {known}"
        ) from None
