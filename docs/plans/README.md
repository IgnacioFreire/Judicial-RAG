# Plans

How a change is written down. Current behavior is in [`../product-specs/`](../product-specs/index.md). This folder holds the plan for a change, not a second copy of that behavior.

## Sizes

| Size | When | Artifact |
|---|---|---|
| Lightweight | Typo, comment, or refactor with no behavior or contract change | None. The commit says what was skipped |
| Change | Anything a user could observe differently, including a contract in `models/` | `docs/plans/<kebab-name>.md` |

A name is stable kebab-case (`citation-page`, not `fix`).

## What a plan contains

- Why the change exists, and what it will not do
- Which file under `docs/product-specs/` changes, and the new requirement text
- Modules to touch, and the test that would prove each scenario
- An ordered task list
- The tech-debt id from [`../tech-debt-tracker.md`](../tech-debt-tracker.md), when the change pays one down

Stop for an explicit yes (`go ahead`, `approved`, `yes`) before writing the plan, again before editing code, and again before closing if the change touches answer criteria, privacy, or `models/`. Silence is not approval.

When the change is done, update the product spec in the same change, delete any debt row it paid, and move the plan to `completed/`.

Completed: [`completed/manual-notebooks.md`](completed/manual-notebooks.md), [`completed/supabase-storage.md`](completed/supabase-storage.md), [`completed/parser-tiers.md`](completed/parser-tiers.md), [`completed/supabase-vector-index.md`](completed/supabase-vector-index.md), [`completed/retrieval-tiers.md`](completed/retrieval-tiers.md), [`completed/react-shadcn-ui.md`](completed/react-shadcn-ui.md), [`completed/multi-page-workspace.md`](completed/multi-page-workspace.md), [`completed/workspace-preferences.md`](completed/workspace-preferences.md), [`completed/dashboard-layout.md`](completed/dashboard-layout.md). Nothing is in progress.
