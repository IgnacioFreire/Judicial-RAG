"""
extractor.py

PDF content extraction using Docling and HybridChunker.
Handles native digital PDFs. OCR is not used: a scanned PDF is not a
supported input. Uses Docling's native document hierarchy to produce
semantically coherent chunks with section headings as metadata, avoiding
the need for regex-based section detection.
"""

import asyncio
import logging
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from docling.chunking import HybridChunker
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling_core.transforms.chunker.tokenizer.huggingface import HuggingFaceTokenizer
from transformers import AutoTokenizer

from config.settings import settings
from models.document import Chunk, DocumentMetadata, DocumentResult

logger = logging.getLogger(__name__)

_executor: ThreadPoolExecutor | None = None
_tokenizer: HuggingFaceTokenizer | None = None
_converter: DocumentConverter | None = None


def _make_pipeline_options() -> PdfPipelineOptions:
    """Build Docling pipeline options with only the features we need.

    Table structure analysis, page image generation, picture image
    generation, and OCR are off. The product reads the digital text layer.

    Returns:
        Configured PdfPipelineOptions instance.
    """
    options = PdfPipelineOptions()
    options.do_ocr = False
    options.do_table_structure = False
    options.generate_page_images = False
    options.generate_picture_images = False
    return options


def _make_converter() -> DocumentConverter:
    """Build a DocumentConverter with minimal pipeline options.

    Returns:
        Configured DocumentConverter instance.
    """
    return DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(pipeline_options=_make_pipeline_options())
        }
    )


def _pool() -> ThreadPoolExecutor:
    """Build the extraction thread pool on first use."""
    global _executor
    if _executor is None:
        _executor = ThreadPoolExecutor(max_workers=settings.max_parallel_pdfs)
        logger.debug("Thread pool created with %d workers", settings.max_parallel_pdfs)
    return _executor


def _chunk_tokenizer() -> HuggingFaceTokenizer:
    """Load the chunk-size tokenizer on first use.

    bert-base-multilingual-cased measures tokens only. Embeddings are
    intfloat/multilingual-e5-large in embedder.py. 512 tokens keeps a
    chunk inside that model's input.
    """
    global _tokenizer
    if _tokenizer is None:
        _tokenizer = HuggingFaceTokenizer(
            tokenizer=AutoTokenizer.from_pretrained("bert-base-multilingual-cased"),
            max_tokens=512,
        )
        logger.debug(
            "Chunking tokenizer loaded: bert-base-multilingual-cased (max_tokens=512)"
        )
    return _tokenizer


def _get_converter() -> DocumentConverter:
    """Build the digital Docling converter on first use."""
    global _converter
    if _converter is None:
        _converter = _make_converter()
        logger.debug("Docling converter ready (digital, OCR off)")
    return _converter


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


async def extract(pdf_path: Path) -> DocumentResult:
    """Extract text and metadata from a digital PDF asynchronously.

    Offloads Docling's synchronous conversion to a thread pool so multiple
    PDFs can be processed concurrently without blocking the event loop.
    OCR is not applied.

    Args:
        pdf_path: Absolute path to the PDF file.

    Returns:
        DocumentResult with all chunks and document metadata.
    """
    logger.info("Queuing extraction: %s", pdf_path.name)
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(_pool(), _extract_sync, pdf_path)


# ---------------------------------------------------------------------------
# Internal implementation
# ---------------------------------------------------------------------------


