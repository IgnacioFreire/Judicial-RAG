# React UI with shadcn/ui

Closed 2026-09-27. Streamlit is gone. FastAPI serves `web/dist`.

Replace the Streamlit page with a React screen that uses [shadcn/ui](https://ui.shadcn.com/). Keep the same layout, copy, and product behavior. The pipeline, models, storage, and Supabase index stay as they are.

**Stop.** Do not install packages or edit `app/` until a person confirms this plan (`go ahead`, `approved`, or `yes`). New libraries (FastAPI, React, Vite, Tailwind, shadcn) also need that confirmation: [`core-beliefs.md`](../../design-docs/core-beliefs.md) forbids adding a dependency without a named design and a human yes.

## Why

Streamlit owns the only screen (`app/main.py` plus four components). Every click reruns the script. The product already has a stable contract: upload PDFs, save a schema, choose three session tiers, run, stream progress, show answers. That contract should stay. The UI library should not.

React plus shadcn lets the same regions (sidebar vs body, expanders, badges, disabled-while-running) be real components instead of Streamlit widgets, without inventing a second page or new extraction rules.

## What this will not do

- It will not change prompts, `QuestionType`, citation pages, answer criteria, parser/chunk/retrieval maps, or isolation by `session_id`.
- It will not add user login, a schema library, a second route, or a public PDF store. [`SECURITY.md`](../../SECURITY.md) still has no end-user authentication; the HTTP API is the same trust model as port 8501 today.
- It will not let the browser talk to Docling, the index, or `call_llm`. The browser talks only to the process that already calls `pipeline.orchestrator.run`.
- It will not persist the question schema to disk (still session memory only).
- It will not rewrite notebooks. They stay Python.
- It will not run Streamlit and React in production together. Streamlit is removed when the React screen covers the same scenarios.

## Product spec

No new spec file. Existing requirements stay; wording that names Streamlit or “script rerun” is updated in the same change as the code.

| Spec | New requirement text |
|---|---|
| [`../product-specs/session.md`](../../product-specs/session.md) | Isolation and the 60-minute creation clock stay. “Next UI load” means the next `GET` that bootstraps the session (page open or refresh), which MUST run `cleanup_expired_sessions` before serving state. Preferences (parser, chunk, retrieval) live on the server session; Reset keeps them. The browser MUST send the session cookie on every request. |
| [`../product-specs/document-upload.md`](../../product-specs/document-upload.md) | Upload remains one or more PDFs, 20 MB per file, replace-by-name, delete files dropped from the current selection. The control is a multi-file picker, not `st.file_uploader`. Ready count and rejection messages stay. |
| [`../product-specs/question-schema.md`](../../product-specs/question-schema.md) | Drafts stay unsaved until **Save schema**. Validation still uses `UserQuestion` / `QuestionSchema`. Drafts MAY live only in the browser until save. The saved schema MUST live on the server session, not in `localStorage`. |
| [`../product-specs/variable-extraction.md`](../../product-specs/variable-extraction.md) | Run enablement, disable-while-running, per-PDF warnings after the run, and result grouping stay. Progress MUST reach the browser as a stream of the existing `ProgressEvent` fields (`stage`, `source`, `message`, `current`, `total`). A hard pipeline exception MUST surface as an error, not as a silent empty result list. |

Copy and layout stay in [`../DESIGN.md`](../../DESIGN.md). That file currently points at `app/components/`; it will point at `web/src/components/` and keep the same English strings.

## Current Streamlit map (source of truth for the React tree)

One wide screen. No router. Sidebar then body, as in [`../DESIGN.md`](../../DESIGN.md).

```
app/main.py
  set_page_config, logging, title, caption
  sidebar: uploader → question_form → advanced_settings
  body: Run / Reset, progress, run_errors, results_viewer
  _run_pipeline → asyncio.run(orchestrator.run(...))

app/session_state.py     server keys listed in FRONTEND.md
app/components/uploader.py
app/components/question_form.py   drafts in st.session_state["question_drafts"]
app/components/advanced_settings.py
app/components/results_viewer.py
```

| Streamlit piece | Behavior to keep | React / shadcn stand-in |
|---|---|---|
| `st.sidebar` + `st.divider` | Left column: upload, questions, advanced | CSS grid / `aside`. `Separator` |
| Title + caption | `⚖️ Judicial RAG` and the DESIGN caption | page header, not a route |
| `uploader.render` | `st.file_uploader` multiple PDF, 20 MB, `store_uploads`, disabled while processing | `Input` `type="file"` + list. `Alert` for reject / ready / empty |
| `question_form.render` | Expandable drafts, four types, category rows, Add / Save / Remove, Pydantic errors | `Accordion` or `Collapsible` per draft. `Input`, `Textarea`, `Select`, `Button` |
| `advanced_settings.render` | Expander, three `selectbox`es, `format_func` labels from DESIGN | `Collapsible` titled Advanced settings. Three `Select`s |
| Run / Reset columns | Primary run, reset, `can_run`, tooltips | `Button` variants. `Tooltip` for “Upload PDFs and save a schema first.” |
| `st.progress` + `st.empty` | Bar when `total > 0`, else status text | `Progress` + muted status line |
| `st.warning` / `st.error` / `st.success` | Batch failures after rerun; pipeline exception | `Alert` |
| `results_viewer` | One expander per PDF, badge colors, not-found caption, provenance, bordered citation | `Accordion` + `Badge` + `Card` for citation |
| Disable while `is_processing` | Upload, schema, run, reset | `disabled` on the same controls |

Confidence colors (DESIGN): high green, medium orange, low red, `not_found` gray. Provenance strings: `Extracted directly` / `Inferred through reasoning`. Missing answer: `No answer found.`

Type labels in `question_form.py` (`_TYPE_OPTIONS`) are product copy. Move them with the form; do not invent new type names.

## Session and HTTP (why Streamlit cannot just be swapped)

Today the process **is** the UI. `st.session_state` holds `session_id`, schema, results, processing flag, upload widget objects, run errors, and three tiers. `init()` mints a UUID once and calls `get_or_create_session`. `cleanup_expired_sessions()` runs on every rerun. Run uses `asyncio.run` because the script is sync.

A browser cannot import `pipeline/`. The replacement is:

1. **HTTP API in the same Python process** that already owns temp dirs and the orchestrator. Package name stays `app/` so the inward dependency (`app` → `pipeline`, `storage`, `models`, `config`) does not grow a new layer above the UI.
2. **React in `web/`**, Vite + TypeScript. Production: FastAPI serves `web/dist`. Local: Vite proxies `/api` to the API.
3. **Session cookie** (`HttpOnly`, `SameSite=Lax`). First request without a cookie mints the UUID (same as `session_state.init`). Later requests load that server session. Do not put `session_id` in `localStorage`.
4. **Server session record** (in-process dict, one process, same as Streamlit today): schema, results, is_processing, run_errors, the three tiers, list of accepted filenames (not raw Streamlit `UploadedFile` objects). Drafts stay in React state until save.
5. **One run per session.** Reject a second `POST /api/run` with 409 while `is_processing`.
6. **Progress:** Server-Sent Events on the run request (or `GET /api/run/events` after `POST` starts the task). Serialize `ProgressEvent` without the `Exception` object; send `stage`, `source`, `message`, `current`, `total`. `Stage.ERROR` messages become `run_errors` and stay after the stream ends (same as `set_run_errors` then `st.rerun()`).
7. **Cleanup:** `cleanup_expired_sessions()` on session bootstrap (`GET /api/session`), not on every keystroke.

Port: keep **8501** for the combined server so Spaces/docs that name that port stay true, unless a later deploy plan changes it. Vite remains 5173 in development only.

Logging noise loggers in `main.py` (docling, transformers, …) move to the FastAPI lifespan, same WARNING list.

## Extract logic before deleting Streamlit

These functions already have tests or Pydantic validation. They must not stay behind `import streamlit`.

| Today | After extract |
|---|---|
| `uploader.store_uploads`, `_file_name`, `_MAX_MB` | `storage/uploads.py` (or `app/uploads.py` if storage must not grow). `tests/test_uploads.py` only changes the import. |
| `question_form._build_schema`, `_empty_draft`, `_empty_category` | `app/schema_drafts.py` (pure). Returns `QuestionSchema` or a structured error (`question_index`, message). No `st.error`. |
| Tier labels | Keep reading `PARSER_TIERS`, `CHUNK_TIERS`, `EMBEDDING_TIERS`. Expose options on `GET /api/session` so the UI does not hardcode method names. |

`tests/test_question_form.py` today only checks widget keys. After the move, test `_build_schema` (or its new name) for valid extraction, classification with fewer than two categories, and empty list.

## API sketch (contracts are `models/`)

All JSON bodies that leave the server are Pydantic models. Do not send ad hoc dicts for answers; use `DocumentAnswers` / `AgentAnswer`.

| Method | Path | Role |
|---|---|---|
| `GET` | `/api/session` | Cookie + cleanup. Return tiers, defaults, accepted file names, whether schema is saved, `is_processing`, `run_errors`, results if any, select option labels. |
| `PUT` | `/api/uploads` | Multipart PDFs. Size check then `store_uploads`. Return accepted names and rejected `{name, size}` rows. Empty file list clears the directory (empty-uploader spec). |
| `PUT` | `/api/schema` | Body is the draft list the form would save. Validate; store `QuestionSchema`. |
| `PATCH` | `/api/session/tiers` | `{parser_tier, chunk_tier, embedding_tier}` each `fast`/`medium`/`slow`. |
| `POST` | `/api/run` | 400 if no PDFs or no schema; 409 if processing. SSE of progress; end with results or error. |
| `POST` | `/api/reset` | Same as `state.reset()`: clear results, uploads on disk, errors, processing; keep session id, schema, tiers. |

Do not add webhooks or extra PDF stores.

## React tree (mirrors `app/components/`)

```
web/
  src/
    App.tsx                 main.py layout: header, aside, run row, alerts, results
    lib/api.ts              fetch + EventSource, credentials include
    lib/session.ts          types matching GET /api/session
    components/
      Uploader.tsx
      QuestionForm.tsx
      QuestionEditor.tsx    one draft + categories
      AdvancedSettings.tsx
      RunBar.tsx            Run pipeline / Reset / Progress
      ResultsViewer.tsx
      AnswerCard.tsx
      ui/                   shadcn primitives only
```

shadcn primitives expected: `button`, `input`, `textarea`, `select`, `accordion` or `collapsible`, `separator`, `badge`, `alert`, `progress`, `card`, `tooltip`, `label`, `scroll-area`. Add a component only when a Streamlit widget above needs it.

State: one React context or a small store that mirrors `FRONTEND.md` keys (`schemaSaved`, `results`, `isProcessing`, `acceptedFiles`, `runErrors`, three tiers). Drafts stay local to `QuestionForm` until save, same exception as today.

`can_run`: accepted files length > 0 **and** schema saved **and** not processing.

Reset: `POST /api/reset`, then clear file input and results in the client; keep draft editors and saved schema (spec: schema remains; DESIGN: Reset does not wipe questions).

## Dependencies (confirm before `uv add` / `npm create`)

Python (replace Streamlit): `fastapi`, `uvicorn[standard]`, `python-multipart`. Test client: Starlette/FastAPI `TestClient` (comes with FastAPI).

Frontend: Vite, React 19, TypeScript, Tailwind CSS v4 (or the version shadcn’s CLI pins), shadcn/ui CLI, `class-variance-authority`, `clsx`, `tailwind-merge`, `lucide-react`. Do not add a router, a form library, or a state library unless the form becomes unreadable; the current form is a list of drafts.

CI: Node on GitHub Actions — `npm ci` + `npm run build` + `npm run lint` in `web/`, in addition to `uv run ruff` and `pytest`. Pin a Node version in the workflow.

`pyproject.toml`: drop `streamlit`. `known-first-party` unchanged unless a new Python package appears.

## Tests

| Scenario | Test |
|---|---|
| Replace-by-name, remove from batch, empty batch, path traversal names | Existing `tests/test_uploads.py` after the import move |
| Schema validation without Streamlit | New tests on the extracted builder |
| Cookie mints one session; two clients get two ids | `TestClient` |
| Upload over 20 MB rejected, other file kept | API test with synthetic bytes |
| Run 400 without schema or files; 409 when processing | API test with faked `orchestrator.run` |
| SSE includes ERROR message that remains on later `GET /api/session` | API test |
| Reset keeps tiers and schema, clears results and files | API test |
| GET session options match `PARSER_TIERS` / chunk / embedding maps | API test replacing `tests/test_advanced_settings.py` |
| Orchestrator still isolated | Existing `tests/test_orchestrator.py` unchanged |

Do not paste case text into fixtures. Synthetic PDFs only if an API test needs a path; prefer mocking `run` for HTTP tests.

## Docs and grades (same change as the cutover)

- Rewrite [`../FRONTEND.md`](../../FRONTEND.md): FastAPI routes, cookie, `web/src/components/`, which state is server vs draft.
- [`../ARCHITECTURE.md`](../../ARCHITECTURE.md): diagram `app/` is HTTP; `web/` is the screen. `app` still does not open the index.
- [`../DESIGN.md`](../../DESIGN.md): same layout; file paths under `web/`.
- [`../SECURITY.md`](../../SECURITY.md): surface is the HTTP API + static files; still no end-user login; cookie is the session boundary inside one process.
- [`../RELIABILITY.md`](../../RELIABILITY.md): cleanup on session GET, not Streamlit rerun.
- [`../QUALITY_SCORE.md`](../../QUALITY_SCORE.md): `app/` grade after API tests; add `web/` as B until UI tests exist (none required in v1 beyond build + lint).
- [`../AGENTS.md`](../../../AGENTS.md) and README: `uv run python -m app` instead of Streamlit. Local: also `npm run dev` in `web/`.
- [`../design-docs/index.md`](../../design-docs/index.md) checked date when FRONTEND/ARCHITECTURE are compared to the new tree.

No tech-debt row is paid. If the API is left without tests, add a tracker row in that change rather than claiming A.

## Order

1. Confirm this plan and the dependency list.
2. Move `store_uploads` off Streamlit; keep tests green.
3. Extract schema-from-drafts; add validation tests.
4. Add FastAPI `app` entry: session cookie, GET session, uploads, schema, tiers, reset. Fake `run`. Logging lifespan. Keep Streamlit `main.py` working until step 7 so the product still has a UI.
5. Scaffold `web/` with Vite + Tailwind + shadcn. Proxy `/api`.
6. Port components in this order (each one is usable against the API): `Uploader` → `AdvancedSettings` → `QuestionForm` → `RunBar` (SSE) → `ResultsViewer`. Match DESIGN copy.
7. Serve `web/dist` from FastAPI. Switch the documented start command. Delete Streamlit files (`app/components/*.py` widgets, `session_state.py` Streamlit keys, `tests/test_advanced_settings.py` AppTest).
8. Update product specs, FRONTEND, ARCHITECTURE, DESIGN, SECURITY, RELIABILITY, QUALITY_SCORE, AGENTS, README, CI.
9. `uv run ruff check`, `uv run pytest`, `web` lint and production build.

## Close

When the Streamlit entry is gone and the specs match the API + React screen, move this file to `completed/`. That cutover does not change answer criteria or `models/`; a second human yes at close is not required for those gates. A yes is still required before step 2 (implementation).
