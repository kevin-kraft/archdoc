from __future__ import annotations
from archdoc.catalog.models import EndpointImplementationKind
from collections import Counter

from archdoc.catalog.models import (
    EndpointCatalogItem,
    EndpointServiceLinkItem,
    ServiceCatalogItem,
    OperationCatalogItem,
)
from archdoc.facts.models import AssignmentFact, ClassFact, FunctionFact, RawCodeFacts
from archdoc.validator.models import (
    ValidationIssue,
    ValidationReport,
    ValidationSummary
)

def validate_catalog(
    facts: RawCodeFacts,
    services: list[ServiceCatalogItem],
    endpoints: list[EndpointCatalogItem],
    links: list[EndpointServiceLinkItem],
) -> ValidationReport:
    issues: list[ValidationIssue] = []

    operation_ids = {
        operation.id
        for service in services
        for operation in service.operations
    }

    service_ids = {service.id for service in services}
    endpoint_ids = {endpoint.id for endpoint in endpoints}

    _check_duplicate_services(services, issues)
    _check_duplicate_operations(services, issues)
    _check_duplicate_endpoints(endpoints, issues)
    _check_identity_consistency(
        services=services,
        endpoints=endpoints,
        links=links,
        issues=issues,
    )
    _check_resolved_logical_id_collisions(
        services=services,
        endpoints=endpoints,
        links=links,
        issues=issues,
    )
    _check_reused_service_class_names(
        services=services,
        issues=issues,
    )
    _check_service_db_session_initialization(
        facts=facts,
        services=services,
        issues=issues,
    )

    _check_broken_links(
        links=links,
        service_ids=service_ids,
        operation_ids=operation_ids,
        endpoint_ids=endpoint_ids,
        issues=issues,
    )

    _check_unlinked_endpoints(
        endpoints=endpoints,
        links=links,
        issues=issues,
    )

    internal_referenced_operation_ids = _find_internal_service_operation_references(
        facts=facts,
        services=services,
    )

    _check_unreferenced_operations(
        services=services,
        links=links,
        internal_referenced_operation_ids=internal_referenced_operation_ids,
        issues=issues,
    )

    _check_empty_services(
        services=services,
        issues=issues,
    )

    _check_raw_parse_errors(
        facts=facts,
        issues=issues,
    )

    summary = _build_summary(
        services=services,
        endpoints=endpoints,
        links=links,
        internal_referenced_operation_ids=internal_referenced_operation_ids,
        issues=issues,
    )

    return ValidationReport(
        summary=summary,
        issues=issues,
    )

# def _check_duplicate_ids(
#     items: list[str],
#     code: str,
#     label: str,
#     issues: list[ValidationIssue],
# ) -> None:
#     counts = Counter(items)

#     for item_id, count in counts.items():
#         if count <= 1:
#             continue

#         issues.append(
#             ValidationIssue(
#                 code=code,
#                 severity="error",
#                 message=f"Duplicate {label} id: {item_id}",
#                 item_id=item_id,
#                 details={"count": count},
#             )
#         )

def _check_broken_links(
    links: list[EndpointServiceLinkItem],
    service_ids: set[str],
    operation_ids: set[str],
    endpoint_ids: set[str],
    issues: list[ValidationIssue],
) -> None:
    for link in links:
        if link.endpoint_id not in endpoint_ids:
            issues.append(
                ValidationIssue(
                    code="link_unknown_endpoint",
                    severity="error",
                    message=f"Link references unknown endpoint: {link.endpoint_id}",
                    item_id=link.endpoint_id,
                    source_file=link.source.file,
                    line_start=link.source.line_start,
                    line_end=link.source.line_end,
                    details={"link": link.model_dump(mode="json")},
                )
            )

        if link.service_id not in service_ids:
            issues.append(
                ValidationIssue(
                    code="link_unknown_service",
                    severity="error",
                    message=f"Link references unknown service: {link.service_id}",
                    item_id=link.service_id,
                    source_file=link.source.file,
                    line_start=link.source.line_start,
                    line_end=link.source.line_end,
                    details={"link": link.model_dump(mode="json")},
                )
            )

        if link.operation_id not in operation_ids:
            issues.append(
                ValidationIssue(
                    code="link_unknown_operation",
                    severity="error",
                    message=f"Link references unknown operation: {link.operation_id}",
                    item_id=link.operation_id,
                    source_file=link.source.file,
                    line_start=link.source.line_start,
                    line_end=link.source.line_end,
                    details={"link": link.model_dump(mode="json")},
                )
            )
