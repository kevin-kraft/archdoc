from __future__ import annotations

import re

from archdoc.catalog.identity import build_catalog_identity
from archdoc.catalog.models import (
    ActionOwnerRef,
    ArchitectureActionItem,
    DetectionConfidence,
    DetectionInfo,
    EndpointImplementationKind,
    EndpointCatalogItem,
    EntityFieldInfo,
    EntityTypeInfo,
    OperationCatalogItem,
    QueryInfo,
    ServiceCatalogItem,
    SourceRef,
)
from archdoc.config.models import ActionPatternConfig, ArchdocConfig
from archdoc.facts.models import AssignmentFact, CallFact, ClassFact, FileFact, FunctionFact, RawCodeFacts


def map_actions(
    facts: RawCodeFacts,
    config: ArchdocConfig,
    services: list[ServiceCatalogItem],
    endpoints: list[EndpointCatalogItem],
) -> list[ArchitectureActionItem]:
    if not config.mapping.actions.enabled:
        return []

    operation_index = _operation_index(services)
    endpoint_index = _endpoint_index(endpoints)
    entity_index = _entity_index(facts, config)
    actions: list[ArchitectureActionItem] = []

    for file in facts.files:
        if file.error:
            continue

        for class_fact in file.classes:
            actions.extend(_map_class_entity_actions(file, class_fact, len(actions)))

            for method in class_fact.methods:
                owners = _owners_for_method(file, class_fact, method, operation_index)
                for owner in owners:
                    actions.extend(_map_function_actions(method, owner, config, len(actions), entity_index))

                    if config.mapping.actions.include_unmatched_type_usages:
                        actions.extend(_map_type_usage_actions(method, owner, len(actions)))

        for function in file.functions:
            owner = _owner_for_function(file, function, endpoint_index)
            actions.extend(_map_function_actions(function, owner, config, len(actions), entity_index))

            if config.mapping.actions.include_unmatched_type_usages:
                actions.extend(_map_type_usage_actions(function, owner, len(actions)))

    return sorted(actions, key=lambda action: action.id)


def _operation_index(
    services: list[ServiceCatalogItem],
) -> dict[str, list[tuple[ServiceCatalogItem, OperationCatalogItem]]]:
    index: dict[str, list[tuple[ServiceCatalogItem, OperationCatalogItem]]] = {}

    for service in services:
        for operation in service.operations:
            index.setdefault(operation.qualified_name, []).append((service, operation))

    return index


def _endpoint_index(
    endpoints: list[EndpointCatalogItem],
) -> dict[str, list[EndpointCatalogItem]]:
    index: dict[str, list[EndpointCatalogItem]] = {}

    for endpoint in endpoints:
        index.setdefault(endpoint.qualified_name, []).append(endpoint)

    return index


def _entity_index(
    facts: RawCodeFacts,
    config: ArchdocConfig,
) -> dict[str, EntityTypeInfo]:
    if not config.mapping.entities.enabled:
        return {}

    index: dict[str, EntityTypeInfo] = {}

    for file in facts.files:
        if file.error or not _path_matches(file.path, config.mapping.entities.paths):
            continue

        for class_fact in file.classes:
            entity_kind = _entity_kind(class_fact, config)
            if entity_kind is None:
                continue

            source = SourceRef(
                file=class_fact.source.file,
                line_start=class_fact.source.line_start,
                line_end=class_fact.source.line_end,
            )
            entity = EntityTypeInfo(
                name=class_fact.name,
                qualified_name=class_fact.qualified_name,
                module=file.module,
                kind=entity_kind,
                table_name=_class_table_name(class_fact, config),
                source=source,
                fields=[
                    EntityFieldInfo(
                        name=field.name,
                        annotation=field.annotation,
                        value=field.value,
                        value_call=field.value_call,
                        source=SourceRef(
                            file=field.source.file,
                            line_start=field.source.line_start,
                            line_end=field.source.line_end,
                        ),
                    )
                    for field in class_fact.fields
                    if _is_entity_field(field.name, field.value_call, config)
                ],
            )
            index.setdefault(entity.name, entity)

    return index


