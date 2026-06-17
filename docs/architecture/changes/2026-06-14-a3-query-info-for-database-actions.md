# A3: Query Info for Database Actions

## Context

The service action graph originally showed database actions such as
`self.db.execute(query)` only with the executed variable name. That was
semantically correct, but not informative enough because the actual SQLAlchemy
query was often defined in a previous assignment:

```python
query = select(IAMUser).where(
    and_(IAMUser.id == user_id, IAMUser.org_id == org_id)
)
result = await self.db.execute(query)
```

## Change

`ArchitectureActionItem` now has an optional `query` field.

The query field captures:

- assigned query variable
- full source expression
- query operation, for example `select`
- referenced entities
- where filters
- joins
- ordering/grouping clauses
- limit

Example:

```json
{
  "variable": "query",
  "expression": "select(IAMUser).where(and_(IAMUser.id == user_id, IAMUser.org_id == org_id))",
  "operation": "select",
  "entities": ["IAMUser"],
  "filters": ["IAMUser.id == user_id", "IAMUser.org_id == org_id"],
  "joins": [],
  "ordering": [],
  "limit": null
}
```

## Mapper Behavior

The action mapper resolves:

- `self.db.execute(query)` through previous assignments
- inline expressions like `self.db.execute(select(Role.id).where(...))`

SQLAlchemy query-builder syntax such as `select(...)`, `.where(...)`, and
`and_(...)` is not exported as its own `database_action`. It is now query detail
attached to the actual session/database action.

## Frontend Impact

The service action graph can display more useful labels, for example:

- `execute: select IAMUser where IAMUser.id == user_id`
- `execute: select UserRole where UserRole.user_id == user.id`

## Verified Case

`AdminUserService.update_user` now resolves query details for:

- `query`
- `existing_query`
- inline `select(Role.id)`
- inline `select(UserRole)`
