# Supabase vector index

Closed 2026-09-27. Chunk text in `public.chunks` is accepted for this test account.

## Why

The search index is an in-memory Chroma client. It dies with the process, and every caller (`pipeline/embedder.py`, `pipeline/vector_store.py`, `storage/cleanup.py`, the tests, and the notebooks that embed) talks to that client. The store decision in [`../../design-docs/supabase.md`](../../design-docs/supabase.md) is one Supabase project, with embeddings in `pgvector`. This change replaces Chroma everywhere that client is used.

## What this will not do

- It does not add a Streamlit login, a React client, or a Supabase user per browser session. The server signs in as the existing admin test user. UI sessions stay isolated by `session_id` on every read and write. Row level security limits rows to that signed-in user.
- It does not move PDF bytes out of the per-session temporary directory, and it does not store schemas or answers in Postgres.
- It does not put the service role key in `.env` or in `.env.example`.
- It does not change prompts, `QuestionType`, citation rules, or answer criteria.
- It does not keep chunk text after the session timeout. A process exit no longer drops the index by itself. The next UI load deletes rows that are past the timeout.

Chunk text leaves the process and sits in Supabase until that cleanup. That is a privacy change. This file stays in `docs/plans/` until a human confirms that is acceptable.

## Product spec

[`../../product-specs/session.md`](../../product-specs/session.md) changes.

### Requirement: Process exit

The system MUST keep the search index in Supabase when the process exits. Uploaded PDFs MUST still be removed when the process exits. On each UI load the system MUST delete index rows that this process no longer tracks once they are older than the configured timeout, measured from when each row was first stored. A session this process still tracks MUST still be deleted from its creation time, as the session-lifetime requirement says.

#### Scenario: Restart within the timeout

- **WHEN** the process restarts and the UI loads before the timeout measured from when the rows were stored
- **THEN** those index rows are still stored
- **AND** the previous PDFs are not on disk

#### Scenario: Restart after the timeout

- **WHEN** the process restarts and the UI loads after that timeout
- **THEN** those index rows are deleted

### Requirement: No case text in the repository

The application MUST NOT write uploaded PDFs, chunk text, or API keys into the git repository. Chunk text and embeddings for a session MUST be stored in Supabase under that session id.

#### Scenario: Normal run

- **WHEN** the user uploads a PDF and runs the pipeline
- **THEN** the PDF stays in a temporary directory for that session
- **AND** the chunk text and embeddings are stored in Supabase under that session id
- **AND** the application does not add the PDF or an API key to the repository

## Modules

| Path | Change |
|---|---|
| `supabase/schema.sql` | `chunks` table, `pgvector`, owner policy, `match_session_chunks`. Applied once in the SQL editor. |
| `pipeline/index_store.py` | Memory store for tests. Supabase store for the app and the notebooks. |
| `pipeline/embedder.py` | Write and delete through the store. Drop `chromadb` and `get_collection`. |
| `pipeline/vector_store.py` | Search and `list_sources` through the store. Same result dict. |
| `storage/cleanup.py` | Delete the session index, then sweep rows older than the timeout. |
| `config/settings.py` | Read the existing Supabase admin settings. Do not require them at import. |
| `pyproject.toml` | Remove `chromadb`. Move `supabase` into the main dependencies so the image can sign in. |
| `tests/` | Force the memory store. Cover isolation, replacement, source filter, and the timeout sweep. |
| `app/main.py` | Stop silencing `chromadb`. Silence the Supabase client loggers. |

`delete_collection`, `delete_source`, `embed_document`, `search`, and `list_sources` keep their names so the notebooks and the orchestrator do not grow a second API. `get_collection` goes away.

Distance stays cosine distance: lower is closer. The citation score in `pipeline/rag_agent.py` is still `1 - distance`.

## Tests

| Scenario | Test |
|---|---|
| Re-embedding a shorter PDF drops the old chunk ids | `tests/test_embedder.py` |
| Two sessions do not see each other's chunks | `tests/test_embedder.py` |
| Search returns only the requested session and PDF | `tests/test_vector_store.py` |
| A second run drops a PDF that is no longer uploaded | `tests/test_orchestrator.py` |
| Rows older than the timeout are deleted on cleanup; fresher rows stay | `tests/test_index_store.py` |
| Headings come back as a list of strings | `tests/test_vector_store.py` |

Pytest does not sign in and does not write to the project. The HTTP client is not covered here.

## Order

1. Record this plan.
2. Add `supabase/schema.sql` and the store. Keep a memory backend for tests.
3. Point the embedder, the vector store, and cleanup at that store. Remove `chromadb`.
4. Update the session spec, the architecture note, and the security note in the same change.
5. Run `uv run pytest` and `uv run ruff check` on the files touched.
6. The maintainer runs `supabase/schema.sql` once in the Supabase SQL editor before the app or an embedding notebook can write.

## Debt

TD-12 stays. `storage/cleanup.py` still calls `pipeline.embedder.delete_collection`. This change does not add another `storage/` import of `pipeline/`.

## Close

Closed. Chunk text in `public.chunks` is accepted for this test account. The session spec matches the running app.
