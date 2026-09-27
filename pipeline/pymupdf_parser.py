"""Fast parser. PyMuPDF4LLM reads the digital text layer, one chunk per page."""

import logging
from pathlib import Path

from models.document import DocumentResult
from pipeline.parsed_pages import document_from_pages, plain_text

logger = logging.getLogger(__name__)


def extract_pymupdf(pdf_path: Path) -> DocumentResult:
    """Extract one chunk per page from the PDF text layer.

    Raises:
        FileNotFoundError: The path does not exist.
        RuntimeError: PyMuPDF4LLM failed to read the file.
    """
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    import pymupdf4llm

    try:
        payload = pymupdf4llm.to_markdown(str(pdf_path), page_chunks=True)
    except Exception as exc:
        logger.exception("PyMuPDF4LLM failed for %s", pdf_path.name)
        raise RuntimeError(
            f"PyMuPDF4LLM failed to convert {pdf_path.name}: {exc}"
        ) from exc

    pages = _pages(payload)
    logger.info("PyMuPDF4LLM extracted %s — %d pages", pdf_path.name, len(pages))
    return document_from_pages(pdf_path.name, pages, prepend_headings=False)


def _pages(payload: object) -> list[tuple[int, str, list[str]]]:
    if isinstance(payload, str):
        text = payload.strip()
        return [(1, text, [])] if text else []
    if not isinstance(payload, list):
        return []

    pages: list[tuple[int, str, list[str]]] = []
    for index, item in enumerate(payload):
        if not isinstance(item, dict):
            continue
        raw_metadata = item.get("metadata")
        metadata = raw_metadata if isinstance(raw_metadata, dict) else {}
        text = item.get("text") if isinstance(item.get("text"), str) else ""
        headings = _headings(item.get("toc_items"))
        pages.append((_page_number(metadata, index), text, headings))
    return pages


def _page_number(metadata: dict, index: int) -> int:
    for key in ("page", "page_number"):
        value = metadata.get(key)
        if isinstance(value, int) and value >= 1:
            return value
    return index + 1


def _headings(items: object) -> list[str]:
    if not isinstance(items, list):
        return []
    headings: list[str] = []
    for item in items:
        title = _heading_title(item)
        if title and title not in headings:
            headings.append(title)
    return headings


def _heading_title(item: object) -> str:
    if isinstance(item, str):
        return plain_text(item)
    if isinstance(item, dict):
        for key in ("title", "text", "name"):
            value = item.get(key)
            if isinstance(value, str) and value.strip():
                return plain_text(value)
        return ""
    if isinstance(item, (list, tuple)) and len(item) >= 2 and isinstance(item[1], str):
        return plain_text(item[1])
    return ""
