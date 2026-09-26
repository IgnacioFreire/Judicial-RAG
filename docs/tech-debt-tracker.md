# Technical debt

Living list. Each row is drift checked in the code on 2026-09-26. New code does not copy it. When a change pays a row, delete the row in that same change.

This is not a product spec. Active plans live in [`plans/`](plans/README.md). Finished ones move to `plans/completed/`.

| Id | What happens | Where | Effect |
|---|---|---|---|
| TD-06 | There is no CI workflow. The automated check is pre-commit: ruff and commitizen | `.pre-commit-config.yaml` | A push can skip whatever the local hook did not run |
| TD-08 | Citation page and score come from the top retrieved chunk, not from the fragment the model quoted. Specified as current behavior in [`product-specs/variable-extraction.md`](product-specs/variable-extraction.md) | `pipeline/rag_agent.py` `_build_citation` | The page on screen may not be the page of the quoted text |
| TD-12 | `storage/cleanup.py` imports `pipeline.embedder.delete_collection` | `storage/cleanup.py` | Exception to the layer direction. Do not add more |
| TD-14 | Docs have no mechanical check for links or freshness | `docs/` | A doc can rot with CI silent. The same change that alters behavior updates the product spec |
