"""One situation sentence for the slow chunk tier.

The sentence is embedded with the chunk. The stored citation text stays
the chunk alone. The passage is sent to the configured LLM and is not logged.
"""

import logging

from services.llm_client import call_llm

logger = logging.getLogger(__name__)

_MAX_CHARS = 400


def situation_sentence(headings: list[str], text: str) -> str:
    """Return one short sentence, or an empty string when the model declines."""
    heading = " > ".join(headings) if headings else "(no heading)"
    prompt = (
        "Write one short sentence in Spanish that says where this passage sits. "
        "Use only the heading and the passage. Do not add facts, names, or dates "
        "that are not written there. Return the sentence only.\n\n"
        f"Heading: {heading}\n\nPassage:\n{text}"
    )
    raw = call_llm(prompt).strip()
    sentence = raw.splitlines()[0].strip().strip('"') if raw else ""
    if len(sentence) > _MAX_CHARS:
        sentence = sentence[:_MAX_CHARS].rsplit(" ", 1)[0]
    logger.debug("Context sentence: %d chars", len(sentence))
    return sentence