def _check_unlinked_endpoints(
    endpoints: list[EndpointCatalogItem],
    links: list[EndpointServiceLinkItem],
    issues: list[ValidationIssue],
) -> None:
    covered_endpoint_ids = _covered_endpoint_ids(endpoints, links)

    for endpoint in endpoints:
        if endpoint.id in covered_endpoint_ids:
            continue

        implementation_kind = endpoint.implementation.kind

        if implementation_kind == EndpointImplementationKind.DIRECT_DB_ACCESS:
            severity = "warning"
            code = "endpoint_direct_db_access"
            message = (
                f"Endpoint has no linked service operation and appears to access the database directly: "
                f"{endpoint.http_method} {endpoint.path}"
            )

        elif implementation_kind == EndpointImplementationKind.ROUTER_INTERNAL:
            severity = "info"
            code = "endpoint_router_internal"
            message = (
                f"Endpoint has no linked service operation and appears to contain router-local logic: "
                f"{endpoint.http_method} {endpoint.path}"
            )

        elif implementation_kind == EndpointImplementationKind.SERVICE_CANDIDATE:
            severity = "warning"
            code = "endpoint_service_candidate_not_linked"
            message = (
                f"Endpoint appears to call a service, but no service operation link was resolved: "
                f"{endpoint.http_method} {endpoint.path}"
            )

        elif implementation_kind == EndpointImplementationKind.STATIC_OR_TRIVIAL:
            severity = "info"
            code = "endpoint_static_or_trivial"
            message = (
                f"Endpoint has no linked service operation and appears to be static or trivial: "
                f"{endpoint.http_method} {endpoint.path}"
            )

        elif implementation_kind == EndpointImplementationKind.EXTERNAL_CALL:
            severity = "warning"
            code = "endpoint_external_call_without_service_link"
            message = (
                f"Endpoint has no linked service operation and appears to call an external API/client: "
                f"{endpoint.http_method} {endpoint.path}"
            )

        elif implementation_kind == EndpointImplementationKind.PASSTHROUGH:
            severity = "info"
            code = "endpoint_passthrough"
            message = (
                f"Endpoint has no linked service operation and appears to delegate to a helper/function: "
                f"{endpoint.http_method} {endpoint.path}"
            )

        else:
            severity = "warning"
            code = "endpoint_without_service_link"
            message = (
                f"Endpoint has no linked service operation: "
                f"{endpoint.http_method} {endpoint.path}"
            )

        issues.append(
            ValidationIssue(
                code=code,
                severity=severity,
                message=message,
                item_id=endpoint.id,
                source_file=endpoint.source.file,
                line_start=endpoint.source.line_start,
                line_end=endpoint.source.line_end,
                details={
                    "module": endpoint.module,
                    "function_name": endpoint.function_name,
                    "qualified_name": endpoint.qualified_name,
                    "http_method": endpoint.http_method,
                    "path": endpoint.path,
                    "implementation_kind": str(endpoint.implementation.kind),
                    "implementation_confidence": str(endpoint.implementation.confidence),
                    "implementation_reason": endpoint.implementation.reason,
                    "implementation_signals": endpoint.implementation.signals,
                },
            )
        )


