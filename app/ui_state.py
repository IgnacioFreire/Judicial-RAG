"""In-process UI session fields that Streamlit used to keep in session_state."""

from dataclasses import dataclass, field

from config.chunkers import DEFAULT_CHUNK_TIER
from config.embeddings import DEFAULT_EMBEDDING_TIER
from config.parsers import DEFAULT_PARSER_TIER
from models.query import DocumentAnswers, QuestionSchema

_ui: dict[str, "UiState"] = {}


@dataclass
class UiState:
    """Server-side fields for one browser cookie."""

    schema: QuestionSchema | None = None
    results: list[DocumentAnswers] | None = None
    is_processing: bool = False
    run_errors: list[str] = field(default_factory=list)
    pipeline_error: str | None = None
    parser_tier: str = DEFAULT_PARSER_TIER
    chunk_tier: str = DEFAULT_CHUNK_TIER
    embedding_tier: str = DEFAULT_EMBEDDING_TIER
    success_message: str | None = None


def get_or_create_ui(session_id: str) -> UiState:
    """Return the UI record for a session cookie, creating an empty one if needed."""
    state = _ui.get(session_id)
    if state is None:
        state = UiState()
        _ui[session_id] = state
    return state


def reset_run_fields(state: UiState) -> None:
    """Clear results and uploads-related UI after Reset. Keep schema and tiers."""
    state.results = None
    state.is_processing = False
    state.run_errors = []
    state.pipeline_error = None
    state.success_message = None