def _path_matches(path: str, configured_paths: list[str]) -> bool:
    normalized = path.replace("\\", "/").strip("/")
    return any(
        normalized == configured.strip("/")
        or normalized.startswith(f"{configured.strip('/')}/")
        or f"/{configured.strip('/')}/" in f"/{normalized}/"
        for configured in configured_paths
        if configured.strip("/")
    )


def _entity_kind(class_fact: ClassFact, config: ArchdocConfig) -> str | None:
    signal_kinds = {signal.kind for signal in class_fact.signals}

    if signal_kinds & {"sqlalchemy_model_base", "orm_model_base"}:
        return "sqlalchemy_model"

    if "pydantic_model_base" in signal_kinds and config.mapping.entities.include_pydantic_models:
        return "pydantic_model"

    base_names = {_normalize_base_name(base) for base in class_fact.bases}
    configured_bases = set(config.mapping.entities.class_base_names)

    if base_names & configured_bases:
        return "sqlalchemy_model"

    if config.mapping.entities.include_pydantic_models and base_names & {"BaseModel"}:
        return "pydantic_model"

    return None


def _normalize_base_name(value: str) -> str:
    return value.rsplit(".", 1)[-1]


def _class_table_name(class_fact: ClassFact, config: ArchdocConfig) -> str | None:
    for field in class_fact.fields:
        if field.name in config.mapping.entities.table_name_fields and field.value:
            return field.value.strip().strip("'\"")

    return None


def _is_entity_field(name: str, value_call: str | None, config: ArchdocConfig) -> bool:
    if name in config.mapping.entities.table_name_fields:
        return True

    if value_call is None:
        return False

    call_name = value_call.rsplit(".", 1)[-1]
    return call_name in config.mapping.entities.field_value_calls


def _owners_for_method(
    file: FileFact,
    class_fact: ClassFact,
    method: FunctionFact,
    operation_index: dict[str, list[tuple[ServiceCatalogItem, OperationCatalogItem]]],
) -> list[ActionOwnerRef]:
    operation_entries = operation_index.get(method.qualified_name)

    if operation_entries:
        return [
            ActionOwnerRef(
                type="operation",
                id=operation.id,
                qualified_name=operation.qualified_name,
                class_name=service.class_name,
                module=file.module,
            )
            for service, operation in operation_entries
        ]

    return [
        ActionOwnerRef(
            type="method",
            id=method.qualified_name,
            qualified_name=method.qualified_name,
            class_name=class_fact.name,
            module=file.module,
        )
    ]


def _owner_for_function(
    file: FileFact,
    function: FunctionFact,
    endpoint_index: dict[str, list[EndpointCatalogItem]],
) -> ActionOwnerRef:
    endpoints = sorted(
        endpoint_index.get(function.qualified_name, []),
        key=lambda item: (
            item.implementation.kind != EndpointImplementationKind.SERVICE_OPERATION,
            item.id,
        ),
    )

    if endpoints:
        return ActionOwnerRef(
            type="endpoint",
            id=endpoints[0].id,
            qualified_name=function.qualified_name,
            module=file.module,
        )

    return ActionOwnerRef(
        type="function",
        id=function.qualified_name,
        qualified_name=function.qualified_name,
        module=file.module,
    )


def _map_function_actions(
    function: FunctionFact,
    owner: ActionOwnerRef,
    config: ArchdocConfig,
    offset: int,
    entity_index: dict[str, EntityTypeInfo],
) -> list[ArchitectureActionItem]:
    actions: list[ArchitectureActionItem] = []
    assignment_index = _assignment_index(function.assignments)
    dependency_gate_calls = {"require_permission", "require_any_permission", "has_permission", "require_org_context"}
    nested_permission_lines = {
        call.source.line_start
        for call in function.calls
        if call.nested_in_call and call.name in dependency_gate_calls
    }
    db_action_ranges = {
        (
            call.source.line_start,
            call.source.line_end or call.source.line_start,
        )
        for call in function.calls
        if call.call_role == "db_call"
    }

    for call in function.calls:
        if call.name == "Depends" and (
            call.source.line_start in nested_permission_lines
            or any(token in " ".join([*call.args, *call.kwargs.values()]) for token in dependency_gate_calls)
        ):
            continue
        if call.call_role == "sqlalchemy_query_call":
            continue
        if _is_nested_sqlalchemy_expression_inside_db_call(call, db_action_ranges):
            continue

        worker_action = _worker_action_from_call(
            call=call,
            owner=owner,
            config=config,
            ordinal=offset + len(actions),
        )
        if worker_action is not None:
            actions.append(worker_action)
            continue

        for pattern in config.mapping.actions.patterns:
            if not _matches_pattern(call, pattern):
                continue

            action = _action_from_call(
                call=call,
                owner=owner,
                pattern=pattern,
                ordinal=offset + len(actions),
                assignment_index=assignment_index,
                entity_index=entity_index,
            )
            actions.append(action)
            break

    return actions


