# User Story Trace Compact Details

## Context

The user-story trace graph rendered session-level database transactions as graph
nodes. Type usage was already treated as non-topological detail in the service
action graph, and the trace view should follow the same separation of concerns.
The service-action operation inspector also had the more complete review shape:
`Type Usage` plus `Detected Method Flow`.

## Change

The user-story trace graph now keeps `database_transaction` and `type_usage`
nodes out of the visible path topology. The trace payload remains unchanged, but
those compact detail nodes are collected from the existing edges and rendered in
the selected node inspector.

The service-action graph and user-story trace now share the operation action
detail components for action labels, type usage, query details, source labels,
and method-flow rendering.

The trace graph node selection now expands from essential story, endpoint,
service, and operation nodes over visible edges instead of preselecting the first
N ordered nodes. After expansion it prunes selected nodes that have no visible
edge, which prevents disconnected floating graph nodes.

Operation dependency targets now also attach their generated operation actions
and get a service-to-operation `owns` edge. This keeps trace detail views
consistent for operations reached through `calls_service`, such as
`get_financial_stats`.

## Design Rationale

Session commits, flushes, rollbacks, refreshes, and type references are useful
review context, but they are not independent architecture hops. Keeping them in
the inspector makes the graph easier to scan while preserving the generated
facts for detailed review.

The shared inspector components keep the service graph as the source of the UI
pattern and avoid a second, weaker trace-specific rendering path.

Dependency operation actions are attached in the trace backend instead of being
patched in the frontend because the UI should not query hidden catalog context
for selected graph nodes. The trace API remains the complete read model for the
trace view.

## Verification

- `npm run typecheck`
- `.venv\\Scripts\\python.exe -m py_compile ui_backend\\app\\storage.py`
- local trace selection simulation over imported user-story traces returned
  `floating_visible_nodes 0`
- `finance.financial.operation.get_financial_stats` trace check returns 6
  `database_action` details and 1 `type_usage` detail for linked finance stories