def _covered_endpoint_ids(
    endpoints: list[EndpointCatalogItem],
    links: list[EndpointServiceLinkItem],
) -> set[str]:
    endpoint_by_id = {endpoint.id: endpoint for endpoint in endpoints}
    linked_endpoint_ids = {link.endpoint_id for link in links}
    linked_qualified_names = {
        endpoint.qualified_name
        for endpoint_id in linked_endpoint_ids
        if (endpoint := endpoint_by_id.get(endpoint_id)) is not None
    }

    covered_endpoint_ids = set(linked_endpoint_ids)
    covered_endpoint_ids.update(
        endpoint.id
        for endpoint in endpoints
        if endpoint.qualified_name in linked_qualified_names
    )
    return covered_endpoint_ids


def _find_internal_service_operation_references(
    facts: RawCodeFacts,
    services: list[ServiceCatalogItem],
) -> set[str]:
    operation_index = _build_service_operation_lookup(services)
    function_index = _build_method_function_index(facts)
    referenced_operation_ids: set[str] = set()

    for service in services:
        for operation in service.operations:
            method_entry = function_index.get(operation.qualified_name)
            if method_entry is None:
                continue

            class_fact, method_fact = method_entry
            variable_types = _infer_service_method_variable_types(class_fact, method_fact)

            for call in method_fact.calls:
                if call.nested_in_call:
                    continue

                receiver, method_name = _split_receiver_call(call.name)
                if not receiver or not method_name:
                    continue

                service_class = variable_types.get(receiver)
                if not service_class:
                    continue

                target = operation_index.get((service_class, method_name))
                if target is None:
                    continue

                _target_service, target_operation = target
                referenced_operation_ids.add(target_operation.id)

    return referenced_operation_ids


def _build_service_operation_lookup(
    services: list[ServiceCatalogItem],
) -> dict[tuple[str, str], tuple[ServiceCatalogItem, OperationCatalogItem]]:
    lookup: dict[tuple[str, str], tuple[ServiceCatalogItem, OperationCatalogItem]] = {}

    for service in services:
        for operation in service.operations:
            lookup[(service.class_name, operation.method)] = (service, operation)
            lookup[(service.qualified_name, operation.method)] = (service, operation)

    return lookup


def _build_method_function_index(
    facts: RawCodeFacts,
) -> dict[str, tuple[ClassFact, FunctionFact]]:
    index: dict[str, tuple[ClassFact, FunctionFact]] = {}

    for file in facts.files:
        for class_fact in file.classes:
            for method in class_fact.methods:
                index[method.qualified_name] = (class_fact, method)

    return index


def _infer_service_method_variable_types(
    class_fact: ClassFact,
    method_fact: FunctionFact,
) -> dict[str, str]:
    variable_types: dict[str, str] = {}

    for parameter in method_fact.parameters:
        if parameter.annotation and _looks_like_service_class(parameter.annotation):
            variable_types[parameter.name] = _normalize_type_name(parameter.annotation)

    for init_method in class_fact.methods:
        if init_method.name != "__init__":
            continue
        _collect_service_assignments(init_method.assignments, variable_types)

    _collect_service_assignments(method_fact.assignments, variable_types)
    return variable_types


def _collect_service_assignments(
    assignments: list[AssignmentFact],
    variable_types: dict[str, str],
) -> None:
    for assignment in assignments:
        if not assignment.value_call:
            continue

        service_class = _normalize_type_name(assignment.value_call)
        if not _looks_like_service_class(service_class):
            continue

        variable_types[assignment.target] = service_class


def _split_receiver_call(call_name: str) -> tuple[str | None, str | None]:
    if "." not in call_name:
        return None, None

    receiver, method_name = call_name.rsplit(".", 1)
    if not receiver or not method_name:
        return None, None

    return receiver, method_name


def _looks_like_service_class(name: str) -> bool:
    normalized = _normalize_type_name(name)
    return normalized.endswith("Service")


def _normalize_type_name(name: str) -> str:
    normalized = name.strip().strip("'\"")

    if "[" in normalized:
        normalized = normalized.split("[", 1)[0]

    if "." in normalized:
        normalized = normalized.rsplit(".", 1)[-1]

    return normalized