def _worker_action_from_call(
    call: CallFact,
    owner: ActionOwnerRef,
    config: ArchdocConfig,
    ordinal: int,
) -> ArchitectureActionItem | None:
    if not config.mapping.workers.enabled:
        return None

    details = _worker_details_from_call(call, config)
    if details is None:
        return None

    source = SourceRef(
        file=call.source.file,
        line_start=call.source.line_start,
        line_end=call.source.line_end,
    )
    job_type = _clean_literal(details.get("job_type"))
    resource = job_type or call.root_name or call.name
    action_id = f"{owner.id}.action.{ordinal}.worker_action.{_slug(call.name)}"

    return ArchitectureActionItem(
        id=action_id,
        identity=build_catalog_identity(
            kind="architecture_action",
            logical_id=action_id,
            display_name=f"{owner.id} worker {resource}",
            source=source,
            qualified_name=owner.qualified_name,
            extra_parts=["worker_action", call.name, str(ordinal)],
            aliases=[call.name, resource],
        ),
        kind="worker_action",
        action="enqueue",
        access="async",
        owner=owner,
        call_name=call.name,
        resource=resource,
        entity=job_type,
        source=source,
        detection=DetectionInfo(
            method="pattern",
            rule=str(details.get("dispatch_style", "worker_dispatch")),
            confidence=DetectionConfidence.HIGH,
            evidence=[
                f"call={call.name}",
                f"job_type={job_type or 'unknown'}",
                f"owner={owner.id}",
            ],
        ),
        details={
            **details,
            "job_type": job_type,
            "args": call.args,
            "kwargs": call.kwargs,
            "awaited": call.awaited,
            "root_name": call.root_name,
        },
    )


def _worker_details_from_call(call: CallFact, config: ArchdocConfig) -> dict | None:
    for dispatch in config.mapping.workers.dispatch_calls:
        if call.name == dispatch.name or call.name.endswith(f".{dispatch.name}"):
            return {
                "dispatch_style": "worker_dispatch_call",
                "job_type": _call_arg_value(call, dispatch.job_type_arg, 0),
                "payload": _call_arg_value(call, dispatch.payload_arg, 1),
                "scheduled_at": _call_arg_value(call, dispatch.schedule_arg),
                "priority": _call_arg_value(call, dispatch.priority_arg),
                "org_id": _call_arg_value(call, dispatch.org_arg),
            }

    for constructor in config.mapping.workers.job_model_constructors:
        if call.name == constructor.class_name or call.name.endswith(f".{constructor.class_name}"):
            return {
                "dispatch_style": "job_model_constructor",
                "job_type": _call_arg_value(call, constructor.job_type_kwarg),
                "payload": _call_arg_value(call, constructor.payload_kwarg),
                "scheduled_at": _call_arg_value(call, constructor.schedule_kwarg),
                "priority": _call_arg_value(call, constructor.priority_kwarg),
                "org_id": _call_arg_value(call, constructor.org_kwarg),
            }

    if any(call.name.endswith(suffix) for suffix in config.mapping.workers.queue_method_suffixes):
        return {
            "dispatch_style": "queue_method_suffix",
            "job_type": call.root_name or call.name,
            "payload": call.args[0] if call.args else None,
            "scheduled_at": None,
            "priority": None,
            "org_id": None,
        }

    return None


