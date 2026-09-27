"""Parser and chunk tier maps, and page assembly. The text below is synthetic."""

import pytest

from config.chunkers import CHUNK_TIERS, DEFAULT_CHUNK_TIER, chunk_method_for
from config.embeddings import (
    DEFAULT_EMBEDDING_TIER,
    EMBEDDING_TIERS,
    embedding_method_for,
)
from config.parsers import DEFAULT_PARSER_TIER, PARSER_TIERS, method_for
from models.document import Chunk, DocumentMetadata, DocumentResult
from pipeline.chunking import merge_page_rows, retier_page_document
from pipeline.marker_parser import pages_from_marker
from pipeline.parsed_pages import document_from_pages
from pipeline.pymupdf_parser import _pages


def test_tiers_map_to_the_three_methods() -> None:
    assert PARSER_TIERS == {
        "fast": "pymupdf4llm",
        "medium": "docling",
        "slow": "marker",
    }
    assert DEFAULT_PARSER_TIER == "medium"
    assert method_for("fast") == "pymupdf4llm"


def test_chunk_tiers_map_to_the_three_methods() -> None:
    assert CHUNK_TIERS == {
        "fast": "window",
        "medium": "hybrid",
        "slow": "context",
    }
    assert DEFAULT_CHUNK_TIER == "medium"
    assert chunk_method_for("slow") == "context"


def test_embedding_tiers_map_to_the_three_methods() -> None:
    assert EMBEDDING_TIERS == {
        "fast": "dense",
        "medium": "hybrid",
        "slow": "rerank",
    }
    assert DEFAULT_EMBEDDING_TIER == "fast"
    assert embedding_method_for("medium") == "hybrid"


def test_unknown_embedding_tier_is_rejected() -> None:
    with pytest.raises(ValueError, match="not configured"):
        embedding_method_for("colbert")


def test_unknown_chunk_tier_is_rejected() -> None:
    with pytest.raises(ValueError, match="not configured"):
        chunk_method_for("semantic")


def test_page_rows_on_the_same_page_join() -> None:
    rows = merge_page_rows(
        [
            (1, "first line", ["SECTION"]),
            (1, "second line", ["SECTION", "NEXT"]),
            (2, "other page", []),
        ]
    )
    assert rows == [
        (1, "first line\nsecond line", ["SECTION", "NEXT"]),
        (2, "other page", []),
    ]


def test_fast_window_splits_a_long_page(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("pipeline.chunking._tokenizer", lambda _name: _WordTokenizer())
    monkeypatch.setattr("pipeline.chunking._WINDOW_TOKENS", 2)
    words = " ".join(f"word{index}" for index in range(5))
    document = DocumentResult(
        metadata=DocumentMetadata(filename="a.pdf", total_pages=1, total_chunks=1),
        chunks=[
            Chunk(
                text=words,
                source="a.pdf",
                page=2,
                chunk_index=0,
                chunk_id="a.pdf_2_0",
            )
        ],
    )
    windowed = retier_page_document(document, "fast")
    assert [chunk.page for chunk in windowed.chunks] == [2, 2, 2]
    assert windowed.chunks[0].text == "word0 word1"
    assert windowed.chunks[-1].text == "word4"


class _WordTokenizer:
    def encode(self, text: str, add_special_tokens: bool = False) -> list[str]:
        return text.split()

    def decode(self, token_ids: list[str], skip_special_tokens: bool = True) -> str:
        return " ".join(token_ids)


def test_unknown_tier_is_rejected() -> None:
    with pytest.raises(ValueError, match="not configured"):
        method_for("ocr")


def test_pymupdf_page_chunks_keep_page_and_heading() -> None:
    pages = _pages(
        [
            {
                "metadata": {"page": 2},
                "toc_items": [(1, "SECTION", 2)],
                "text": "synthetic line",
            },
            {"metadata": {}, "toc_items": [], "text": "   "},
        ]
    )
    document = document_from_pages("a.pdf", pages, prepend_headings=False)
    assert document.metadata.total_chunks == 1
    assert document.chunks[0].page == 2
    assert document.chunks[0].headings == ["SECTION"]
    assert document.chunks[0].text == "synthetic line"
    assert document.chunks[0].chunk_id == "a.pdf_2_0"


def test_marker_groups_a_page_and_prepends_the_heading() -> None:
    rendered = {
        "block_type": "Document",
        "children": [
            {
                "block_type": "Page",
                "id": "/page/0",
                "children": [
                    {"block_type": "SectionHeader", "html": "<h2>SECTION</h2>"},
                    {"block_type": "Text", "html": "<p>synthetic line</p>"},
                ],
            }
        ],
    }
    pages = pages_from_marker(rendered)
    document = document_from_pages("a.pdf", pages, prepend_headings=True)
    assert document.chunks[0].page == 1
    assert document.chunks[0].headings == ["SECTION"]
    assert document.chunks[0].text == "SECTION\nsynthetic line"
