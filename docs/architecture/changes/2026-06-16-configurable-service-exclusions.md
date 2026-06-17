# Configurable Service Exclusions

## Context

The service mapper treated every class ending in `Service` under configured
service paths as a catalog service. This made technical infrastructure classes
such as `AuditService` appear as business service-operation targets when
routers called methods like `AuditService.log_event(...)`.

Those calls are useful architecture facts, but they should usually be reviewed
as audit/logging actions rather than as primary endpoint-to-service interfaces.

## Change

Service mapping now supports a configurable exclusion list:

```yaml
mapping:
  services:
    exclude_classes:
      - AuditService
```

Entries can use either the short class name or the qualified class name. Excluded
classes are not emitted into the service catalog, so the endpoint-service linker
does not create primary interface links to them.

Audit/logging behavior remains visible through the existing action mapping
rules. `AuditService.log_event(...)` calls still produce `audit_action` records
when they match the configured action patterns.

## Current Utilis Policy

The current configuration excludes:

- `AuditService`

This keeps audit logging visible as technical behavior without letting audit
calls dominate endpoint-service coverage.

## Verification

- `python3 -m py_compile archdoc/src/archdoc/config/models.py archdoc/src/archdoc/mapper/service_mapper.py`
- `archdoc map -c archdoc.yml`
- `archdoc export-schemas -c archdoc.yml`
- verified `AuditService` count in generated services is `0`
- verified endpoint-service links to `AuditService` are `0`
- verified generated `audit_action` records remain present
- validation report has `0` errors
