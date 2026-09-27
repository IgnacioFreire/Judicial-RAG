# Manual notebooks

## Why

The pipeline can be run only through Streamlit. There is no way to stop after extraction, retrieval, or one agent call and read the counts, the timings, and the mapped rows. These notebooks are a local harness for that. Each one exercises one process and prints how long it took and what it produced.

## What this will not do

- It does not change extraction, retrieval, prompts, `QuestionType`, citation pages, or answer criteria.
- It does not score legal correctness. A date format, a category, or a rounding rule stays in the operator's question, not in the notebook.
- It does not persist Chroma, write case text to disk, or add an API.
- It does not import Streamlit. Size checks repeat the 20 MB limit from [`../product-specs/document-upload.md`](../product-specs/document-upload.md) instead of importing `app/`.
- It does not commit PDFs, notebook outputs, or a saved run that contains answers or citations.
- It does not pay down a row in [`../tech-debt-tracker.md`](../tech-debt-tracker.md).

## Product spec

No file under `docs/product-specs/` changes. The notebooks call the public functions that already implement those requirements. They are not a behavior a person sees in the app.

## Dependency

Add `jupyter` and `supabase` to the `dev` group in `pyproject.toml`. Do not add pandas. Tables are plain text built in `notebooks/helpers.py`. The Supabase client is used by `notebooks/01_pdfs.ipynb` only.

Launch with:

```bash
uv sync --group dev
uv run jupyter lab notebooks
```

`.env` must already exist. The extraction notebook downloads Docling models on first use. Embedding and the agent call Hugging Face and the configured LLM. Those calls cost time and quota. The PDF notebook does not.

## Privacy

Notebooks may show chunk text, answers, and citations on the operator's machine. That display is off unless the operator sets `SHOW_TEXT = True` in that notebook.

`notebooks/01_pdfs.ipynb` signs in to Supabase as the admin test user and reads the private `pdfs` bucket. Credentials stay in `.env`. The notebook prints names, sizes, and byte counts. It does not print PDF text and it does not write the files into the repo.

Committed notebooks have empty outputs and a null execution count. `.gitignore` ignores `.ipynb_checkpoints/` and everything under `notebooks/inputs/` except `.gitkeep`. PDFs stay out of git. Do not paste a ruling into a notebook cell, a fixture, or this plan.

KPI rows store counts, filenames, durations, confidence, and answer source. They do not store answer text or citation text.

## Kernel

Chroma is in memory and dies with the kernel. Notebooks do not share an index. Each notebook that needs an earlier stage runs that stage itself in a setup section. Setup time is printed apart from the stage under test.

Each notebook creates its own collection name, `nb-` plus a UUID, and deletes that collection in the last cell. It never uses another session's collection.

## Shared file

`notebooks/helpers.py` is one small module imported by the notebooks. There is no `support.py` and no notebook test module.

| Function | Does |
|---|---|
| `accepted_pdfs(directory)` | Lists `*.pdf` at or under 20 MB. Returns accepted paths and a rejection reason per other file (not a PDF, over 20 MB, empty name). Skips `.gitkeep`. |
| `classify_uploads(files)` | Same 20 MB rule for objects already listed from Supabase: name and size in bytes. |
| `new_session_id()` | Returns `nb-<uuid>`. |
| `timed(name)` | Context manager. Records the name and `time.perf_counter` duration in seconds. |
| `preview(text, enabled)` | Returns a character count when `enabled` is false and the text when it is true. |
| `result_rows(results)` | One dict per answer: document, label, question type, confidence, answer source, citation page, citation score, citation source, citation character count. Omits answer text and citation text. |
| `answered_counts(results)` | Per document, the count of answers whose confidence is not `not_found`, and the total. Same rule as `app/components/results_viewer.py`. |
| `phase_durations(events)` | From progress events stamped by the KPI notebook: phase 1 is the first `extracting` event until the first `answering` event; phase 2 is the first `answering` event until `complete`. Per question, the gap from that question's `answering` event to the next event. Phase 1 PDFs run concurrently, so this is wall time, not a sum of per-PDF times. |
| `kpi_summary(results, failures, durations)` | Counts: PDFs indexed, PDFs failed, questions, answers, confidence histogram, direct, inferred, rows with a citation, not-found rate. Plus the durations above. |

`SHOW_TEXT` lives in the notebook. The operator opts in per notebook.

## Notebooks

Notebooks `02` through `07` still read local files from `NOTEBOOK_PDF_DIR`, or from `notebooks/inputs/` when that variable is unset. The operator puts local PDFs there. The question cell is a template: one `UserQuestion` of type `extraction` with a generic label and instruction. The operator replaces it before running retrieval, the agent, results, or KPIs. The template is not a legal rule.

### `notebooks/01_pdfs.ipynb`

Process: sign in as the admin test user and read PDFs from the private Supabase bucket.

Cells:

1. Load `.env`, sign in, list the bucket, and call `classify_uploads`.
2. Print each object's name, size in MB, and accepted or rejected.
3. Print the accepted count, the rejected count, and the duration of the listing.
4. Download each accepted object into memory and print its name and byte count.

