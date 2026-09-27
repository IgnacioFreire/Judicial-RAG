# Architecture

Map of judicial-rag as of 2026-09-27. This is the code that exists, not a target architecture. Drift is listed in [`tech-debt-tracker.md`](tech-debt-tracker.md). Observable behavior is in [`product-specs/`](product-specs/index.md).

## What the process does

```
PDF on disk (session)
        │
        ▼
pipeline/extractor.py     parser tier and chunk tier → models.document.DocumentResult
        │
        ▼
pipeline/embedder.py      Hugging Face Inference → that session's Supabase index
        │
        ▼
pipeline/vector_store.py  retrieval tier, filtered by PDF filename
        │
        ▼
pipeline/rag_agent.py     prompt by QuestionType → services/llm_client.py
        │
        ▼
models.query.DocumentAnswers
        │
        ▼
app/                      FastAPI + React (`web/`)
```

`pipeline/orchestrator.py` is the only coordinator. Phase 1 extracts and embeds every PDF in the current upload together, and drops indexed filenames that are no longer in that upload. Phase 2 asks questions one after another, only for PDFs indexed in that run. What happens when a PDF or a question fails is specified in [`product-specs/variable-extraction.md`](product-specs/variable-extraction.md).

## Packages

| Package | Responsibility | Does not |
|---|---|---|
| `models/` | Pydantic contracts for documents and for questions and answers | I/O, network, the UI |
| `config/` | Settings from the environment (`settings.py`) and the tier maps (`parsers.py`, `chunkers.py`, `embeddings.py`) | Call the LLM or read PDFs |
| `services/` | `llm_client.py` routes Anthropic, OpenAI, DeepSeek, and Gemini | Choose chunks or the question type |
| `pipeline/` | Extract, index, search, and answer | Render UI or own the temp directory |
| `storage/` | Per-session temp directory and expiry | Interpret PDF content |
| `app/` | HTTP session, upload, schema, progress, results | Reimplement the pipeline |

`app/main.py` exports the FastAPI app. Internal imports are absolute (`from pipeline...`, `from models...`). The package is installed by `uv sync`, so the process does not insert the repo root on `sys.path`. `web/` is the React screen and talks only to `/api`.

## Dependency direction

Inward. A package does not import the layer above it.

```
models ───────────── (no imports from this repo)
config ───────────── (no imports from this repo)
services ─────────── config
pipeline ─────────── models, config, services
storage ──────────── config, pipeline.embedder
app ──────────────── models, pipeline, storage, config
tests ────────────── any package; production does not import tests
```

A change keeps these edges:

- `models/` and `config/` do not import the rest of the repo.
- `pipeline/` does not import `app/` or `storage/`.
- `app/` does not open the search index or call Docling. It asks `pipeline.orchestrator.run`.
- The project is installed into the environment, so `app/main.py` does not rewrite `sys.path`.
- The only `storage/` edge into the pipeline is `cleanup.py` → `pipeline.embedder.delete_collection`. That exception is known. Do not add more `pipeline/` imports from `storage/`.

Cross-cutting concerns enter at one place:

| Concern | Where it enters |
|---|---|
| LLM provider and model, parallelism, timeout | `config/settings.py`, read by whoever needs it |
| Model call | `services/llm_client.call_llm` |
| Data isolation | `session_id` on every index read and write, and as the temp-directory prefix |
| Progress toward the UI | `OnProgress` callback the orchestrator invokes and `app/main.py` implements |

## Boundary contracts

Data that crosses packages is a model in `models/`, not an ad hoc dict.

| Boundary | Type |
|---|---|
| Extractor → embedder | `DocumentResult` |
| UI → orchestrator | `list[Path]`, `QuestionSchema`, `session_id`, parser tier, chunk tier, retrieval tier |
| Orchestrator → UI | `list[DocumentAnswers]`, `ProgressEvent` |
| Agent → UI | `AgentAnswer` (`answer`, `citation`, `confidence`, `answer_source`) |

The exception is a search hit: `pipeline/vector_store.search` returns `list[dict]`. Do not extend that dict into other packages. If a new field has to leave the pipeline, add it to a model in `models/`.

## State that is not in the repo

The decided store for users, sessions, PDF bytes, and the vector index is one Supabase project ([`design-docs/supabase.md`](design-docs/supabase.md)). The search index is that project's `chunks` table (`pgvector`), described in [`../supabase/schema.sql`](../supabase/schema.sql). The HTTP server signs in as the admin test user and scopes every read and write by `session_id`. PDF bytes still live in a `tempfile.TemporaryDirectory` per session (`storage/session_manager.py`) until that process exits or the session is cleaned up. Notebooks `01_pdfs.ipynb`, `02_extraction.ipynb`, and `03_embedding.ipynb` read the private `pdfs` bucket as the admin test user. Notebooks that embed write the same `chunks` table.

## UI

One React screen (`web/src/App.tsx`) served by FastAPI (`app/server.py`). Sidebar: upload and the question editor. Body: run, reset, results. Server fields live in `app/ui_state.py`. Editor drafts live in `QuestionForm` until save. Detail is in [`FRONTEND.md`](FRONTEND.md).
