# Frontend

Streamlit, one script. There is no router and no extra page.

| File | Role |
|---|---|
| `app/main.py` | `set_page_config`, logging, sidebar, Run and Reset, bridge to `pipeline.orchestrator.run` |
| `app/session_state.py` | Sole owner of the `st.session_state` keys listed below |
| `app/components/uploader.py` | `st.file_uploader`. Writes accepted files into `session.pdf_dir`. The size rule is in [`product-specs/document-upload.md`](product-specs/document-upload.md) |
| `app/components/question_form.py` | Drafts and **Save schema** |
| `app/components/results_viewer.py` | Expanders of `DocumentAnswers` |
| `app/components/advanced_settings.py` | Sidebar expander for the parser tier |

## State keys

In `app/session_state.py`:

| Key | Type | Initial value |
|---|---|---|
| `session_id` | `str` UUID | New on first load. Reused across reruns |
| `schema` | `QuestionSchema \| None` | `None` |
| `results` | `list[DocumentAnswers] \| None` | `None` |
| `is_processing` | `bool` | `False` |
| `uploaded_files` | `list` | `[]` |
| `run_errors` | `list[str]` | `[]`. Failure messages from the latest run. Shown again after the rerun that ends the run. Cleared on Reset and at the start of the next run |
| `parser_tier` | `str` | `medium`. One of `fast`, `medium`, `slow`. Kept on Reset. The method names are in `config/parsers.py` |

Components use the accessors (`state.schema()`, `state.set_results()`, …). Do not add raw keys in `main.py` or in the viewer.

Current exception: `question_form.py` stores drafts in `st.session_state["question_drafts"]`. Each draft and each category row has a stable `id`. Widget keys use that id, so removing a row does not reuse another row's widget state. A new editor field stays on that draft until **Save schema** builds a `UserQuestion`. Do not move the draft into `session_state.py` unless another component must read it.

## Startup

`main()` calls `state.init()` and `cleanup_expired_sessions()` on every rerun. `init()` creates the UUID if it is missing and ensures a `storage` `Session` with that id (`get_or_create_session`). A Streamlit rerun must not mint another UUID.

Run uses `asyncio.run(run(...))` because the Streamlit script is synchronous. When it finishes, the `finally` block clears `is_processing` and calls `st.rerun()`.

## UI logging

`main.py` sets the root logger to INFO and raises `docling`, `transformers`, `huggingface_hub`, `rapidocr`, `httpx`, and `chromadb` to WARNING. Do not lower that threshold to "see what the PDF said."

## What not to add here

- Direct calls to Docling, Chroma, or `call_llm`.
- A second page to manage schemas, without a spec.
- Result state computed in the component instead of reading `DocumentAnswers`.
