# Scanner Scope Regression Test Harness

## Context

Manual Utilis analysis showed that Archdoc still has syntax and recognition
edge cases. One important false-positive class comes from Python AST traversal:
`ast.walk()` descends into nested local functions, lambdas, and classes. That
can attribute calls inside a local helper definition to the outer endpoint or
service method, even when the helper is only defined and never executed.

For endpoint-service linking this is risky because a router function can appear
to call a service operation just because an unused local helper contains that
call.

## Change

Added a lightweight Archdoc test harness under:

- `archdoc/tests`

The harness builds small synthetic Python projects in temporary directories, so
recognition behavior can be tested without depending on the full Utilis source
tree.

Covered cases now include:

- modern Python function syntax and annotations
- async calls and nested SQLAlchemy expressions
- local helper functions not leaking calls or assignments into the outer scope
- FastAPI router prefix and include-router prefix mapping
- endpoint-to-service linking
- database action and transaction detection
- deterministic duplicate service and operation ID resolution

The scanner now walks only the current implementation scope for function call
and assignment extraction. Nested function, class, and lambda bodies are not
counted as part of the outer function body.

Removed noisy debug output from:

- `archdoc/src/archdoc/config/loader.py`
- `archdoc/src/archdoc/mapper/service_mapper.py`

## Architecture Impact

This keeps the scanner closer to its intended responsibility: extracting
syntax-level facts from the code that belongs to the current scope. It reduces
false-positive architecture links while preserving deterministic AST-based
analysis.

The test harness is intentionally small and fixture-driven. New Utilis syntax
or recognition bugs should be added as minimal synthetic fixtures first, then
fixed in the mapper/scanner/linker. This avoids using the full Utilis codebase
as the only regression test.

## Tradeoffs

Nested local functions are no longer represented inside the outer function's
call list. That is the right default for endpoint and service implementation
mapping, but it also means Archdoc does not yet model nested helper functions as
first-class facts. If nested functions become architecturally relevant later,
they should be extracted as separate scoped facts instead of folded into the
outer function.

## Verification

Ran from the repository root:

```bash
.\.venv\Scripts\python.exe -m unittest discover -s archdoc\tests -v
.\.venv\Scripts\python.exe -m py_compile archdoc\src\archdoc\scanner\python_scanner.py archdoc\src\archdoc\config\loader.py archdoc\src\archdoc\mapper\service_mapper.py archdoc\tests\conftest.py archdoc\tests\test_python_scanner.py archdoc\tests\test_archdoc_pipeline.py
```

Result:

- 4 tests passed
- Python compile check passed