def _check_unreferenced_operations(
    services: list[ServiceCatalogItem],
    links: list[EndpointServiceLinkItem],
    internal_referenced_operation_ids: set[str],
    issues: list[ValidationIssue],
) -> None:
    referenced_operation_ids = {link.operation_id for link in links}
    referenced_operation_ids.update(internal_referenced_operation_ids)

    for service in services:
        for operation in service.operations:
            if operation.id in referenced_operation_ids:
                continue

            issues.append(
                ValidationIssue(
                    code="operation_without_endpoint_link",
                    severity="info",
                    message=f"Service operation is not linked from any endpoint: {operation.id}",
                    item_id=operation.id,
                    source_file=operation.source.file,
                    line_start=operation.source.line_start,
                    line_end=operation.source.line_end,
                    details={
                        "service_id": service.id,
                        "service_class": service.class_name,
                        "method": operation.method,
                        "qualified_name": operation.qualified_name,
                    },
                )
            )

def _check_empty_services(
    services: list[ServiceCatalogItem],
    issues: list[ValidationIssue],
) -> None:
    for service in services:
        if service.operations:
            continue

        issues.append(
            ValidationIssue(
                code="service_without_operations",
                severity="warning",
                message=f"Service has no mapped operations: {service.id}",
                item_id=service.id,
                source_file=service.source.file,
                line_start=service.source.line_start,
                line_end=service.source.line_end,
                details={
                    "class_name": service.class_name,
                    "qualified_name": service.qualified_name,
                },
            )
        )


def _check_service_db_session_initialization(
    facts: RawCodeFacts,
    services: list[ServiceCatalogItem],
    issues: list[ValidationIssue],
) -> None:
    services_by_qualified_name: dict[str, list[ServiceCatalogItem]] = {}
    for service in services:
        services_by_qualified_name.setdefault(service.qualified_name, []).append(service)
    for file in facts.files:
        if file.error:
            continue

        for class_fact in file.classes:
            matching_services = services_by_qualified_name.get(class_fact.qualified_name, [])
            if not matching_services:
                continue

            has_self_db_assignment = any(
                assignment.target == "self.db"
                for method in class_fact.methods
                for assignment in method.assignments
            )
            if has_self_db_assignment:
                continue

            for service in matching_services:
                operation_ids_by_qualified_name = {
                    operation.qualified_name: operation.id
                    for operation in service.operations
                }

                for method in class_fact.methods:
                    db_calls = [
                        call
                        for call in method.calls
                        if call.name.startswith("self.db.")
                    ]
                    if not db_calls:
                        continue

                    operation_id = operation_ids_by_qualified_name.get(method.qualified_name)
                    first_call = db_calls[0]
                    issues.append(
                        ValidationIssue(
                            code="service_db_session_not_initialized",
                            severity="warning",
                            message=(
                                "Service method uses self.db, but the service class has no detected self.db assignment."
                            ),
                            item_id=operation_id or method.qualified_name,
                            source_file=first_call.source.file,
                            line_start=first_call.source.line_start,
                            line_end=first_call.source.line_end,
                            details={
                                "service_id": service.id,
                                "service_class": service.class_name,
                                "method": method.name,
                                "qualified_name": method.qualified_name,
                                "db_calls": [call.name for call in db_calls],
                            },
                        )
                    )


def _check_raw_parse_errors(
    facts: RawCodeFacts,
    issues: list[ValidationIssue],
) -> None:
    for file in facts.files:
        if not file.error:
            continue

        issues.append(
            ValidationIssue(
                code="raw_file_parse_error",
                severity="error",
                message=f"Raw scanner could not parse file: {file.path}",
                item_id=file.path,
                source_file=file.path,
                details={"error": file.error},
            )
        )
