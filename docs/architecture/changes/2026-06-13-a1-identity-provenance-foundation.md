# A1 Identity and Provenance Foundation

Date: 2026-06-13

## Context

The architecture documentation pipeline is moving from a static generated
viewer toward a reviewable architecture model. Generated JSON is now consumed
by a SQLite-backed UI backend, and human review state lives in overlays.

That makes stable identity and explainable detection metadata foundational:

- overlays need durable targets
- SQLite needs explicit keys
- later BPMN/user-story links need stable architecture anchors
- reviewers need to understand why archdoc generated a fact or relation

## Implemented in this Slice

This slice introduces the first compatibility-safe identity/provenance layer.

### Catalog Identity

Generated catalog items now carry an `identity` object:

```json
{
  "catalog_id": "...",
  "logical_id": "...",
  "source_id": "...",
  "display_name": "...",
  "aliases": ["..."]
}
```

Meaning:

- `catalog_id`: the stable catalog target for UI/backend usage
- `logical_id`: human-readable architecture ID
- `source_id`: deterministic source fingerprint from file, lines, qualified name, and context
- `display_name`: UI-friendly label
- `aliases`: compatibility/search aliases

For non-colliding items, `catalog_id` remains equal to the existing `id`.
Colliding items are resolved in a follow-up slice by assigning deterministic
source-based suffixes. The original logical ID stays available through
`logical_id` and `aliases`.

### Detection Evidence

`DetectionInfo` now supports an `evidence` list.

This lets mappers and linkers explain why an item was detected, for example:

- matching class name/path rules for services
- route method/path/function facts for endpoints
- call/endpoint/operation evidence for endpoint-service links

### Endpoint-Service Link IDs

Endpoint-service links now have an explicit `id` and `identity`, instead of
only being identified implicitly by endpoint, operation, and source line.

The UI backend import remains backward-compatible: if a generated link has no
explicit `id`, the backend still derives the old fallback ID.

## Files Changed

- `archdoc/src/archdoc/catalog/models.py`
- `archdoc/src/archdoc/catalog/identity.py`
- `archdoc/src/archdoc/mapper/service_mapper.py`
- `archdoc/src/archdoc/mapper/endpoint_mapper.py`
- `archdoc/src/archdoc/linker/endpoint_service_linker.py`
- `ui_backend/app/storage.py`

## Design Constraints

This slice deliberately does not yet change the primary generated `id` format.

Reason:

- current overlays and UI routes already target `id`
- a hard ID migration should be explicit and probably include aliases/migration support
- adding `identity` first lets downstream code adopt the safer contract gradually

## Still Open

Recommended next A1 follow-up:

- write generated `identity.catalog_id` into dedicated SQLite columns
- migrate overlay targeting from raw `id` to `identity.catalog_id`
- add overlay alias lookup for IDs that were collision-resolved

## Validation Performed

Python syntax compile was run for the changed backend/generator modules:

```bash
python -m py_compile archdoc\src\archdoc\catalog\models.py archdoc\src\archdoc\catalog\identity.py archdoc\src\archdoc\mapper\service_mapper.py archdoc\src\archdoc\mapper\endpoint_mapper.py archdoc\src\archdoc\linker\endpoint_service_linker.py ui_backend\app\storage.py
```

The compile check passed.

JSON schemas were exported with the local virtual environment:

```bash
$env:PYTHONPATH='archdoc/src'; .venv\Scripts\python.exe -c "from archdoc.schema_exporter import export_json_schemas; paths = export_json_schemas(__import__('pathlib').Path('docs/architecture/schemas')); print(len(paths))"
```

This wrote 11 schema files.

An in-memory mapping check was run to ensure services, endpoints, and links can
be instantiated with the new identity fields:

```bash
$env:PYTHONPATH='archdoc/src'; .venv\Scripts\python.exe -c "from archdoc.config.loader import load_config; from archdoc.facts.loader import load_raw_facts; from archdoc.mapper.service_mapper import map_services; from archdoc.mapper.endpoint_mapper import map_endpoints; from archdoc.linker.endpoint_service_linker import link_endpoints_to_services; cfg=load_config(__import__('pathlib').Path('archdoc.yml')); facts=load_raw_facts(cfg.output.raw_facts); services=map_services(facts,cfg); endpoints=map_endpoints(facts,cfg); links=link_endpoints_to_services(facts,endpoints,services); print(len(services), sum(len(s.operations) for s in services), len(endpoints), len(links))"
```

Result:

```text
83 558 730 428
```

`archdoc map -c archdoc.yml` was also attempted, but writing the configured
`output.catalog_dir` failed because it resolves to `..\docs\architecture\...`,
outside the current writable workspace root. The generator logic completed far
enough to reach catalog writing; no config path was changed in this slice.
