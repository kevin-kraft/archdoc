# A1 Deterministic ID Collision Resolution

Date: 2026-06-13

## Context

The first identity/provenance slice added `identity` metadata to generated
catalog items. The next problem was duplicate generated IDs, especially where
similar service classes or inherited service operations produced the same
logical operation IDs.

Duplicate IDs are harmful because:

- generated service files can overwrite each other
- React table row keys collide
- SQLite generated tables cannot distinguish records cleanly
- overlays cannot target one concrete generated item
- BPMN/user-story links would inherit ambiguity

## Implemented in this Slice

### Resolver Stage

A deterministic resolver was added:

- `archdoc/src/archdoc/catalog/id_resolver.py`

The resolver runs after service/endpoint mapping and before endpoint-service
linking.

Pipeline order now:

```text
map services/endpoints
-> resolve catalog ID collisions
-> link endpoints to services
-> resolve link ID collisions
-> validate/write/export
```

### Collision Policy

When duplicate IDs exist, every item in the duplicate group receives a
deterministic suffix derived from its `identity.source_id`.

Example shape:

```text
calendar.calendar
-> calendar.calendar--c7cbd5be88
-> calendar.calendar--4d39334627
```

The original ID is preserved as:

- `identity.logical_id`
- an entry in `identity.aliases`

This keeps the canonical generated ID unique while retaining the human-readable
legacy ID for explanation and future overlay migration.

### Operation Rebase

When a service ID is collision-resolved, its operation IDs are rebased to the
resolved service ID before operation-level collision resolution runs.

This prevents operation IDs from keeping an ambiguous parent prefix.

### Identity Validation

The catalog validator now checks:

- `item.id == item.identity.catalog_id`
- duplicate `identity.source_id` per target type

This makes identity drift visible in validation instead of hidden in generated
data.

## Files Changed

- `archdoc/src/archdoc/catalog/id_resolver.py`
- `archdoc/src/archdoc/cli.py`
- `archdoc/src/archdoc/validator/catalog_validator.py`
- `docs/architecture/schemas/*.schema.json`

## Validation Performed

Python compile:

```bash
.venv\Scripts\python.exe -m py_compile archdoc\src\archdoc\catalog\id_resolver.py archdoc\src\archdoc\cli.py archdoc\src\archdoc\validator\catalog_validator.py
```

In-memory pipeline check:

```bash
$env:PYTHONPATH='archdoc/src'; .venv\Scripts\python.exe -c "from pathlib import Path; from collections import Counter; from archdoc.config.loader import load_config; from archdoc.facts.loader import load_raw_facts; from archdoc.mapper.service_mapper import map_services; from archdoc.mapper.endpoint_mapper import map_endpoints; from archdoc.catalog.id_resolver import resolve_catalog_id_collisions, resolve_link_id_collisions; from archdoc.linker.endpoint_service_linker import link_endpoints_to_services; from archdoc.linker.mark_linked_endpoint_implementations import mark_linked_endpoint_implementations; from archdoc.validator.catalog_validator import validate_catalog; cfg=load_config(Path('archdoc.yml')); facts=load_raw_facts(cfg.output.raw_facts); services=map_services(facts,cfg); endpoints=map_endpoints(facts,cfg); before_service_dupes=sum(1 for _id,c in Counter(s.id for s in services).items() if c>1); before_op_dupes=sum(1 for _id,c in Counter(o.id for s in services for o in s.operations).items() if c>1); services,endpoints=resolve_catalog_id_collisions(services,endpoints); links=resolve_link_id_collisions(link_endpoints_to_services(facts,endpoints,services)); endpoints=mark_linked_endpoint_implementations(endpoints,links); report=validate_catalog(facts,services,endpoints,links); after_service_dupes=sum(1 for _id,c in Counter(s.id for s in services).items() if c>1); after_op_dupes=sum(1 for _id,c in Counter(o.id for s in services for o in s.operations).items() if c>1); print('counts', len(services), sum(len(s.operations) for s in services), len(endpoints), len(links)); print('dupes', before_service_dupes, before_op_dupes, after_service_dupes, after_op_dupes); print('validation', report.summary.errors, report.summary.warnings, report.summary.infos); print('identity_issues', [issue.code for issue in report.issues if 'identity' in issue.code][:5])"
```

Result:

```text
counts 83 558 730 428
dupes 1 5 0 0
validation 0 247 375
identity_issues []
```

Schema export:

```bash
$env:PYTHONPATH='archdoc/src'; .venv\Scripts\python.exe -c "from pathlib import Path; from archdoc.schema_exporter import export_json_schemas; paths=export_json_schemas(Path('docs/architecture/schemas')); print(len(paths))"
```

Result:

```text
11
```

## Still Open

Recommended next follow-up:

- persist `identity.catalog_id`, `identity.logical_id`, and `identity.source_id`
  as dedicated SQLite columns
- allow overlay lookup through `identity.aliases`
- decide whether frontend review targets should switch from `id` to
  `identity.catalog_id` everywhere in one migration step