def _build_summary(
    services: list[ServiceCatalogItem],
    endpoints: list[EndpointCatalogItem],
    links: list[EndpointServiceLinkItem],
    internal_referenced_operation_ids: set[str],
    issues: list[ValidationIssue],
) -> ValidationSummary:
    covered_endpoint_ids = _covered_endpoint_ids(endpoints, links)
    referenced_operation_ids = {link.operation_id for link in links}
    referenced_operation_ids.update(internal_referenced_operation_ids)

    operation_count = sum(len(service.operations) for service in services)

    unreferenced_operation_count = 0

    for service in services:
        for operation in service.operations:
            if operation.id not in referenced_operation_ids:
                unreferenced_operation_count += 1

    errors = sum(1 for issue in issues if issue.severity == "error")
    warnings = sum(1 for issue in issues if issue.severity == "warning")
    infos = sum(1 for issue in issues if issue.severity == "info")

    return ValidationSummary(
        services=len(services),
        operations=operation_count,
        endpoints=len(endpoints),
        endpoint_service_links=len(links),
        linked_endpoints=len(covered_endpoint_ids),
        unlinked_endpoints=len(endpoints) - len(covered_endpoint_ids),
        unreferenced_operations=unreferenced_operation_count,
        errors=errors,
        warnings=warnings,
        infos=infos,
    )

def _check_duplicate_services(
    services: list[ServiceCatalogItem],
    issues: list[ValidationIssue],
) -> None:
    by_id: dict[str, list[ServiceCatalogItem]] = {}

    for service in services:
        by_id.setdefault(service.id, []).append(service)

    for service_id, items in by_id.items():
        if len(items) <= 1:
            continue

        first = items[0]

        issues.append(
            ValidationIssue(
                code="duplicate_service_id",
                severity="error",
                message=f"Duplicate service id: {service_id}",
                item_id=service_id,
                source_file=first.source.file,
                line_start=first.source.line_start,
                line_end=first.source.line_end,
                details={
                    "count": len(items),
                    "duplicates": [
                        {
                            "service_id": item.id,
                            "class_name": item.class_name,
                            "qualified_name": item.qualified_name,
                            "source_file": item.source.file,
                            "line_start": item.source.line_start,
                            "line_end": item.source.line_end,
                        }
                        for item in items
                    ],
                },
            )
        )


def _check_duplicate_operations(
    services: list[ServiceCatalogItem],
    issues: list[ValidationIssue],
) -> None:
    by_id: dict[str, list[tuple[ServiceCatalogItem, OperationCatalogItem]]] = {}

    for service in services:
        for operation in service.operations:
            by_id.setdefault(operation.id, []).append((service, operation))

    for operation_id, items in by_id.items():
        if len(items) <= 1:
            continue

        first_service, first_operation = items[0]

        issues.append(
            ValidationIssue(
                code="duplicate_operation_id",
                severity="error",
                message=f"Duplicate operation id: {operation_id}",
                item_id=operation_id,
                source_file=first_operation.source.file,
                line_start=first_operation.source.line_start,
                line_end=first_operation.source.line_end,
                details={
                    "count": len(items),
                    "duplicates": [
                        {
                            "operation_id": operation.id,
                            "method": operation.method,
                            "qualified_name": operation.qualified_name,
                            "service_id": service.id,
                            "service_class": service.class_name,
                            "source_file": operation.source.file,
                            "line_start": operation.source.line_start,
                            "line_end": operation.source.line_end,
                        }
                        for service, operation in items
                    ],
                },
            )
        )
def _check_duplicate_endpoints(
    endpoints: list[EndpointCatalogItem],
    issues: list[ValidationIssue],
) -> None:
    by_id: dict[str, list[EndpointCatalogItem]] = {}

    for endpoint in endpoints:
        by_id.setdefault(endpoint.id, []).append(endpoint)

    for endpoint_id, items in by_id.items():
        if len(items) <= 1:
            continue

        first = items[0]

        qualified_names = {item.qualified_name for item in items}
        source_locations = {
            (
                item.source.file,
                item.source.line_start,
                item.source.line_end,
            )
            for item in items
        }
        paths = {item.path for item in items}

        same_function = len(qualified_names) == 1
        same_source = len(source_locations) == 1
        different_paths = len(paths) > 1

        if same_function and same_source and different_paths:
            code = "endpoint_id_collision_same_function"
            severity = "warning"
            message = (
                f"Endpoint ID collision for multiple route decorators on the same function: {endpoint_id}"
            )
        else:
            code = "duplicate_endpoint_id"
            severity = "error"
            message = f"Duplicate endpoint id: {endpoint_id}"

        issues.append(
            ValidationIssue(
                code=code,
                severity=severity,
                message=message,
                item_id=endpoint_id,
                source_file=first.source.file,
                line_start=first.source.line_start,
                line_end=first.source.line_end,
                details={
                    "count": len(items),
                    "same_function": same_function,
                    "same_source": same_source,
                    "different_paths": different_paths,
                    "duplicates": [
                        {
                            "endpoint_id": item.id,
                            "module": item.module,
                            "function_name": item.function_name,
                            "qualified_name": item.qualified_name,
                            "http_method": item.http_method,
                            "path": item.path,
                            "source_file": item.source.file,
                            "line_start": item.source.line_start,
                            "line_end": item.source.line_end,
                        }
                        for item in items
                    ],
                },
            )
        )


