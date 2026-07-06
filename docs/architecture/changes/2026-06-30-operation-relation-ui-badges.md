# Operation Relation UI Badges

Date: 2026-06-30

## Context

Archdoc now models operation-to-operation relationships such as `service_call` and `inherited_operation`. These relationships need to be visible wherever developers inspect operations, not only in raw generated JSON.

## Change

- Added reusable operation relation badges for frontend tables and graph inspectors.
- Marked `inherited_operation` relations with a distinct branch-style badge and hover information explaining facade/inheritance semantics.
- Added operation relation summaries to the Operations catalog table.
- Added a Relations filter to the Operations catalog table for inherited/facade operations, service calls, and operations without relations.
- Extended the operations table backend endpoint to return relevant incoming and outgoing operation links per operation row.
- Added relation badges directly to operation nodes in the Service Action Graph and reused the same badge component in the graph inspector.

## Architectural Decision

Operation relation rendering is centralized in a shared frontend primitive instead of duplicated per view. This keeps future relation types maintainable and makes `inherited_operation` visually consistent across the Operations tab and Service Action Graph.

## Tradeoffs

The tooltip currently uses accessible native hover text through `title` and `aria-label`. This keeps the implementation lightweight and framework-neutral, but a future richer tooltip component could support formatted details if reviewers need more context than a one-sentence explanation.