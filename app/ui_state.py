"""In-process UI session fields for one browser cookie."""

from dataclasses import dataclass, field
from datetime import UTC, datetime

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
    documents: dict[str, "DocumentRow"] = field(default_factory=dict)


@dataclass
class DocumentRow:
    """One accepted PDF in the current session."""

    name: str
    status: str
    accepted_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None


def sync_accepted(state: UiState, names: list[str]) -> None:
    """Keep a row for each accepted filename and drop the rest."""
    now = datetime.now(UTC)
    keep = set(names)
    for name in list(state.documents):
        if name not in keep:
            del state.documents[name]
    for name in names:
        if name not in state.documents:
            state.documents[name] = DocumentRow(
                name=name,
                status="ready",
                accepted_at=now,
            )


def mark_queued(state: UiState, names: list[str]) -> None:
    """Mark the files in this run as queued and clear a previous finish time."""
    for name in names:
        row = state.documents.get(name)
        if row is None:
            continue
        row.status = "queued"
        row.started_at = None
        row.finished_at = None


def note_progress(state: UiState, stage: str, source: str) -> None:
    """Update one file from a progress event that names it."""
    if not source:
        return
    row = state.documents.get(source)
    if row is None:
        return
    now = datetime.now(UTC)
    if stage == "error":
        row.status = "failed"
        row.finished_at = now
        if row.started_at is None:
            row.started_at = now
        return
    if stage in {"extracting", "embedding", "answering"}:
        row.status = stage
        if row.started_at is None:
            row.started_at = now


def close_run(state: UiState, done_names: set[str]) -> None:
    """Mark finished files done and any file still in the run as failed."""
    now = datetime.now(UTC)
    running = {"queued", "extracting", "embedding", "answering"}
    for row in state.documents.values():
        if row.name in done_names:
            row.status = "done"
            row.finished_at = now
        elif row.status in running:
            row.status = "failed"
            if row.finished_at is None:
                row.finished_at = now


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
    state.documents = {}
