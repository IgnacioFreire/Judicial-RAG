"""
orchestrator.py

Main pipeline coordinator.
Receives uploaded PDFs and user questions, runs extraction and embedding
concurrently across documents, then runs the RAG agent for every
(document, question) pair and reports progress in real time via callbacks.
"""

import asyncio
import logging
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from models.query import AgentAnswer, AnswerConfidence, DocumentAnswers, QuestionSchema
from pipeline.embedder import delete_source, embed_document
from pipeline.rag_agent import answer_question
from pipeline.vector_store import list_sources

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Progress reporting
# ---------------------------------------------------------------------------


class Stage(str, Enum):
    """Pipeline stage emitted to the UI via the progress callback.

    Inherits from str so values serialise naturally in Streamlit widgets
    without an explicit .value call.
    """

    EXTRACTING = "extracting"
    EMBEDDING = "embedding"
    ANSWERING = "answering"
    COMPLETE = "complete"
    ERROR = "error"


@dataclass
class ProgressEvent:
    """A single progress update emitted by the orchestrator.

    Attributes:
        stage:   Current pipeline stage.
        source:  PDF filename this event refers to. Empty for global events.
        message: Human-readable status message for the UI.
        current: Completed units in the current stage (0 if unknown).
        total:   Total units in the current stage (0 if unknown).
        error:   Exception instance if stage is ERROR, None otherwise.
    """

    stage: Stage
    source: str
    message: str
    current: int = 0
    total: int = 0
    error: Exception | None = None


# Callback type the UI provides to receive progress events.
# Must not block — the orchestrator calls it from an async context.
OnProgress = Callable[[ProgressEvent], None]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


async def run(
    pdf_paths: list[Path],
    schema: QuestionSchema,
    session_id: str,
    on_progress: OnProgress | None = None,
    is_scanned: bool = False,
) -> list[DocumentAnswers]:
    """Run the full pipeline for a list of PDFs and a question schema.

    Two-phase execution:
    1. Extraction + embedding run concurrently across all PDFs so that
       slow documents do not block fast ones.
    2. The RAG agent answers questions sequentially per document to stay
       within LLM API rate limits.

    Failures in phase 1 are isolated per document — a bad PDF does not
    abort the rest of the batch. Phase 2 answers only the PDFs this run
    indexed, in filename order. Failures in phase 2 produce NOT_FOUND
    answers so every question always has a placeholder in the output.

    Args:
        pdf_paths:   Absolute paths to the uploaded PDF files.
        schema:      User-defined question schema applied to every document.
        session_id:  User session identifier for vector store isolation.
        on_progress: Optional callback invoked on every progress event.
        is_scanned:  Whether the PDFs require OCR for text extraction.

    Returns:
        One DocumentAnswers per PDF indexed in this run, each containing
        one AgentAnswer per question in the schema, ordered by filename.
    """
    total_pdfs = len(pdf_paths)
    total_questions = len(schema.questions)

    logger.info(
        "Pipeline started: %d PDF(s), %d question(s) (session=%s)",
        total_pdfs,
        total_questions,
        session_id,
    )

    _emit(
        on_progress,
        ProgressEvent(
            stage=Stage.EXTRACTING,
            source="",
            message=f"Extracting and indexing {total_pdfs} document(s)...",
            total=total_pdfs,
        ),
    )

    _drop_stale_sources(session_id, pdf_paths)
    indexed = await _index_all(pdf_paths, session_id, is_scanned, on_progress)
    results = _answer_all(sorted(set(indexed)), schema, session_id, on_progress)

    logger.info(
        "Pipeline complete: %d document(s), %d answer(s) (session=%s)",
        len(results),
        sum(len(r.answers) for r in results),
        session_id,
    )

    _emit(
        on_progress,
        ProgressEvent(
            stage=Stage.COMPLETE,
            source="",
            message="Pipeline complete.",
            current=len(results),
            total=len(results),
        ),
    )

    return results


# ---------------------------------------------------------------------------
# Phase 1 — extraction and embedding
# ---------------------------------------------------------------------------


def _drop_stale_sources(session_id: str, pdf_paths: list[Path]) -> None:
    """Remove indexed PDFs that are not part of this run's upload set."""
    keep = {path.name for path in pdf_paths}
    for source in list_sources(session_id):
        if source not in keep:
            delete_source(session_id, source)


