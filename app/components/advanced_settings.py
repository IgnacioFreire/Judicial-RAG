"""Advanced settings. The parser tier is a preference of this session."""

import streamlit as st

from app import session_state as state
from config.chunkers import CHUNK_TIERS
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

        current_chunk = state.chunk_tier()
        chunk_options = list(CHUNK_TIERS)
        chunk_choice = st.selectbox(
            "Chunking",
            options=chunk_options,
            index=(
                chunk_options.index(current_chunk)
                if current_chunk in chunk_options
                else 1
            ),
            format_func=lambda tier: f"{_LABELS[tier]} — {CHUNK_TIERS[tier]}",
            disabled=state.is_processing(),
            help=(
                "Fast keeps one chunk per page. Medium splits sections at 512 tokens. "
                "Slow uses the embedding tokenizer and 256 tokens."
            ),
        )
        state.set_chunk_tier(chunk_choice)