def _call_arg_value(call: CallFact, keyword: str | None, positional_index: int | None = None) -> str | None:
    if keyword and keyword in call.kwargs:
        return call.kwargs[keyword]

    if positional_index is not None and positional_index < len(call.args):
        return call.args[positional_index]

    return None


def _is_nested_sqlalchemy_expression_inside_db_call(
    call: CallFact,
    db_action_ranges: set[tuple[int, int]],
) -> bool:
    return (
        call.nested_in_call
        and call.call_role == "sqlalchemy_query_call"
        and any(start <= call.source.line_start <= end for start, end in db_action_ranges)
    )


def _assignment_index(assignments: list[AssignmentFact]) -> dict[str, AssignmentFact]:
    result: dict[str, AssignmentFact] = {}

    for assignment in assignments:
        result[assignment.target] = assignment

    return result


def _map_class_entity_actions(
    file: FileFact,
    class_fact: ClassFact,
    offset: int,
) -> list[ArchitectureActionItem]:
    actions: list[ArchitectureActionItem] = []

    for signal in class_fact.signals:
        if signal.kind not in {"sqlalchemy_model_base", "orm_model_base", "pydantic_model_base"}:
            continue

        source = SourceRef(
            file=class_fact.source.file,
            line_start=class_fact.source.line_start,
            line_end=class_fact.source.line_end,
        )
        owner = ActionOwnerRef(
            type="class",
            id=class_fact.qualified_name,
            qualified_name=class_fact.qualified_name,
            class_name=class_fact.name,
            module=file.module,
        )
        kind = "entity_declaration"
        action = "declare"
        entity_id = f"{owner.id}.action.{offset + len(actions)}.{kind}"

        actions.append(
            ArchitectureActionItem(
                id=entity_id,
                identity=build_catalog_identity(
                    kind="architecture_action",
                    logical_id=entity_id,
                    display_name=f"{class_fact.name} {kind}",
                    source=source,
                    qualified_name=class_fact.qualified_name,
                    extra_parts=[kind, action],
                    aliases=[class_fact.name],
                ),
                kind=kind,
                action=action,
                access=None,
                owner=owner,
                call_name=None,
                resource=signal.data.get("base"),
                entity=class_fact.name,
                source=source,
                detection=DetectionInfo(
                    method="signal",
                    rule=signal.kind,
                    confidence=DetectionConfidence.HIGH,
                    evidence=[f"signal={signal.kind}", f"class={class_fact.qualified_name}"],
                ),
                details={"signal": signal.model_dump(mode="json")},
            )
        )

    return actions


def _map_type_usage_actions(
    function: FunctionFact,
    owner: ActionOwnerRef,
    offset: int,
) -> list[ArchitectureActionItem]:
    actions: list[ArchitectureActionItem] = []
    seen: set[str] = set()

    type_names = [
        parameter.annotation
        for parameter in function.parameters
        if parameter.annotation
    ]

    if function.returns:
        type_names.append(function.returns)

    for type_name in type_names:
        normalized = _normalize_type_reference(type_name)
        if not normalized or normalized in seen:
            continue

        seen.add(normalized)
        source = SourceRef(
            file=function.source.file,
            line_start=function.source.line_start,
            line_end=function.source.line_end,
        )
        action_id = f"{owner.id}.action.{offset + len(actions)}.type_usage.{_slug(normalized)}"

        actions.append(
            ArchitectureActionItem(
                id=action_id,
                identity=build_catalog_identity(
                    kind="architecture_action",
                    logical_id=action_id,
                    display_name=f"{owner.id} uses {normalized}",
                    source=source,
                    qualified_name=owner.qualified_name,
                    extra_parts=["type_usage", normalized],
                    aliases=[normalized],
                ),
                kind="type_usage",
                action="use",
                access=None,
                owner=owner,
                call_name=None,
                resource=normalized,
                entity=normalized,
                source=source,
                detection=DetectionInfo(
                    method="annotation",
                    rule="function_signature_type_reference",
                    confidence=DetectionConfidence.MEDIUM,
                    evidence=[f"type={normalized}", f"function={function.qualified_name}"],
                ),
                details={"raw_type": type_name},
            )
        )

    return actions


