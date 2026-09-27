"""
test_embedder.py

Unit tests for pipeline/embedder.py.
Tests embedding generation, session index writes, and stored text
without calling the real HF Inference API — all external calls are
mocked so tests run fast and offline.

Run all:     uv run pytest tests/test_embedder.py -v
Run a class: uv run pytest tests/test_embedder.py::TestSessionIndex -v
"""

from unittest.mock import patch

import numpy as np
import pytest

from models.document import Chunk, DocumentMetadata, DocumentResult

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_vector() -> list[float]:
    """A deterministic 1024-dimensional unit vector for testing."""
    rng = np.random.default_rng(seed=42)
    vector = rng.random(1024).astype(np.float32)
    return vector.tolist()


@pytest.fixture
def chunk() -> Chunk:
    """Minimal valid chunk representing a judicial text fragment."""
    return Chunk(
        text="El tribunal absolvió al acusado por falta de pruebas.",
        source="sentencia_001.pdf",
        page=1,
        chunk_index=0,
        chunk_id="sentencia_001.pdf_1_0",
        headings=["FALLO"],
    )


@pytest.fixture
def chunk_no_headings() -> Chunk:
    """Chunk with no section headings — tests empty headings serialisation."""
    return Chunk(
        text="Texto del encabezado de la sentencia.",
        source="sentencia_001.pdf",
        page=1,
        chunk_index=1,
        chunk_id="sentencia_001.pdf_1_1",
    )


@pytest.fixture
def document(chunk: Chunk, chunk_no_headings: Chunk) -> DocumentResult:
    """DocumentResult with two chunks for embedding tests."""
    return DocumentResult(
        metadata=DocumentMetadata(
            filename="sentencia_001.pdf",
            total_pages=3,
            total_chunks=2,
        ),
        chunks=[chunk, chunk_no_headings],
    )


@pytest.fixture
def empty_document() -> DocumentResult:
    """DocumentResult with no chunks — tests the early-exit path."""
    return DocumentResult(
        metadata=DocumentMetadata(
            filename="empty.pdf",
            total_pages=1,
            total_chunks=0,
        ),
        chunks=[],
    )


@pytest.fixture
def mock_inference(mock_vector: list[float]):
    """Patches the HF InferenceClient so no real API calls are made."""

    def _extract(texts, model=None):
        rows = len(texts) if isinstance(texts, list) else 1
        return np.tile(np.array(mock_vector, dtype=np.float32), (rows, 1))

    with patch("pipeline.embedder._inference") as mock:
        mock.feature_extraction.side_effect = _extract
        yield mock


# ---------------------------------------------------------------------------
# Collection management
# ---------------------------------------------------------------------------


class TestSessionIndex:
    @pytest.mark.asyncio
    async def test_delete_collection_removes_rows(
        self, mock_inference, document: DocumentResult
    ) -> None:
        from pipeline.embedder import delete_collection, embed_document
        from pipeline.index_store import get_index

        session_id = "session-delete-test"
        await embed_document(document, session_id)
        delete_collection(session_id)
        assert get_index().count(session_id) == 0

    def test_delete_nonexistent_collection_does_not_raise(self) -> None:
        # Deleting a session that never indexed must not raise — a session
        # may end before any PDFs are processed
        from pipeline.embedder import delete_collection

        delete_collection("session-never-existed-99999")


# ---------------------------------------------------------------------------
# Stored fields
# ---------------------------------------------------------------------------


class TestStoredFields:
    @pytest.mark.asyncio
    async def test_headings_round_trip(
        self, mock_inference, document: DocumentResult
    ) -> None:
        from pipeline.embedder import embed_document
        from pipeline.vector_store import search

        session_id = "session-headings"
        await embed_document(document, session_id)
        hits = search("pregunta", session_id, document.metadata.filename, n_results=5)
        found = {hit["text"]: hit["headings"] for hit in hits}
        assert found[document.chunks[0].text] == ["FALLO"]
        assert found[document.chunks[1].text] == []

    @pytest.mark.asyncio
    async def test_multiple_headings_round_trip(self, mock_inference) -> None:
        from pipeline.embedder import embed_document
        from pipeline.vector_store import search

        chunk = Chunk(
            text="Texto.",
            source="doc.pdf",
            page=2,
            chunk_index=0,
            chunk_id="doc.pdf_2_0",
            headings=["FUNDAMENTOS DE DERECHO", "PRIMERO.-"],
        )
        document = DocumentResult(
            metadata=DocumentMetadata(
                filename="doc.pdf",
                total_pages=2,
                total_chunks=1,
            ),
            chunks=[chunk],
        )
        await embed_document(document, "session-multi-headings")
        hits = search("pregunta", "session-multi-headings", "doc.pdf")
        assert hits[0]["headings"] == ["FUNDAMENTOS DE DERECHO", "PRIMERO.-"]
        assert hits[0]["page"] == 2
        assert hits[0]["chunk_index"] == 0
        assert hits[0]["source"] == "doc.pdf"


