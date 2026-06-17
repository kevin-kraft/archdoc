from __future__ import annotations

from archdoc.catalog.models import (
    DetectionConfidence,
    DetectionInfo,
    EndpointCatalogItem,
    EndpointServiceLinkItem,
    IgnoredCallRole,
    OperationCatalogItem,
    OperationIndex,
    ServiceCallMatch,
    ServiceCatalogItem,
    ServiceResolutionRule,
    SourceRef,
    VariableTypeMap,
)
from archdoc.catalog.identity import build_catalog_identity
from typing import TypeGuard

from archdoc.facts.models import AssignmentFact, FunctionFact, RawCodeFacts
from archdoc.utils.class_index import (
    ClassIndex,
    build_class_index,
    resolve_method_owner_path,
)


IGNORED_CALL_ROLES = {role.value for role in IgnoredCallRole}


def link_endpoints_to_services(
    facts: RawCodeFacts,
    endpoints: list[EndpointCatalogItem],
    services: list[ServiceCatalogItem],
) -> list[EndpointServiceLinkItem]:
    operation_index = _build_operation_index(services)
    class_index = build_class_index(facts)

    endpoint_index = {
        endpoint.qualified_name: endpoint
        for endpoint in endpoints
    }

    links: list[EndpointServiceLinkItem] = []

    for file in facts.files:
        if file.error:
            continue

        helper_index = {
            helper.name: helper
            for helper in file.functions
        }

        for fn in file.functions:
            endpoint = endpoint_index.get(fn.qualified_name)

            if endpoint is None:
                continue

            variable_types = _infer_variable_types(fn, file.assignments)

            for call in _meaningful_calls_for_service_linking(fn):
                match = _match_service_operation_call(
                    call_name=call.name,
                    variable_types=variable_types,
                    operation_index=operation_index,
                    class_index=class_index,
                )

                if match is None:
                    continue

                links.append(
                    _build_link(
                        endpoint=endpoint,
                        match=match,
                        call_name=call.name,
                        source=SourceRef(
                            file=call.source.file,
                            line_start=call.source.line_start,
                            line_end=call.source.line_end,
                        ),
                        evidence=[
                            f"call={call.name}",
                            f"endpoint={endpoint.qualified_name}",
                            f"operation={match.operation.qualified_name}",
                        ],
                    )
                )

            links.extend(
                _link_endpoint_via_forwarded_service_helpers(
                    endpoint=endpoint,
                    fn=fn,
                    helper_index=helper_index,
                    endpoint_variable_types=variable_types,
                    operation_index=operation_index,
                    class_index=class_index,
                )
            )

    return _dedupe_links(links)


def _build_link(
    endpoint: EndpointCatalogItem,
    match: ServiceCallMatch,
    call_name: str,
    source: SourceRef,
    evidence: list[str],
) -> EndpointServiceLinkItem:
    link_id = _link_id(
        endpoint_id=endpoint.id,
        operation_id=match.operation.id,
        source=source,
    )

    return EndpointServiceLinkItem(
        id=link_id,
        identity=build_catalog_identity(
            kind="endpoint_service_link",
            logical_id=link_id,
            display_name=f"{endpoint.http_method} {endpoint.path} -> {match.service.class_name}.{match.operation.method}",
            source=source,
            qualified_name=call_name,
            extra_parts=[endpoint.id, match.operation.id, call_name],
            aliases=[f"{endpoint.id}|{match.operation.id}"],
        ),
        endpoint_id=endpoint.id,
        endpoint_qualified_name=endpoint.qualified_name,
        service_id=match.service.id,
        service_class=match.service.class_name,
        operation_id=match.operation.id,
        operation_method=match.operation.method,
        call_name=call_name,
        source=source,
        detection=DetectionInfo(
            method="rule",
            rule=match.rule.value,
            confidence=match.confidence,
            evidence=evidence,
        ),
        review_status="generated",
    )


def _build_operation_index(
    services: list[ServiceCatalogItem],
) -> OperationIndex:
    """
    Build lookup index for service operations.

    Supports both:
    - short class name: CalendarService.detect_conflicts
    - qualified class name: app.services.calendar.core.CalendarService.detect_conflicts
    """
    index: OperationIndex = {}

    for service in services:
        for operation in service.operations:
            value = (service, operation)

            index[(service.class_name, operation.method)] = value
            index[(service.qualified_name, operation.method)] = value

    return index


def _infer_variable_types(
    fn: FunctionFact,
    module_assignments: list[AssignmentFact] | None = None,
) -> VariableTypeMap:
    """
    Infer local variable -> service class mappings.

    Examples:
    - service: FinancialService = Depends(...)
    - service = FinancialService(db)
    """
    variable_types: VariableTypeMap = {}

    for param in fn.parameters:
        if _looks_like_service_class(param.annotation):
            variable_types[param.name] = param.annotation

    for assignment in [*(module_assignments or []), *fn.assignments]:
        if _looks_like_service_class(assignment.value_call):
            variable_types[assignment.target] = assignment.value_call

    return variable_types