def _matches_pattern(call: CallFact, pattern: ActionPatternConfig) -> bool:
    if call.nested_in_call and not pattern.include_nested_calls:
        return False

    if pattern.kind == "permission_action":
        return _matches_permission_pattern(call, pattern)

    if pattern.call_roles and call.call_role in pattern.call_roles:
        return True

    if pattern.call_names and call.name in pattern.call_names:
        return True

    if any(call.name.startswith(prefix) for prefix in pattern.call_prefixes):
        return True

    if any(call.name.endswith(suffix) for suffix in pattern.call_suffixes):
        return True

    haystack = " ".join([call.name, *call.args, *call.kwargs.values()])
    return any(token in haystack for token in pattern.call_contains)


def _matches_permission_pattern(call: CallFact, pattern: ActionPatternConfig) -> bool:
    if pattern.call_names and call.name in pattern.call_names:
        return True

    haystack = " ".join([*call.args, *call.kwargs.values()])
    if not any(token in haystack for token in pattern.call_contains):
        return False

    return call.name == "Depends" or call.name.startswith("router.")


def _action_from_call(
    call: CallFact,
    owner: ActionOwnerRef,
    pattern: ActionPatternConfig,
    ordinal: int,
    assignment_index: dict[str, AssignmentFact],
    entity_index: dict[str, EntityTypeInfo],
) -> ArchitectureActionItem:
    source = SourceRef(
        file=call.source.file,
        line_start=call.source.line_start,
        line_end=call.source.line_end,
    )
    action = pattern.action or _infer_action(call)
    kind = _effective_action_kind(call, pattern.kind, action)
    access = pattern.access or _infer_access(call, action)
    resource = _extract_resource(call, kind)
    query = _extract_query_info(call, kind, assignment_index, entity_index)
    if query is not None:
        resource = _query_resource_label(query, fallback=resource)
    entity = _extract_entity(call, kind, resource)
    action_id = f"{owner.id}.action.{ordinal}.{_slug(kind)}.{_slug(call.name)}"

    return ArchitectureActionItem(
        id=action_id,
        identity=build_catalog_identity(
            kind="architecture_action",
            logical_id=action_id,
            display_name=f"{owner.id} {kind} {call.name}",
            source=source,
            qualified_name=owner.qualified_name,
            extra_parts=[kind, call.name, str(ordinal)],
            aliases=[call.name, *(filter(None, [resource, entity]))],
        ),
        kind=kind,
        action=action,
        access=access,
        owner=owner,
        call_name=call.name,
        resource=resource,
        entity=entity,
        query=query,
        source=source,
        detection=DetectionInfo(
            method="pattern",
            rule=pattern.name,
            confidence=_confidence(pattern.confidence),
            evidence=[
                f"call={call.name}",
                f"call_role={call.call_role}",
                f"owner={owner.id}",
            ],
        ),
        details={
            "args": call.args,
            "kwargs": call.kwargs,
            "awaited": call.awaited,
            "nested_in_call": call.nested_in_call,
            "root_name": call.root_name,
        },
    )


def _extract_query_info(
    call: CallFact,
    kind: str,
    assignment_index: dict[str, AssignmentFact],
    entity_index: dict[str, EntityTypeInfo],
) -> QueryInfo | None:
    if kind != "database_action":
        return None

    if not call.name.endswith(".execute") and call.call_role != "sqlalchemy_query_call":
        return None

    raw_argument = call.args[0] if call.args else None
    if not raw_argument:
        return None

    variable = raw_argument if _is_simple_identifier(raw_argument) else None
    assignment = assignment_index.get(variable) if variable else None
    expression = assignment.value if assignment and assignment.value else raw_argument

    if not expression:
        return None

    entities = _query_entities(expression)

    return QueryInfo(
        variable=variable,
        expression=expression,
        operation=_query_operation(expression),
        entities=entities,
        filters=_query_filters(expression),
        joins=_query_clause_values(expression, "join"),
        ordering=[
            *_query_clause_values(expression, "order_by"),
            *_query_clause_values(expression, "group_by"),
        ],
        limit=_query_limit(expression),
        entity_details=[
            entity_index[entity]
            for entity in entities
            if entity in entity_index
        ],
    )


