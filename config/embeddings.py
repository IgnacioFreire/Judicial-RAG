"""Retrieval tiers a user can choose.

The tier is the user setting. The method is fixed here and is the same
for every user. fast, medium, and slow are the only tiers. Fast is the
current vector search, so a session that does not change this setting
keeps today's answers.
"""

EMBEDDING_TIERS: dict[str, str] = {
    "fast": "dense",
    "medium": "hybrid",
    "slow": "rerank",
}

DEFAULT_EMBEDDING_TIER = "fast"

# Multilingual cross-encoder. Loaded only when a session picks the slow tier.
RERANK_MODEL = "cross-encoder/mmarco-mMiniLMv2-L12-H384-v1"


def embedding_method_for(tier: str) -> str:
    """Return the retrieval method configured for a tier.

    Raises:
        ValueError: The tier is not one of the configured keys.
    """
    try:
        return EMBEDDING_TIERS[tier]
    except KeyError:
        known = ", ".join(EMBEDDING_TIERS)
        raise ValueError(
            f"Embedding tier '{tier}' is not configured. Choose one of: {known}"
        ) from None
