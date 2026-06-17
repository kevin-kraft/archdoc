# Duplicate Operation Action Ownership

## Context

`CompensationService.get_participant_payouts` was visible as more than one
service operation:

- `finance.compensation.operation.get_participant_payouts`
- `finance.financial.operation.get_participant_payouts`

The action mapper indexed operations by `qualified_name` as a single value. When
multiple catalog operations shared the same source method, only one operation ID
received the detected actions. The other operation appeared empty in the service
graph inspector.

## Change

The action mapper now indexes operations by `qualified_name` to a list of
catalog operation owners. For class methods, architecture actions are emitted for
each matching operation owner.

This makes shared or duplicated service catalog entries explicit instead of
silently assigning method actions to only one operation.

## Additional Validation

Added a conservative validator warning:

- `service_db_session_not_initialized`

The warning is emitted when a service method calls `self.db.*`, but the service
class has no detected `self.db = ...` assignment. This flags possible
architecture/runtime drift such as service classes that rely on an implicit DB
session contract.

## Verified Example

Read-only verification showed both operation IDs now receive:

```text
database_action self.db.execute query: query Payout services/finance/compensation.py:40
```

The new validator warning also targets:

```text
finance.compensation.operation.get_participant_payouts
services/finance/compensation.py:40
```

## Verification

- Python compile for action mapper and catalog validator
- in-memory map/action verification
- in-memory validation verification
- `npm run typecheck`

The persisted generated JSON files still need a normal `archdoc map -c
archdoc.yml` run. The write step was blocked by the current execution approval
limit in this session.
