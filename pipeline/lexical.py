"""Word search over chunks already stored for one PDF.

BM25 ranks rare words above common ones. Reciprocal rank fusion joins
that list with the dense list. No extra package.
"""

import math
import re

_TOKEN = re.compile(r"\w+", re.UNICODE)
_K1 = 1.5
_B = 0.75
_RRF_K = 60


def tokens(text: str) -> list[str]:
    """Lowercase word tokens. Punctuation is dropped."""
    return [part.lower() for part in _TOKEN.findall(text)]


def bm25_order(query: str, rows: list[dict]) -> list[str]:
    """Return chunk ids with a positive BM25 score, best first."""
    query_terms = tokens(query)
    if not query_terms or not rows:
        return []
    documents = [tokens(str(row.get("text", ""))) for row in rows]
    scores = _bm25(query_terms, documents)
    ranked = sorted(
        range(len(rows)),
        key=lambda index: (
            -scores[index],
            rows[index].get("chunk_index", 0),
            str(rows[index].get("chunk_id", "")),
        ),
    )
    return [
        str(rows[index]["chunk_id"])
        for index in ranked
        if scores[index] > 0 and rows[index].get("chunk_id")
    ]


def fuse(
    dense: list[dict], lexical_ids: list[str], rows: list[dict], limit: int
) -> list[dict]:
    """Join the two rankings. A chunk found only by words gets distance 1."""
    if limit < 1:
        return []
    by_id = {str(row["chunk_id"]): row for row in rows if row.get("chunk_id")}
    dense_by_id = {str(hit["chunk_id"]): hit for hit in dense if hit.get("chunk_id")}
    scores: dict[str, float] = {}
    _add_ranks(scores, [str(hit["chunk_id"]) for hit in dense if hit.get("chunk_id")])
    _add_ranks(scores, lexical_ids)
    ordered = sorted(scores, key=lambda chunk_id: (-scores[chunk_id], chunk_id))
    fused: list[dict] = []
    for chunk_id in ordered:
        if chunk_id in dense_by_id:
            fused.append(dense_by_id[chunk_id])
        elif chunk_id in by_id:
            fused.append({**by_id[chunk_id], "distance": 1.0})
        if len(fused) == limit:
            return fused
    return fused


def _add_ranks(scores: dict[str, float], ranking: list[str]) -> None:
    for rank, chunk_id in enumerate(ranking):
        scores[chunk_id] = scores.get(chunk_id, 0.0) + 1.0 / (_RRF_K + rank + 1)


def _bm25(query_terms: list[str], documents: list[list[str]]) -> list[float]:
    count = len(documents)
    average = sum(len(document) for document in documents) / count
    document_frequency: dict[str, int] = {}
    for document in documents:
        for term in set(document):
            document_frequency[term] = document_frequency.get(term, 0) + 1
    scores: list[float] = []
    for document in documents:
        frequency: dict[str, int] = {}
        for term in document:
            frequency[term] = frequency.get(term, 0) + 1
        length = len(document)
        score = 0.0
        for term in query_terms:
            seen = document_frequency.get(term, 0)
            if seen == 0 or term not in frequency:
                continue
            idf = math.log(1 + (count - seen + 0.5) / (seen + 0.5))
            term_frequency = frequency[term]
            length_scale = (length / average) if average else 1.0
            denominator = term_frequency + _K1 * (1 - _B + _B * length_scale)
            score += idf * term_frequency * (_K1 + 1) / denominator
        scores.append(score)
    return scores