# ---------------------------------------------------------------------------
# Vector generation
# ---------------------------------------------------------------------------


class TestToVector:
    def test_returns_list_of_floats(
        self, mock_inference, mock_vector: list[float]
    ) -> None:
        from pipeline.embedder import _to_vector

        result = _to_vector("passage: some text")
        assert isinstance(result, list)
        assert all(isinstance(v, float) for v in result)

    def test_vector_has_correct_dimension(
        self, mock_inference, mock_vector: list[float]
    ) -> None:
        from pipeline.embedder import _to_vector

        result = _to_vector("passage: some text")
        assert len(result) == 1024

    def test_passage_prefix_is_passed_to_api(self, mock_inference) -> None:
        from pipeline.embedder import _to_vector

        _to_vector("passage: texto judicial")
        mock_inference.feature_extraction.assert_called_once()
        sent = mock_inference.feature_extraction.call_args[0][0]
        assert sent[0].startswith("passage:")

    def test_query_prefix_is_passed_to_api(self, mock_inference) -> None:
        from pipeline.embedder import embed_query

        embed_query("¿Cuál es el fallo?")
        mock_inference.feature_extraction.assert_called_once()
        sent = mock_inference.feature_extraction.call_args[0][0]
        assert sent[0].startswith("query:")


# ---------------------------------------------------------------------------
# Document embedding
# ---------------------------------------------------------------------------


class TestEmbedDocument:
    @pytest.mark.asyncio
    async def test_embeds_all_chunks(
        self, mock_inference, document: DocumentResult
    ) -> None:
        from pipeline.embedder import embed_document
        from pipeline.index_store import get_index

        session_id = "session-embed-all"
        await embed_document(document, session_id)
        assert get_index().count(session_id) == len(document.chunks)

    @pytest.mark.asyncio
    async def test_context_sentence_is_embedded_not_stored(
        self, mock_inference, chunk: Chunk
    ) -> None:
        from pipeline.embedder import embed_document
        from pipeline.index_store import get_index

        document = DocumentResult(
            metadata=DocumentMetadata(
                filename=chunk.source,
                total_pages=1,
                total_chunks=1,
            ),
            chunks=[chunk],
        )
        with patch(
            "pipeline.chunk_context.call_llm",
            return_value="Situación sintética.",
        ):
            await embed_document(document, "session-context", chunk_tier="slow")
        sent = mock_inference.feature_extraction.call_args[0][0]
        stored = get_index().text("session-context", chunk.chunk_id)
        assert sent[0].startswith("passage: Situación sintética.")
        assert stored == chunk.text

    @pytest.mark.asyncio
    async def test_upsert_is_idempotent(
        self, mock_inference, document: DocumentResult
    ) -> None:
        # Embedding the same document twice must not create duplicates —
        # upsert deduplicates by chunk_id
        from pipeline.embedder import embed_document
        from pipeline.index_store import get_index

        session_id = "session-upsert-idem"
        await embed_document(document, session_id)
        await embed_document(document, session_id)
        assert get_index().count(session_id) == len(document.chunks)

    @pytest.mark.asyncio
    async def test_empty_document_does_not_raise(
        self, mock_inference, empty_document: DocumentResult
    ) -> None:
        # A document with no chunks is a valid outcome — the extractor
        # may produce zero chunks for a blank or unreadable PDF
        from pipeline.embedder import embed_document

        await embed_document(empty_document, "session-empty")

    @pytest.mark.asyncio
    async def test_sessions_are_isolated(
        self, mock_inference, document: DocumentResult
    ) -> None:
        # Chunks embedded under session A must not appear in session B
        from pipeline.embedder import embed_document
        from pipeline.index_store import get_index

        await embed_document(document, "session-a")
        assert get_index().count("session-b") == 0

    @pytest.mark.asyncio
    async def test_chunk_text_stored_without_prefix(
        self, mock_inference, document: DocumentResult
    ) -> None:
        # The raw chunk text (without "passage: " prefix) must be stored
        # so it can be returned as a citation to the user
        from pipeline.embedder import embed_document
        from pipeline.index_store import get_index

        session_id = "session-text-check"
        await embed_document(document, session_id)
        stored = get_index().text(session_id, document.chunks[0].chunk_id)
        assert stored == document.chunks[0].text

    @pytest.mark.asyncio
    async def test_reembed_drops_chunks_from_the_previous_version(
        self, mock_inference, document: DocumentResult
    ) -> None:
        from pipeline.embedder import embed_document
        from pipeline.index_store import get_index

        session_id = "session-replace-shorter"
        await embed_document(document, session_id)
        shorter = DocumentResult(
            metadata=DocumentMetadata(
                filename=document.metadata.filename,
                total_pages=1,
                total_chunks=1,
            ),
            chunks=[document.chunks[0]],
        )
        await embed_document(shorter, session_id)
        assert get_index().count(session_id) == 1
        assert get_index().ids(session_id) == [document.chunks[0].chunk_id]
