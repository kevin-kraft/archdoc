# Validation Operation Link Stats

## Context

The validation page listed many linkage warnings, especially operation mapping
warnings, but did not summarize how much of the generated service operation
catalog is connected to endpoints or other service operations.

## Change

Added a validation stats API:

- `GET /api/validation/stats`

The endpoint aggregates from SQLite:

- total operations
- operations linked from endpoints
- operations with outgoing service calls
- operations called by other services
- operations participating in any operation dependency
- total/resolved/unresolved operation links
- validation issue counts by code and severity

The validation UI now shows an `Operation Mapping Coverage` section with
endpoint coverage, service dependency coverage, operation link counts, and
resolved operation-link counts.

The validation issue table also gained grouped code filters:

- `Service linkage open`
- `Endpoint mapping open`
- `Operation mapping open`

## Current Snapshot

At the time of implementation:

- operations: 558
- operations linked from endpoints: 323
- operations with outgoing service calls: 67
- operations called by other services: 33
- operations participating in any operation dependency: 92
- operation links: 115
- resolved operation links: 76
- unresolved operation links: 39
- `operation_without_endpoint_link` issues: 222

## Verification

- Python compile for `ui_backend`
- direct `read_validation_stats()` check
- grouped validation issue filter checks
- `npm run typecheck`
