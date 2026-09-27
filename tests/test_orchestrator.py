"""Tests for which PDFs a run answers."""

import sys
from pathlib import Path
from types import ModuleType

import numpy as np
import pytest

from models.document import Chunk, DocumentMetadata, DocumentResult
from models.query import (
    AgentAnswer,
    AnswerConfidence,
    QuestionSchema,
    QuestionType,
    UserQuestion,
)


def _document(name: str, chunks: int = 1) -> DocumentResult:
    """Synthetic document. The text is not a ruling."""
    rows = [
        Chunk(
            text=f"synthetic fragment {index} of {name}",
            source=name,
            page=1,
            chunk_index=index,
            chunk_id=f"{name}_1_{index}",
        )
        for index in range(chunks)
    ]
    return DocumentResult(
        metadata=DocumentMetadata(
            filename=name,
            total_pages=1,
            total_chunks=chunks,
        ),
        chunks=rows,
    )


def _schema() -> QuestionSchema:
    return QuestionSchema(
        name="User schema",
        questions=[
            UserQuestion(
                label="Item",
                question="What is recorded?",
                question_type=QuestionType.EXTRACTION,
            )
        ],
    )


@pytest.fixture
def mock_inference():
    """Avoid the Hugging Face API while still writing Chroma."""
    from unittest.mock import patch

    def _extract(texts, model=None):
        rows = len(texts) if isinstance(texts, list) else 1
        return np.ones((rows, 1024), dtype=np.float32)

    with patch("pipeline.embedder._inference") as mock:
        mock.feature_extraction.side_effect = _extract
        yield mock


@pytest.mark.asyncio
async def test_second_run_answers_only_the_files_still_uploaded(
    tmp_path: Path,
    mock_inference,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    docs = {"a.pdf": _document("a.pdf"), "b.pdf": _document("b.pdf")}

    async def fake_extract(pdf_path: Path, tier: str = "medium") -> DocumentResult:
        return docs[pdf_path.name]

    fake_extractor = ModuleType("pipeline.extractor")
    fake_extractor.extract = fake_extract
    monkeypatch.setitem(sys.modules, "pipeline.extractor", fake_extractor)

    answered: list[str] = []

    def fake_answer(
        question: UserQuestion, session_id: str, source: str
    ) -> AgentAnswer:
        answered.append(source)
        return AgentAnswer(
            question=question,
            document=source,
            answer="synthetic",
            confidence=AnswerConfidence.HIGH,
        )

    monkeypatch.setattr("pipeline.orchestrator.answer_question", fake_answer)

    from pipeline.embedder import get_collection
    from pipeline.orchestrator import run

    session_id = "session-current-batch"
    a = tmp_path / "a.pdf"
    b = tmp_path / "b.pdf"
    a.write_bytes(b"%PDF")
    b.write_bytes(b"%PDF")

    first = await run([a, b], _schema(), session_id)
    assert [item.document for item in first] == ["a.pdf", "b.pdf"]

    answered.clear()
    second = await run([a], _schema(), session_id)
    assert [item.document for item in second] == ["a.pdf"]
    assert answered == ["a.pdf"]

    stored = get_collection(session_id).get(include=["metadatas"])
    sources = {meta["source"] for meta in stored["metadatas"]}
    assert sources == {"a.pdf"}


@pytest.mark.asyncio
async def test_pdf_with_no_text_is_a_visible_failure(
    tmp_path: Path,
    mock_inference,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    docs = {
        "empty.pdf": _document("empty.pdf", chunks=0),
        "ok.pdf": _document("ok.pdf"),
    }

    async def fake_extract(pdf_path: Path, tier: str = "medium") -> DocumentResult:
        return docs[pdf_path.name]

    fake_extractor = ModuleType("pipeline.extractor")
    fake_extractor.extract = fake_extract
    monkeypatch.setitem(sys.modules, "pipeline.extractor", fake_extractor)

    def fake_answer(
        question: UserQuestion, session_id: str, source: str
    ) -> AgentAnswer:
        return AgentAnswer(
            question=question,
            document=source,
            answer="synthetic",
            confidence=AnswerConfidence.HIGH,
        )

    monkeypatch.setattr("pipeline.orchestrator.answer_question", fake_answer)

    from pipeline.orchestrator import Stage, run

    events = []
    empty = tmp_path / "empty.pdf"
    ok = tmp_path / "ok.pdf"
    empty.write_bytes(b"%PDF")
    ok.write_bytes(b"%PDF")

    results = await run(
        [empty, ok],
        _schema(),
        "session-empty-pdf",
        on_progress=events.append,
    )
    assert [item.document for item in results] == ["ok.pdf"]
    failures = [event for event in events if event.stage == Stage.ERROR]
    assert len(failures) == 1
    assert failures[0].source == "empty.pdf"
    assert "no text" in failures[0].message
