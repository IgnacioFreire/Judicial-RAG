# Interface design

Layout and copy only. Upload, save, run, reset, and results behave as specified in [`product-specs/`](product-specs/index.md). Do not restate those rules here.

One wide dashboard screen. Title `⚖️ Judicial RAG`. Caption: "Extract and classify variables from judicial PDF documents."

The shell follows a finance-dashboard layout (dark workspace sidebar, light overview, metric cards). It is still a single page: no extra routes.

```
┌ dark sidebar ──────────┬ light body ─────────────────────┐
│ brand                  │ Overview + caption              │
│ Upload documents       │ metric cards                    │
│ Define questions       │ Run pipeline          Reset     │
│ Advanced settings      │ progress / error / success      │
│                        │ Results                         │
└────────────────────────┴─────────────────────────────────┘
```

## Copy

| Element | String |
|---|---|
| Run | `Run pipeline` |
| Reset | `Reset` |
| Add a draft | `Add question` |
| Persist the schema | `Save schema` |
| Advanced settings | `Advanced settings` |
| Parser tier | `Parser` |
| Fast option | `Fast — pymupdf4llm` |
| Medium option | `Medium — docling` |
| Slow option | `Slow — marker` |
| Chunking tier | `Chunking` |
| Fast chunk option | `Fast — window` |
| Medium chunk option | `Medium — hybrid` |
| Slow chunk option | `Slow — context` |
| Retrieval tier | `Retrieval` |
| Fast retrieval option | `Fast — dense` |
| Medium retrieval option | `Medium — hybrid` |
| Slow retrieval option | `Slow — rerank` |
| Missing answer | `No answer found.` |
| Direct provenance | `Extracted directly` |
| Inferred provenance | `Inferred through reasoning` |

Confidence badges: `high` green, `medium` orange, `low` red, `not_found` gray.

Visible strings are English. A copy change is its own plan and touches the components under `web/src/components/` together.

## Editor fields

Each draft shows label, question text, type, optional output format, and optional notes. Classification adds category code and label rows. Validation outcomes are in [`product-specs/question-schema.md`](product-specs/question-schema.md).