def _extract_sync(pdf_path: Path) -> DocumentResult:
    """Run Docling extraction and chunking synchronously.

    Separated from the async wrapper so it can run in a thread
    without carrying async context.

    Args:
        pdf_path: Absolute path to the PDF file.

    Returns:
        DocumentResult with all chunks and document metadata.

    Raises:
        FileNotFoundError: If the PDF does not exist at the given path.
        RuntimeError: If Docling fails to convert the document.
    """
    logger.debug("_extract_sync started: %s", pdf_path.name)
    t_start = time.perf_counter()

    if not pdf_path.exists():
        logger.error("PDF not found: %s", pdf_path)
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    logger.debug("Using digital converter for %s", pdf_path.name)

    try:
        t_convert = time.perf_counter()
        result = _get_converter().convert(str(pdf_path))
        logger.debug(
            "Docling conversion complete: %s (%.2fs)",
            pdf_path.name,
            time.perf_counter() - t_convert,
        )
    except Exception as e:
        # logger.exception logs the message and the full traceback automatically
        logger.exception("Docling conversion failed for %s", pdf_path.name)
        raise RuntimeError(f"Docling failed to convert {pdf_path.name}: {e}") from e

    chunker = HybridChunker(
        tokenizer=_chunk_tokenizer(),
        # Merge consecutive undersized chunks that share the same headings
        # to avoid fragmenting short paragraphs across chunk boundaries
        merge_peers=True,
    )

    t_chunk = time.perf_counter()
    chunks = _build_chunks(chunker, result.document, pdf_path.name)
    logger.debug(
        "Chunking complete: %s — %d chunks in %.2fs",
        pdf_path.name,
        len(chunks),
        time.perf_counter() - t_chunk,
    )

    metadata = DocumentMetadata(
        filename=pdf_path.name,
        total_pages=max((c.page for c in chunks), default=1),
        total_chunks=len(chunks),
    )

    logger.info(
        "Extraction complete: %s — %d chunks, %d pages (total %.2fs)",
        pdf_path.name,
        metadata.total_chunks,
        metadata.total_pages,
        time.perf_counter() - t_start,
    )

    return DocumentResult(metadata=metadata, chunks=chunks)


def _build_chunks(
    chunker: HybridChunker,
    doc: object,
    filename: str,
) -> list[Chunk]:
    """Convert HybridChunker output into Chunk model instances.

    Uses chunker.contextualize() rather than the raw chunk text so that
    the heading breadcrumb is prepended to every chunk. This gives the
    embedding model the section context alongside the chunk content, which
    improves retrieval precision for section-specific questions like
    "what was the ruling?" or "what articles were cited?".

    Skips empty chunks that can appear as layout artefacts in Docling's
    output for pages that contain only images or decorative elements.

    Args:
        chunker: Configured HybridChunker instance.
        doc: DoclingDocument returned by DocumentConverter.
        filename: Source PDF filename used for chunk_id and source fields.

    Returns:
        Ordered list of Chunk instances, one per non-empty Docling chunk.
    """
    chunks: list[Chunk] = []
    skipped = 0

    for chunk_index, docling_chunk in enumerate(chunker.chunk(dl_doc=doc)):
        text = chunker.contextualize(chunk=docling_chunk)

        if not text.strip():
            skipped += 1
            logger.debug("Skipping empty chunk %d in %s", chunk_index, filename)
            continue

        page = _get_page(docling_chunk)
        headings = list(docling_chunk.meta.headings or [])

        logger.debug(
            "Chunk %d: page=%d heading_count=%d text_chars=%d",
            chunk_index,
            page,
            len(headings),
            len(text),
        )

        chunks.append(
            Chunk(
                text=text,
                source=filename,
                page=page,
                chunk_index=chunk_index,
                chunk_id=f"{filename}_{page}_{chunk_index}",
                headings=headings,
            )
        )

    if skipped:
        logger.debug("Skipped %d empty chunks in %s", skipped, filename)

    return chunks


def _get_page(docling_chunk: object) -> int:
    """Extract the page number from a Docling chunk's provenance metadata.

    Navigates the chain: chunk.meta.doc_items[0].prov[0].page_no.
    Each level can be absent depending on the Docling version and the
    type of content element, so every access is guarded by the try/except.

    Args:
        docling_chunk: A chunk produced by HybridChunker.

    Returns:
        1-indexed page number, or 1 as a safe fallback.
    """
    try:
        doc_items = docling_chunk.meta.doc_items
        if doc_items and doc_items[0].prov:
            return doc_items[0].prov[0].page_no
    except Exception:
        # Provenance metadata is absent for some element types — fall back
        # to page 1 rather than crashing the entire extraction
        logger.debug(
            "Could not extract page number from chunk provenance, defaulting to 1"
        )
    return 1
