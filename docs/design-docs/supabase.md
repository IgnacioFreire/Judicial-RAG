# Supabase

Decision confirmed on 2026-09-27. One Supabase project is the store for users, sessions, PDF bytes, and the vector index (`pgvector`). The free plan is the target for the test account.

## What is true now

`notebooks/01_pdfs.ipynb`, `notebooks/02_extraction.ipynb`, and `notebooks/03_embedding.ipynb` sign in as one admin test user and read the private bucket `pdfs`. The account belongs to the maintainer. The notebooks use the anon key plus that user's email and password, all from `.env`. They do not use the service role key. The extraction and embedding notebooks write accepted PDFs to a temporary directory for Docling and delete those files in the last cell.

The Streamlit app signs in as that same admin test user and writes the search index to `public.chunks` (`pgvector`). The schema is [`../../supabase/schema.sql`](../../supabase/schema.sql). Apply it once in the SQL editor before the first embedding. PDF uploads still go to a temporary directory. [`../product-specs/session.md`](../product-specs/session.md) is the behavior of that index.

## Bucket

Private bucket, name `pdfs`, files at the bucket root. The admin test user is the only reader. That user's email and password live in `.env` (`SUPABASE_ADMIN_EMAIL`, `SUPABASE_ADMIN_PASSWORD`). They are not written in this repository.

How a person who clones the repo sets that account is in [`../../notebooks/README.md`](../../notebooks/README.md).

Uploads for this test account are made from the Supabase dashboard. The notebook reads them. It does not upload.

## Later

The index is already in `pgvector`, scoped by session id, under the one admin test user. What is still open: a React client with its own login token, a user row for `parser_tier`, `chunk_tier`, and `embedding_tier`, PDF bytes in the private bucket for the app, and sessions, schemas, and results in Postgres. Each of those rows would be scoped by user id and session id. The mapping from tier to method stays in `config/parsers.py`, `config/chunkers.py`, and `config/embeddings.py`. That move needs its own confirmation before the app code changes, because it replaces session isolation with a user account.

Streamlit already keeps `parser_tier`, `chunk_tier`, and `embedding_tier` on the current session, under Advanced settings. There is no user row yet, so the preference lasts for that session only.
