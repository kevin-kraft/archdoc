# archdoc — deterministic architecture documentation generator

This package is a deterministic documentation generator for Python backends.
It does not infer business meaning from runtime behavior. Instead, it reads the source tree, extracts syntax-level facts from Python AST, maps those facts to service and endpoint catalog records, validates the result, and writes stable JSON artifacts for downstream docs.

For the current end-to-end architecture, including the SQLite UI backend,
overlay layer, and Docusaurus review frontend, see:

- [../docs/architecture/README.md](../docs/architecture/README.md)

## Scope

The implementation in this repository is centered on these files:

- [utilis/docs-site-docasaurus/archdoc/src/archdoc/cli.py](utilis/docs-site-docasaurus/archdoc/src/archdoc/cli.py)
- [utilis/docs-site-docasaurus/archdoc/src/archdoc/scanner/python_scanner.py](utilis/docs-site-docasaurus/archdoc/src/archdoc/scanner/python_scanner.py)
- [utilis/docs-site-docasaurus/archdoc/src/archdoc/mapper/service_mapper.py](utilis/docs-site-docasaurus/archdoc/src/archdoc/mapper/service_mapper.py)
- [utilis/docs-site-docasaurus/archdoc/src/archdoc/mapper/endpoint_mapper.py](utilis/docs-site-docasaurus/archdoc/src/archdoc/mapper/endpoint_mapper.py)
- [utilis/docs-site-docasaurus/archdoc/src/archdoc/linker/endpoint_service_linker.py](utilis/docs-site-docasaurus/archdoc/src/archdoc/linker/endpoint_service_linker.py)
- [utilis/docs-site-docasaurus/archdoc/src/archdoc/config/loader.py](utilis/docs-site-docasaurus/archdoc/src/archdoc/config/loader.py)
- [utilis/docs-site-docasaurus/archdoc/src/archdoc/facts/writer.py](utilis/docs-site-docasaurus/archdoc/src/archdoc/facts/writer.py)
- [utilis/docs-site-docasaurus/archdoc/src/archdoc/exporter/docusaurus_exporter.py](utilis/docs-site-docasaurus/archdoc/src/archdoc/exporter/docusaurus_exporter.py)

## Configuration source

The current generator configuration is defined in:

- [utilis/docs-site-docasaurus/archdoc.yml](utilis/docs-site-docasaurus/archdoc.yml)

Observed defaults from that file:

