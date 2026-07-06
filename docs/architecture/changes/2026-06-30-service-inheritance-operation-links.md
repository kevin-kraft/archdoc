# Service Inheritance Operation Links

Date: 2026-06-30

## Context

Finance facade services can expose operations implemented in inherited domain services. In Utilis, `FinancialService` inherits `BudgetService`, so endpoints may correctly call `FinancialService.create_budget` even though the implementation lives in `BudgetService.create_budget`.

Before this change, Archdoc could map the endpoint to the facade operation, but the declaring service operation still looked unreferenced. The operation link mapper also indexed a source method by a single `qualified_name`, which lost the fact that one source method can have multiple architecture owners.

## Changes

- Added `inherited_operation` operation links from facade-owned operations to their declaring service operations.
- Updated service-call operation link mapping to keep all operation owners for a shared source method instead of overwriting by `qualified_name`.
- Expanded validator operation coverage by shared `qualified_name`, so a facade-linked inherited operation also covers the declaring operation.
- Stabilized scoped AST traversal order so extracted calls keep source order.
- Updated the Service Action Graph inspector wording from service-call-only labels to generic operation-link labels, while rendering inherited links as `inherited operation`.
- Added regression tests for inherited facade operation links and source-ordered call extraction.

## Architectural Decision

Inheritance is modeled as an operation-level relationship, not as an endpoint-link special case. This keeps the graph generalizable for other facades, mixins, and service aggregation patterns while preserving the distinction between runtime calls (`service_call`) and ownership/capability exposure (`inherited_operation`).

## Tradeoffs

The validator now treats operations with the same source `qualified_name` as covered together. This is intentional for inherited methods, but it can hide an unreferenced duplicate if two generated operations point to the same source method for reasons other than inheritance. The graph still exposes the relationship through operation links so reviewers can inspect these cases.