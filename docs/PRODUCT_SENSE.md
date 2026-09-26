# Product sense

judicial-rag pulls variables out of judicial PDFs the person just uploaded. It does not advise, and it does not ship a legal ontology. Statutes, deadlines, and offense codes come from the person's questions, not from this repo.

What the screen does is specified in [`product-specs/`](product-specs/index.md). This page does not restate those requirements.

## Boundaries that are not requirements yet

- It is not a search across a historical corpus, and it is not a case-law database.
- It is not a place to store case text for examples, tests, or docs.

## Language

Working docs are English. UI copy is English. The language of an explanation answer is a requirement in [`product-specs/variable-extraction.md`](product-specs/variable-extraction.md).

## How a new criterion is decided

A rule for "the answer is correct" (a date format, a category, a rounding step) is written in that question's `notes` or `output_format`, or in a product spec if it becomes product behavior. It is not hardcoded into the shared prompt because one case needed it.
