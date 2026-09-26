# AGENTS.md

Map of **judicial-rag**. Read this first. It is not the manual: it points at the source of truth and stops.

The product extracts variables from judicial PDFs. The user uploads documents, defines questions, and gets, for each PDF and question, an answer, a confidence, and a citation. Packages: `app/`, `pipeline/`, `models/`, `services/`, `storage/`, `config/`.

## Where to look

| If you need… | Open |
|---|---|
| Why the product exists and what not to invent | [`docs/PRODUCT_SENSE.md`](docs/PRODUCT_SENSE.md) |
| Modules and which way dependencies point | [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) |
| Rules that apply to every change | [`docs/design-docs/core-beliefs.md`](docs/design-docs/core-beliefs.md) |
| Design index and whether it is still current | [`docs/design-docs/index.md`](docs/design-docs/index.md) |
| Current behavior | [`docs/product-specs/`](docs/product-specs/index.md) |
| How a change is planned | [`docs/plans/README.md`](docs/plans/README.md) |
| UI layout and copy | [`docs/DESIGN.md`](docs/DESIGN.md), [`docs/FRONTEND.md`](docs/FRONTEND.md) |
| Known drift | [`docs/tech-debt-tracker.md`](docs/tech-debt-tracker.md) |
| What is solid and what is not | [`docs/QUALITY_SCORE.md`](docs/QUALITY_SCORE.md) |
| Failures, isolation, limits | [`docs/RELIABILITY.md`](docs/RELIABILITY.md) |
| Secrets, PDFs, logs | [`docs/SECURITY.md`](docs/SECURITY.md) |
| How this repo uses Docling and embeddings | [`docs/references/index.md`](docs/references/index.md) |

`docs/` is English. Identifiers, flags, and paths stay as they are in the code. UI copy is English.

If a document and the code disagree, the code wins. Record the disagreement in [`docs/tech-debt-tracker.md`](docs/tech-debt-tracker.md). Update the product spec in the same change as the code. Do not restate that requirement in a second doc.

## Working cycle

Detail is in [`docs/plans/README.md`](docs/plans/README.md).

- **Lightweight** (no behavior change): edit and verify. Do not open a plan.
- **Behavior change**: write `docs/plans/<kebab-name>.md`, then update [`docs/product-specs/`](docs/product-specs/index.md) when the code lands. Stop for an explicit human yes before the plan, again before implementing, and again before closing if the change touches answer criteria, privacy, or `models/`.
- Do not invent legal rules, categories, or extraction criteria. They come from the user's schema or from a product spec.

## Commands

```bash
uv sync --group dev
uv run streamlit run app/main.py
uv run pytest
uv run pytest --cov=pipeline --cov-report=term-missing
uv run ruff check .
uv run ruff format .
uv run pre-commit install
```

Copy `.env.example` to `.env`. Do not commit `.env` or `*.pdf`. Local app: `http://localhost:8501`.

## Before calling work done

- Tests for the behavior you touched pass, or you say which command you could not run and why.
- `uv run ruff check` passes on what you touched.
- A behavior change updates the product spec, and `docs/QUALITY_SCORE.md` if a module grade changed.
- The diff contains no secrets, PDFs, or case text.

## Boundaries

Ask before adding a dependency, changing what a `QuestionType` means, relaxing session isolation, logging document text, or skipping the cycle on a behavior change.

Never commit `.env` or PDFs. Never paste case text into docs, logs, specs, or plans. Never read or write another session's Chroma collection. Never treat a legal rule as true unless it is in a spec or in the user's schema.
