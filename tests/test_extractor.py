"""Chunk assembly without running Docling conversion.

The text below is synthetic. It is not a ruling.
"""

from types import SimpleNamespace

from pipeline.extractor import _build_chunks, _get_page, _make_pipeline_options


class _Chunker:
    def __init__(self, chunks: list) -> None:
        self._chunks = chunks

    def chunk(self, dl_doc: object) -> list:
        return self._chunks

    def contextualize(self, chunk: object) -> str:
        return chunk.text


def _chunk(text: str, page: int, headings: list[str]) -> SimpleNamespace:
    provenance = SimpleNamespace(page_no=page)
    item = SimpleNamespace(prov=[provenance])
    return SimpleNamespace(
        text=text,
        meta=SimpleNamespace(headings=headings, doc_items=[item]),
    )


def test_empty_chunks_are_skipped_and_page_is_kept() -> None:
    chunker = _Chunker(
        [
            _chunk("   ", 1, []),
            _chunk("synthetic line", 3, ["SECTION"]),
        ]
    )
    chunks = _build_chunks(chunker, object(), "a.pdf")
    assert len(chunks) == 1
    assert chunks[0].text == "synthetic line"
    assert chunks[0].page == 3
    assert chunks[0].headings == ["SECTION"]
    assert chunks[0].chunk_id == "a.pdf_3_1"
    assert chunks[0].source == "a.pdf"


def test_missing_provenance_defaults_to_page_one() -> None:
    chunk = SimpleNamespace(meta=SimpleNamespace(headings=[], doc_items=[]))
    assert _get_page(chunk) == 1


def test_digital_pipeline_leaves_ocr_off() -> None:
    options = _make_pipeline_options()
    assert options.do_ocr is False
    assert options.do_table_structure is False
