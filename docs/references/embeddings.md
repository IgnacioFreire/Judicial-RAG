# Embeddings and Chroma in this repo

User-visible consequences are specified in [`../product-specs/variable-extraction.md`](../product-specs/variable-extraction.md) and [`../product-specs/session.md`](../product-specs/session.md).

## Model

`InferenceClient` from `huggingface_hub`, provider `hf-inference`, key `HUGGINGFACE_API_KEY`. The default model in settings is `intfloat/multilingual-e5-large`, dimension 1024.

That model is asymmetric. The code prefixes:

- `passage: ` on chunk text at index time.
- `query: ` on the question at search time.

The text stored in Chroma is the chunk without the prefix. The prefix is sent only to the API.

`.env.example` names `intfloat/multilingual-e5-large-instruct`, which does not use that prefix pair. Do not change the example or the default without picking one model and aligning prefixes, dimension, and settings (TD-01).

## Collection

In-memory `chromadb.Client()`. One collection per `session_id`. `get_or_create_collection`. Reindexing the same PDF deletes that filename's chunks first, then upserts by `chunk_id` (`{filename}_{page}_{chunk_index}`), so a shorter replacement does not leave old ids.

Metadata written: `source`, `page`, `chunk_index`, `headings` serialized with `|` (Chroma does not store lists). On read, `vector_store` splits on `|`.

## Search

`pipeline/vector_store.search` embeds the question and queries with `where={"source": source}` and `n_results` default 5. Distance is the cosine distance Chroma returns: lower means closer. `list_sources` reads metadata only and returns sorted PDF filenames.

`embedder` writes. `vector_store` reads. Those roles are not swapped.