def _link_endpoint_via_forwarded_service_helpers(
    endpoint: EndpointCatalogItem,
    fn: FunctionFact,
    helper_index: dict[str, FunctionFact],
    endpoint_variable_types: VariableTypeMap,
    operation_index: OperationIndex,
    class_index: ClassIndex,
) -> list[EndpointServiceLinkItem]:
    links: list[EndpointServiceLinkItem] = []

    for helper_call in _meaningful_helper_calls(fn, helper_index):
        helper = helper_index[helper_call.name]
        forwarded_services = _forwarded_service_variables(
            helper_call=helper_call,
            helper=helper,
            endpoint_variable_types=endpoint_variable_types,
        )

        if not forwarded_services:
            continue

        helper_variable_types = _infer_variable_types(helper)
        helper_variable_types.update(forwarded_services)

        for service_call in _meaningful_calls_for_service_linking(helper):
            match = _match_service_operation_call(
                call_name=service_call.name,
                variable_types=helper_variable_types,
                operation_index=operation_index,
                class_index=class_index,
            )

            if match is None:
                continue

            links.append(
                _build_link(
                    endpoint=endpoint,
                    match=ServiceCallMatch(
                        service=match.service,
                        operation=match.operation,
                        confidence=DetectionConfidence.MEDIUM,
                        rule=ServiceResolutionRule.SERVICE_VARIABLE_FORWARDED_TO_TYPED_HELPER,
                    ),
                    call_name=f"{helper_call.name}->{service_call.name}",
                    source=SourceRef(
                        file=service_call.source.file,
                        line_start=service_call.source.line_start,
                        line_end=service_call.source.line_end,
                    ),
                    evidence=[
                        f"endpoint={endpoint.qualified_name}",
                        f"helper_call={helper_call.name}",
                        f"helper={helper.qualified_name}",
                        f"service_call={service_call.name}",
                        f"operation={match.operation.qualified_name}",
                    ],
                )
            )

    return links


def _meaningful_helper_calls(
    fn: FunctionFact,
    helper_index: dict[str, FunctionFact],
):
    return [
        call
        for call in fn.calls
        if not call.nested_in_call
        and call.name in helper_index
        and helper_index[call.name].qualified_name != fn.qualified_name
    ]


def _forwarded_service_variables(
    helper_call,
    helper: FunctionFact,
    endpoint_variable_types: VariableTypeMap,
) -> VariableTypeMap:
    forwarded: VariableTypeMap = {}

    for index, arg in enumerate(helper_call.args):
        if arg not in endpoint_variable_types:
            continue

        if index >= len(helper.parameters):
            continue

        param = helper.parameters[index]
        service_class = endpoint_variable_types[arg]

        if _looks_like_service_class(param.annotation) and param.annotation != service_class:
            continue

        forwarded[param.name] = service_class

    for param_name, arg in helper_call.kwargs.items():
        if arg not in endpoint_variable_types:
            continue

        helper_param = next(
            (param for param in helper.parameters if param.name == param_name),
            None,
        )

        if helper_param is None:
            continue

        service_class = endpoint_variable_types[arg]

        if _looks_like_service_class(helper_param.annotation) and helper_param.annotation != service_class:
            continue

        forwarded[helper_param.name] = service_class

    return forwarded


def _looks_like_service_class(value: str | None) -> TypeGuard[str]:
    return value is not None and value.endswith("Service")


def _meaningful_calls_for_service_linking(fn: FunctionFact):
    return [
        call
        for call in fn.calls
        if not call.nested_in_call
        and (
            call.call_role not in IGNORED_CALL_ROLES
            or _looks_like_direct_service_operation_call(call.name)
        )
    ]


def _looks_like_direct_service_operation_call(call_name: str) -> bool:
    receiver_name, method_name = _split_receiver_and_method(call_name)

    return (
        receiver_name is not None
        and method_name is not None
        and receiver_name.endswith("Service")
    )


def _match_service_operation_call(
    call_name: str,
    variable_types: VariableTypeMap,
    operation_index: OperationIndex,
    class_index: ClassIndex,
) -> ServiceCallMatch | None:
    """
    Resolve a call to a service operation.

    Handles:
    - service.method(...)
    - service = FinancialService(db)
    - FinancialService inherits from domain services / mixins
    - Direct class-style calls like AuditService.log_event(...)
    """
    receiver_name, method_name = _split_receiver_and_method(call_name)

    if receiver_name and method_name:
        service_class = variable_types.get(receiver_name)

        if service_class is not None:
            direct_match = _lookup_operation(
                operation_index=operation_index,
                class_name=service_class,
                method_name=method_name,
            )

            if direct_match is not None:
                service, operation = direct_match
                return ServiceCallMatch(
                    service=service,
                    operation=operation,
                    confidence=DetectionConfidence.HIGH,
                    rule=ServiceResolutionRule.TYPED_OR_ASSIGNED_SERVICE_VARIABLE_METHOD_CALL,
                )

            inherited_match = _match_inherited_service_operation(
                service_class=service_class,
                method_name=method_name,
                operation_index=operation_index,
                class_index=class_index,
            )

            if inherited_match is not None:
                return inherited_match

    return _match_direct_service_class_call(
        call_name=call_name,
        operation_index=operation_index,
    )


