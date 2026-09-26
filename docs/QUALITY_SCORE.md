# Quality scores

Scale used on 2026-09-26. Update it when a change moves a grade.

| Grade | Meaning |
|---|---|
| A | The module does what it says and tests cover the contract |
| B | Implemented and coherent; tests do not cover the whole contract |
| C | Works, with a known drift row in the tracker |
| D | The file does not do what it announces. Do not extend it: either a change implements it or a change deletes it |

| Module | Grade | Why |
|---|---|---|
| `models/document.py`, `models/query.py` | A | Validation covered in `tests/test_document.py` and `tests/test_query.py` |
| `pipeline/embedder.py` | B | Tests with a mocked client (prefixes, isolation, upsert, replacement) |
| `pipeline/vector_store.py` | C | Clear read path, filtered by `source`. No tests of its own |
| `pipeline/extractor.py` | C | Real conversion and chunking. `tests/test_extractor.py` is empty |
| `pipeline/rag_agent.py` | B | Four instructions, fenced-JSON recovery, and a `NOT_FOUND` fallback. Tests cover the format hint and parsing. Citation page is still the top chunk (TD-08) |
| `pipeline/orchestrator.py` | B | Two phases, per-PDF and per-question failures contained. Tests cover which files a run answers |
| `services/llm_client.py` | B | Four providers behind `call_llm`. No tests |
| `config/settings.py` | B | Validates the active provider and its key. Chunk size is not a setting |
| `storage/` | B | Session and deletion are implemented. Timeout is measured from `created_at`, as the session spec requires. No tests |
| `app/` | C | The full path is usable. No UI tests |
| `docs/` | C | Written against the code on this date. No automatic freshness check (TD-14) |
| Delivery | C | `Dockerfile` for Hugging Face Spaces (port 8501, `uv sync --no-group dev`). No CI workflow (TD-06) |

LangGraph is a dependency and has no imports (TD-13). It does not get a module grade until a change uses it or removes it.
