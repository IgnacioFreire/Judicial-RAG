# Notebooks

Local harness for one pipeline stage at a time. Launch from the repo root:

```bash
uv sync --group dev
uv run jupyter lab notebooks
```

Each notebook that embeds creates its own in-memory Chroma collection and deletes it in the last cell. Do not commit notebook outputs. PDFs stay out of git.

## Admin test account

`01_pdfs.ipynb` signs in to your own Supabase project and reads the private bucket `pdfs`. The email and password belong to the person who runs the notebook. They stay in `.env` on that machine. `.gitignore` already excludes `.env`, so a clone does not receive someone else's account.

1. Copy `.env.example` to `.env` in the repo root. Do not commit `.env`.
2. In the Supabase dashboard, open Authentication and add one user. Use your email and a password you choose.
3. In `.env`, set `SUPABASE_ADMIN_EMAIL` to that email and `SUPABASE_ADMIN_PASSWORD` to that password.
4. In Project Settings → API, copy the project URL into `SUPABASE_URL` and the anon key into `SUPABASE_ANON_KEY`. Leave the service role key out of `.env`.
5. Create a private bucket named `pdfs`. Leave `SUPABASE_PDF_BUCKET=pdfs` unless you chose another name.
6. Open the SQL editor and create the read policy below. Where the statement mentions the email, paste the same address you put in `SUPABASE_ADMIN_EMAIL`. Run it in the dashboard. Do not copy that address back into a file in the git repository.

```sql
create policy "admin test user reads pdfs"
on storage.objects for select
to authenticated
using (
  bucket_id = 'pdfs'
  and auth.jwt() ->> 'email' = '<SUPABASE_ADMIN_EMAIL from your .env>'
);
```

7. Upload PDFs from the Storage page in the dashboard.
8. Restart the notebook kernel and run `01_pdfs.ipynb`.

The notebook prints names, sizes, and byte counts. It does not print PDF text.

Notebooks `02` through `07` still open local files from `NOTEBOOK_PDF_DIR`, or from `notebooks/inputs/` when that variable is unset.

`SHOW_TEXT` defaults to false. Turn it on in a notebook to print chunk text, answers, or citations on this machine.