def _split_receiver_and_method(call_name: str) -> tuple[str | None, str | None]:
    parts = call_name.split(".")

    if len(parts) < 2:
        return None, None

    return parts[-2], parts[-1]


def _match_inherited_service_operation(
    service_class: str,
    method_name: str,
    operation_index: OperationIndex,
    class_index: ClassIndex,
) -> ServiceCallMatch | None:
    path = resolve_method_owner_path(
        class_name=service_class,
        method_name=method_name,
        class_index=class_index,
    )

    if path is None:
        return None

    path_match = _match_operation_in_resolution_path(
        path=path,
        method_name=method_name,
        operation_index=operation_index,
    )

    return path_match


def _match_operation_in_resolution_path(
    path,
    method_name: str,
    operation_index: OperationIndex,
) -> ServiceCallMatch | None:
    """
    Match operation using an inheritance resolution path.

    Policy:
    1. Prefer service classes in path.
       Example:
       FinancialService -> TransactionsService -> TransactionsBatchMixin
       Prefer TransactionsService over TransactionsBatchMixin.

    2. Fallback to physical implementation owner.
       Example:
       If only TransactionsBatchMixin is in the operation catalog, link there.
    """

    # Prefer architecture-level service classes.
    for cls in path:
        if not cls.name.endswith("Service"):
            continue

        match = _lookup_operation_for_class_fact(
            operation_index=operation_index,
            cls=cls,
            method_name=method_name,
        )

        if match is not None:
            service, operation = match
            return ServiceCallMatch(
                service=service,
                operation=operation,
                confidence=DetectionConfidence.HIGH,
                rule=ServiceResolutionRule.RECURSIVE_INHERITED_SERVICE_METHOD_CALL_SERVICE_PREFERRED,
            )

    # Fallback to actual implementation owner / mixin.
    for cls in reversed(path):
        match = _lookup_operation_for_class_fact(
            operation_index=operation_index,
            cls=cls,
            method_name=method_name,
        )

        if match is not None:
            service, operation = match
            return ServiceCallMatch(
                service=service,
                operation=operation,
                confidence=DetectionConfidence.HIGH,
                rule=ServiceResolutionRule.RECURSIVE_INHERITED_SERVICE_METHOD_CALL_OWNER_FALLBACK,
            )

    return None


def _lookup_operation_for_class_fact(
    operation_index: OperationIndex,
    cls,
    method_name: str,
) -> tuple[ServiceCatalogItem, OperationCatalogItem] | None:
    return (
        operation_index.get((cls.name, method_name))
        or operation_index.get((cls.qualified_name, method_name))
    )


def _lookup_operation(
    operation_index: OperationIndex,
    class_name: str,
    method_name: str,
) -> tuple[ServiceCatalogItem, OperationCatalogItem] | None:
    return operation_index.get((class_name, method_name))


def _match_direct_service_class_call(
    call_name: str,
    operation_index: OperationIndex,
) -> ServiceCallMatch | None:
    """
    Matches calls like:
    - AuditService.log_event(...)
    - FinancialService.cancel_payout(...)
    - _finance_core.AuditService.log_event(...)
    """
    possible_service_class, method_name = _split_receiver_and_method(call_name)

    if possible_service_class is None or method_name is None:
        return None

    if not possible_service_class.endswith("Service"):
        return None

    match = _lookup_operation(
        operation_index=operation_index,
        class_name=possible_service_class,
        method_name=method_name,
    )

    if match is None:
        return None

    service, operation = match

    return ServiceCallMatch(
        service=service,
        operation=operation,
        confidence=DetectionConfidence.MEDIUM,
        rule=ServiceResolutionRule.DIRECT_SERVICE_CLASS_METHOD_CALL,
    )


def _dedupe_links(
    links: list[EndpointServiceLinkItem],
) -> list[EndpointServiceLinkItem]:
    seen: set[tuple[str, str, int]] = set()
    deduped: list[EndpointServiceLinkItem] = []

    for link in links:
        key = (
            link.endpoint_id,
            link.operation_id,
            link.source.line_start,
        )

        if key in seen:
            continue

        seen.add(key)
        deduped.append(link)

    return deduped


def _link_id(endpoint_id: str, operation_id: str, source: SourceRef) -> str:
    return "|".join(
        [
            endpoint_id,
            operation_id,
            str(source.line_start),
        ]
    )
