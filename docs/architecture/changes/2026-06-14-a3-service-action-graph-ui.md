# A3: Service Action Graph UI

## Context

The architecture action catalog is generated as JSON, but the review backend and
frontend still needed a queryable view for service-centered analysis.

## Change

Added SQLite ingestion for generated architecture actions:

- `generated_actions`
- direct query columns for kind, action, access, owner, call, resource, entity,
  and source
- schema version `3`
- `architecture_actions.json` included in generated source hashing

Added backend graph route:

- `GET /api/graph/services`

The route returns:

- service summaries
- selected service
- operations owned by the service
- endpoints linked to those operations
- endpoint-service links
- actions owned by those operations

Added Docusaurus generated-docs page:

- `architecture/generated/service-actions`

The page uses `@xyflow/react` and `elkjs` to render a service-centered graph.

## Graph Model

The graph currently displays:

- service node
- operation nodes
- linked endpoint nodes
- grouped action nodes
- detected external targets for audit, worker, and external actions

Actions are grouped by owner, kind, and resource/call label to keep large
services readable.

## Follow-Up

The next backend step is to add explicit service-to-service action detection so
the graph can show internal service dependencies beyond endpoint links and
worker/external targets.
