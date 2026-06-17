# Docstring Inspector Mapping

## Context

The service graph inspector showed structural metadata, but class-level service
documentation and full method docstrings were not visible enough for review.

## Change

The scanner now captures class docstrings in `ClassFact`. The service mapper
copies class docstrings into `ServiceCatalogItem` as:

- `description`: first non-empty docstring line
- `docstring`: full class docstring

Operation catalog items already carry method docstrings; the inspector now shows
the full method docstring in addition to the short `description` field.

The service graph inspector displays:

- service class description
- service class docstring
- operation method description
- operation method docstring

## Design Rationale

Docstrings are generated source facts, not review overlays. They belong in the
deterministic catalog because they explain what the code currently claims to do.
Human review notes remain in the overlay layer.

## Verification

- Python compile for scanner, facts, catalog, and service mapper
- `archdoc scan -c archdoc.yml`
- `archdoc map -c archdoc.yml`
- `archdoc export-schemas -c archdoc.yml`
- forced SQLite generated import
- verified generated catalog contains service and operation docstrings
- `npm run typecheck`