def _is_simple_identifier(value: str) -> bool:
    return bool(re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", value))


def _query_resource_label(query: QueryInfo, fallback: str | None) -> str:
    prefix = query.operation or "query"
    entities = ", ".join(query.entities[:3])

    if query.variable and entities:
        return f"{query.variable}: {prefix} {entities}"

    if query.variable:
        return f"{query.variable}: {prefix}"

    if entities:
        return f"{prefix} {entities}"

    return fallback or query.expression


def _query_operation(expression: str) -> str | None:
    stripped = expression.strip()

    for operation in ("select", "insert", "update", "delete"):
        if stripped.startswith(f"{operation}(") or stripped.startswith(f"{operation}."):
            return operation

    return None


def _query_entities(expression: str) -> list[str]:
    entities: list[str] = []

    for operation in ("select", "insert", "update", "delete"):
        for argument in _top_level_call_args(expression, operation):
            entities.extend(_query_entity_candidates(argument))

    entities.extend(_model_attribute_references(expression))

    cleaned: list[str] = []
    for entity in entities:
        candidate = entity.strip()
        if not candidate:
            continue

        candidate = candidate.split("(", 1)[0]

        if "." in candidate:
            candidate = candidate.split(".", 1)[0]

        if "[" in candidate:
            candidate = candidate.split("[", 1)[0]

        if not _looks_like_query_entity(candidate):
            continue

        if candidate not in cleaned:
            cleaned.append(candidate)

    return cleaned


def _query_entity_candidates(argument: str) -> list[str]:
    nested_model_refs = _model_attribute_references(argument)
    if nested_model_refs:
        return nested_model_refs

    return [argument]


def _model_attribute_references(expression: str) -> list[str]:
    return re.findall(r"\b([A-Z][A-Za-z0-9_]*)\.[A-Za-z_][A-Za-z0-9_]*", expression)


def _looks_like_query_entity(candidate: str) -> bool:
    sql_helpers = {
        "and_",
        "case",
        "cast",
        "desc",
        "distinct",
        "func",
        "literal",
        "or_",
        "select",
        "text",
    }

    return candidate not in sql_helpers and bool(re.match(r"^[A-Z][A-Za-z0-9_]*$", candidate))


def _query_filters(expression: str) -> list[str]:
    filters = _query_clause_values(expression, "where")
    flattened: list[str] = []

    for item in filters:
        if item.startswith("and_(") and item.endswith(")"):
            flattened.extend(_split_top_level_args(item[5:-1]))
        else:
            flattened.append(item)

    return _unique_strings([item.strip() for item in flattened if item.strip()])


def _query_limit(expression: str) -> str | None:
    values = _query_clause_values(expression, "limit")
    return values[0] if values else None


def _query_clause_values(expression: str, clause: str) -> list[str]:
    values: list[str] = []
    marker = f".{clause}("
    index = 0

    while True:
        start = expression.find(marker, index)
        if start < 0:
            return values

        args_start = start + len(marker)
        args_end = _matching_paren_index(expression, args_start - 1)
        if args_end is None:
            return values

        values.extend(_split_top_level_args(expression[args_start:args_end]))
        index = args_end + 1


def _top_level_call_args(expression: str, function_name: str) -> list[str]:
    marker = f"{function_name}("
    start = expression.find(marker)
    if start < 0:
        return []

    args_start = start + len(marker)
    args_end = _matching_paren_index(expression, args_start - 1)
    if args_end is None:
        return []

    return _split_top_level_args(expression[args_start:args_end])


def _matching_paren_index(value: str, open_index: int) -> int | None:
    depth = 0
    quote: str | None = None
    escaped = False

    for index in range(open_index, len(value)):
        char = value[index]

        if quote is not None:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                quote = None
            continue

        if char in {"'", '"'}:
            quote = char
            continue

        if char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
            if depth == 0:
                return index

    return None


def _split_top_level_args(value: str) -> list[str]:
    args: list[str] = []
    start = 0
    depth = 0
    quote: str | None = None
    escaped = False

    for index, char in enumerate(value):
        if quote is not None:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                quote = None
            continue

        if char in {"'", '"'}:
            quote = char
            continue

        if char in "([{":
            depth += 1
        elif char in ")]}":
            depth -= 1
        elif char == "," and depth == 0:
            args.append(value[start:index].strip())
            start = index + 1

    final = value[start:].strip()
    if final:
        args.append(final)

    return args


def _infer_action(call: CallFact) -> str | None:
    if call.name.endswith(".add") or call.name == "insert":
        return "create"

    if call.name.endswith(".get") or call.name == "select":
        return "read"

    if call.name == "update":
        return "update"

    if call.name == "delete":
        return "delete"

    if call.name.endswith(".commit"):
        return "commit"

    if call.name.endswith(".flush"):
        return "flush"

    if call.name.endswith(".refresh"):
        return "refresh"

    if call.name.endswith(".execute"):
        return "execute"

    return None


def _effective_action_kind(call: CallFact, configured_kind: str, action: str | None) -> str:
    if configured_kind == "database_action" and action in {"commit", "flush", "refresh"}:
        return "database_transaction"

    return configured_kind


def _infer_access(call: CallFact, action: str | None) -> str | None:
    if action in {"read"}:
        return "read"

    if action in {"create", "update", "delete", "commit"}:
        return "write"

    if call.call_role in {"db_call", "sqlalchemy_query_call"}:
        return "data"

    return None


def _extract_resource(call: CallFact, kind: str) -> str | None:
    if kind == "permission_action":
        return _extract_permission_resource(call)

    if kind == "database_transaction":
        if call.name.endswith(".commit"):
            return "session commit"
        if call.name.endswith(".flush"):
            return "session flush"
        if call.name.endswith(".refresh"):
            return f"refresh {call.args[0]}" if call.args else "session refresh"
        if call.name.endswith(".rollback"):
            return "session rollback"

    if kind == "audit_action" and "action" in call.kwargs:
        return _clean_literal(call.kwargs["action"])

    if call.args:
        return _normalize_type_reference(call.args[0]) or call.args[0]

    return call.root_name or call.name


def _extract_entity(call: CallFact, kind: str, resource: str | None) -> str | None:
    if kind in {"database_action", "entity_declaration", "type_usage"}:
        return resource

    return None


def _extract_permission_resource(call: CallFact) -> str | None:
    candidates = [*call.args, *call.kwargs.values()]

    if call.name in {"require_permission", "require_any_permission", "has_permission"} and candidates:
        return _clean_permission_value(candidates[0])

    haystack = " ".join(candidates)
    match = re.search(
        r"(?:require_permission|require_any_permission|has_permission)\(([^)]*)\)",
        haystack,
    )
    if match:
        return _clean_permission_value(match.group(1).split(",", 1)[0])

    return None


def _clean_permission_value(value: str) -> str:
    return value.strip().strip("'\"")


def _clean_literal(value: str | None) -> str | None:
    if value is None:
        return None

    cleaned = value.strip().strip("'\"")
    return cleaned or None


def _normalize_type_reference(value: str | None) -> str | None:
    if not value:
        return None

    cleaned = value.strip().strip("'\"")
    cleaned = re.sub(r"\s+", "", cleaned)

    if not cleaned or cleaned in {"None", "str", "int", "float", "bool", "dict", "list", "set"}:
        return None

    if "[" in cleaned and cleaned.endswith("]"):
        inner = cleaned[cleaned.find("[") + 1 : -1]
        return _normalize_type_reference(inner.split(",", 1)[0]) or cleaned

    if "." in cleaned:
        cleaned = cleaned.rsplit(".", 1)[-1]

    if not cleaned[:1].isupper():
        return None

    return cleaned


def _confidence(value: str) -> DetectionConfidence:
    try:
        return DetectionConfidence(value)
    except ValueError:
        return DetectionConfidence.UNKNOWN


def _slug(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_.-]+", "-", value).strip("-").lower() or "unknown"


def _unique_strings(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []

    for value in values:
        if value in seen:
            continue

        seen.add(value)
        result.append(value)

    return result
