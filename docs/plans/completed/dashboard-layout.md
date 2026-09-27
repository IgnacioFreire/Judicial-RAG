# Dashboard layout

## Why

The workspace screens should read as one dashboard: a full-height sidebar, one overview metric panel, recent documents beside next-step links, and a documents table with status pills.

## Out of scope

- New routes, API fields, or extraction rules.
- Copying a third-party component library.

## Product spec

Update [`product-specs/workspace.md`](../../product-specs/workspace.md) so the overview shows the summary, run controls, a recent list, and links to upload and to the question editor.

## Modules

| Area | Files |
|---|---|
| Web | `web/src/components/AppShell.tsx`, `web/src/pages/Overview.tsx`, `web/src/pages/Documents.tsx`, `web/src/components/StatusBadge.tsx` |
| Docs | `DESIGN.md`, `FRONTEND.md` |

## Tasks

1. Record the overview composition in the workspace spec.
2. Rebuild the shell, overview, and document table.
3. Point `DESIGN.md` and `FRONTEND.md` at that composition.

## Verification

`cd web && npm run build`. No API contract change, so no new pytest.
