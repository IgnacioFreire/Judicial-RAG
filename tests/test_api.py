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


def test_documents_start_ready_and_reset_clears_them(client: TestClient) -> None:
    empty = client.get("/api/documents")
    assert empty.status_code == 200
    assert empty.json() == []
    client.put("/api/uploads", files=[("files", ("a.pdf", b"a", "application/pdf"))])
    listed = client.get("/api/documents").json()
    assert listed[0]["name"] == "a.pdf"
    assert listed[0]["status"] == "ready"
    assert listed[0]["accepted_at"]
    client.post("/api/reset")
    assert client.get("/api/documents").json() == []


def test_run_marks_failed_and_done(client: TestClient) -> None:
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
                stage=Stage.EXTRACTING,
                source="a.pdf",
                message="Extracting a.pdf",
                current=1,
                total=2,
            )
        )
        on_progress(
            ProgressEvent(
                stage=Stage.ERROR,
                source="bad.pdf",
                message="bad.pdf was not processed",
            )
        )
        return results

    client.put("/api/schema", json=[_extraction_draft()])
    client.put(
        "/api/uploads",
        files=[
            ("files", ("a.pdf", b"a", "application/pdf")),
            ("files", ("bad.pdf", b"b", "application/pdf")),
        ],
    )
    with patch("app.server.run", new=AsyncMock(side_effect=fake_run)):
        with client.stream("POST", "/api/run") as stream:
            b"".join(stream.iter_bytes())
    rows = {row["name"]: row for row in client.get("/api/documents").json()}
    assert rows["bad.pdf"]["status"] == "failed"
    assert rows["bad.pdf"]["finished_at"]
    assert rows["a.pdf"]["status"] == "done"
    assert rows["a.pdf"]["finished_at"]
    detail = client.get("/api/documents/a.pdf")
    assert detail.status_code == 200
    assert detail.json()["answers"]["document"] == "a.pdf"


def test_other_session_cannot_read_a_document() -> None:
    owner = TestClient(app)
    other = TestClient(app)
    owner.put("/api/uploads", files=[("files", ("a.pdf", b"a", "application/pdf"))])
    missing = other.get("/api/documents/a.pdf")
    assert missing.status_code == 404


def test_sign_out_starts_a_fresh_session(client: TestClient) -> None:
    client.put("/api/uploads", files=[("files", ("a.pdf", b"a", "application/pdf"))])
    old_cookie = client.cookies["jr_session"]
    body = client.post("/api/sign-out")
    assert body.status_code == 200
    assert body.json()["signed_out"] is True
    assert client.cookies["jr_session"] != old_cookie
    session = client.get("/api/session").json()
    assert session["accepted_files"] == []


def test_session_key_override_is_not_returned(client: TestClient) -> None:
    secret = "session-only-secret"
    body = client.put(
        "/api/profile/keys",
        json={"deepseek_api_key": secret},
    )
    assert body.status_code == 200
    assert secret not in body.text
    profile = client.get("/api/profile").json()
    assert profile["llm_key_configured"] is True
    assert secret not in str(profile)


def test_profile_does_not_return_the_key(client: TestClient) -> None:
    import config.settings as settings_mod

    secret = "test-secret-key-not-for-logs"
    previous_provider = settings_mod.settings.llm_provider
    previous_key = settings_mod._settings.deepseek_api_key
    settings_mod._settings.deepseek_api_key = secret
    settings_mod._settings.llm_provider = "deepseek"
    try:
        body = client.get("/api/profile")
        assert body.status_code == 200
        assert secret not in body.text
        payload = body.json()
        assert payload["llm_key_configured"] is True
        assert payload["llm_provider"] == "deepseek"
        assert "input_tokens" in payload
        assert "output_tokens" in payload
    finally:
        settings_mod._settings.llm_provider = previous_provider
        settings_mod._settings.deepseek_api_key = previous_key


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
