# Frontend

React (Vite) with four routes. FastAPI in `app/` is the only process that calls `pipeline.orchestrator.run`.

| Path | Page |
|---|---|
| `/` | Overview: summary cards, run, reset, recent PDFs |
| `/documents` | Upload and the document table |
| `/documents/:name` | One PDF: status, times, answers when the run finished it |
| `/settings` | Question editor, save schema, three tiers, read-only type list |

`web/src/components/AppShell.tsx` is the sidebar and header. `ProfileMenu` holds profile, theme, locale, keys, and sign out. `web/src/i18n/` holds English and Spanish copy. Pages live in `web/src/pages/`.

| File | Role |
|---|---|
| `app/server.py` | Cookie session, `/api/*`, static `web/dist` |
| `app/ui_state.py` | Schema, results, tiers, and one row per accepted PDF |
| `services/llm_usage.py` | Generation token totals for the bound session |
| `web/src/pages/Overview.tsx` | Summary and run |
| `web/src/pages/Documents.tsx` | Upload and table |
| `web/src/pages/DocumentDetail.tsx` | One PDF |
| `web/src/pages/Settings.tsx` | Questions and tiers |

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
| `GET` | `/api/documents` |
| `GET` | `/api/documents/{name}` |
| `GET` | `/api/profile` |
| `GET` | `/api/profile/keys` |
| `PUT` | `/api/profile/keys` |
| `POST` | `/api/sign-out` |
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
