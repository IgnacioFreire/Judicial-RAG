# Interface design

Layout and copy only. Upload, save, run, reset, and results behave as specified in [`product-specs/`](product-specs/index.md). Do not restate those rules here.

One dashboard shell. Title `⚖️ Judicial RAG`. Caption: "Extract and classify variables from judicial PDF documents."

```
┌ nav ───────────────────┬ page ───────────────────────────┐
│ Overview               │ the selected route              │
│ Documents              │                                 │
│ Settings               │ profile popover in the header  │
└────────────────────────┴─────────────────────────────────┘
```

| Route | Contents |
|---|---|
| Overview | Caption, metric cards, Run pipeline, Reset, recent PDFs |
| Documents | Upload, table of name, status, accepted time, finished time |
| Document | Status, times, and that PDF's answers |
| Settings | Define questions, Save schema, Advanced settings, read-only question types |

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

The UI supports English and Spanish via `web/src/i18n/`. Theme (light or dark) is stored in the browser. Contextual help uses a `?` control that opens a short dialog. Profile offers sign out (new session cookie), session API keys, theme, and language.

Copy that is not yet in the locale files may stay English until moved into `en.ts` / `es.ts`.

## Editor fields

Each draft shows label, question text, type, optional output format, and optional notes. Classification adds category code and label rows. Validation outcomes are in [`product-specs/question-schema.md`](product-specs/question-schema.md).
