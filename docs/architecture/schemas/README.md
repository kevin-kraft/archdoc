# Archdoc JSON Schemas

This directory is the configured output target for generated JSON Schema files.

Generate or refresh schemas with:

```bash
archdoc export-schemas -c archdoc.yml
```

The schemas describe the deterministic archdoc JSON contracts and are intended
for separate tooling such as a review API, editor UI, or validator workflow.