No Docling. The bytes are discarded after the count. Later notebooks do not see this bucket yet.

### `notebooks/02_extraction.ipynb`

Process: `pipeline.extractor.extract` on each accepted PDF.

Cells:

1. Setup: `accepted_pdfs`. Time this separately.
2. For each path, `await extract(path)` inside `timed("extract")`.
3. Print filename, `total_pages`, `total_chunks`, heading count, and min, median, and max characters per chunk.
4. Optional: with `SHOW_TEXT`, print one chunk's page, headings, and text.

A PDF that raises is printed as a failure with the exception type and message, and the loop continues. A PDF with zero chunks is printed as a failure, matching the orchestrator's "produced no text" rule. This notebook does not embed.

### `notebooks/03_embedding.ipynb`

Process: `pipeline.embedder.embed_document`.

Cells:

1. Setup: extract each accepted PDF. Time as setup.
2. `new_session_id()`, then `await embed_document(document, session_id)` per successful `DocumentResult`, each inside `timed("embed")`.
3. Print filename, chunk count, `list_sources(session_id)`, and the embed duration.
4. Last cell: `delete_collection(session_id)`.

### `notebooks/04_retrieval.ipynb`

Process: `pipeline.vector_store.search` for one question string and one source file.

Cells:

1. Setup: extract and embed. Time as setup.
2. Operator sets `question` and `n_results` (default 5, the store default).
3. `search(...)` inside `timed("search")`.
4. Print one row per hit: rank, page, headings, distance, character count. With `SHOW_TEXT`, also the chunk text.
5. Last cell: `delete_collection(session_id)`.

### `notebooks/05_agent.ipynb`

Process: `pipeline.rag_agent.answer_question` for one `UserQuestion` and one source file.

Cells:

1. Setup: extract and embed. Time as setup.
2. Operator edits the `UserQuestion` template.
3. `answer_question(...)` inside `timed("answer")`.
4. Print label, question type, confidence, answer source, citation page, citation score, citation character count, and duration. With `SHOW_TEXT`, also the answer and the citation text.
5. Last cell: `delete_collection(session_id)`.

### `notebooks/06_results.ipynb`

Process: map `list[DocumentAnswers]` to the same columns the UI shows, without rendering Streamlit.

Cells:

1. A first section builds a synthetic `DocumentAnswers` in memory (no PDF, no API) and prints `result_rows` and `answered_counts`. This is the mapping the operator can re-run without quota.
2. Setup for a real file: extract, embed, then `answer_question` for every question in the operator's schema. Time setup apart from mapping.
3. Build `DocumentAnswers` and print `result_rows` and `answered_counts`. Duration of the mapping call is printed on its own.
4. Last cell: `delete_collection(session_id)`.

### `notebooks/07_kpis.ipynb`

Process: one full `pipeline.orchestrator.run`, then operational KPIs.

Cells:

1. Operator edits the schema template. Paths come from `accepted_pdfs`.
2. `new_session_id()`. Callback appends each `ProgressEvent` with a `time.perf_counter` stamp. `await run(...)` inside `timed("run")`.
3. Print `phase_durations`, `kpi_summary`, and `answered_counts`. Failures are the `error` events from the callback.
4. Print `result_rows` so the operator can read the mapped table next to the KPIs. Text stays out unless `SHOW_TEXT` is set, and even then it is printed from the live objects, not written to `notebooks/`.
5. Last cell: `delete_collection(session_id)`.

## Modules

| Path | Change |
|---|---|
| `notebooks/helpers.py` | New. One small module for timing, PDF listing, result rows, and KPI summary. |
| `notebooks/01_pdfs.ipynb` through `notebooks/07_kpis.ipynb` | New. One process each. Empty outputs. |
| `notebooks/README.md` | How to point at a local PDF directory, what each notebook calls, kernel lifetime, and the rule against committing outputs. |
| `notebooks/inputs/.gitkeep` | Empty input directory. |
| `pyproject.toml` | `jupyter` in the dev group. |
| `.gitignore` | Checkpoints and `notebooks/inputs/*` except `.gitkeep`. |
| `README.md` | One line under the existing commands pointing at `notebooks/README.md`. |

`pipeline/`, `models/`, `app/`, `services/`, and `tests/` stay untouched. No `notebooks/support.py`.

## Tests

No new tests. The notebooks are a local harness, and this change does not add a test module for them or for `notebooks/helpers.py`.

## Order

1. Add the gitignore rules and `notebooks/inputs/.gitkeep`.
2. Add `jupyter` to the dev group and sync.
3. Write `notebooks/helpers.py`.
4. Write the seven notebooks with empty outputs.
5. Write `notebooks/README.md` and the one-line pointer in `README.md`.
6. Run `uv run ruff check notebooks/helpers.py`.

## Close

No product spec update. No quality-grade change. When the notebooks land, move this file to `docs/plans/completed/`.
