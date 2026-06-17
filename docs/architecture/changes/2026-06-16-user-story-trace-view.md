# User Story Trace View

## Context

The user-story demo linked manual story endpoint references to generated
endpoints and service operations, but the review UI still showed the
architecture path as nested cards. It did not provide a compact trace from the
story through endpoint, service, operation, detected actions, and entities.

## Change

The UI backend now exposes a story-specific architecture trace endpoint:

```text
GET /api/user-stories/{story_id}/trace
```

The trace payload contains:

- `story`
- `nodes`
- `edges`
- `unresolved_refs`
- `summary`

The first trace slice is generated from existing read-model data:

- declared user-story endpoint references
- matched generated endpoints
- endpoint-service links
- service and operation catalog records
- operation-owned architecture actions
- entities referenced by action/entity/query metadata
- outgoing operation dependency links

The Docusaurus user-story detail view now loads this trace and renders an
initial review graph section with summary metrics and a horizontally scrollable
node flow.

## Design Notes

This slice intentionally does not add frontend click-trace scanning yet. The
trace starts from declared endpoint references because that data is already
available and deterministic. Frontend action references can be layered in later
as manual story frontmatter or generated frontend scan facts.

The graph rendering is intentionally lightweight in the first slice. It avoids
introducing another React Flow surface before the trace payload shape settles.
The payload is structured so a richer graph renderer can replace the current
flow view later.

## Verification

- `python3 -m py_compile ui_backend/app/main.py ui_backend/app/storage.py`
- `node node_modules/typescript/bin/tsc`
- direct storage check for `read_user_story_trace("US-ADMIN-001")`
- HTTP check for `/api/user-stories/US-ADMIN-001/trace`
- verified the sample trace returns endpoint, service, operation, action, and
  entity nodes with no unresolved endpoint references
