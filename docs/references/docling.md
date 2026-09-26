# Docling in this repo

Used only in `pipeline/extractor.py`. User-visible consequences are specified in [`../product-specs/document-upload.md`](../product-specs/document-upload.md).

## What is on

Two `DocumentConverter` instances are built when the module is imported:

- Digital: `do_ocr=False`.
- OCR: `do_ocr=True`.

`extract(pdf_path, is_scanned=...)` picks one. Whether the user can choose OCR is a requirement in [`../product-specs/document-upload.md`](../product-specs/document-upload.md) (TD-04).

Off in both: table structure, page images, picture images. Do not turn them on to "use more of Docling" without a change. The module comment says judicial PDFs are not processed that way, and the UI never uses images.

## How text is split

`HybridChunker` with tokenizer `bert-base-multilingual-cased`, `max_tokens=512`, `merge_peers=True`. The tokenizer measures size. It does not compute the embedding.

Stored text is `chunker.contextualize()`, so the heading is inside the chunk. Headings are also stored on `Chunk.headings`. Empty chunks are skipped. The page comes from `meta.doc_items[0].prov[0].page_no`, and if that chain is missing, page 1.

`CHUNK_SIZE` and `CHUNK_OVERLAP` in settings do not participate (TD-02).

## Thread

Conversion is synchronous and runs on a `ThreadPoolExecutor` of `max_parallel_pdfs` workers (1–10, default 4), so it does not block the event loop. The converter is built once at import. A new one is not built per PDF.
