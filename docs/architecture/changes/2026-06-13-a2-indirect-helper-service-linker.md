# A2 Indirect Helper Service Linker

Date: 2026-06-13

## Context

Some endpoints initialize a service and pass it into a local helper function.
The helper function then calls the actual service operation.

Example shape:

```python
analytics_service = AnalyticsService(db)

kpi_data = await _get_dashboard_kpi_data(
    db,
    org_id,
    org_uuid,
    scope,
    owned_experiment_filter,
    analytics_service,
)

async def _get_dashboard_kpi_data(..., analytics_service: AnalyticsService):
    return await analytics_service.calculate_system_analytics(org_id)
```

Before this slice, the raw facts contained the service initialization and the
helper service call separately, but the linker only connected direct calls made
inside the endpoint function.

## Implemented in this Slice

### Call Arguments

`CallFact` now records:

- `args`
- `kwargs`

This allows the linker to see that an endpoint passes `analytics_service` into
`_get_dashboard_kpi_data(...)`.

### Indirect Helper Linking

The endpoint-service linker now detects:

```text
endpoint function
-> helper function call
-> forwarded service variable
-> helper service operation call
```

When this is found, the linker emits a normal `EndpointServiceLinkItem` with a
specific detection rule:

```text
service_variable_forwarded_to_typed_helper
```

The link evidence records:

- endpoint qualified name
- helper call
- helper qualified name
- service call inside the helper
- resolved service operation

This keeps existing UI/backend consumers compatible while making the indirect
relation explainable.

## Files Changed

- `archdoc/src/archdoc/facts/models.py`
- `archdoc/src/archdoc/scanner/python_scanner.py`
- `archdoc/src/archdoc/catalog/models.py`
- `archdoc/src/archdoc/linker/endpoint_service_linker.py`
- `docs/architecture/generated_raw/raw_code_facts.json`
- `site/static/archdoc/*.json`
- `docs/architecture/schemas/*.schema.json`

## Validation Performed

Python compile:

```bash
.venv\Scripts\python.exe -m py_compile archdoc\src\archdoc\facts\models.py archdoc\src\archdoc\scanner\python_scanner.py archdoc\src\archdoc\catalog\models.py archdoc\src\archdoc\linker\endpoint_service_linker.py
```

Raw scan:

```bash
$env:PYTHONPATH='archdoc/src'; .venv\Scripts\python.exe -m archdoc.cli scan -c archdoc.yml
```

In-memory map/validation:

```text
counts 83 558 730 457
validation 0 222 364
candidate_not_linked 23
rules {'service_variable_forwarded_to_typed_helper': 3}
analytics_links 1
```

The verified analytics link:

```text
get_aggregated_dashboard_analytics
-> _get_dashboard_kpi_data
-> analytics_service.calculate_system_analytics
```

Static Docusaurus JSON and SQLite generated tables were refreshed.

Backend query check:

```text
candidate 23
all 586
```

Frontend typecheck:

```bash
npm run typecheck
```

## Still Open

Recommended next follow-up:

- add a generalized relation model for endpoint -> helper -> operation paths
- show detection rule/evidence in the interface table UI
- extend helper linking beyond same-module helper functions if needed
