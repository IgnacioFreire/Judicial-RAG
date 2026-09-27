# Parser tiers

Closed 2026-09-27. Fast extraction no longer implies one chunk per page; chunking is [`../../product-specs/chunking.md`](../../product-specs/chunking.md).

## Why

A user should choose how a PDF is read: a fast text-layer pass, the current Docling pass, or a slower layout pass. Judicial PDFs are public and mostly digital, so the default stays the middle tier.

## What this will not do

- It does not change prompts, `QuestionType`, citation pages, or answer criteria.
- It does not turn on Docling OCR or Docling table structure.
- It does not store the tier in `.env`. The tier belongs to the session, and later to the user profile.
- It does not let a user remap a tier to a different library. That map is `config/parsers.py`.

## Product spec

[`../../product-specs/document-upload.md`](../../product-specs/document-upload.md) gains the parser-tier requirement. Default medium uses docling without OCR. Fast uses pymupdf4llm. Slow uses marker and may OCR a region with no usable text. The UI still does not ask whether a PDF is scanned. How pages are later split is in [`../../product-specs/chunking.md`](../../product-specs/chunking.md).

[`../../product-specs/session.md`](../../product-specs/session.md) records the tier as a session preference that Reset keeps. A future user profile stores the same field. The method map is not per user.

## Modules

| Path | Change |
|---|---|
| `config/parsers.py` | `fast` → pymupdf4llm, `medium` → docling, `slow` → marker. |
| `pipeline/extractor.py` | Dispatch on the tier. Medium stays the Docling path. |
| `pipeline/pymupdf_parser.py` | Fast path. |
| `pipeline/marker_parser.py` | Slow path. |
| `pipeline/parsed_pages.py` | One chunk per non-empty page. |
| `pipeline/orchestrator.py` | Pass the session tier into `extract`. |
| `app/ui_state.py` | Store `parser_tier`. Reset keeps it. |
| `web/src/components/AdvancedSettings.tsx` | Sidebar control (was Streamlit). |

## Tests

- `tests/test_parsers.py`: the map, a rejected tier, one synthetic PyMuPDF page, one synthetic Marker page.
- `tests/test_extractor.py`: Docling chunk assembly and OCR off, unchanged.
- `tests/test_orchestrator.py`: fakes accept the tier argument.

## Order

1. Add the map and the three parser functions.
2. Thread the tier from the sidebar through `run`.
3. Update the upload spec, the session spec, and the UI copy.
4. Run `uv run ruff check` and `uv run pytest tests/test_parsers.py tests/test_extractor.py tests/test_orchestrator.py`.
