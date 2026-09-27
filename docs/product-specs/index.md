# Product specs

Behavior a person can rely on. A change to it is a plan in [`../plans/`](../plans/README.md), and the spec is updated in the same change as the code. Do not restate these requirements in another doc.

| Spec | What it covers |
|---|---|
| [`document-upload.md`](document-upload.md) | PDF upload, the 20 MB limit, and the parser and chunk tiers |
| [`question-schema.md`](question-schema.md) | Save rules, the four question types, schema lifetime |
| [`variable-extraction.md`](variable-extraction.md) | One row per question, citations, batch failures |
| [`session.md`](session.md) | Isolation and session lifetime |

Checked against the code on 2026-09-27.
