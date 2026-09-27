# Supabase

Decision confirmed on 2026-09-27. One Supabase project is the store for users, sessions, PDF bytes, and the vector index (`pgvector`). The free plan is the target for the test account.

## What is true now

`notebooks/01_pdfs.ipynb` signs in as one admin test user and reads the private bucket `pdfs`. The account belongs to the maintainer. The notebook uses the anon key plus that user's email and password, all from `.env`. It does not use the service role key.

The Streamlit app still writes uploads to a temporary directory and keeps Chroma in memory. [`../product-specs/session.md`](../product-specs/session.md) and [`../product-specs/document-upload.md`](../product-specs/document-upload.md) still describe that behavior. They change when the app code moves, not before.

## Bucket

Private bucket, name `pdfs`, files at the bucket root. The admin test user is the only reader. That user's email and password live in `.env` (`SUPABASE_ADMIN_EMAIL`, `SUPABASE_ADMIN_PASSWORD`). They are not written in this repository.

How a person who clones the repo sets that account is in [`../../notebooks/README.md`](../../notebooks/README.md).

Uploads for this test account are made from the Supabase dashboard. The notebook reads them. It does not upload.

## Later

A React client keeps a login token. The server stores sessions, schemas, and results in Postgres, PDF bytes in the private bucket, and embeddings in `pgvector`, each row scoped by user id and session id. That move needs its own confirmation before the app code changes, because it replaces session isolation.
