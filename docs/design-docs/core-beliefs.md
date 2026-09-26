# Working beliefs

Opinionated rules. They apply to every change. When today's code already breaks one, the tracker names it. New code does not copy the break.

## The repo is the system of record

What an agent cannot read in the repo does not exist: chats, external docs, the memory of a previous session. Durable decisions are written in `docs/` or in code. Case text is not promoted into documentation.

`AGENTS.md` is the index. Detail lives in the linked doc. Do not grow `AGENTS.md` with a rule that only affects one module: put it in that topic's doc and leave the pointer.

## Invariants, not style

Fix the boundaries. Inside them, the implementation may vary.

1. What crosses packages is a model in `models/`. Validate with Pydantic at that boundary. Do not prescribe the library for an internal detail the model already expresses.
2. Observable behavior lives only in [`../product-specs/`](../product-specs/index.md). Update that spec in the same change as the code. Do not copy the requirement into another doc.
3. Dependencies follow [`../ARCHITECTURE.md`](../ARCHITECTURE.md). `app/` does not enter `pipeline/`. `pipeline/` does not enter `app/`.
4. Do not add a dependency for a helper of a few lines, and do not reimplement Docling, Chroma, or the LLM client. A new library is named in the design and a person confirms it.

## Judicial text does not spread

Log, key, and repository rules are in [`../SECURITY.md`](../SECURITY.md). Do not paste case fragments into docs, tests that use real data, or plans.

The agent does not invent legal categories, deadlines, or extraction criteria. The user's question schema or an approved spec does.

## Human judgment enters at the criterion, not on every line

Lightweight work (no behavior change) needs no plan. Work that changes what counts as a correct answer, session isolation, or the `models/` contract waits for an explicit confirmation before it is implemented and before it is called done. Silence is not approval.

Format is `ruff`'s job (`pyproject.toml`, line length 88, target 3.11). Do not open a review to restyle code the linter already accepts.

## Debt is written where the next run will see it

A bad pattern already in the repo is recorded in [`../tech-debt-tracker.md`](../tech-debt-tracker.md) in the same change that finds it, if it is not fixed there. New code does not copy the pattern. When a comment and the code disagree, the code wins, and the comment or the tracker is corrected.
