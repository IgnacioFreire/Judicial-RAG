# Retrieval tiers

Closed 2026-09-27. Specs: [`../../product-specs/chunking.md`](../../product-specs/chunking.md) and [`../../product-specs/retrieval.md`](../../product-specs/retrieval.md).

## Why

A page-sized chunk can leave the end of the page out of the embedding. A vector-only search can miss a number, a name, or a date that is written in the text. The session can already choose a parser and a chunk cut. It should also choose the new cuts and the new retrieval methods.

This does not change the default answers. Chunking still defaults to medium. Retrieval defaults to fast, which is the current dense search. The slow chunk tier sends passage text to the configured LLM. The slow retrieval tier downloads a cross-encoder on first use. No new package is added.

## Spec

[`../../product-specs/chunking.md`](../../product-specs/chunking.md): fast chunking is a 512-token window of the embedding tokenizer, with the page kept on the chunk. Medium stays the section chunker, measured with that same tokenizer. Slow keeps those section chunks and, at embed time, prepends one situation sentence from the LLM. The stored citation text stays the chunk.

[`../../product-specs/retrieval.md`](../../product-specs/retrieval.md): fast retrieval is dense cosine search, top 5. Medium fuses that list with a word search. Slow reranks a few dozen fused candidates. The citation score stays `1 - distance` from the dense hit when the chunk was in that list.

[`../../product-specs/session.md`](../../product-specs/session.md): `embedding_tier` is a session preference. Default fast. Reset keeps it. A future user profile stores it. The map is not per user.

## Modules

| Module | Change |
|---|---|
| `config/chunkers.py` | `window`, `hybrid`, `context` |
| `config/embeddings.py` | `dense`, `hybrid`, `rerank` |
| `pipeline/chunking.py` | Window every page at 512 embedding tokens |
| `pipeline/extractor.py` | Docling fast windows pages. Medium and slow use the section chunker with the embedding tokenizer |
| `pipeline/embedder.py` | Slow chunk tier prepends the situation sentence to the embedded text only |
| `pipeline/lexical.py` | BM25 and reciprocal-rank fusion, no new dependency |
| `pipeline/rerank.py` | Lazy cross-encoder |
| `pipeline/vector_store.py` | Dispatch the retrieval tier |
| `app/` | Third advanced-settings control, passed through `run` |

## Tests

- The two maps and an unknown tier.
- A long page splits and a short page stays one chunk, with a fake tokenizer.
- A rare word outranks an earlier chunk under hybrid search.
- The rerank tier reorders candidates without loading the model in the test.
- The context sentence is sent to the embedding API and is not the stored text.
