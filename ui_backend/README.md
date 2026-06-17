# Archdoc UI Backend

Small FastAPI backend for reviewing generated archdoc catalogs.

For the current end-to-end architecture, including generator boundaries,
SQLite import behavior, overlays, and frontend structure, see:

- [../docs/architecture/README.md](../docs/architecture/README.md)

Responsibilities:

- read generated archdoc JSON artifacts
- materialize generated JSON into a local SQLite read model
- read and write manual overlay JSON
- return an effective catalog for editor UIs

Non-goals:

- running `archdoc scan` or `archdoc map`
- mutating generated catalog files
- owning frontend build/deploy

Run locally from `docs-site-docasaurus`:

```bash
python -m pip install -e ./archdoc fastapi uvicorn
uvicorn ui_backend.app.main:app --reload --port 8010
```

By default the backend creates:

- `docs/architecture/archdoc-review.sqlite3`
- `docs/architecture/overlays/review-overlay.json`

Generated tables are replaceable import/cache tables. Review tables are
persistent and are not overwritten when generated JSON changes.

Relevant environment variables:

- `ARCHDOC_STATIC_DIR`
- `ARCHDOC_OVERLAY_PATH`
- `ARCHDOC_DB_PATH`

Force a generated JSON reimport without deleting review data:

```bash
curl -X POST "http://localhost:8010/api/import/generated?force=true"
```

The Docusaurus frontend expects the API at `http://localhost:8010` unless
`ARCHDOC_API_BASE_URL` is set on `window` before the app loads.
