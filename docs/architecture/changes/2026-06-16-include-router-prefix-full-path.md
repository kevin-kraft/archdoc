# Include Router Prefix Full Path Mapping

## Context

Endpoint paths were previously derived from the local route decorator and the
local `APIRouter(prefix=...)` declaration. This covered routers such as
`profile_fields.router`, where the module itself defines
`APIRouter(prefix="/profile-fields")`.

It did not cover routers whose runtime prefix is added in `main.py` through
`target.include_router(..., prefix=...)`. Examples include integrations, jobs,
financial routes, calendar routes, and several admin routes. In those cases the
generated endpoint table could show only the local decorator path such as `/`
or `/google-calendar/auth-url` instead of the runtime path such as
`/integrations/google-calendar/auth-url`.

## Change

Endpoint catalog items now carry three route path fields:

- `path`: the local decorator path, for example `""`, `/`, or `/{id}`
- `router_prefix`: the prefix declared on the local `APIRouter`
- `include_prefix`: the prefix declared where the router is included in
  `main.py`
- `full_path`: the canonical generated path composed from
  `include_prefix + router_prefix + path`

The mapper reads `target.include_router(<module>.router, prefix=...)` calls from
raw scan facts and maps imported router module names back to endpoint modules.
The canonical runtime registration on `app` is used for `full_path`; compatibility
mirrors under `/api`, `/v1`, and `/api/v1` are intentionally not expanded into
separate generated endpoints.

For duplicate local aliases such as:

```python
@router.get("/", response_model=list[ProfileFieldResponse])
@router.get("", response_model=list[ProfileFieldResponse], include_in_schema=False)
```

the generated endpoints can share the same `full_path`, but their source
identities remain distinct because the local decorator path is part of endpoint
identity provenance.

## Frontend and Backend Impact

The SQLite read model stores `include_prefix`, `router_prefix`, and `full_path`
for generated endpoints. User-story endpoint matching checks `full_path` while
retaining fallback behavior for older generated data.

The Docusaurus review UI now prefers `full_path` in:

- API Endpoint Catalog
- Endpoint-Service Interfaces
- User Story catalog links
- Service Action Graph endpoint labels and inspector details

The API Endpoint Catalog still shows local composition detail as secondary
context, for example `include prefix + router prefix + local path`.

## Verification

- `python3 -m py_compile` for changed mapper/catalog/backend modules
- `node node_modules/typescript/bin/tsc`
- `archdoc scan -c archdoc.yml`
- `archdoc map -c archdoc.yml`
- forced `ui_backend` generated import
- verified validation report has `0` errors and no
  `duplicate_identity_source_id` issues
- verified generated examples:
  - `profile_fields.list_fields`: `router_prefix="/profile-fields"`,
    `full_path="/profile-fields"`
  - `integrations.list_integrations`: `include_prefix="/integrations"`,
    `full_path="/integrations"`
  - `integrations.google_calendar_auth_url`:
    `full_path="/integrations/google-calendar/auth-url"`
