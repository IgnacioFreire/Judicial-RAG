"""Chunk tiers a user can choose.

The tier is the user setting. The method is fixed here and is the same
for every user. fast, medium, and slow are the only tiers.
"""

CHUNK_TIERS: dict[str, str] = {
    "fast": "page",
    "medium": "hybrid",
    "slow": "fine",
}

DEFAULT_CHUNK_TIER = "medium"


def chunk_method_for(tier: str) -> str:
    """Return the chunk method configured for a tier.

    Raises:
        ValueError: The tier is not one of the configured keys.
    """
    try:
        return CHUNK_TIERS[tier]
    except KeyError:
        known = ", ".join(CHUNK_TIERS)
        raise ValueError(
            f"Chunk tier '{tier}' is not configured. Choose one of: {known}"
        ) from None
