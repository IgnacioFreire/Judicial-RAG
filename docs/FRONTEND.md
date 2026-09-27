# Frontend

React (Vite) on one screen. FastAPI in `app/` is the only process that calls `pipeline.orchestrator.run`. There is no router.

| File | Role |
|---|---|
| `app/server.py` | Cookie session, `/api/*`, static `web/dist` |
| `app/ui_state.py` | Server fields that Streamlit kept in `st.session_state` |
| `app/schema_drafts.py` | Save-schema validation |
| `storage/uploads.py` | 20 MB rule and `store_uploads` |
| `web/src/App.tsx` | Title, sidebar, run row, alerts, results |
| `web/src/components/Uploader.tsx` | Multi-file PDF picker |
| `web/src/components/QuestionForm.tsx` | Drafts and **Save schema** |
| `web/src/components/QuestionEditor.tsx` | One draft and category rows |
| `web/src/components/AdvancedSettings.tsx` | Parser, chunk, and retrieval tiers |
| `web/src/components/RunBar.tsx` | Run, Reset, progress |
| `web/src/components/ResultsViewer.tsx` | One expander per PDF |

## State

Server (cookie `jr_session`, HttpOnly, SameSite=Lax), in `app/ui_state.py`:

| Field | Type | Initial |
|---|---|---|
| `schema` | `QuestionSchema \| None` | `None` |
| `results` | `list[DocumentAnswers] \| None` | `None` |
| `is_processing` | `bool` | `False` |
| `run_errors` | `list[str]` | `[]` |
| `pipeline_error` | `str \| None` | `None` |
| `parser_tier` | `str` | `medium` |
| `chunk_tier` | `str` | `medium` |
| `embedding_tier` | `str` | `fast` |

`session_id` is the cookie. Accepted PDFs live in `storage` `Session.pdf_dir`. `GET /api/session` runs `cleanup_expired_sessions` then returns the view.

Drafts live only in `QuestionForm` until **Save schema**. They are not written to `localStorage`.

## HTTP

| Method | Path |
|---|---|
| `GET` | `/api/session` |
| `PUT` | `/api/uploads` |
| `PUT` | `/api/schema` |
| `PATCH` | `/api/session/tiers` |
| `POST` | `/api/run` (SSE: `stage`, `source`, `message`, `current`, `total`) |
| `POST` | `/api/reset` |

A second run while `is_processing` is 409. Run without PDFs or a saved schema is 400.

## Startup

`uv run python -m app` serves the API on port 8501. If `web/dist` exists, that process also serves the UI. Local UI iteration: `npm run dev` in `web/` (proxies `/api` to 8501).

Root logging is INFO. `docling`, `transformers`, `huggingface_hub`, `rapidocr`, `httpx`, `supabase`, `postgrest`, and `gotrue` stay at WARNING.

## What not to add here

- Direct calls to Docling, the search index, or `call_llm` from `web/`.
- A second page to manage schemas, without a spec.
- Result state computed in the component instead of reading `DocumentAnswers`.
