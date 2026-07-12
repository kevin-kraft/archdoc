# Archdoc for Utilis

This repository contains the technical architecture documentation pipeline for
the Utilis Python backend. It consists of three deliberately separated parts:

1. `archdoc` scans Python source code and generates deterministic JSON catalogs.
2. `ui_backend` imports the generated data into SQLite and provides review APIs.
3. `site` renders catalogs, graphs, validation results, and user-story traces in
   Docusaurus.

Generated architecture data is replaceable. Human review state is stored
separately in SQLite and in the review overlay so a new generator run does not
overwrite manual decisions.

## Quick Start With Docker

### Requirements

- Docker Desktop or Docker Engine with Docker Compose v2
- generated files in `site/static/archdoc` (included in this checkout)

From the repository root, build and start the review backend and documentation
site:

```bash
docker compose up --build -d
```

Open:

- documentation and review UI: <http://localhost:8088>
- backend health through nginx: <http://localhost:8088/health>

Check the containers or follow their logs:

```bash
docker compose ps
docker compose logs -f
```

Stop the application without deleting review data:

```bash
docker compose down
```

The named Docker volume `archdoc-review-data` stores the SQLite database and
review overlay. `docker compose down -v` deletes that review state and should
only be used when a complete reset is intended.

The Docker stack displays the generated catalog packaged into the images. It
does not scan the Utilis source tree at container startup. After regenerating
the catalog locally, rebuild the images with `docker compose up --build -d`.

## Generate A Fresh Catalog

Generation requires Python 3.11 or newer and access to the Utilis backend source.
The default `archdoc.yml` expects this repository next to the backend and resolves
the source directory as `../api/app`.

For a different Python backend, generate a generic starter configuration with
`archdoc init` and adjust `project.source_root`. A documented copy is available
at `archdoc/archdoc.example.yml`.

### Windows PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -e .\archdoc
.\.venv\Scripts\archdoc.exe scan -c archdoc.yml
.\.venv\Scripts\archdoc.exe map -c archdoc.yml
.\.venv\Scripts\archdoc.exe export-schemas -c archdoc.yml
```

### macOS / Linux

```bash
python3 -m venv .venv
./.venv/bin/python -m pip install --upgrade pip
./.venv/bin/python -m pip install -e ./archdoc
./.venv/bin/archdoc scan -c archdoc.yml
./.venv/bin/archdoc map -c archdoc.yml
./.venv/bin/archdoc export-schemas -c archdoc.yml
```

These commands update raw AST facts, catalog JSON, validation output,
Docusaurus static JSON, and JSON schemas. Restart the local backend or rebuild
the Docker images after generation so the UI imports the new snapshot.

## Manual Development Setup

For a full local setup with separate generator, FastAPI backend, Docusaurus
development server, tests, and troubleshooting, see [docs/setup.md](docs/setup.md).

## Documentation Map

- [Architecture and ownership boundaries](docs/architecture/README.md)
- [High-level system overview](docs/architecture/high-level-overview.md)
- [German high-level overview](docs/architecture/high-level-overview.de.md)
- [Archdoc package details](archdoc/README.md)
- [Architecture change history](docs/architecture/changes)

## Repository Layout

```text
archdoc/          deterministic scanner, mapper, linker, validator, and exporter
ui_backend/       FastAPI review API and SQLite read model
site/             Docusaurus review frontend
docs/             architecture docs, user stories, overlays, and generated data
archdoc.yml       Utilis-specific scan and mapping configuration
docker-compose.yml
```

The generator is intentionally independent of the review application. Do not
write manual review information into generated catalog files; use the review UI
and overlay layer instead.
