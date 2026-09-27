"""
embedder.py

Embedding generation and vector store writes.
Converts document chunks into vectors with the HF Inference API and
stores them in the session index with their metadata.
Each session id is isolated so documents from different sessions never mix.
"""

import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

import numpy as np
from huggingface_hub import InferenceClient

from config.chunkers import DEFAULT_CHUNK_TIER, chunk_method_for
from config.settings import settings
from models.document import Chunk, DocumentResult
from pipeline.index_store import IndexRow, get_index
from services.llm_usage import bind, unbind

logger = logging.getLogger(__name__)

_inference = None
_executor: ThreadPoolExecutor | None = None

# multilingual-e5-large uses asymmetric prefixes for retrieval:
# "passage: " for documents at index time, "query: " for questions at
# search time. This distinction is central to the model's retrieval quality.
_PASSAGE_PREFIX = "passage: "
_QUERY_PREFIX = "query: "

# Maximum number of chunks sent to the HF API in a single batch.
# Keeps individual requests small to stay within rate limits and timeouts.
_BATCH_SIZE = 32


async def embed_document(
    document: DocumentResult,
    session_id: str,
    chunk_tier: str = DEFAULT_CHUNK_TIER,
) -> None:
    """Embed all chunks of a document and store them in the session index.

    Re-processing the same PDF replaces that filename's chunks. A shorter
    file does not leave the previous chunk ids behind.

    Args:
        document: Extraction result from extractor.py containing all chunks.
        session_id: Unique identifier for the user session.
        chunk_tier: Chunk setting. Slow prepends a situation sentence
            to the embedded text only.
    """
    logger.info(
        "Embedding started: %s — %d chunks (session=%s)",
        document.metadata.filename,
        document.metadata.total_chunks,
        session_id,
    )
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(_pool(), _embed_sync, document, session_id, chunk_tier)
    logger.info(
        "Embedding complete: %s (session=%s)",
        document.metadata.filename,
        session_id,
    )


def embed_query(text: str) -> list[float]:
    """Embed a user question for similarity search against stored chunks.

    Uses the "query: " prefix required by multilingual-e5-large for
    retrieval queries, which produces embeddings in the same vector space
    as the "passage: " embeddings stored during indexing.

    Args:
        text: The user question or search query.

    Returns:
        1024-dimensional float vector.
    """
    logger.debug("Embedding query (%d chars)", len(text))
    return _to_vector(f"{_QUERY_PREFIX}{text}")


def delete_source(session_id: str, source: str) -> None:
    """Delete every chunk stored for one PDF inside a session.

    Called before re-indexing that filename, and when a run no longer
    includes it.

    Args:
        session_id: Unique identifier for the user session.
        source: PDF filename stored on the chunk.
    """
    get_index().delete_source(session_id, source)
    logger.info("Deleted indexed source %s (session=%s)", source, session_id)


def delete_collection(session_id: str) -> None:
    """Delete every indexed chunk for a session.

    Called by storage/cleanup.py when a session ends or times out.
    A session that never indexed anything is a no-op.

    Args:
        session_id: Unique identifier for the user session.
    """
    get_index().delete_session(session_id)
    logger.debug("Index deleted for session=%s", session_id)


def delete_expired_index(cutoff: datetime) -> None:
    """Delete chunks first stored at or before cutoff.

    Args:
        cutoff: Aware UTC timestamp. Rows stored at or before this time go.
    """
    get_index().delete_older_than(cutoff)
    logger.debug("Expired index rows deleted up to %s", cutoff.isoformat())


def reset_inference_client() -> None:
    """Drop the cached HF client after session key overrides change."""
    global _inference
    _inference = None


def _client() -> InferenceClient:
    """Build the Hugging Face client on first use."""
    global _inference
    from services.session_secrets import huggingface_api_key

    if _inference is None:
        _inference = InferenceClient(
            provider="hf-inference",
            api_key=huggingface_api_key(),
        )
        logger.debug("HF InferenceClient initialised: %s", settings.embedding_model)
    return _inference


