# A2 Validation Review Workflow

Date: 2026-06-13

## Context

A2 made generated identity queryable in SQLite. The next review workflow issue
was validation: the frontend still loaded the full effective catalog report for
issue browsing, and the backend did not expose validation issues as a first
class paged table.

## Implemented in this Slice

### Validation Issue API

Added a server-side validation issue table endpoint:

```text
GET /api/table/validation-issues
```

Supported query parameters:

- `search`
- `severity`
- `code`
- `review_status`
- `sort`
- `direction`
- `limit`
- `offset`

Preset code filters:

- `resolved_collisions`
- `identity`

### Validation Frontend

The Validation page now keeps the dashboard summary, issue count table, endpoint
implementation table, and multi-link overview, but the main issue table is now
a paged server-backed `DataTable`.

The table supports:

- text search
- severity filter
- code presets for identity/resolved collision signals
- review status filter
- sorting
- pagination
- inline review overlay editor

### Overlay Writes Prefer Catalog IDs

Overlay writes for generated target types now normalize target IDs through the
active generated SQLite tables.

The backend resolves target IDs by:

- generated `id`
- `identity.catalog_id`
- `identity.logical_id`
- `identity.aliases`

When a match is found, the stored overlay target uses `catalog_id`.

### SQLite Schema Versioning

The SQLite database now stores a simple schema version in:

```text
schema_meta(key='schema_version')
```

The current backend schema version is also exposed in `/health` as:

```json
{
  "db_schema_version": "2"
}
```

This is intentionally lightweight; future versions can replace the current
tolerant `ALTER TABLE` approach with explicit migrations.

## Files Changed

- `ui_backend/app/storage.py`
- `ui_backend/app/main.py`
- `site/src/components/archdoc/archdocApi.ts`
- `site/src/components/archdoc/ValidationSummary.tsx`

## Validation Performed

Backend compile:

```bash
.venv\Scripts\python.exe -m py_compile ui_backend\app\storage.py ui_backend\app\main.py ui_backend\app\models.py
```

Frontend typecheck:

```bash
npm run typecheck
```

Backend validation issue smoke check:

```bash
$env:PYTHONPATH='.'; .venv\Scripts\python.exe -c "from ui_backend.app.storage import initialize_schema_only, import_generated_if_needed, query_validation_issues; initialize_schema_only(); import_generated_if_needed(); print('all', query_validation_issues(limit=3).total, len(query_validation_issues(limit=3).rows)); print('resolved', query_validation_issues(code='resolved_collisions', limit=10).total); print('identity', query_validation_issues(code='identity', limit=10).total)"
```

Result:

```text
all 629 3
resolved 6
identity 1
```

## Still Open

Recommended next follow-up:

- add dedicated validation issue code taxonomy documentation
- add UI shortcut chips for the most common validation issue codes
- add full SQLite migration files if the backend grows beyond local review usage
