# Data Dictionary Refresh

## Context

The architecture data dictionary still described the early endpoint/service
catalog shape. Since then, the generated model gained operation links,
architecture actions, query/entity details and user-story trace read models.

## Change

The data dictionary now documents the current catalog and UI read-model fields:

- operation links for service calls and inherited operations
- architecture action fields and current action kinds
- query and entity-detail payloads for database actions
- service-action graph detail sections
- user-story trace node, edge and compaction semantics
- updated scope status for implemented action, query, type-usage and trace
  features

## Design Rationale

The dictionary should explain the stable contracts consumed by the UI, not just
the original generator output. Documenting trace compaction here also makes the
shared service-action graph and user-story trace behavior explicit: database
transactions and type usage are detail context, not separate architecture path
nodes.

## Verification

- Documentation-only change; Docusaurus validation handled by site build.
