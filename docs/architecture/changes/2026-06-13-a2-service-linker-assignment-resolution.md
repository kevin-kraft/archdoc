# A2 Service Linker Assignment Resolution

Date: 2026-06-13

## Context

Some endpoints were reported as `endpoint_service_candidate_not_linked` even
though they clearly interacted with services. Two patterns were responsible:

1. Service instances assigned outside the endpoint function.
2. Direct service class operation calls such as
   `UnifiedCampaignService.create_campaign(...)`.

The first pattern matters for module-level wiring:

```python
analytics_service = AnalyticsService()

@router.get("/...")
async def endpoint():
    return await analytics_service.get_system_analytics(...)
```

The second pattern matters for service classes used as stateless operation
facades:

```python
return await UnifiedCampaignService.create_campaign(...)
```

## Implemented in this Slice

### Module-Level Assignment Facts

`FileFact` now includes module-level assignments:

```json
{
  "assignments": [...]
}
```

The scanner extracts top-level `Assign` and `AnnAssign` nodes without mixing in
function-local assignments.

### Linker Variable Resolution

The endpoint-service linker now combines:

- module-level service assignments
- endpoint-local service assignments
- typed service parameters

This lets service variables declared at module scope participate in endpoint
service operation linking.

### Direct Service Operation Calls

The linker no longer discards calls like:

```text
UnifiedCampaignService.create_campaign
```

even when the scanner labels them as `constructor_call`. Constructor calls are
still ignored by default, but service-class operation calls are allowed through
to the direct service matcher.

## Files Changed

- `archdoc/src/archdoc/facts/models.py`
- `archdoc/src/archdoc/scanner/python_scanner.py`
- `archdoc/src/archdoc/mapper/endpoint_mapper.py`
- `archdoc/src/archdoc/linker/endpoint_service_linker.py`
- `docs/architecture/generated_raw/raw_code_facts.json`
- `site/static/archdoc/*.json`
- `docs/architecture/schemas/*.schema.json`

## Validation Performed

Python compile:

```bash
.venv\Scripts\python.exe -m py_compile archdoc\src\archdoc\facts\models.py archdoc\src\archdoc\scanner\python_scanner.py archdoc\src\archdoc\linker\endpoint_service_linker.py archdoc\src\archdoc\mapper\endpoint_mapper.py
```

Raw scan:

```bash
$env:PYTHONPATH='archdoc/src'; .venv\Scripts\python.exe -m archdoc.cli scan -c archdoc.yml
```

In-memory map/validation after the linker fix:

```text
counts 83 558 730 454
validation 0 223 364
candidate_not_linked 24
email_campaign_candidate_warnings 0
```

Before this slice, the same in-memory pipeline had:

```text
links 428
candidate_not_linked 48
```

The static Docusaurus JSON was refreshed and SQLite was reimported.

Backend query check:

```text
candidate 24
all 587
resolved 6
```

Frontend typecheck:

```bash
npm run typecheck
```

## Notes

The remaining `endpoint_service_candidate_not_linked` issues need separate
review. Some are likely true architecture signals where an endpoint constructs a
service but delegates work to helper functions or uses the service only as an
input to non-cataloged logic.