def _pool() -> ThreadPoolExecutor:
    """Build the embedding thread pool on first use."""
    global _executor
    if _executor is None:
        _executor = ThreadPoolExecutor(max_workers=settings.max_parallel_pdfs)
    return _executor


def _embed_sync(
    document: DocumentResult,
    session_id: str,
    chunk_tier: str = DEFAULT_CHUNK_TIER,
) -> None:
    """Embed all chunks synchronously and upsert them into the session index.

    Processes chunks in fixed-size batches to respect API rate limits.
    The previous version of the same PDF is deleted first so a shorter
    file cannot leave old ids.

    Args:
        document: Extraction result containing the chunks to embed.
        session_id: User session identifier for isolation.
    """
    chunks = document.chunks
    token = bind(session_id)
    try:
        delete_source(session_id, document.metadata.filename)
        if not chunks:
            logger.warning("No chunks to embed for %s", document.metadata.filename)
            return

        total = len(chunks)
        for start in range(0, total, _BATCH_SIZE):
            batch = chunks[start : start + _BATCH_SIZE]
            logger.debug(
                "Embedding batch %d-%d / %d for %s",
                start + 1,
                start + len(batch),
                total,
                document.metadata.filename,
            )
            _upsert_batch(session_id, batch, chunk_tier)
    finally:
        unbind(token)


def _upsert_batch(
    session_id: str,
    chunks: list[Chunk],
    chunk_tier: str = DEFAULT_CHUNK_TIER,
) -> None:
    """Generate embeddings for a batch and upsert them into the session index.

    Args:
        session_id: User session identifier.
        chunks: Batch of chunks to embed and store.
    """
    texts = [_passage(chunk, chunk_tier) for chunk in chunks]
    embeddings = _to_vectors(texts)
    rows = [
        IndexRow(
            chunk_id=chunk.chunk_id,
            source=chunk.source,
            page=chunk.page,
            chunk_index=chunk.chunk_index,
            headings=list(chunk.headings),
            text=chunk.text,
            embedding=embedding,
        )
        for chunk, embedding in zip(chunks, embeddings, strict=True)
    ]
    get_index().upsert(session_id, rows)
    logger.debug("Upserted %d chunks", len(chunks))


def _passage(chunk: Chunk, chunk_tier: str) -> str:
    """Build the text sent to the embedding model. The stored text is separate."""
    body = chunk.text
    if chunk_method_for(chunk_tier) == "context":
        from pipeline.chunk_context import situation_sentence

        sentence = situation_sentence(chunk.headings, chunk.text)
        if sentence:
            body = f"{sentence}\n{chunk.text}"
    return f"{_PASSAGE_PREFIX}{body}"


def _to_vector(text: str) -> list[float]:
    """Embed a single text string via the HF Inference API.

    Args:
        text: Text to embed, including the appropriate prefix.

    Returns:
        1024-dimensional float vector as a Python list.
    """
    return _to_vectors([text])[0]


def _to_vectors(texts: list[str]) -> list[list[float]]:
    """Embed a batch of texts in one HF Inference API call.

    Args:
        texts: Texts to embed, including the appropriate prefix.

    Returns:
        One float vector per text, each of length embedding_dimensions.

    Raises:
        RuntimeError: If the API shape does not match the batch or the
            configured dimension.
    """
    if not texts:
        return []
    raw = _client().feature_extraction(texts, model=settings.embedding_model)
    array = np.asarray(raw, dtype=float)
    if array.ndim == 1:
        array = array.reshape(1, -1)
    expected = settings.embedding_dimensions
    if array.ndim != 2 or array.shape != (len(texts), expected):
        raise RuntimeError(
            f"Expected embeddings shape {(len(texts), expected)}, got {array.shape}"
        )
    return array.tolist()
