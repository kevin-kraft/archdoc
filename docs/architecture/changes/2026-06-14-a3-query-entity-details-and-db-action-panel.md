# A3: Query Entity Details and DB Action Panel

## Context

Database action graph nodes were useful as topology signals, but long
SQLAlchemy expressions were not readable inside graph nodes. The graph also did
not expose which model definitions a query touched, so users had to jump back
to the backend source to understand fields, table names, and mapped types.

## Change

The raw scanner now records class-level fields as `ClassFact.fields`. This keeps
the scanner layer syntactic: it captures field name, annotation, assigned value,
value call, and source location without deciding whether the class is an ORM
model.

The action mapper now builds a configurable entity index from model-like
classes. `mapping.entities` controls:

- model paths
- accepted base class names
- field mapping call names such as `Column`, `mapped_column`, and `relationship`
- table-name field names such as `__tablename__`
- whether Pydantic models are included

Structured database `QueryInfo` now includes `entity_details` for entities found
in query expressions. Each detail contains model kind, module, table name,
source, and mapped fields.

The service action graph UI keeps database nodes compact. Clicking a database
action opens a detail panel with:

- action method and source
- query variable, operation, entities, and full expression
- filters, joins, ordering, and limit
- model/table details and mapped fields for referenced entities

## Rationale

This keeps graph readability and semantic detail separate. The node stays a
small routing element, while the panel provides inspectable architecture data.
The generator remains a deterministic JSON producer; no review state is written
back into generated files.

## Limits

Query parsing is still expression-based rather than a full SQLAlchemy semantic
interpreter. It resolves common `select(...)`, `.where(...)`, `.join(...)`,
`.order_by(...)`, `.group_by(...)`, and `.limit(...)` patterns and enriches
matched entity names with model definitions. Ambiguous duplicate class names are
currently resolved by deterministic first match and should later become a
validator warning.

## Verification

- `archdoc scan -c archdoc.yml`
- targeted static export using existing archdoc mapper/exporter functions
- SQLite generated import with `force=True`
- `python -m py_compile` for changed archdoc modules
- `npm run typecheck`
- `npm run build`
