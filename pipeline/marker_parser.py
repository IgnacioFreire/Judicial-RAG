"""Slow parser. Marker reads layout and may OCR a region with no text layer."""

import logging
from pathlib import Path

from models.document import DocumentResult
from pipeline.parsed_pages import document_from_pages, plain_text

logger = logging.getLogger(__name__)

_converter: object | None = None


def extract_marker(pdf_path: Path) -> DocumentResult:
    """Extract one chunk per page with Marker.

    Raises:
        FileNotFoundError: The path does not exist.
        RuntimeError: Marker is not installed or failed to read the file.
    """
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    try:
        rendered = _get_converter()(str(pdf_path))
    except Exception as exc:
        logger.exception("Marker failed for %s", pdf_path.name)
        raise RuntimeError(f"Marker failed to convert {pdf_path.name}: {exc}") from exc

    pages = pages_from_marker(rendered)
    logger.info("Marker extracted %s — %d pages", pdf_path.name, len(pages))
    return document_from_pages(pdf_path.name, pages, prepend_headings=True)


def pages_from_marker(rendered: object) -> list[tuple[int, str, list[str]]]:
    """Group Marker blocks by page. Headings stay out of the body."""
    node = _as_dict(rendered)
    collected: list[tuple[int, str, list[str]]] = []
    _walk(node, page=1, headings=[], out=collected, is_root=True)
    return _join_pages(collected)


def _get_converter():
    global _converter
    if _converter is None:
        try:
            from marker.config.parser import ConfigParser
            from marker.converters.pdf import PdfConverter
            from marker.models import create_model_dict
        except ImportError as exc:
            raise RuntimeError(
                "Marker is not installed. Install marker-pdf to use the slow parser."
            ) from exc
        config_parser = ConfigParser({"output_format": "json"})
        _converter = PdfConverter(
            config=config_parser.generate_config_dict(),
            artifact_dict=create_model_dict(),
            processor_list=config_parser.get_processors(),
            renderer=config_parser.get_renderer(),
            llm_service=config_parser.get_llm_service(),
        )
        logger.debug("Marker converter ready")
    return _converter


def _as_dict(node: object) -> dict:
    if isinstance(node, dict):
        return node
    if hasattr(node, "model_dump"):
        dumped = node.model_dump()
        if isinstance(dumped, dict):
            return dumped
    children = getattr(node, "children", None)
    html = getattr(node, "html", None) or getattr(node, "markdown", None)
    return {
        "block_type": getattr(node, "block_type", ""),
        "id": getattr(node, "id", ""),
        "page_id": getattr(node, "page_id", None),
        "html": html or "",
        "children": children or [],
    }


def _walk(
    node: dict,
    page: int,
    headings: list[str],
    out: list[tuple[int, str, list[str]]],
    *,
    is_root: bool,
) -> list[str]:
    block_type = str(node.get("block_type") or "")
    current = _page_of(node, page) if "Page" in block_type else page

    html = node.get("html") or node.get("text") or ""
    text = plain_text(html) if isinstance(html, str) else ""
    is_heading = "Header" in block_type or block_type in {"Title", "SectionHeader"}
    active = [text] if is_heading and text else headings
    if text and not is_heading and "Page" not in block_type and not is_root:
        out.append((current, text, list(headings)))

    carried = active
    for child in node.get("children") or []:
        child_node = child if isinstance(child, dict) else _as_dict(child)
        carried = _walk(child_node, current, carried, out, is_root=False)
    return carried


def _page_of(node: dict, current: int) -> int:
    page_id = node.get("page_id")
    if isinstance(page_id, int) and page_id >= 0:
        return page_id + 1
    raw_id = str(node.get("id") or "")
    if "/page/" in raw_id:
        number = raw_id.rsplit("/", 1)[-1]
        if number.isdigit():
            return int(number) + 1
    return current


def _join_pages(
    blocks: list[tuple[int, str, list[str]]],
) -> list[tuple[int, str, list[str]]]:
    grouped: list[tuple[int, str, list[str]]] = []
    for page, text, headings in blocks:
        if grouped and grouped[-1][0] == page:
            previous_page, previous_text, previous_headings = grouped[-1]
            merged_headings = list(previous_headings)
            for heading in headings:
                if heading not in merged_headings:
                    merged_headings.append(heading)
            grouped[-1] = (previous_page, f"{previous_text}\n{text}", merged_headings)
            continue
        grouped.append((page, text, list(headings)))
    return grouped