async def _index_all(
    pdf_paths: list[Path],
    session_id: str,
    is_scanned: bool,
    on_progress: OnProgress | None,
) -> list[str]:
    """Extract and embed all PDFs concurrently via asyncio.gather.

    return_exceptions=True ensures a failure in one task does not cancel
    the others — each document is independently logged and reported.

    Args:
        pdf_paths:   PDFs to index.
        session_id:  User session identifier.
        is_scanned:  Whether to enable OCR.
        on_progress: Progress callback.

    Returns:
        Filenames that were indexed and can be answered. A PDF that
        produced no chunks is omitted, matching an empty search index.
    """
    total = len(pdf_paths)
    tasks = [
        _index_one(path, session_id, is_scanned, on_progress, idx, total)
        for idx, path in enumerate(pdf_paths, start=1)
    ]
    outcomes = await asyncio.gather(*tasks, return_exceptions=True)
    indexed: list[str] = []
    for outcome in outcomes:
        if isinstance(outcome, str):
            indexed.append(outcome)
        elif isinstance(outcome, BaseException):
            logger.error("Indexing task failed", exc_info=outcome)
    return indexed


async def _index_one(
    pdf_path: Path,
    session_id: str,
    is_scanned: bool,
    on_progress: OnProgress | None,
    current: int,
    total: int,
) -> str | None:
    """Extract and embed a single PDF, emitting progress at each stage.

    Docling is imported here so importing the orchestrator does not load
    extraction models.

    Args:
        pdf_path:    Absolute path to the PDF.
        session_id:  User session identifier.
        is_scanned:  Whether to enable OCR.
        on_progress: Progress callback.
        current:     1-based index of this PDF in the batch.
        total:       Total number of PDFs in the batch.

    Returns:
        The PDF filename when it was indexed, otherwise None.
    """
    from pipeline.extractor import extract

    source = pdf_path.name

    try:
        _emit(
            on_progress,
            ProgressEvent(
                stage=Stage.EXTRACTING,
                source=source,
                message=f"Extracting {source}...",
                current=current,
                total=total,
            ),
        )

        document = await extract(pdf_path, is_scanned=is_scanned)
        logger.debug("Extracted %s: %d chunks", source, document.metadata.total_chunks)

        _emit(
            on_progress,
            ProgressEvent(
                stage=Stage.EMBEDDING,
                source=source,
                message=f"Embedding {source} ({document.metadata.total_chunks} chunks)",
                current=current,
                total=total,
            ),
        )

        await embed_document(document, session_id)
        logger.debug("Indexed %s (%d/%d)", source, current, total)
        if document.metadata.total_chunks == 0:
            return None
        return source

    except Exception as e:
        logger.exception("Failed to index %s", source)
        _emit(
            on_progress,
            ProgressEvent(
                stage=Stage.ERROR,
                source=source,
                message=f"Failed to process {source}: {e}",
                current=current,
                total=total,
                error=e,
            ),
        )
        return None


# ---------------------------------------------------------------------------
# Phase 2 — question answering
# ---------------------------------------------------------------------------


def _answer_all(
    sources: list[str],
    schema: QuestionSchema,
    session_id: str,
    on_progress: OnProgress | None,
) -> list[DocumentAnswers]:
    """Answer every question for every indexed document.

    Sequential execution keeps LLM API usage predictable and avoids rate
    limit errors. Questions are answered in schema order so the UI renders
    them consistently regardless of which document is being processed.

    Args:
        sources:     Filenames indexed in this run, already sorted.
        schema:      Question schema to apply to every document.
        session_id:  User session identifier.
        on_progress: Progress callback.

    Returns:
        One DocumentAnswers per source, in the same order as sources.
    """
    total = len(sources) * len(schema.questions)
    completed = 0
    results: list[DocumentAnswers] = []

    for source in sources:
        answers: list[AgentAnswer] = []

        for question in schema.questions:
            completed += 1
            _emit(
                on_progress,
                ProgressEvent(
                    stage=Stage.ANSWERING,
                    source=source,
                    message=f"'{question.label}' — {source} ({completed}/{total})",
                    current=completed,
                    total=total,
                ),
            )

            try:
                answer = answer_question(
                    question=question,
                    session_id=session_id,
                    source=source,
                )
                logger.debug(
                    "Answered %r for %s (confidence=%s)",
                    question.label,
                    source,
                    answer.confidence.value,
                )
            except Exception:
                logger.exception("Failed to answer %r for %s", question.label, source)
                # Produce a NOT_FOUND placeholder so every question always
                # has an entry in the output — the UI shows it as unanswered
                # rather than leaving a gap in the results table
                answer = AgentAnswer(
                    question=question,
                    document=source,
                    confidence=AnswerConfidence.NOT_FOUND,
                )

            answers.append(answer)

        results.append(DocumentAnswers(document=source, answers=answers))

    return results


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------


def _emit(on_progress: OnProgress | None, event: ProgressEvent) -> None:
    """Invoke the progress callback safely.

    Wrapped in try/except so a buggy callback never crashes the pipeline —
    progress reporting is best-effort and must not affect correctness.

    Args:
        on_progress: Optional callback to invoke.
        event:       Progress event to pass to the callback.
    """
    if on_progress is None:
        return
    try:
        on_progress(event)
    except Exception:
        # Log at WARNING rather than ERROR — a broken callback is annoying
        # but not a pipeline failure
        logger.warning("Progress callback raised", exc_info=True)
