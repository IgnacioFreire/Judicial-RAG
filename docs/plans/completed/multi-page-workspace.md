# Multi-page workspace

Closed 2026-09-27. Overview, documents, document detail, settings, and a read-only profile popover.

**Stop.** Do not add `react-router`, edit routes, or return secrets until a person confirms this plan. Showing or editing API keys, and letting the user rewrite the shared prompt templates, are not part of this plan. Those change privacy and answer criteria and need their own yes.

## Why

The screen is one column of forms plus results. A person cannot see, at a glance, which PDFs are running, which failed, and which answers belong to which file, without scrolling the same page that also holds the schema editor.

The shell already looks like a dashboard (dark sidebar, metric cards). The sidebar should navigate. The forms should live on the page that owns them.

## What this will not do

- It will not add end-user login, a user row, or a password field. [`../../design-docs/supabase.md`](../../design-docs/supabase.md) still has one admin test user. Replacing session isolation with accounts is a later plan.
- It will not persist runs, schemas, or answers past the current process and the session timeout. Reset and timeout still drop uploads and results, as [`../../product-specs/session.md`](../../product-specs/session.md) and [`../../product-specs/question-schema.md`](../../product-specs/question-schema.md) say. The table is a view of that session, not an archive.
- It will not write PDFs, chunk text, or answers to a new store.
- It will not send API keys, the Supabase anon key, or the admin password to the browser. The popover shows that a key is configured, not the key.
- It will not let the UI edit `.env` or provider keys.
- It will not let the UI rewrite the instructions in `pipeline/rag_agent.py`. The editable text stays the question, the output format, and the notes. Changing those shared instructions changes what counts as an answer and waits for a separate yes.
- It will not add charts of income, a second product, or a theme switcher.

## Pages

One React tree. `react-router` (to be confirmed) maps paths. FastAPI already serves `index.html` for unknown paths when `web/dist` exists, so client routes work after a refresh.

| Path | Name | What is on it |
|---|---|---|
| `/` | Overview | Caption, four metric cards (documents, schema, questions, answered), last run status, short list of the latest PDFs linking to detail, Run and Reset |
| `/documents` | Documents | Upload control. Table of every PDF accepted in this session |
| `/documents/:name` | Document | One PDF: status, times, and the answer rows for that file only. Unknown name: empty state, not another session's file |
| `/settings` | Settings | Question drafts, Save schema, parser / chunk / retrieval. A read-only list of the four question types and the fact that each type uses the instruction in `pipeline/rag_agent.py` |

The dark sidebar is navigation: Overview, Documents, Settings. It is not the form. The profile control sits in the top bar on every page and opens a popover, not a route.

Copy that already exists in [`../../DESIGN.md`](../../DESIGN.md) stays: `Run pipeline`, `Reset`, `Add question`, `Save schema`, `Advanced settings`, tier labels, `No answer found.`, provenance strings, confidence colors.

## Document row

A row is one accepted filename in the current session. Status comes from the run, not from a new pipeline stage enum.

| Status | When |
|---|---|
| `queued` | Accepted, and a run has started that includes this file, before its extract event |
| `extracting` | Latest progress for this file is `extracting` |
| `embedding` | Latest progress for this file is `embedding` |
| `answering` | Latest progress for this file is `answering` |
| `done` | The file is in `results` after the run |
| `failed` | The file produced a `Stage.ERROR` message (not indexed). It does not appear as an answered document |
| `ready` | Accepted, no run has included it yet |

Times, stored on the server session when the event happens:

- `accepted_at` — upload accepted
- `started_at` — first progress event for that file in the current run
- `finished_at` — file reaches `done` or `failed`

The table shows name, status, accepted time, finished time, and a link to `/documents/:name`. Removing a file from the picker deletes it from disk (existing upload rule) and drops its row.

Detail reads `DocumentAnswers` for that filename. It does not recompute answers. A `failed` or `ready` file has no answer list; the page says so.

## Profile popover

Read-only.

| Field | Source | Shown as |
|---|---|---|
| Email | `SUPABASE_ADMIN_EMAIL` | The address, labeled as the Supabase account this process uses |
| LLM | `llm_provider`, `llm_model` | Names only |
| Active LLM key | Whether the active provider's key is non-empty | `Configured` or `Missing`. Never the secret |
| Embeddings | `embedding_provider`, `embedding_model` | Names only |
| Hugging Face key | Whether `HUGGINGFACE_API_KEY` is non-empty | `Configured` or `Missing` |
| Tokens | Sum of input and output tokens reported by `call_llm` during this session | Two integers. Zero before the first model call |

