"""HTTP session, upload, schema, tiers, run, and reset."""

from collections.abc import Iterator
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from config.chunkers import CHUNK_TIERS
from config.embeddings import EMBEDDING_TIERS
from config.parsers import PARSER_TIERS
from models.query import (
    AgentAnswer,
    AnswerConfidence,
    DocumentAnswers,
    QuestionType,
    UserQuestion,
)
from pipeline.orchestrator import ProgressEvent, Stage
from storage.uploads import MAX_BYTES


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        yield test_client


def _extraction_draft() -> dict:
    return {
        "label": "Date",
        "question": "What is the date?",
        "question_type": "extraction",
        "output_format": "",
        "notes": "",
        "categories": [],
    }


def test_cookie_is_stable_on_one_client(client: TestClient) -> None:
    first = client.get("/api/session")
    second = client.get("/api/session")
    assert first.status_code == 200
    assert second.status_code == 200
    cookie = client.cookies.get("jr_session")
    assert cookie
    assert cookie == first.cookies.get("jr_session")


def test_two_clients_get_two_session_ids() -> None:
    first = TestClient(app)
    second = TestClient(app)
    a = first.get("/api/session")
    b = second.get("/api/session")
    assert a.cookies["jr_session"] != b.cookies["jr_session"]


def test_session_tier_options_match_config(client: TestClient) -> None:
    body = client.get("/api/session").json()
    assert body["parser_tier"] == "medium"
    assert body["chunk_tier"] == "medium"
    assert body["embedding_tier"] == "fast"
    parser_labels = [row["label"] for row in body["parser_options"]]
    assert "pymupdf4llm" in parser_labels[0]
    assert "docling" in parser_labels[1]
    assert "marker" in parser_labels[2]
    assert [row["value"] for row in body["parser_options"]] == list(PARSER_TIERS)
    chunk_shown = [row["label"] for row in body["chunk_options"]]
    assert "window" in chunk_shown[0]
    assert "hybrid" in chunk_shown[1]
    assert "context" in chunk_shown[2]
    assert [row["value"] for row in body["chunk_options"]] == list(CHUNK_TIERS)
    retrieval_shown = [row["label"] for row in body["embedding_options"]]
    assert "dense" in retrieval_shown[0]
    assert "hybrid" in retrieval_shown[1]
    assert "rerank" in retrieval_shown[2]
    assert [row["value"] for row in body["embedding_options"]] == list(EMBEDDING_TIERS)


def test_upload_rejects_oversize_and_keeps_the_rest(client: TestClient) -> None:
    small = ("ok.pdf", b"%PDF-small", "application/pdf")
    huge = ("big.pdf", b"x" * (MAX_BYTES + 1), "application/pdf")
    response = client.put(
        "/api/uploads",
        files=[("files", small), ("files", huge)],
    )
    assert response.status_code == 200
    body = response.json()
    assert body["accepted_files"] == ["ok.pdf"]
    assert len(body["rejected"]) == 1
    assert "big.pdf" in body["rejected"][0]["detail"]


def test_empty_upload_clears_files(client: TestClient) -> None:
    client.put("/api/uploads", files=[("files", ("a.pdf", b"a", "application/pdf"))])
    response = client.put("/api/uploads", files=[])
    assert response.status_code == 200
    assert response.json()["accepted_files"] == []


def test_save_schema_then_reset_keeps_schema_and_tiers(client: TestClient) -> None:
    saved = client.put("/api/schema", json=[_extraction_draft()])
    assert saved.json()["saved"] is True
    client.patch(
        "/api/session/tiers",
        json={"parser_tier": "fast", "chunk_tier": "slow", "embedding_tier": "slow"},
    )
    client.put("/api/uploads", files=[("files", ("a.pdf", b"a", "application/pdf"))])
    reset = client.post("/api/reset")
    body = reset.json()
    assert body["schema_saved"] is True
    assert body["parser_tier"] == "fast"
    assert body["chunk_tier"] == "slow"
    assert body["embedding_tier"] == "slow"
    assert body["accepted_files"] == []
    assert body["results"] is None


def test_run_requires_pdfs_and_schema(client: TestClient) -> None:
    response = client.post("/api/run")
    assert response.status_code == 400


def test_run_conflict_when_processing(client: TestClient) -> None:
    client.put("/api/schema", json=[_extraction_draft()])
    client.put("/api/uploads", files=[("files", ("a.pdf", b"a", "application/pdf"))])
    from app.ui_state import get_or_create_ui

    session_id = client.cookies["jr_session"]
    get_or_create_ui(session_id).is_processing = True
    response = client.post("/api/run")
    assert response.status_code == 409
    get_or_create_ui(session_id).is_processing = False


def test_run_sse_keeps_error_after_done(client: TestClient) -> None:
    question = UserQuestion(
        label="Date",
        question="What is the date?",
        question_type=QuestionType.EXTRACTION,
    )
    results = [
        DocumentAnswers(
            document="a.pdf",
            answers=[
                AgentAnswer(
                    question=question,
                    document="a.pdf",
                    confidence=AnswerConfidence.NOT_FOUND,
                )
            ],
        )
    ]

    async def fake_run(**kwargs):
        on_progress = kwargs["on_progress"]
        on_progress(
            ProgressEvent(
                stage=Stage.ERROR,
                source="bad.pdf",
                message="bad.pdf was not processed",
            )
        )
        return results

    client.put("/api/schema", json=[_extraction_draft()])
    client.put("/api/uploads", files=[("files", ("a.pdf", b"a", "application/pdf"))])
    with patch("app.server.run", new=AsyncMock(side_effect=fake_run)):
        with client.stream("POST", "/api/run") as stream:
            payload = b"".join(stream.iter_bytes()).decode()
    assert "bad.pdf was not processed" in payload
    assert '"type":"done"' in payload
    session = client.get("/api/session").json()
    assert "bad.pdf was not processed" in session["run_errors"]
    assert session["results"][0]["document"] == "a.pdf"
    assert session["is_processing"] is False
