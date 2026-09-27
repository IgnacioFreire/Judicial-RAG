# Quality scores

Scale used on 2026-09-26. Last grade pass 2026-09-27.

| Grade | Meaning |
|---|---|
| A | The module does what it says and tests cover the contract |
| B | Implemented and coherent; tests do not cover the whole contract |
| C | Works, with a known drift row in the tracker |
| D | The file does not do what it announces. Do not extend it: either a change implements it or a change deletes it |

| Module | Grade | Why |
|---|---|---|
| `models/document.py`, `models/query.py` | A | Validation covered in `tests/test_document.py` and `tests/test_query.py` |
| `pipeline/embedder.py` | B | Tests with a mocked client (prefixes, isolation, upsert, replacement, context sentence) |
| `pipeline/vector_store.py` | B | Dense, hybrid, and rerank dispatch. Tests cover heading decoding, source filter, word fusion, and a mocked rerank. The Supabase HTTP client and the real cross-encoder are not exercised |
| `pipeline/chunking.py` | A | Windowing a long page is covered in `tests/test_parsers.py` |
| `pipeline/lexical.py` | A | BM25 plus fusion covered through hybrid search in `tests/test_vector_store.py` |
| `pipeline/rerank.py` | B | Loaded only on the slow retrieval tier. Tests stub `score` |
| `pipeline/chunk_context.py` | B | Slow chunk tier. Tests stub `call_llm` |
| `pipeline/extractor.py` | B | Chunk assembly is tested. Docling conversion itself is not |
| `pipeline/rag_agent.py` | B | Four instructions, fenced-JSON recovery, and a `NOT_FOUND` fallback. Tests cover the format hint and parsing. Citation page is still the top chunk (TD-08) |
| `pipeline/orchestrator.py` | B | Two phases, per-PDF and per-question failures contained. Tests cover which files a run answers |
| `services/llm_client.py` | B | Four providers behind `call_llm`. No tests |
| `config/settings.py` | B | Validates the active provider and its key. Chunk size is not a setting |
| `config/parsers.py` | A | The three tiers map to the three methods. Covered in `tests/test_parsers.py` |
| `config/chunkers.py` | A | The three chunk tiers map to window, hybrid, and context. Covered in `tests/test_parsers.py` |
| `config/embeddings.py` | A | The three retrieval tiers map to dense, hybrid, and rerank. Covered in `tests/test_parsers.py` |
| `storage/` | B | Session and deletion are implemented. Timeout is measured from `created_at`, as the session spec requires. No tests |
| `app/` | B | HTTP session, upload, schema, tiers, run SSE, and reset are covered in `tests/test_api.py`. The long pipeline is mocked. |
| `web/` | B | One screen matching DESIGN copy. Lint and production build run in CI. No browser tests. |
| `docs/` | B | `tests/test_doc_links.py` checks relative links. Freshness is still updated in the same change as the code |
| Delivery | B | GitHub Actions runs ruff, pytest, and the web lint/build on push and pull request |
