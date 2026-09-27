# Docling in this repo

Used for the medium parser tier in `pipeline/extractor.py`. User-visible consequences are specified in [`../product-specs/document-upload.md`](../product-specs/document-upload.md) and [`../product-specs/chunking.md`](../product-specs/chunking.md). The fast and slow parser tiers do not use this converter.

## What is on

One `DocumentConverter`, built on the first extraction, with `do_ocr=False`. Importing the module does not download models. Extraction reads the digital text layer. The upload spec does not ask the user whether a PDF is scanned.

Off: OCR, table structure, page images, picture images. Do not turn them on to "use more of Docling" without a change.

## How text is split

`HybridChunker` with tokenizer `intfloat/multilingual-e5-large`, `max_tokens=512`, `merge_peers=True`, for the medium and slow chunk tiers. The fast tier windows each page at the same limit. The tokenizer measures size. It does not compute the embedding.

Stored text is `chunker.contextualize()`, so the heading is inside the chunk. Headings are also stored on `Chunk.headings`. Empty chunks are skipped. The page comes from `meta.doc_items[0].prov[0].page_no`, and if that chain is missing, page 1.

Chunk size is this tokenizer limit. There is no character `CHUNK_SIZE` setting.

## Thread

Conversion is synchronous and runs on a `ThreadPoolExecutor` of `max_parallel_pdfs` workers (1–10, default 4), so it does not block the event loop. The converter is built on the first PDF. A new one is not built per PDF.
