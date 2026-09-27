# Workspace preferences

## Why

Users need light and dark themes, English and Spanish UI copy, contextual help, a cleaner shared layout, sign-out for the browser session, and a place to set API keys for this session without exposing values in responses.

## Out of scope

- End-user Supabase login in the browser.
- Persisting API keys to disk or `.env`.
- Changing answer criteria or `models/`.

## Product spec

Update [`product-specs/workspace.md`](../../product-specs/workspace.md) with theme, locale, help, sign-out, and session keys.

## Modules

| Area | Files |
|---|---|
| API | `app/server.py`, `app/ui_state.py`, `services/session_secrets.py`, `services/llm_client.py`, `pipeline/embedder.py` |
| Web | `web/src/i18n/*`, `web/src/preferences.tsx`, `web/src/components/*`, pages |
| Tests | `tests/test_api.py` |
| Docs | `FRONTEND.md`, `DESIGN.md`, `SECURITY.md` |

## Tasks

1. Session key overrides and sign-out endpoints; wire secrets during runs.
2. Theme and locale providers with local persistence.
3. `PageHeader`, `HelpDialog`, shared shell styling.
4. Profile menu: sign out, keys dialog, theme and language toggles.
5. Translate pages and update docs.

## Verification

- `uv run pytest tests/test_api.py`
- `uv run ruff check` on touched Python
- `cd web && npm run build`
