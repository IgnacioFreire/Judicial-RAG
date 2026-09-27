"""Apply a chunk tier to text that is already split by page.

Docling chooses its own chunker for the medium and slow tiers. Every
other path, and the fast tier, cuts each page into 512-token windows of
the embedding tokenizer. The page stays on the chunk.
"""

from transformers import AutoTokenizer

from config.chunkers import chunk_method_for
from models.document import Chunk, DocumentMetadata, DocumentResult

_tokenizers: dict[str, object] = {}

_WINDOW_MODEL = "intfloat/multilingual-e5-large"
_WINDOW_TOKENS = 512


def merge_page_rows(
    rows: list[tuple[int, str, list[str]]],
) -> list[tuple[int, str, list[str]]]:
    """Join successive rows that share a page. Headings stay in first-seen order."""
    grouped: list[tuple[int, str, list[str]]] = []
    for page, text, headings in rows:
        body = text.strip()
        if not body:
            continue
        if grouped and grouped[-1][0] == page:
            previous_page, previous_text, previous_headings = grouped[-1]
            merged = list(previous_headings)
            for heading in headings:
                if heading not in merged:
                    merged.append(heading)
            grouped[-1] = (previous_page, f"{previous_text}\n{body}", merged)
            continue
        grouped.append((page, body, list(headings)))
    return grouped


def retier_page_document(document: DocumentResult, chunk_tier: str) -> DocumentResult:
    """Cut each page into windows that fit the embedding model."""
    method = chunk_method_for(chunk_tier)
    if method in {"window", "hybrid", "context"}:
        return _window_document(document, _WINDOW_MODEL, _WINDOW_TOKENS)
    raise RuntimeError(f"No chunker is implemented for method '{method}'")


def _window_document(
    document: DocumentResult,
    model_name: str,
    max_tokens: int,
) -> DocumentResult:
    chunks: list[Chunk] = []
    for chunk in document.chunks:
        for part in _windows(chunk.text, model_name, max_tokens):
            index = len(chunks)
            chunks.append(
                Chunk(
                    text=part,
                    source=chunk.source,
                    page=chunk.page,
                    chunk_index=index,
                    chunk_id=f"{chunk.source}_{chunk.page}_{index}",
                    headings=list(chunk.headings),
                )
            )
    return DocumentResult(
        metadata=DocumentMetadata(
            filename=document.metadata.filename,
            total_pages=max((chunk.page for chunk in chunks), default=1),
            total_chunks=len(chunks),
        ),
        chunks=chunks,
    )


def _windows(text: str, model_name: str, max_tokens: int) -> list[str]:
    tokenizer = _tokenizer(model_name)
    token_ids = tokenizer.encode(text, add_special_tokens=False)
    if len(token_ids) <= max_tokens:
        stripped = text.strip()
        return [stripped] if stripped else []
    parts: list[str] = []
    for start in range(0, len(token_ids), max_tokens):
        piece = tokenizer.decode(
            token_ids[start : start + max_tokens],
            skip_special_tokens=True,
        ).strip()
        if piece:
            parts.append(piece)
    return parts


def _tokenizer(model_name: str):
    cached = _tokenizers.get(model_name)
    if cached is None:
        cached = AutoTokenizer.from_pretrained(model_name)
        _tokenizers[model_name] = cached
    return cached
