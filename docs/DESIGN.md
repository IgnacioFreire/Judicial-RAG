# Interface design

Layout and copy only. Upload, save, run, reset, and results behave as specified in [`product-specs/`](product-specs/index.md). Do not restate those rules here.

One wide screen. Title `⚖️ Judicial RAG`. Caption: "Extract and classify variables from judicial PDF documents."

```
┌ sidebar ───────────────┬ body ───────────────────────────┐
│ Upload documents       │ Run pipeline          Reset     │
│ [PDF, multiple]        │ progress / error / success      │
│ Define questions       │ Results                         │
│ editors + categories   │ one expander per PDF            │
│ Add question           │                                 │
│ Save schema            │                                 │
└────────────────────────┴─────────────────────────────────┘
```

## Copy

| Element | String |
|---|---|
| Run | `Run pipeline` |
| Reset | `Reset` |
| Add a draft | `Add question` |
| Persist the schema | `Save schema` |
| Missing answer | `No answer found.` |
| Direct provenance | `Extracted directly` |
| Inferred provenance | `Inferred through reasoning` |

Confidence badges: `high` green, `medium` orange, `low` red, `not_found` gray.

Visible strings are English. A copy change is its own plan and touches the three components under `app/components/` and `app/main.py` together.

## Editor fields

Each draft shows label, question text, type, optional output format, and optional notes. Classification adds category code and label rows. Validation outcomes are in [`product-specs/question-schema.md`](product-specs/question-schema.md).
