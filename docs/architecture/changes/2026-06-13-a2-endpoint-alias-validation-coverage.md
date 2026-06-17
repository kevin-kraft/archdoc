# A2: Endpoint Alias Validation Coverage

## Context

Some FastAPI routes are represented twice in the catalog:

- the local router decorator path
- the effective path after `include_router(..., prefix=...)`

The linker resolves the effective prefixed endpoint, but the local decorator
endpoint used to remain as `endpoint_service_candidate_not_linked`.

## Change

The validator now treats endpoint variants with the same `qualified_name` as
covered when any sibling route is linked to a service operation.

This affects validation only:

- no endpoint-service link is duplicated
- generated endpoint items remain visible
- alias routes no longer create false service-candidate warnings
- `linked_endpoints` and `unlinked_endpoints` now use coverage semantics

## Result

`endpoint_service_candidate_not_linked` dropped from 23 to 1 in the current
Utilis catalog. The remaining issue is a real unresolved service-link candidate:

- `routers.participants.get.param-participant-id.profile.completion.get-profile-completion`
