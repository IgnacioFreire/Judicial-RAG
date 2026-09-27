"""Headings come back as a list of strings, and search stays on one PDF."""

from unittest.mock import patch

import numpy as np
import pytest

from models.document import Chunk, DocumentMetadata, DocumentResult
from pipeline.vector_store import _headings


def test_json_array_round_trips() -> None:
    assert _headings('["FALLO", "PRIMERO"]') == ["FALLO", "PRIMERO"]


def test_empty_headings() -> None:
    assert _headings("") == []
    assert _headings("[]") == []


def test_invalid_heading_payload_is_empty() -> None:
    assert _headings("not-json") == []
    assert _headings('{"heading": "FALLO"}') == []
    assert _headings(None) == []


def test_heading_list_round_trips() -> None:
    assert _headings(["FALLO", "PRIMERO"]) == ["FALLO", "PRIMERO"]


@pytest.mark.asyncio
async def test_search_returns_only_the_requested_pdf() -> None:
    def _extract(texts, model=None):
        rows = len(texts) if isinstance(texts, list) else 1
        return np.ones((rows, 1024), dtype=np.float32)

    def _document(name: str, text: str) -> DocumentResult:
        return DocumentResult(
            metadata=DocumentMetadata(filename=name, total_pages=1, total_chunks=1),
            chunks=[
                Chunk(
                    text=text,
                    source=name,
                    page=1,
                    chunk_index=0,
                    chunk_id=f"{name}_1_0",
                )
            ],
        )

    with patch("pipeline.embedder._inference") as mock:
        mock.feature_extraction.side_effect = _extract
        from pipeline.embedder import embed_document
        from pipeline.vector_store import search

        await embed_document(_document("a.pdf", "fragment a"), "session-search")
        await embed_document(_document("b.pdf", "fragment b"), "session-search")
        await embed_document(_document("a.pdf", "other session"), "session-other")
        hits = search("question", "session-search", "a.pdf")

    assert [hit["text"] for hit in hits] == ["fragment a"]
    assert hits[0]["source"] == "a.pdf"


@pytest.mark.asyncio
async def test_hybrid_search_ranks_a_rare_word_first() -> None:
    def _extract(texts, model=None):
        rows = len(texts) if isinstance(texts, list) else 1
        return np.ones((rows, 1024), dtype=np.float32)

    document = DocumentResult(
        metadata=DocumentMetadata(filename="a.pdf", total_pages=1, total_chunks=2),
        chunks=[
            Chunk(
                text="alpha common words",
                source="a.pdf",
                page=1,
                chunk_index=0,
                chunk_id="a.pdf_1_0",
            ),
            Chunk(
                text="beta unique",
                source="a.pdf",
                page=1,
                chunk_index=1,
                chunk_id="a.pdf_1_1",
            ),
        ],
    )
    with patch("pipeline.embedder._inference") as mock:
        mock.feature_extraction.side_effect = _extract
        from pipeline.embedder import embed_document
        from pipeline.vector_store import search

        await embed_document(document, "session-hybrid")
        dense = search("unique", "session-hybrid", "a.pdf", embedding_tier="fast")
        hybrid = search("unique", "session-hybrid", "a.pdf", embedding_tier="medium")

    assert dense[0]["text"] == "alpha common words"
    assert hybrid[0]["text"] == "beta unique"


@pytest.mark.asyncio
async def test_rerank_reorders_without_loading_a_model() -> None:
    def _extract(texts, model=None):
        rows = len(texts) if isinstance(texts, list) else 1
        return np.ones((rows, 1024), dtype=np.float32)

    document = DocumentResult(
        metadata=DocumentMetadata(filename="a.pdf", total_pages=1, total_chunks=2),
        chunks=[
            Chunk(
                text="alpha common words",
                source="a.pdf",
                page=1,
                chunk_index=0,
                chunk_id="a.pdf_1_0",
            ),
            Chunk(
                text="beta unique",
                source="a.pdf",
                page=1,
                chunk_index=1,
                chunk_id="a.pdf_1_1",
            ),
        ],
    )
    with (
        patch("pipeline.embedder._inference") as mock,
        patch("pipeline.rerank.score", return_value=[0.1, 0.9]),
    ):
        mock.feature_extraction.side_effect = _extract
        from pipeline.embedder import embed_document
        from pipeline.vector_store import search

        await embed_document(document, "session-rerank")
        hits = search("unique", "session-rerank", "a.pdf", embedding_tier="slow")

    assert hits[0]["text"] == "alpha common words"
