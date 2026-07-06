# Archdoc Manual Setup

This guide explains how to install and run the local `archdoc` package without
Docker.

## Requirements

- Python 3.11 or newer
- A checkout that contains this docs repository
- For a full Utilis scan: access to the Utilis backend source expected by
  `archdoc.yml`

The default `archdoc.yml` assumes this repository lives next to the Utilis
backend source and resolves:

- project root: `..`
- source root: `../api/app`

If you only have the standalone docs repository, installation still works, but
`archdoc scan -c archdoc.yml` will fail until the configured source root exists
or the config points to another Python project.

## 1. Create A Virtual Environment

From the repository root:

### Windows PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
```

### macOS / Linux

```bash
python3 -m venv .venv
./.venv/bin/python -m pip install --upgrade pip
```

## 2. Install The Archdoc Package

Install `archdoc` in editable mode from the local package directory:

### Windows PowerShell

```powershell
.\.venv\Scripts\python.exe -m pip install -e .\archdoc
```

### macOS / Linux

```bash
./.venv/bin/python -m pip install -e ./archdoc
```

Editable mode keeps the CLI pointed at your working tree, so code changes under
`archdoc/src/archdoc` are picked up without reinstalling.

## 3. Verify The CLI

### Windows PowerShell

```powershell
.\.venv\Scripts\archdoc.exe --help
```

### macOS / Linux

```bash
./.venv/bin/archdoc --help
```

Expected commands include:

- `scan`
- `map`
- `export-schemas`

If the executable script is not available, run through Python module resolution:

### Windows PowerShell

```powershell
.\.venv\Scripts\python.exe -m archdoc.cli --help
```

### macOS / Linux

```bash
./.venv/bin/python -m archdoc.cli --help
```

## 4. Generate Architecture Data

Run these from the repository root after confirming `archdoc.yml` points to a
valid source tree.

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

The generator writes replaceable output to the configured locations, including:

- raw facts
- generated catalog JSON
- validation report
- Docusaurus static JSON
- JSON schemas

Generated files are not manual review state. Review state belongs in overlays
and the SQLite review database.

## 5. Run The Test Harness

The current test harness uses Python's standard `unittest`, so no separate
`pytest` install is required.

### Windows PowerShell

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s archdoc\tests -v
```

### macOS / Linux

```bash
./.venv/bin/python -m unittest discover -s archdoc/tests -v
```

## 6. Optional: Run The Review Backend

Install backend dependencies into the same virtual environment:

### Windows PowerShell

```powershell
.\.venv\Scripts\python.exe -m pip install -r .\ui_backend\requirements.txt
.\.venv\Scripts\python.exe -m uvicorn ui_backend.app.main:app --reload --port 8010
```

### macOS / Linux

```bash
./.venv/bin/python -m pip install -r ./ui_backend/requirements.txt
./.venv/bin/python -m uvicorn ui_backend.app.main:app --reload --port 8010
```

Health check:

```text
http://localhost:8010/health
```

The backend imports generated JSON from `site/static/archdoc` by default and
stores review state in:

- `docs/architecture/archdoc-review.sqlite3`
- `docs/architecture/overlays/review-overlay.json`

## 7. Optional: Run The Docusaurus Site

From `site`:

```bash
npm install
npm run start
```

The frontend expects the review backend at `http://localhost:8010` during local
development. If the backend is unavailable, some views can fall back to static
JSON if generated files exist under `site/static/archdoc`.

For Docker deployments, open the site through the published nginx port, for
example `http://localhost:8088`. API calls stay on the same origin and are
proxied from `/api/*` and `/health` to the backend container. The browser does
not need direct access to `http://localhost:8010` in this mode.

## Common Problems

### `Source root does not exist`

`archdoc.yml` points to a source root that is not present. Either place this
repository in the expected Utilis workspace layout or change:

```yaml
project:
  root: ..
  source_root: api/app
```

### `archdoc` Command Not Found

Use the virtual environment executable path directly, for example:

```powershell
.\.venv\Scripts\archdoc.exe --help
```

Or run:

```powershell
.\.venv\Scripts\python.exe -m archdoc.cli --help
```

### Generated Catalog Is Empty In The UI

Run `archdoc scan` and `archdoc map` first, then restart the backend or force a
reimport:

```bash
curl -X POST "http://localhost:8010/api/import/generated?force=true"
```