def _check_identity_consistency(
    services: list[ServiceCatalogItem],
    endpoints: list[EndpointCatalogItem],
    links: list[EndpointServiceLinkItem],
    issues: list[ValidationIssue],
) -> None:
    identity_rows: list[tuple[str, str, str, str | None, int | None, int | None]] = []

    for service in services:
        _check_item_identity("service", service, service.source, issues)
        identity_rows.append(("service", service.id, service.identity.source_id, service.source.file, service.source.line_start, service.source.line_end))

        for operation in service.operations:
            _check_item_identity("operation", operation, operation.source, issues)
            identity_rows.append(("operation", operation.id, operation.identity.source_id, operation.source.file, operation.source.line_start, operation.source.line_end))

    for endpoint in endpoints:
        _check_item_identity("endpoint", endpoint, endpoint.source, issues)
        identity_rows.append(("endpoint", endpoint.id, endpoint.identity.source_id, endpoint.source.file, endpoint.source.line_start, endpoint.source.line_end))

    for link in links:
        _check_item_identity("endpoint_service_link", link, link.source, issues)
        identity_rows.append(("endpoint_service_link", link.id, link.identity.source_id, link.source.file, link.source.line_start, link.source.line_end))

    by_source_id: dict[tuple[str, str], list[tuple[str, str, str, str | None, int | None, int | None]]] = {}

    for row in identity_rows:
        target_type, _item_id, source_id, *_ = row
        by_source_id.setdefault((target_type, source_id), []).append(row)

    for (target_type, source_id), rows in by_source_id.items():
        if len(rows) <= 1:
            continue

        first = rows[0]
        issues.append(
            ValidationIssue(
                code="duplicate_identity_source_id",
                severity="error",
                message=f"Duplicate {target_type} source identity: {source_id}",
                item_id=source_id,
                source_file=first[3],
                line_start=first[4],
                line_end=first[5],
                details={
                    "target_type": target_type,
                    "source_id": source_id,
                    "duplicates": [
                        {
                            "item_id": row[1],
                            "source_file": row[3],
                            "line_start": row[4],
                            "line_end": row[5],
                        }
                        for row in rows
                    ],
                },
            )
        )


def _check_item_identity(target_type: str, item, source, issues: list[ValidationIssue]) -> None:
    if item.id == item.identity.catalog_id:
        return

    issues.append(
        ValidationIssue(
            code="catalog_identity_mismatch",
            severity="error",
            message=f"{target_type} id does not match identity.catalog_id: {item.id}",
            item_id=item.id,
            source_file=source.file,
            line_start=source.line_start,
            line_end=source.line_end,
            details={
                "target_type": target_type,
                "id": item.id,
                "catalog_id": item.identity.catalog_id,
                "logical_id": item.identity.logical_id,
                "source_id": item.identity.source_id,
            },
        )
    )


