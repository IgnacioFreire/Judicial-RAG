# Supabase storage

## Why

The maintainer chose Supabase as the store for distinct users and durable sessions. The first slice is the PDF notebook: it reads the private bucket with one admin test account.

## What this will not do

- It does not change the Streamlit uploader, the temp directory, Chroma, prompts, `QuestionType`, or answer criteria.
- It does not put the service role key in the notebook or in `.env.example` as a usable secret.
- It does not open the bucket to anonymous users.
- It does not write PDF bytes into the git repository.

## Product spec

No file under `docs/product-specs/` changes in this slice. The running app still matches [`../product-specs/document-upload.md`](../product-specs/document-upload.md) and [`../product-specs/session.md`](../product-specs/session.md). Those specs change in the same change that moves `app/` and `storage/`.

## Modules

| Path | Change |
|---|---|
| `docs/design-docs/supabase.md` | The store decision. |
| `notebooks/01_pdfs.ipynb` | Sign in and read the `pdfs` bucket. Empty outputs. |
| `notebooks/02_extraction.ipynb` | Download accepted PDFs and run `extract`. Empty outputs. |
| `notebooks/helpers.py` | `classify_uploads` for name and size. |
| `.env.example` | Placeholders for the admin test account. |
| `pyproject.toml` | `supabase` in the dev group. |

`pipeline/`, `models/`, `app/`, and `services/` stay untouched.

## Tests

No new tests. The notebook signs in to a private project.

## Order

1. Record the decision and point to it from the architecture and security docs.
2. Add `classify_uploads` and the notebook.
3. Document the bucket policy and the `.env` keys.
4. Run `uv run ruff check notebooks/helpers.py`.

## Close

Do not move this file to `completed/` until the notebook reads the bucket and the decision docs match. The app migration stays open: it touches privacy, and it waits for another explicit yes before `app/` or `storage/` change.
