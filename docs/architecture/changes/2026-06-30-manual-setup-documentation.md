# Manual Setup Documentation

## Context

The repository explained the Archdoc architecture and Docker deployment, but did
not have a clear manual setup path for installing the local `archdoc` Python
package. This made it unclear how to get the CLI available outside Docker.

## Change

Added a manual setup guide:

- `docs/setup.md`

The guide covers:

- Python version requirements
- creating a local virtual environment
- installing `archdoc` in editable mode with `pip install -e ./archdoc`
- verifying the CLI
- running `scan`, `map`, and `export-schemas`
- running the `unittest` test harness
- optionally running the FastAPI review backend
- optionally running the Docusaurus site
- common setup problems such as missing Utilis source root or missing generated JSON

Linked the guide from:

- root `README.md`
- `docs/architecture/README.md`

## Architecture Impact

No runtime architecture changed. This improves onboarding and makes the manual
local development path explicit alongside the existing Docker deployment path.

## Verification

Reviewed the new documentation links and commands for consistency with the
current package layout:

- local package path: `./archdoc`
- CLI script: `archdoc = archdoc.cli:app`
- config path: `archdoc.yml`
- backend module: `ui_backend.app.main:app`
- test path: `archdoc/tests`