def _check_resolved_logical_id_collisions(
    services: list[ServiceCatalogItem],
    endpoints: list[EndpointCatalogItem],
    links: list[EndpointServiceLinkItem],
    issues: list[ValidationIssue],
) -> None:
    _check_resolved_item_logical_ids(
        target_type="service",
        items=services,
        issues=issues,
        severity="info",
    )
    _check_resolved_item_logical_ids(
        target_type="operation",
        items=[
            operation
            for service in services
            for operation in service.operations
        ],
        issues=issues,
        severity="info",
    )
    _check_resolved_item_logical_ids(
        target_type="endpoint",
        items=endpoints,
        issues=issues,
        severity="warning",
    )
    _check_resolved_item_logical_ids(
        target_type="endpoint_service_link",
        items=links,
        issues=issues,
        severity="info",
    )


def _check_resolved_item_logical_ids(
    target_type: str,
    items: list,
    issues: list[ValidationIssue],
    severity: str,
) -> None:
    by_logical_id: dict[str, list] = {}

    for item in items:
        by_logical_id.setdefault(item.identity.logical_id, []).append(item)

    for logical_id, logical_items in sorted(by_logical_id.items()):
        catalog_ids = {item.identity.catalog_id for item in logical_items}

        if len(catalog_ids) <= 1:
            continue

        first = logical_items[0]
        issues.append(
            ValidationIssue(
                code=f"resolved_{target_type}_logical_id_collision",
                severity=severity,
                message=(
                    f"Multiple {target_type} items share logical_id {logical_id} "
                    "and were assigned unique catalog IDs."
                ),
                item_id=logical_id,
                source_file=first.source.file,
                line_start=first.source.line_start,
                line_end=first.source.line_end,
                details={
                    "target_type": target_type,
                    "logical_id": logical_id,
                    "count": len(logical_items),
                    "recommendation": (
                        "Review whether the similarly identified architecture items are intentional. "
                        "If they are expected, keep the resolved catalog IDs; otherwise adjust naming "
                        "or mapping configuration."
                    ),
                    "resolved_items": [
                        _resolved_item_details(item)
                        for item in logical_items
                    ],
                },
            )
        )


def _check_reused_service_class_names(
    services: list[ServiceCatalogItem],
    issues: list[ValidationIssue],
) -> None:
    by_class_name: dict[str, list[ServiceCatalogItem]] = {}

    for service in services:
        by_class_name.setdefault(service.class_name, []).append(service)

    for class_name, class_services in sorted(by_class_name.items()):
        if len(class_services) <= 1:
            continue

        source_files = {service.source.file for service in class_services}

        if len(source_files) <= 1:
            continue

        first = class_services[0]
        issues.append(
            ValidationIssue(
                code="service_class_name_reused",
                severity="info",
                message=(
                    f"Service class name is reused across multiple source files: {class_name}"
                ),
                item_id=class_name,
                source_file=first.source.file,
                line_start=first.source.line_start,
                line_end=first.source.line_end,
                details={
                    "class_name": class_name,
                    "count": len(class_services),
                    "recommendation": (
                        "Review whether these classes represent distinct architecture services. "
                        "If yes, the resolved catalog IDs keep them separate; if not, refine mapping "
                        "or rename/exclude one candidate."
                    ),
                    "services": [
                        {
                            "catalog_id": service.identity.catalog_id,
                            "logical_id": service.identity.logical_id,
                            "module": service.module,
                            "qualified_name": service.qualified_name,
                            "source_file": service.source.file,
                            "line_start": service.source.line_start,
                            "line_end": service.source.line_end,
                        }
                        for service in class_services
                    ],
                },
            )
        )


def _resolved_item_details(item) -> dict:
    details = {
        "catalog_id": item.identity.catalog_id,
        "logical_id": item.identity.logical_id,
        "source_id": item.identity.source_id,
        "display_name": item.identity.display_name,
        "source_file": item.source.file,
        "line_start": item.source.line_start,
        "line_end": item.source.line_end,
    }

    if hasattr(item, "qualified_name"):
        details["qualified_name"] = item.qualified_name
    if hasattr(item, "class_name"):
        details["class_name"] = item.class_name
    if hasattr(item, "method"):
        details["method"] = item.method
    if hasattr(item, "http_method"):
        details["http_method"] = item.http_method
    if hasattr(item, "path"):
        details["path"] = item.path

    return details
