# Embeddings in this repo

User-visible consequences are specified in [`../product-specs/retrieval.md`](../product-specs/retrieval.md), [`../product-specs/chunking.md`](../product-specs/chunking.md), and [`../product-specs/session.md`](../product-specs/session.md).

## Model

`InferenceClient` from `huggingface_hub`, provider `hf-inference`, key `HUGGINGFACE_API_KEY`. The default model in settings is `intfloat/multilingual-e5-large`, dimension 1024.

That model is asymmetric. The code prefixes:

- `passage: ` on chunk text at index time.
- `query: ` on the question at search time.

The text stored in Supabase is the chunk without the prefix. The prefix is sent only to the API. `.env.example` uses the same model name.

## Index

`pipeline/index_store.py`. The running app and the notebooks use `SupabaseIndex`: the `chunks` table in [`../../supabase/schema.sql`](../../supabase/schema.sql), cosine distance via `match_session_chunks`. Tests call `use_memory_index()` and do not sign in.

One set of rows per `session_id`. Reindexing the same PDF deletes that filename's chunks first, then upserts by `(session_id, chunk_id)` where `chunk_id` is `{filename}_{page}_{chunk_index}`, so a shorter replacement does not leave old ids. A repeated chunk id keeps its first `created_at`. A batch of chunks is embedded in one Inference API call.

Columns written: `source`, `page`, `chunk_index`, `headings` as a JSON array, `content`, and the 1024-dimension embedding. On read, `vector_store` accepts headings as a list or as a JSON string.

The server signs in as the admin test user. It does not use the service role key. Row level security limits rows to that user. Queries also filter on `session_id`.

## Search

`pipeline/vector_store.search` embeds the question and queries one session and one `source`, with `n_results` default 5. Distance is cosine distance: lower means closer. The fast retrieval tier is that search. Medium fuses it with BM25. Slow reranks the fused shortlist with `cross-encoder/mmarco-mMiniLMv2-L12-H384-v1`, loaded on first use. `list_sources` reads filenames only and returns them sorted.

The slow chunk tier sends each chunk to the configured LLM and embeds `passage: ` plus the returned sentence plus the chunk. The stored text has no sentence.

`embedder` writes. `vector_store` reads. Those roles are not swapped.
