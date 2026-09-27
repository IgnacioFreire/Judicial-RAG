"""
session_state.py

Centralised Streamlit session state initialisation and access.
All st.session_state keys live here so they are never scattered across
components. Using string constants instead of raw keys prevents typos
and makes renaming straightforward.
"""

import uuid

import streamlit as st

from config.chunkers import DEFAULT_CHUNK_TIER
from config.embeddings import DEFAULT_EMBEDDING_TIER
from config.parsers import DEFAULT_PARSER_TIER
from models.query import QuestionSchema
from storage.session_manager import get_or_create_session

# ---------------------------------------------------------------------------
# State keys
# ---------------------------------------------------------------------------
# One constant per key. Every component imports from here rather than
# using raw strings, so a rename is a single-line change.

_SESSION_ID = "session_id"
_SCHEMA = "schema"
_RESULTS = "results"
_IS_PROCESSING = "is_processing"
_UPLOADED_FILES = "uploaded_files"
_RUN_ERRORS = "run_errors"
_PARSER_TIER = "parser_tier"
_CHUNK_TIER = "chunk_tier"
_EMBEDDING_TIER = "embedding_tier"


# ---------------------------------------------------------------------------
# Initialisation
# ---------------------------------------------------------------------------


def init() -> None:
    """Initialise all session state keys on the first page load.

    Streamlit reruns the full script on every interaction. setdefault
    ensures existing values survive reruns — only absent keys are set.
    Called once at the top of app/main.py before any component renders.
    """
    if _SESSION_ID not in st.session_state:
        # Generate a stable UUID for this browser session. Used as the
        # index session id and temporary directory prefix so each
        # user's data stays fully isolated from other users.
        st.session_state[_SESSION_ID] = str(uuid.uuid4())

    st.session_state.setdefault(_SCHEMA, None)
    st.session_state.setdefault(_RESULTS, None)
    st.session_state.setdefault(_IS_PROCESSING, False)
    st.session_state.setdefault(_UPLOADED_FILES, [])
    st.session_state.setdefault(_RUN_ERRORS, [])
    st.session_state.setdefault(_PARSER_TIER, DEFAULT_PARSER_TIER)
    st.session_state.setdefault(_CHUNK_TIER, DEFAULT_CHUNK_TIER)
    st.session_state.setdefault(_EMBEDDING_TIER, DEFAULT_EMBEDDING_TIER)

    # Ensure the backend Session object exists for this ID so the
    # temporary directory is ready before any component tries to use it
    get_or_create_session(st.session_state[_SESSION_ID])


# ---------------------------------------------------------------------------
# Accessors and mutators
# ---------------------------------------------------------------------------
# Thin wrappers around st.session_state. Components call these instead of
# accessing st.session_state directly so the key names stay encapsulated.


def session_id() -> str:
    """Return the UUID identifying this browser session.

    Returns:
        UUID string set at session initialisation.
    """
    return st.session_state[_SESSION_ID]


def schema() -> QuestionSchema | None:
    """Return the current question schema, or None if not yet defined.

    Returns:
        QuestionSchema instance, or None before the user saves a schema.
    """
    return st.session_state[_SCHEMA]


def set_schema(value: QuestionSchema) -> None:
    """Persist the question schema for the current session.

    Args:
        value: QuestionSchema built from the user's question form.
    """
    st.session_state[_SCHEMA] = value


def results() -> list | None:
    """Return the pipeline results, or None if the pipeline has not run.

    Returns:
        List of DocumentAnswers from the orchestrator, or None.
    """
    return st.session_state[_RESULTS]


def set_results(value: list) -> None:
    """Persist the pipeline results for display in the results viewer.

    Args:
        value: List of DocumentAnswers returned by orchestrator.run().
    """
    st.session_state[_RESULTS] = value


def is_processing() -> bool:
    """Return True while the pipeline is running.

    Used by the UI to disable buttons and show a spinner during processing.

    Returns:
        True if the pipeline is active, False otherwise.
    """
    return st.session_state[_IS_PROCESSING]


def set_processing(value: bool) -> None:
    """Set the processing flag.

    Args:
        value: True when the pipeline starts, False when it completes
            or fails.
    """
    st.session_state[_IS_PROCESSING] = value


def uploaded_files() -> list:
    """Return the list of files uploaded in the current session.

    Returns:
        List of Streamlit UploadedFile objects, empty before any upload.
    """
    return st.session_state[_UPLOADED_FILES]


def set_uploaded_files(value: list) -> None:
    """Persist the uploaded file objects for use by the pipeline.

    Args:
        value: List of Streamlit UploadedFile objects from st.file_uploader.
    """
    st.session_state[_UPLOADED_FILES] = value


def run_errors() -> list[str]:
    """Return failure messages from the latest run.

    Returns:
        Messages for PDFs that were not indexed. Empty before the first run.
    """
    return st.session_state[_RUN_ERRORS]


def set_run_errors(value: list[str]) -> None:
    """Persist failure messages so they survive the rerun at the end of a run.

    Args:
        value: One message per PDF that failed to index.
    """
    st.session_state[_RUN_ERRORS] = value


def parser_tier() -> str:
    """Return the parser tier selected for this session.

    Returns:
        One of fast, medium, or slow. Medium until the user changes it.
    """
    return st.session_state[_PARSER_TIER]


def set_parser_tier(value: str) -> None:
    """Persist the parser tier for this session.

    Args:
        value: One of fast, medium, or slow.
    """
    st.session_state[_PARSER_TIER] = value


def chunk_tier() -> str:
    """Return the chunk tier selected for this session.

    Returns:
        One of fast, medium, or slow. Medium until the user changes it.
    """
    return st.session_state[_CHUNK_TIER]


def set_chunk_tier(value: str) -> None:
    """Persist the chunk tier for this session.

    Args:
        value: One of fast, medium, or slow.
    """
    st.session_state[_CHUNK_TIER] = value


def embedding_tier() -> str:
    """Return the retrieval tier selected for this session.

    Returns:
        One of fast, medium, or slow. Fast until the user changes it.
    """
    return st.session_state[_EMBEDDING_TIER]


def set_embedding_tier(value: str) -> None:
    """Persist the retrieval tier for this session.

    Args:
        value: One of fast, medium, or slow.
    """
    st.session_state[_EMBEDDING_TIER] = value


def reset() -> None:
    """Clear results and uploads to prepare for a new pipeline run.

    Intentionally keeps the session ID, the schema, and the parser, chunk,
    and retrieval tiers so a new batch keeps the same questions and cuts.
    """
    st.session_state[_RESULTS] = None
    st.session_state[_UPLOADED_FILES] = []
    st.session_state[_IS_PROCESSING] = False
    st.session_state[_RUN_ERRORS] = []
