# User Story Demo Layer

## Context

The architecture viewer needs a first demonstrable user-story view that connects
manual frontend/user-process documentation with generated backend architecture.

## Change

Added a user-story import and visualization layer:

- Markdown user stories live in `docs/architecture/user-stories`.
- `ui_backend` imports frontmatter and body markdown into the SQLite read model.
- User-story endpoint references are linked to generated endpoints by
  `method + path`, with `/api` prefix tolerance.
- Detail reads resolve endpoint architecture into endpoint, service link,
  service, operation, and operation actions.
- Docusaurus now has a generated docs page at
  `architecture/generated/user-stories`.

## Demo Data

Added `US-ADMIN-001`, a small reset-password story that links to:

- endpoint `POST /users/{user_id}/reset-password`
- service `admin.admin-user`
- operation `reset_password`

## Rationale

This keeps the manual user-story layer separate from generated Archdoc output
while still making generated architecture inspectable from a user-process
perspective. The layer is intentionally read-model based, so later editing,
BPMN references, and frontend-action capture can be added without changing
generated catalog ownership.

## Verification

- Python compile for changed backend files
- SQLite store initialization and user-story import
- Detail lookup for `US-ADMIN-001`
- `npm run typecheck`
- `npm run build`
