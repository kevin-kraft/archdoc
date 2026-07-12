# archdoc — deterministic architecture documentation for Python

`archdoc` scans Python source code, extracts syntax-level facts through the
standard-library AST, maps configurable architecture concepts, and writes
stable JSON artifacts for documentation and review tooling.

The project is developed publicly at
[kevin-kraft/archdoc](https://github.com/kevin-kraft/archdoc). The repository
also contains the architecture visualization and review application.

## Design goals

- deterministic output for an unchanged source tree and configuration
- static analysis without importing or executing the analyzed application
- explicit, project-specific mapping rules instead of hidden inference
- stable source references and identifiers for downstream tooling
- replaceable generated data kept separate from manual review state

`archdoc` is rule-based. It documents evidence found in source code; it does
not claim to prove runtime behavior or business meaning.

## Installation

`archdoc` requires Python 3.11 or newer.

```bash
python -m pip install archdoc
```

For development directly from the repository:

```bash
python -m pip install -e .
```

## Quick start

Create a starter configuration in the project that should be analyzed:

```bash
archdoc init
```

This creates `archdoc.yml` in the current directory. Existing files are not
overwritten unless `--force` is supplied:

```bash
archdoc init --output config/archdoc.yml
archdoc init --force
```

Adjust `project.name` and `project.source_root`, then run:

```bash
archdoc scan -c archdoc.yml
archdoc map -c archdoc.yml
```

The documented starter configuration is available as
[archdoc.example.yml](archdoc.example.yml). The same template is included in
the installed Python package, so `archdoc init` also works after installation
from a wheel.

## Configuration

All paths are resolved relative to the configuration file and
`project.root`. The main sections are:

- `project`: project name, project root, and Python source root
- `scan`: included and excluded file patterns
- `output`: destinations for raw facts, catalogs, and schemas
- `mapping`: rules for services, endpoints, actions, entities, and workers
- `naming`: templates for stable architecture identifiers

Minimal example:

```yaml
project:
  name: example-backend
  root: .
  source_root: app

scan:
  include:
    - "**/*.py"
  exclude:
    - "**/.venv/**"
    - "**/migrations/**"
    - "**/tests/**"

output:
  raw_facts: .archdoc/raw_code_facts.json
  catalog_dir: .archdoc/catalog
  schema_dir: .archdoc/schemas
```

Mapping behavior is configurable because naming conventions and project
layouts differ between Python backends. The generated template documents the
available service, endpoint, entity, worker, and operation-link sections.

## Pipeline

### Scan

`archdoc scan`:

1. loads and validates the YAML configuration;
2. discovers matching Python files in a stable order;
3. parses each file with `ast.parse()`;
4. extracts imports, classes, functions, methods, decorators, calls,
   assignments, and architecture signals;
5. writes the raw facts JSON artifact.

### Map

`archdoc map`:

1. loads the raw facts;
2. maps configured services and their operations;
3. maps route-decorated endpoint functions;
4. links endpoints to detected service operations;
5. maps architecture actions and operation dependencies;
6. validates the resulting catalog;
7. writes JSON artifacts for downstream consumers.

### Export schemas

```bash
archdoc export-schemas -c archdoc.yml
```

This exports JSON Schemas for consumers that need an explicit contract for the
generated artifacts.

## Detection model

Services are detected through configurable source paths, class suffixes, and
method rules. Endpoints are detected through route decorators and configured
router paths. Links are inferred from parameters, assignments, object
construction, and call shapes.

These rules deliberately favor traceability and reproducibility over opaque
semantic guesses. Dynamic dispatch, runtime registration, metaprogramming, and
unconventional project layouts may require adjusted configuration or manual
review.

## Source layout

Important implementation entry points:

- [CLI](src/archdoc/cli.py)
- [configuration models](src/archdoc/config/models.py)
- [configuration loader](src/archdoc/config/loader.py)
- [Python scanner](src/archdoc/scanner/python_scanner.py)
- [service mapper](src/archdoc/mapper/service_mapper.py)
- [endpoint mapper](src/archdoc/mapper/endpoint_mapper.py)
- [endpoint-service linker](src/archdoc/linker/endpoint_service_linker.py)
- [catalog validator](src/archdoc/validator/catalog_validator.py)
- [tests](tests/README.md)

## License

Copyright © Kevin Kraft. Licensed under the
[Apache License 2.0](LICENSE).