`call_llm` today returns only text and logs usage. This plan adds an in-process counter keyed by `session_id` (a `contextvar` set for the duration of `run`). Counts die with the session. They are not a bill and not a quota. Hugging Face embedding calls are not in that sum; the popover says the figures are generation tokens only.

## Product spec

New file [`../../product-specs/workspace.md`](../../product-specs/workspace.md). Do not copy upload, schema, or answer rules into it.

Requirement text to land with the code:

- The UI has four routes: overview, document list, document detail, settings. Settings holds the question editor and the three tiers. Overview is a summary and the run controls.
- The document list shows each accepted PDF of the current session with status `ready`, `queued`, `extracting`, `embedding`, `answering`, `done`, or `failed`, plus accepted and finished times when those events have happened.
- Opening a `done` document shows that document's `DocumentAnswers` only.
- Reset clears the list, the times, and the token counts, and still keeps the schema and the three tiers.
- The profile popover shows the admin email, provider and model names, whether the active keys are set, and this session's generation token totals. It does not show key material.
- A new session does not restore another session's rows, answers, or token totals.

[`../../product-specs/variable-extraction.md`](../../product-specs/variable-extraction.md) keeps run enablement, progress fields, and per-PDF warnings. The warnings remain visible on Overview and on the document row.

[`../../DESIGN.md`](../../DESIGN.md) gains the route map and the profile fields. [`../../FRONTEND.md`](../../FRONTEND.md) lists the routes and the new API.

## API

Same cookie. New reads; existing writes stay.

| Method | Path | Role |
|---|---|---|
| `GET` | `/api/documents` | Rows: name, status, `accepted_at`, `started_at`, `finished_at` |
| `GET` | `/api/documents/{name}` | One row plus `DocumentAnswers` or null |
| `GET` | `/api/profile` | Email, provider, model, key flags, token totals |

`POST /api/run` still streams `ProgressEvent`. The server updates the row status as each event arrives so a refresh during a run shows the latest status. `GET /api/session` keeps returning the summary fields the overview cards need.

`name` in the path is the stored filename, URL-encoded. Reject `..` and any name not in this session with 404.

## Modules

| Path | Change |
|---|---|
| `web/` | `react-router`. `AppShell` with nav and profile popover. Pages `Overview`, `Documents`, `DocumentDetail`, `Settings`. Move `Uploader` to Documents, `QuestionForm` and `AdvancedSettings` to Settings, `RunBar` to Overview |
| `app/ui_state.py` | Per-file status and times. Token totals |
| `app/server.py` | The three GETs. Update rows from the run callback |
| `services/llm_client.py` | After each successful call, add that response's input and output counts to the current session counter. Still return only the text. Do not log keys |
| `docs/product-specs/workspace.md` | New spec |
| `docs/DESIGN.md`, `docs/FRONTEND.md`, `docs/ARCHITECTURE.md`, `docs/SECURITY.md` | Routes, profile surface, "keys are not returned" |

`pipeline/orchestrator.py` stays the coordinator. The UI still does not call Docling or the index.

## Dependency

`react-router` in `web/`. No other library. Confirm before `npm install`.

## Tests

- `GET /api/documents` is empty before upload, then lists an accepted file as `ready`.
- A faked run that emits `ERROR` for one file and returns `DocumentAnswers` for another leaves `failed` and `done` with `finished_at` set.
- `GET /api/documents/{name}` for another session's name is 404.
- `GET /api/profile` includes the provider name and `llm_key_configured: true/false` and does not include a string equal to a test key.
- Reset clears document rows and token totals and keeps the schema and tiers.
- Existing `tests/test_api.py` upload and schema cases still pass.

Do not put a real key or case text in a fixture.

## Order

1. Confirm this plan and `react-router`.
2. Add document rows and token counter on the server. Tests above, UI still one page.
3. Add the three GET routes.
4. Split the React tree into the four routes and the popover. Rebuild `web/dist`.
5. Update `workspace.md`, DESIGN, FRONTEND, ARCHITECTURE, SECURITY, QUALITY_SCORE (`web/` stays B).
6. `uv run ruff check`, `uv run pytest`, `npm run lint`, `npm run build` in `web/`.

## Close

Move this file to `completed/` when the four routes and the popover match `workspace.md`. A further yes is required before any later plan that stores history in Postgres, edits API keys from the browser, or edits the shared prompt text.
