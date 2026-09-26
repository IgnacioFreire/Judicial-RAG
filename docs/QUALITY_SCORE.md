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
| `models/document.py`, `models/query.py` | A | Validation covered in `tests/test_document.py` and `tests/test_query.py`. The schema-persistence docstring is still wrong (TD-07) |
| `pipeline/embedder.py` | B | Tests with a mocked client (prefixes, isolation, upsert). The model name is still TD-01 |
| `pipeline/vector_store.py` | C | Clear read path, filtered by `source`. No tests of its own |
| `pipeline/extractor.py` | C | Real conversion and chunking. `tests/test_extractor.py` is empty. TD-02 |
| `pipeline/rag_agent.py` | B | Four instructions, fenced-JSON recovery, and a `NOT_FOUND` fallback. Tests cover the format hint and parsing. Citation page is still the top chunk (TD-08) |
| `pipeline/orchestrator.py` | B | Two phases, per-PDF and per-question failures contained. No tests |
| `services/llm_client.py` | B | Four providers behind `call_llm`. No tests |
| `config/settings.py` | C | Validates the active provider and its key. Nobody reads `CHUNK_*` (TD-02) |
| `config/prompts.py` | D | Docstring only. Prompts live in `rag_agent.py` (TD-03) |
| `services/ocr_service.py`, `services/parallel_runner.py` | D | Docstring only (TD-03) |
| `storage/` | B | Session and deletion are implemented. Timeout is measured from `created_at` (TD-10). No tests |
| `app/` | C | The full path is usable. No UI tests. OCR forced off (TD-04) |
| `docs/` | C | Written against the code on this date. No automatic freshness check (TD-14) |
| Delivery | C | `Dockerfile` for Hugging Face Spaces (port 8501, `uv sync --no-group dev`). No CI workflow (TD-06) |

LangGraph is a dependency and has no imports (TD-13). It does not get a module grade until a change uses it or removes it.
