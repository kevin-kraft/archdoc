# A1.3 Validator Signals for Resolved Collisions

Date: 2026-06-13

## Context

The ID resolver makes generated catalog IDs technically unique. That removes
hard errors such as duplicate service IDs or duplicate operation IDs.

However, resolved collisions are still architecture signals. For example, if
two source files both produce a logical `CalendarService`, the generator should
not fail, but reviewers should still see that the architecture has two similar
service candidates.

## Implemented in this Slice

The validator now reports resolved logical ID collisions as non-blocking issues.

New issue codes:

- `resolved_service_logical_id_collision`
- `resolved_operation_logical_id_collision`
- `resolved_endpoint_logical_id_collision`
- `resolved_endpoint_service_link_logical_id_collision`

These are emitted when multiple generated items share the same
`identity.logical_id` but have different resolved `identity.catalog_id` values.

The validator also reports reused service class names across different source
files:

- `service_class_name_reused`

This makes cases like multiple `CalendarService` classes visible even when the
ID formula changes later.

## Severity Policy

- resolved service collision: `info`
- resolved operation collision: `info`
- resolved endpoint collision: `warning`
- resolved endpoint-service link collision: `info`
- reused service class name: `info`

The distinction is intentional:

- technical uniqueness problems remain `error`
- architecture review signals are `info` or `warning`
- endpoint collisions are more suspicious because route identity affects API
  surface semantics

## Files Changed

- `archdoc/src/archdoc/validator/catalog_validator.py`

## Validation Performed

Python compile:

```bash
.venv\Scripts\python.exe -m py_compile archdoc\src\archdoc\validator\catalog_validator.py
```

In-memory pipeline check:

```bash
$env:PYTHONPATH='archdoc/src'; .venv\Scripts\python.exe -c "from pathlib import Path; from collections import Counter; from archdoc.config.loader import load_config; from archdoc.facts.loader import load_raw_facts; from archdoc.mapper.service_mapper import map_services; from archdoc.mapper.endpoint_mapper import map_endpoints; from archdoc.catalog.id_resolver import resolve_catalog_id_collisions, resolve_link_id_collisions; from archdoc.linker.endpoint_service_linker import link_endpoints_to_services; from archdoc.linker.mark_linked_endpoint_implementations import mark_linked_endpoint_implementations; from archdoc.validator.catalog_validator import validate_catalog; cfg=load_config(Path('archdoc.yml')); facts=load_raw_facts(cfg.output.raw_facts); services=map_services(facts,cfg); endpoints=map_endpoints(facts,cfg); services,endpoints=resolve_catalog_id_collisions(services,endpoints); links=resolve_link_id_collisions(link_endpoints_to_services(facts,endpoints,services)); endpoints=mark_linked_endpoint_implementations(endpoints,links); report=validate_catalog(facts,services,endpoints,links); counts=Counter(i.code for i in report.issues); print('validation', report.summary.errors, report.summary.warnings, report.summary.infos); print('new_rules', {k:v for k,v in counts.items() if k.startswith('resolved_') or k=='service_class_name_reused'})"
```

Result:

```text
validation 0 247 382
new_rules {
  'resolved_service_logical_id_collision': 1,
  'resolved_operation_logical_id_collision': 5,
  'service_class_name_reused': 1
}
```

Observed signal:

```text
service_class_name_reused info Service class name is reused across multiple source files: CalendarService
```

## Still Open

Recommended next follow-up:

- expose these validation issue codes as filter presets in the UI
- add stable documentation for validator code taxonomy
- persist validation issue `item_id`, `code`, and `severity` as indexed SQLite
  columns for fast review workflows
