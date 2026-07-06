# Archdoc Test Harness

These tests use small synthetic Python projects created in temporary directories.
They are intentionally focused on generator behavior rather than the full Utilis
codebase, so syntax and mapping regressions can be reproduced quickly.

Run from the repository root:

```bash
python -m unittest discover -s archdoc/tests -v
```

The harness currently covers:

- modern Python function syntax and annotations
- nested local helper functions not leaking calls into the outer scope
- FastAPI router prefix and include-router prefix mapping
- endpoint-to-service linking
- database action and transaction detection
- deterministic duplicate catalog ID resolution
