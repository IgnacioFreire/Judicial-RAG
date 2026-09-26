# Security and data

Controls around keys, logs, and the deploy surface. Where uploads and the index live, and the rule that sessions do not see each other, are requirements in [`product-specs/session.md`](product-specs/session.md). This file does not repeat them.

## Keys

`Settings` requires the key for the active `LLM_PROVIDER` (`anthropic`, `openai`, `gemini`, `deepseek`; default `deepseek`) and `HUGGINGFACE_API_KEY` while embeddings are `huggingface`. Those fields use `repr=False`. Do not log the settings object, and do not write a key into a doc, a plan, or a test.

`.gitignore` excludes `.env`, `*.pdf`, and `.venv/`. It also excludes `chroma_db/`, a path the in-memory client does not write (TD-11).

On Hugging Face Spaces, secrets belong in the Space configuration, not in the image. `.dockerignore` excludes `.env` and `*.pdf` from the build context.

## Logs

Allowed at INFO: filename, counts, `session_id`, question type, confidence, durations.

Forbidden at every level: PDF body, full prompt, citation, a model response that contains case facts, keys. Debug logs record lengths and counts, not the text.

## Docs, tests, and plans

Do not paste real rulings. A fixture, if one is ever added, is synthetic or anonymized, and the change that introduces it says so. `docs/` is not a place for examples that name parties, case numbers, or facts.

## Surface

The app listens on port 8501 inside the container, on `0.0.0.0`. The code has no authentication. Anyone who can open the Space can upload a PDF to that instance. Isolation is between sessions of the same process, not an authenticated user boundary.

Do not add an endpoint, a webhook, or an external PDF store without a plan and a human confirmation.
