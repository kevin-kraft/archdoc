# Archdoc - Documentation Generator for Python Backends

This repository contains the technical architecture documentation pipeline for
the Utilis Python backend. It consists of three deliberately separated parts:

1. `archdoc` scans Python source code and generates deterministic architecture
   facts and JSON catalogs.
2. `ui_backend` imports the generated data into SQLite and provides review APIs.
3. `site` renders catalogs, dependency graphs, validation results, and
   user-story traces in Docusaurus.

Generated architecture data is replaceable. Human review state is stored
separately in SQLite and in the review overlay, ensuring that a new generator
run does not overwrite manual decisions.

## Quick Start With Docker

### Requirements

* Docker Desktop or Docker Engine with Docker Compose v2
* Generated catalog files in `site/static/archdoc`

From the repository root, build and start the review backend and documentation
site:

```bash
docker compose up --build -d
```

Open:

* Documentation and review UI: http://localhost:8088
* Backend health endpoint through nginx: http://localhost:8088/health

Check the running containers or follow their logs:

```bash
docker compose ps
docker compose logs -f
```

Stop the application without deleting review data:

```bash
docker compose down
```

The named Docker volume `archdoc-review-data` stores the SQLite database and
review overlay.

The following command also deletes that review state and should only be used
when a complete reset is intended:

```bash
docker compose down -v
```

The Docker stack displays the generated catalog that was packaged into the
container images during the build. It does not scan the Utilis source tree when
the containers start.

After generating or updating the architecture catalog with `archdoc map`, the
Docker images must therefore be rebuilt:

```bash
docker compose up --build -d
```

Without rebuilding the images, the documentation UI may continue to display the
previously generated catalog.

## Generate a Fresh Catalog

Generation requires Python 3.11 or newer and access to the Utilis backend
source.

The default `archdoc.yml` is located in this repository and expects the Utilis
backend source at:

```text
../api/app
```

The configuration assumes the following directory structure:

```text
utilis/
├── api/
│   └── app/
└── archdoc/
    ├── archdoc.yml
    ├── ui_backend/
    ├── site/
    └── docs/
```

For another Python backend, generate a starter configuration with:

```bash
archdoc init
```

Then adjust `project.root`, `project.source_root`, mapping rules, and output
paths in the generated `archdoc.yml`.

A documented example configuration is also available at:

```text
archdoc/archdoc.example.yml
```

## Install Archdoc From PyPI

For normal use, install the published Python package:

### Windows PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install archdoc
```

### macOS / Linux

```bash
python3 -m venv .venv
./.venv/bin/python -m pip install --upgrade pip
./.venv/bin/python -m pip install archdoc
```

Confirm that the command is available:

### Windows PowerShell

```powershell
.\.venv\Scripts\archdoc.exe --help
```

### macOS / Linux

```bash
./.venv/bin/archdoc --help
```

## Run the Generation Pipeline

Run all commands from the repository root containing `archdoc.yml`.

### Windows PowerShell

```powershell
.\.venv\Scripts\archdoc.exe scan -c archdoc.yml
.\.venv\Scripts\archdoc.exe map -c archdoc.yml
.\.venv\Scripts\archdoc.exe export-schemas -c archdoc.yml
```

### macOS / Linux

```bash
./.venv/bin/archdoc scan -c archdoc.yml
./.venv/bin/archdoc map -c archdoc.yml
./.venv/bin/archdoc export-schemas -c archdoc.yml
```

The commands perform the following steps:

* `scan` extracts deterministic architecture facts from the Python source tree.
* `map` creates the architecture catalog, links endpoints and services, and
  generates validation and frontend data.
* `export-schemas` exports the JSON schemas used by the generated artifacts.

The pipeline updates:

* raw AST facts,
* generated catalog JSON,
* validation output,
* Docusaurus static JSON,
* JSON schemas.

After running `map`, rebuild the Docker containers so the updated generated
catalog is copied into the images:

```bash
docker compose up --build -d
```

## Local Archdoc Package Development

Use an editable installation only when modifying the `archdoc` Python package
itself.

### Windows PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -e .\archdoc
```

### macOS / Linux

```bash
python3 -m venv .venv
./.venv/bin/python -m pip install --upgrade pip
./.venv/bin/python -m pip install -e ./archdoc
```

The generation commands remain the same:

### Windows PowerShell

```powershell
.\.venv\Scripts\archdoc.exe scan -c archdoc.yml
.\.venv\Scripts\archdoc.exe map -c archdoc.yml
.\.venv\Scripts\archdoc.exe export-schemas -c archdoc.yml
docker compose up --build -d
```

### macOS / Linux

```bash
./.venv/bin/archdoc scan -c archdoc.yml
./.venv/bin/archdoc map -c archdoc.yml
./.venv/bin/archdoc export-schemas -c archdoc.yml
docker compose up --build -d
```

## Recommended Update Workflow

When the Utilis backend changes, use the following workflow:

```text
1. Update or pull the backend source code.
2. Run `archdoc scan`.
3. Run `archdoc map`.
4. Run `archdoc export-schemas` when schemas have changed.
5. Rebuild the Docker images.
6. Open the review UI and inspect the updated catalog.
```

Example:

```bash
archdoc scan -c archdoc.yml
archdoc map -c archdoc.yml
archdoc export-schemas -c archdoc.yml
docker compose up --build -d
```

If `archdoc` is installed inside a virtual environment, use the corresponding
executable path shown in the previous sections.

## Manual Development Setup

For a full local setup with a separate generator, FastAPI backend, Docusaurus
development server, tests, and troubleshooting, see
[docs/setup.md](docs/setup.md).

## Documentation Map

* [Architecture and ownership boundaries](docs/architecture/README.md)
* [High-level system overview](docs/architecture/high-level-overview.md)
* [German high-level overview](docs/architecture/high-level-overview.de.md)
* [Archdoc package details](archdoc/README.md)
* [Architecture change history](docs/architecture/changes)

## Repository Layout

```text
archdoc/          Python package containing the scanner, mapper, linker,
                  validator, exporter, and CLI
ui_backend/       FastAPI review API and SQLite read model
site/             Docusaurus review frontend
docs/             Architecture documentation, overlays, and generated data
archdoc.yml       Utilis-specific scanning and mapping configuration
docker-compose.yml
```

The generator is intentionally independent of the review application.

Do not write manual review information directly into generated catalog files.
Use the review UI and overlay layer instead, because generated files may be
replaced during the next `scan` or `map` run.
