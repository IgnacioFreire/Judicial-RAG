# Notebooks

Start here to try the pipeline one stage at a time. These notebooks are a local harness. They are not the Streamlit app, and this folder has no automated test suite. You check a notebook by running it and reading what it prints.

## Before you run anything

From the repo root:

```bash
uv sync --group dev
cp .env.example .env
uv run jupyter lab notebooks
```

On Windows, copy `.env.example` to `.env` yourself. Fill in `.env` and do not commit it.

Open one notebook and use its kernel only for that file. Run the cells from top to bottom. Restart the kernel before you open the next notebook. Each notebook that embeds writes its own session index in Supabase and deletes that index in the last cell.

Do not commit notebook outputs, `.ipynb_checkpoints/`, or PDFs.

`SHOW_TEXT` starts as `False`. Set it to `True` in a notebook only when you want chunk text, answers, or citations on this machine. The printed tables still omit that text.

## Admin test account

`01_pdfs.ipynb` signs in to your own Supabase project and reads the private bucket `pdfs`. The email and password belong to the person who runs the notebook. They stay in `.env`. A clone does not receive someone else's account.

1. In the Supabase dashboard, open Authentication and add one user. Use your email and a password you choose.
2. In `.env`, set `SUPABASE_ADMIN_EMAIL` to that email and `SUPABASE_ADMIN_PASSWORD` to that password.
3. In Project Settings → API, copy the project URL into `SUPABASE_URL` and the anon key into `SUPABASE_ANON_KEY`. Leave the service role key out of `.env`.
4. Create a private bucket named `pdfs`. Leave `SUPABASE_PDF_BUCKET=pdfs` unless you chose another name.
5. Open the SQL editor and run the policy below. Where the statement mentions the email, paste the same address you put in `SUPABASE_ADMIN_EMAIL`. Do that in the dashboard only. Do not copy that address into a file in the git repository.

```sql
create policy "admin test user reads pdfs"
on storage.objects for select
to authenticated
using (
  bucket_id = 'pdfs'
  and auth.jwt() ->> 'email' = '<SUPABASE_ADMIN_EMAIL from your .env>'
);
```

6. Upload PDFs from the Storage page in the dashboard.
7. Restart the kernel and run `01_pdfs.ipynb`.

A good run prints the bucket name, one row per object with `accepted` or `rejected: ...`, then `accepted`, `rejected`, and `list` seconds. The last cell prints a byte count for each accepted file and does not print the PDF text. A rejected row names the reason: not a PDF, over 20 MB, or an empty name.

## Extraction from the bucket

`02_extraction.ipynb` uses the same admin account as `01_pdfs.ipynb`. It downloads each accepted PDF into a temporary directory, then runs `extract` once per parser tier. Chunking stays at the default, medium. Parser tiers are in `config/parsers.py`. Narrow `TIERS` to skip a parser. The last cell deletes those files. The first medium parser run downloads Docling models. The first slow parser run downloads Marker models. It does not embed and it does not print chunk text unless you set `SHOW_TEXT = True`.

`03_embedding.ipynb` uses the same admin account and the same private bucket. It downloads each accepted PDF into a temporary directory, extracts it once per chunk tier, and embeds each result. Chunk tiers are in `config/chunkers.py`. Narrow `CHUNK_TIERS_SELECTED` to skip one. The first slow chunk run sends each chunk to the configured LLM. The first slow retrieval is not run in this notebook. Apply `supabase/schema.sql` once in the SQL editor before this notebook. The last cell deletes that session's index rows and the temporary files.

## Local PDFs for the later notebooks

Notebooks `04` through `07` read local PDFs, not the bucket. Put PDFs in `notebooks/inputs/`, or set `NOTEBOOK_PDF_DIR` to another directory. Those calls need the LLM key and `HUGGINGFACE_API_KEY` in `.env`. Any cell that embeds or searches also signs in with the admin test user and writes that run's index to Supabase. The last cell deletes those rows. Apply `supabase/schema.sql` once in the SQL editor before the first of these notebooks.

The question cells are templates. Replace the label and the instruction with your own question before you run retrieval, the agent, results, or KPIs. The template is not a legal rule.

## What to look for

| Notebook | You are checking | A good run shows |
|---|---|---|
| `01_pdfs.ipynb` | Sign-in and the private bucket | Accepted and rejected rows, then byte counts. No Docling. |
| `02_extraction.ipynb` | `extract` on each PDF from the bucket, once per parser tier | Parser, method, filename, pages, chunks, heading count, and min, median, and max characters, plus seconds. A failure prints the exception type and continues. A PDF with no chunks is a failure. The last cell deletes the temporary files. |
| `03_embedding.ipynb` | `extract` once per chunk tier on each PDF from the bucket, then `embed_document` | Chunk tier, chunk method, filename, pages, chunks, heading count, and min, median, and max characters, then embed seconds and indexed sources. Each tier has its own session index. A failure prints the exception type and continues. The last cell deletes those rows and the temporary files. |
| `04_retrieval.ipynb` | `search` for one question and one file | Rank, page, headings, distance, and character count. Default `n_results` is 5. The last cell deletes that session's index rows. |
| `05_agent.ipynb` | `answer_question` for one question and one file | Label, question type, confidence, answer source, citation page, citation score, citation character count, and seconds. The last cell deletes that session's index rows. |
| `06_results.ipynb` | The same columns the UI shows | The first code cell uses an in-memory sample and needs no quota. Later cells answer your questions, then print `result_rows` and `answered_counts` with the mapping time on its own. The last cell deletes that session's index rows. |
| `07_kpis.ipynb` | One full `run` | Phase times, `kpi_summary`, `answered_counts`, and `result_rows`. The last cell deletes that session's index rows. |

Run `06_results.ipynb` through the sample cell first when you want to check the mapping without calling an API.
