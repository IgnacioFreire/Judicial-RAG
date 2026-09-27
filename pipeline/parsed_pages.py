"""Turn page text into the document result the embedder already accepts."""

import re

from models.document import Chunk, DocumentMetadata, DocumentResult

_TAG = re.compile(r"<[^>]+>")


def plain_text(value: str) -> str:
    """Drop HTML tags and collapse whitespace."""
    return " ".join(_TAG.sub(" ", value).split())


def document_from_pages(
    filename: str,
    pages: list[tuple[int, str, list[str]]],
    *,
    prepend_headings: bool,
) -> DocumentResult:
    """Build one chunk per non-empty page.

    Args:
        filename: PDF filename stored on each chunk.
        pages: Page number, body text, and section headings, in order.
        prepend_headings: When true, headings are written above the body,
            matching Docling's contextualize step.
    """
    chunks: list[Chunk] = []
    for page, body, headings in pages:
        text = body.strip()
        if not text:
            continue
        if prepend_headings and headings:
            text = "\n".join([*headings, text])
        index = len(chunks)
        chunks.append(
            Chunk(
                text=text,
                source=filename,
                page=page,
                chunk_index=index,
                chunk_id=f"{filename}_{page}_{index}",
                headings=list(headings),
            )
        )

    return DocumentResult(
        metadata=DocumentMetadata(
            filename=filename,
            total_pages=max((chunk.page for chunk in chunks), default=1),
            total_chunks=len(chunks),
        ),
        chunks=chunks,
    )
