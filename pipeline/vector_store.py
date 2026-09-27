"""
vector_store.py

Query interface for the session search index.
Provides semantic search over embedded document chunks, scoped both
to a user session and to a specific source document. The embedder
writes the index; this module only reads from it.
"""

import json
import logging

from config.embeddings import DEFAULT_EMBEDDING_TIER, embedding_method_for
from pipeline.embedder import embed_query
from pipeline.index_store import get_index
from pipeline.lexical import bm25_order, fuse

logger = logging.getLogger(__name__)

# Number of chunks returned to the agent.
_DEFAULT_N_RESULTS = 5
# Dense and word lists fused before a reranker sees them.
_CANDIDATES = 30


def search(
    question: str,
    session_id: str,
    source: str,
    n_results: int = _DEFAULT_N_RESULTS,
    embedding_tier: str = DEFAULT_EMBEDDING_TIER,
) -> list[dict]:
    """Search for chunks relevant to a question within a single document.

    Embeds the question and queries the session index, filtered to one PDF.
    Returns chunks ordered by descending cosine similarity (ascending distance).

    Args:
        question: The user question or variable to extract.
        session_id: Selects the index rows for this user session.
        source: PDF filename to restrict the search to. Must match the
            `source` field stored at index time.
        n_results: Maximum number of chunks to return.
        embedding_tier: Retrieval setting. Fast is the vector only.

    Returns:
        List of result dicts ordered by relevance, each containing:
            text        — raw chunk text returned as citation to the user.
            source      — PDF filename.
            page        — page number (1-indexed).
            headings    — section breadcrumb as a list of strings.
            chunk_index — position of the chunk within the document.
            distance    — cosine distance; lower means more similar.
    """
    logger.debug(
        "Search: question_chars=%d source=%s n=%d session=%s",
        len(question),
        source,
        n_results,
        session_id,
    )

    query_vector = embed_query(question)
    method = embedding_method_for(embedding_tier)
    index = get_index()
    if method == "dense":
        found = index.search(session_id, source, query_vector, n_results)
    else:
        found = _fused(
            question,
            session_id,
            source,
            query_vector,
            n_results,
            rerank=method == "rerank",
        )
    results = [{**hit, "headings": _headings(hit.get("headings", []))} for hit in found]

    logger.debug(
        "Search returned %d results (top distance=%.4f)",
        len(results),
        results[0]["distance"] if results else float("nan"),
    )
    return results


def list_sources(session_id: str) -> list[str]:
    """Return the unique PDF filenames indexed in a session.

    Used by the orchestrator to iterate over all documents and run the
    agent's questions against each one independently.

    Args:
        session_id: User session identifier.

    Returns:
        Sorted list of unique source filenames. Empty if no documents
        have been indexed yet.
    """
    sources = get_index().list_sources(session_id)
    logger.debug(
        "%d unique source(s) in session=%s: %s",
        len(sources),
        session_id,
        sources,
    )
    return sources


def _fused(
    question: str,
    session_id: str,
    source: str,
    query_vector: list[float],
    n_results: int,
    rerank: bool,
) -> list[dict]:
    """Fuse the vector list with a word list. Slow then reranks that shortlist."""
    index = get_index()
    pool = max(n_results, _CANDIDATES)
    dense = index.search(session_id, source, query_vector, pool)
    rows = index.source_chunks(session_id, source)
    lexical_ids = bm25_order(question, rows)
    limit = pool if rerank else n_results
    fused = fuse(dense, lexical_ids, rows, limit)
    if not rerank:
        return fused
    from pipeline.rerank import score

    scores = score(question, [str(hit.get("text", "")) for hit in fused])
    order = sorted(range(len(fused)), key=lambda index: -scores[index])
    return [fused[index] for index in order[:n_results]]


def _headings(raw: object) -> list[str]:
    """Decode headings stored as a list or as a JSON array."""
    if isinstance(raw, list) and all(isinstance(item, str) for item in raw):
        return list(raw)
    if not isinstance(raw, str) or not raw:
        return []
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return []
    if isinstance(parsed, list) and all(isinstance(item, str) for item in parsed):
        return parsed
    return []
