# A3: Architecture Action Catalog Foundation

## Context

User stories and process documentation need more than endpoint-service links.
They need to answer questions like:

- which operation reads or writes data?
- which endpoint checks which permission?
- which service emits audit events?
- which method dispatches worker/background tasks?
- which class declares an entity/schema/model?

The scanner already extracted raw calls, assignments, annotations, and signals,
but these were not normalized into a reusable catalog layer.

## Change

Introduced a configurable architecture action catalog.

New generated item:

- `ArchitectureActionItem`

New owner model:

- `ActionOwnerRef`

Actions are linked to one owner:

- `endpoint`
- `operation`
- `method`
- `function`
- `class`

Initial action kinds:

- `database_action`
- `permission_action`
- `audit_action`
- `worker_action`
- `external_action`
- `entity_declaration`
- `type_usage`

## Configuration

Action detection is controlled by `mapping.actions.patterns` in `archdoc.yml`.
Patterns can match:

- call roles, for example `db_call`
- exact call names
- call prefixes
- call suffixes
- contained text in call name/args/kwargs
- nested calls when explicitly enabled

This keeps the layer reusable across projects instead of hardcoding Utilis-only
rules.

## Outputs

New static output:

- `site/static/archdoc/architecture_actions.json`

New JSON schemas:

- `docs/architecture/schemas/architecture-action-item.schema.json`
- `docs/architecture/schemas/static-architecture-actions-payload.schema.json`

## Current Utilis Snapshot

The first generated snapshot contains:

- 9456 architecture actions
- 2799 database actions
- 660 permission actions
- 142 audit actions
- 19 external actions
- 1069 entity declarations
- 4767 type usages

## Follow-Up

The next step is to ingest actions into the SQLite read model and expose
server-side table/query routes, then link user stories to actions through shared
IDs.
