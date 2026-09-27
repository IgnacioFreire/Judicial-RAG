# Design documents

Catalog. The **Checked** column says what the text was compared with, and when. A doc that has not been checked recently is not current: read the code and, if the doc is wrong, fix it or add a debt row.

This pass: 2026-09-26.

Observable behavior is not duplicated here. It lives in [`../product-specs/`](../product-specs/index.md).

| Document | What it fixes | Checked |
|---|---|---|
| [`core-beliefs.md`](core-beliefs.md) | Working rules for the repo | Team rules, not executable behavior. Aligned with the code read on 2026-09-26 |
| [`../PRODUCT_SENSE.md`](../PRODUCT_SENSE.md) | Who the product is for, and what it is not | Compared with `README.md` and the flow in `app/main.py` |
| [`../product-specs/index.md`](../product-specs/index.md) | Behavior a user can rely on | Compared with the pipeline, the question form, the uploader, and session cleanup on 2026-09-26 |
| [`../ARCHITECTURE.md`](../ARCHITECTURE.md) | Module map and dependencies | Compared with imports in the tree |
| [`../DESIGN.md`](../DESIGN.md) | Layout and copy. Behavior is in the product specs | Compared with the three components under `app/components/` |
| [`../FRONTEND.md`](../FRONTEND.md) | Where each UI piece and state key lives | Compared with `app/` |
| [`../RELIABILITY.md`](../RELIABILITY.md) | Failure isolation and limits | Compared with the orchestrator, uploader, cleanup, and settings |
| [`../SECURITY.md`](../SECURITY.md) | Secrets, PDFs, logs | Compared with `.gitignore`, `settings.py`, `session_manager.py`, `rag_agent.py` |
| [`../QUALITY_SCORE.md`](../QUALITY_SCORE.md) | Grade per module | Assigned from the code and `tests/` on 2026-09-26 |
| [`../tech-debt-tracker.md`](../tech-debt-tracker.md) | Open drift, not a plan | Each row names a file |
| [`supabase.md`](supabase.md) | Where users, sessions, PDFs, and the index will live | Decision confirmed 2026-09-27. The Streamlit app still uses a temp directory |
| [`../plans/README.md`](../plans/README.md) | How a change is planned. Finished plans sit in `plans/completed/` | [`../plans/manual-notebooks.md`](../plans/manual-notebooks.md) and [`../plans/supabase-storage.md`](../plans/supabase-storage.md) are in progress |

Nothing checks that a doc was re-read after a code change. Relative links in `docs/`, `AGENTS.md`, and `README.md` are checked by `tests/test_doc_links.py`. When a change alters behavior a doc describes, update the product spec in the same change. If you cannot update it yet, add a row to the tracker.
