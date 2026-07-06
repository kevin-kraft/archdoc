# Class Resource Profile DB Origin Validation

## Context

The validator warning `service_db_session_not_initialized` was misleading for
Utilis service classes. It only checked whether the same service class contained
a direct `self.db = ...` assignment. That produced false positives for valid
object models where `self.db` is provided by a base class, forwarded through
`super().__init__(db)`, or exposed through a property-like class resource.

The concrete symptom was a method such as:

```python
async def complete_credential_token(self, token: str, password: str) -> dict[str, Any]:
    result = await self.db.execute(...)
```

Archdoc could see the `self.db.execute(...)` call, but the validator could not
explain where `self.db` came from unless the current class had a direct
assignment.

## Change

Added a generalized class resource profiling layer:

- `archdoc/src/archdoc/validator/class_resource_profile.py`

The profile records origins for instance resources such as `self.db`. It now
recognizes:

- direct instance assignments like `self.db = db`
- constructor parameter assignments
- resource origins inherited from base classes known to the scanner
- `super().__init__(db)` forwarding for session-like constructor parameters
- property methods such as `@property def db(...)`

The catalog validator now uses `ClassResourceProfile` instead of directly
searching for `assignment.target == "self.db"`.

The warning code was renamed from:

- `service_db_session_not_initialized`

To the more accurate:

- `service_db_session_origin_unknown`

This avoids claiming that the session is definitely not initialized. The new
warning means only that Archdoc could not resolve a class resource origin for
`self.db`.

## Architecture Impact

This introduces a reusable object/resource analysis concept instead of a
single-purpose DB-session heuristic. Future validators can reuse the same
profile to reason about other object-owned resources such as workers, clients,
unit-of-work objects, cache handles, or provider adapters.

The validator remains conservative: it does not execute code and does not prove
runtime correctness. It only records static evidence for resource origins.

## Tradeoffs

`super().__init__(db)` recognition is intentionally heuristic for now. If the
base class is available in scanned facts, inherited origins provide stronger
evidence. If the base class is external or not scanned, forwarding a parameter
named `db`, `session`, or `async_session` is treated as enough evidence to avoid
the misleading warning.

This reduces false positives, but it may hide a real issue if a class forwards a
DB-like parameter to a parent that does not actually initialize `self.db`. A
future improvement could distinguish high-confidence inherited origins from
medium-confidence forwarded origins in the UI.

## Verification

Added regression coverage to `archdoc/tests/test_archdoc_pipeline.py`:

- inherited `self.db` origin from a base class does not warn
- `super().__init__(db: AsyncSession)` forwarding does not warn
- unresolved `self.db.execute(...)` emits `service_db_session_origin_unknown`

Ran from the repository root:

```bash
.\.venv\Scripts\python.exe -m unittest discover -s archdoc\tests -v
.\.venv\Scripts\python.exe -m py_compile archdoc\src\archdoc\validator\class_resource_profile.py archdoc\src\archdoc\validator\catalog_validator.py archdoc\tests\test_archdoc_pipeline.py
```

Result:

- 7 tests passed
- Python compile check passed