- project name: utilis
- source root: api/app
- include pattern: **/*.py
- exclude patterns: __pycache__, .venv, venv, migrations, tests
- raw facts output: docs-site-docasaurus/docs/architecture/generated_raw/raw_code_facts.json
- catalog output: ../docs/architecture/catalog/generated
- Docusaurus static export: docs-site-docasaurus/site/static/archdoc

## Pipeline

### 1. Scan phase

Command: `archdoc scan -c archdoc.yml`

What happens:

1. Load YAML config.
2. Resolve the project root and source root.
3. Find Python files with `source_root.glob(include_pattern)`.
4. Exclude files matching the configured glob patterns.
5. Parse each file with Python `ast.parse()`.
6. Extract syntax-level facts:
   - imports
   - classes
   - top-level functions
   - calls
   - assignments
   - decorators
   - route-like signals
   - service/model-like signals
7. Write the raw facts JSON document.

Deterministic properties of this phase:

- file discovery is sorted before processing (`return sorted(filtered)`)
- AST traversal is deterministic for a given source tree
- output JSON is written with `indent=2` and `ensure_ascii=False`

### 2. Map phase

Command: `archdoc map -c archdoc.yml`

What happens:

1. Load the raw facts JSON produced in phase 1.
2. Build service catalog entries from classes that match configured service paths and suffixes.
3. Build endpoint catalog entries from route-decorated functions.
4. Link endpoints to inferred service operations.
5. Validate the generated catalog.
6. Optionally export Docusaurus static JSON data.

## What is considered a service

The current service mapping rules are visible in [utilis/docs-site-docasaurus/archdoc/src/archdoc/mapper/service_mapper.py](utilis/docs-site-docasaurus/archdoc/src/archdoc/mapper/service_mapper.py):

- a file must be under a configured service path such as `services` or `app/services`
- the class name must end with a configured suffix such as `Service`
- public methods are treated as operations by default
- methods matching configured ignore lists are excluded
- service IDs are derived from the class name and path domain

This is a heuristic rule set, not a full semantic analysis of the codebase.

## What is considered an endpoint

The current endpoint mapping rules are visible in [utilis/docs-site-docasaurus/archdoc/src/archdoc/mapper/endpoint_mapper.py](utilis/docs-site-docasaurus/archdoc/src/archdoc/mapper/endpoint_mapper.py):

- a file must be under a configured endpoint path such as `routers` or `app/routers`
- the function must contain a FastAPI-style route signal such as `@router.get("/x")`
- the endpoint ID is generated from module, HTTP method, path, and function name
- the implementation kind is classified from call patterns and assignments

## How service-to-endpoint links are inferred

The linking logic in [utilis/docs-site-docasaurus/archdoc/src/archdoc/linker/endpoint_service_linker.py](utilis/docs-site-docasaurus/archdoc/src/archdoc/linker/endpoint_service_linker.py) uses a rule-based matcher:

- infer variable types from parameters and assignments
- match top-level meaningful calls to known service operations
- fall back to direct class-style calls such as `AuditService.log_event(...)`
- prefer inherited service classes when available

This produces stable links but relies on naming and call-shape heuristics.

## Generated artifacts

The current generated outputs under the repository are:

- raw facts: [utilis/docs-site-docasaurus/docs/architecture/generated_raw/raw_code_facts.json](utilis/docs-site-docasaurus/docs/architecture/generated_raw/raw_code_facts.json)
- service catalog: [utilis/docs-site-docasaurus/docs/architecture/catalog/generated/services](utilis/docs-site-docasaurus/docs/architecture/catalog/generated/services)
- endpoint catalog: [utilis/docs-site-docasaurus/docs/architecture/catalog/generated/endpoints](utilis/docs-site-docasaurus/docs/architecture/catalog/generated/endpoints)
- links: [utilis/docs-site-docasaurus/docs/architecture/catalog/generated/links](utilis/docs-site-docasaurus/docs/architecture/catalog/generated/links)
- validation report: [utilis/docs-site-docasaurus/docs/architecture/catalog/generated/reports/validation_report.json](utilis/docs-site-docasaurus/docs/architecture/catalog/generated/reports/validation_report.json)

## Manual overlay layer

Generated catalog files are treated as read-only output. Manual review state,
labels, ownership, notes, and future BPMN/user-story links live in separate
overlay JSON files.

The overlay schema is defined in:

- [utilis/docs-site-docasaurus/archdoc/src/archdoc/overlay/models.py](utilis/docs-site-docasaurus/archdoc/src/archdoc/overlay/models.py)

The configured overlay directory is:

- [utilis/docs-site-docasaurus/docs/architecture/overlays](utilis/docs-site-docasaurus/docs/architecture/overlays)

Example overlay document:

- [utilis/docs-site-docasaurus/docs/architecture/overlays/review-overlay.example.json](utilis/docs-site-docasaurus/docs/architecture/overlays/review-overlay.example.json)

Overlay entries target generated catalog items by stable ID and target type.
Supported target types include services, operations, endpoints,
endpoint-service links, validation issues, user stories, BPMN processes, and
BPMN tasks. This keeps deterministic generated output separate from human
review decisions.

## JSON schema export

`archdoc` can export JSON Schema files for the generated artifacts and overlay
contract without running UI, backend, or database code.

Command:

```bash
archdoc export-schemas -c archdoc.yml
```

Configured output directory:

- [utilis/docs-site-docasaurus/docs/architecture/schemas](utilis/docs-site-docasaurus/docs/architecture/schemas)

The exported schemas are intended as the contract for a separate review/backend
application. `scan` and `map` do not read or write review overlays, and the
schema export stays an explicit command.

The current validation report in this checkout shows:

- 83 services
- 558 operations
- 730 endpoints
- 428 endpoint-service links
- 363 linked endpoints
- 367 unlinked endpoints
- 248 unreferenced operations
- 6 errors
- 247 warnings
- 370 infos

This snapshot is useful as a deterministic baseline for the current generator run, but it is not a proof that the mapping is semantically complete.

## Known uncertainty and caveats

The following items are intentionally marked as uncertain because the code relies on heuristics rather than a formal specification:

1. Service detection is name-based (`...Service`) and path-based. It may miss classes that use different naming or live outside the configured paths. [UNCERTAIN]
2. Endpoint detection depends on route decorators and signal extraction. It may not catch non-standard routing patterns. [UNCERTAIN]
3. Service-to-endpoint links are inferred from call patterns and variable type hints. They may be incomplete when the call shape is dynamic or indirect. [UNCERTAIN]
4. The current implementation treats duplicate IDs as validation errors, but the exact business meaning of those duplicates is not encoded in the generator itself. [UNCERTAIN]
5. The implementation classifies endpoint kinds from simple rules such as DB calls, external calls, and single-helper delegation. These are heuristic classifications, not authoritative architecture labels. [UNCERTAIN]

## Deterministic summary

If the goal is reproducibility, the most important deterministic properties are:

- explicit YAML configuration
- AST-based extraction rather than runtime introspection
- sorted file discovery
- stable sorting of service and endpoint records
- explicit JSON writer with fixed formatting
- validation report generated from the same catalog data

For that reason, this generator is best described as a deterministic, rule-based documentation pipeline rather than a fully semantic architecture model.
