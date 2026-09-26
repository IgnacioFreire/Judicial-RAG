# Reliability

Engineering limits. What a person can observe when a PDF, a question, or a session fails is specified in [`product-specs/variable-extraction.md`](product-specs/variable-extraction.md) and [`product-specs/session.md`](product-specs/session.md). This file does not repeat those outcomes.

## Mechanisms

| Situation | Mechanism |
|---|---|
| One PDF fails in phase 1 | `asyncio.gather(..., return_exceptions=True)` in `pipeline/orchestrator.py` |
| Progress callback raises | Caught in `_emit`. Warning only |
| Retries | None |

A `not_found` row does not say whether retrieval was empty or the model call failed. The log does.

## Concurrency

Phase 1 runs per PDF, capped by `MAX_PARALLEL_PDFS` (default 4, minimum 1, maximum 10) on the extractor and embedder thread pools. Phase 2 asks questions in series, in schema order. Documents follow `list_sources` (sorted filenames).

## Session clock

`SESSION_TIMEOUT_MINUTES` is an integer from 5 to 1440. The default and the fact that the clock starts at creation are requirements in [`product-specs/session.md`](product-specs/session.md). `cleanup_expired_sessions` runs at the start of each Streamlit rerun. `tempfile.TemporaryDirectory` also removes the upload directory when the process exits.

## Model budget

Retrieval asks for 5 chunks per question. Generation uses `max_tokens=1024` in `services/llm_client.py`. There is no wall-clock budget and no cost budget per run.

## Absent metrics

There is no startup figure, no span figure, and no accuracy figure on a labeled set. Do not invent a threshold in an agent prompt. The repo has no metric to check it against.
