# A2: Internal Service Operation Validation

## Context

The endpoint linker can map a route to the application service operation it
calls directly. Some application service operations then delegate to lower-level
domain services through instance fields, for example:

```python
self._duplicate_service = ParticipantDuplicateService(db)
return await self._duplicate_service.detect_duplicates(...)
```

Before this change, the domain operation was still reported as
`operation_without_endpoint_link`, because the validator only counted direct
endpoint-to-service links.

## Change

The catalog validator now performs a small internal service reference pass:

- collect service instance fields assigned in `__init__`
- collect service variables assigned in the current method
- collect service-typed method parameters
- resolve direct calls like `self._foo_service.bar(...)`
- count the target operation as referenced for validation summary and issue
  generation

## Design Rationale

This keeps the public endpoint-service link model unchanged while reducing false
validation noise for application-service-to-domain-service delegation.

It is intentionally not yet a full endpoint-helper-operation path graph. That
should be introduced as a separate relation model when the UI needs to inspect,
filter, or visualize multi-hop call paths directly.

## Verified Case

`ParticipantDuplicateApplicationService.detect_duplicates` now references
`ParticipantDuplicateService.detect_duplicates` internally, so the domain
operation is no longer reported as an unreferenced endpoint operation.
