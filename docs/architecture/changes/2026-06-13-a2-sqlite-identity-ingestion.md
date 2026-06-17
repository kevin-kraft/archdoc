# A2 SQLite Identity Ingestion

Date: 2026-06-13

## Context

A1 added generated catalog identity:

- `identity.catalog_id`
- `identity.logical_id`
- `identity.source_id`
- `identity.display_name`
- `identity.aliases`

The UI backend previously stored generated items mostly as `payload_json` with a
few query columns. That made the backend depend on JSON payload scans for data
that should be first-class review/query metadata.

## Implemented in this Slice

### Identity Columns

The generated SQLite read-model tables now store identity fields directly:

- `catalog_id`
- `logical_id`
- `source_id`
- `display_name`
- `aliases_json`

Affected tables:

- `generated_services`
- `generated_operations`
- `generated_endpoints`
- `generated_links`

The existing `id` column remains present and compatible. For new generated JSON
with identity, `id` should match `identity.catalog_id`; for old generated JSON,
the backend fills identity columns from fallback values.

### Existing Database Migration

The backend adds missing identity columns with `ALTER TABLE ... ADD COLUMN`.
This lets an existing `archdoc-review.sqlite3` continue to be used.

Identity indexes are created after column migration, so old databases do not
fail during startup.

### Import Fallbacks

Generated JSON without an `identity` object is still accepted.

Fallback behavior:

- `catalog_id`: generated `id`
- `logical_id`: generated `id`
- `source_id`: empty string
- `display_name`: best available label
- `aliases_json`: empty list

### Reimport Detection

If the active import run has missing identity columns, the backend reimports the
generated JSON even when the source hash did not change.

This handles the transition from the old SQLite schema to the identity-aware
schema.

### Search and Review Filters

Server-side table search now includes identity fields.

Endpoint search includes:

- `catalog_id`
- `logical_id`
- `source_id`
- `display_name`
- `aliases_json`

Operation search includes operation identity fields and related service identity
fields.

Interface search includes link identity fields and related endpoint identity
fields.

Review-status filters can match overlays by:

- current generated `id`
- `identity.catalog_id`
- `identity.logical_id`
- `identity.aliases`

### Overlay Lookup Fallback

Effective catalog application now resolves overlays through a shared lookup
helper. This allows current and legacy overlay target IDs to match generated
items through identity aliases.

### Validation Issue Index

Validation issues now have an index for review-oriented lookup:

- `import_run_id`
- `code`
- `severity`
- `item_id`

## Files Changed

- `ui_backend/app/storage.py`
- `docs/architecture/README.md`

## Validation Performed

Python compile:

```bash
.venv\Scripts\python.exe -m py_compile ui_backend\app\storage.py ui_backend\app\main.py ui_backend\app\models.py
```

SQLite import/query smoke check:

```bash
$env:PYTHONPATH='.'; .venv\Scripts\python.exe -c "from ui_backend.app.storage import initialize_schema_only, import_generated_if_needed, query_endpoints, query_operations, query_interfaces; initialize_schema_only(); run_id=import_generated_if_needed(force=True); print('run', run_id); print('endpoints', query_endpoints(search='calendar', limit=3).total, len(query_endpoints(search='calendar', limit=3).rows)); print('operations', query_operations(search='calendar', limit=3).total, len(query_operations(search='calendar', limit=3).rows)); print('interfaces', query_interfaces(search='calendar', limit=3).total, len(query_interfaces(search='calendar', limit=3).rows))"
```

Result:

```text
endpoints 14 3
operations 31 3
interfaces 12 3
```

Identity column fill check:

```text
generated_services 83 0
generated_operations 558 0
generated_endpoints 730 0
generated_links 428 0
```

The second number is the count of rows missing `catalog_id`.

## Still Open

Recommended next follow-up:

- expose validation issue tables through dedicated API routes
- add UI filters for identity/resolved-collision issue codes
- migrate overlay writes to prefer `identity.catalog_id` explicitly
- add SQLite schema versioning instead of ad hoc column migration
