# Facade Service Resource Origin Validation

Date: 2026-06-30

## Context

Facade services can expose inherited domain operations while providing runtime instance resources themselves. In Utilis, `FinancialService` owns `self.db` in its constructor and inherits operations such as `BudgetService.create_budget`.

A class-only resource check can misread this pattern: the declaring class `BudgetService` may not define `self.db`, but the operation can still run with a valid `self.db` when reached through `FinancialService`.

## Change

DB-session origin validation now evaluates service operations in the context of their operation owner:

- if the owning service class has a `self.db` resource profile, inherited methods are accepted for that owner
- if the same source method is also represented by a facade operation with a valid `self.db` owner, the declaring service operation is not warned merely because it lacks its own constructor
- if a method is directly endpoint-linked through a service owner without a `self.db` origin, the warning is still emitted

## Architectural Decision

Resource-origin validation is operation-owner-aware instead of only declaring-class-aware. This matches the catalog model where one source method can appear as multiple architecture operations through inheritance or facade composition.

## Tradeoffs

This intentionally reduces false positives for facade-owned inherited operations. A direct endpoint call to the base service still warns, so the validator does not hide real direct-instantiation risks.

## Verification

Added regression coverage for both sides:

- `FinancialService` inheriting `BudgetService.create_budget` with `self.db` initialized in the facade does not emit `service_db_session_origin_unknown`
- direct `BudgetService.create_budget` usage without a `self.db` origin still emits `service_db_session_origin_unknown`