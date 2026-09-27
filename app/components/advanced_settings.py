"""Advanced settings. The parser tier is a preference of this session."""

import streamlit as st

from app import session_state as state
from config.parsers import PARSER_TIERS

_LABELS = {
    "fast": "Fast",
    "medium": "Medium",
    "slow": "Slow",
}


def render() -> None:
    """Render the parser tier selector."""
    with st.expander("Advanced settings"):
        current = state.parser_tier()
        options = list(PARSER_TIERS)
        choice = st.selectbox(
            "Parser",
            options=options,
            index=options.index(current) if current in options else 1,
            format_func=lambda tier: f"{_LABELS[tier]} — {PARSER_TIERS[tier]}",
            disabled=state.is_processing(),
            help=(
                "Fast reads the text layer. Medium keeps the section structure. "
                "Slow spends longer on each page."
            ),
        )
        state.set_parser_tier(choice)
