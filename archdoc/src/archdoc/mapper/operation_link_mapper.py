from __future__ import annotations

import re

from archdoc.catalog.identity import build_catalog_identity
from archdoc.catalog.models import (
    DetectionConfidence,
    DetectionInfo,
    OperationCatalogItem,
    OperationLinkEndpoint,
    OperationLinkItem,
    ServiceCatalogItem,
    SourceRef,
)
from archdoc.config.models import ArchdocConfig
from archdoc.facts.models import AssignmentFact, ClassFact, FileFact, FunctionFact, RawCodeFacts


def map_operation_links(
    facts: RawCodeFacts,
    config: ArchdocConfig,
    services: list[ServiceCatalogItem],
) -> list[OperationLinkItem]:
    if not config.mapping.operation_links.enabled:
        return []

    operation_by_qualified_name = _operation_by_qualified_name(services)
    service_by_class_name = _service_by_class_name(services)
    operation_by_service_and_method = _operation_by_service_and_method(services)
    links: list[OperationLinkItem] = []

    for file in facts.files:
        if file.error:
            continue

        for class_fact in file.classes:
            class_service_bindings = _class_service_bindings(class_fact, service_by_class_name)

            for method in class_fact.methods:
                source_entry = operation_by_qualified_name.get(method.qualified_name)
                if source_entry is None:
                    continue

                source_service, source_operation = source_entry
                bindings = {
                    **class_service_bindings,
                    **_function_service_bindings(method, service_by_class_name),
                }

                for call in method.calls:
                    target = _target_from_call(
                        call_name=call.name,
                        bindings=bindings,
                        service_by_class_name=service_by_class_name,
                        operation_by_service_and_method=operation_by_service_and_method,
                    )
                    if target is None:
                        continue

                    target_service, target_operation, variable, target_method_name = target
                    if target_operation is not None and target_operation.id == source_operation.id:
                        continue

                    source_ref = SourceRef(
                        file=call.source.file,
                        line_start=call.source.line_start,
                        line_end=call.source.line_end,
                    )
                    target_endpoint = OperationLinkEndpoint(
                        operation_id=target_operation.id if target_operation else None,
                        service_id=target_service.id,
                        qualified_name=target_operation.qualified_name if target_operation else None,
                        class_name=target_service.class_name,
                        method_name=target_method_name,
                    )
                    link_id = (
                        f"{source_operation.id}.link.{len(links)}."
                        f"{_slug(target_service.id)}.{_slug(target_method_name or call.name)}"
                    )

                    links.append(
                        OperationLinkItem(
                            id=link_id,
                            identity=build_catalog_identity(
                                kind="operation_link",
                                logical_id=link_id,
                                display_name=f"{source_operation.method} -> {target_service.class_name}.{target_method_name}",
                                source=source_ref,
                                qualified_name=source_operation.qualified_name,
                                extra_parts=[source_operation.id, target_service.id, target_method_name or call.name],
                                aliases=[
                                    source_operation.id,
                                    target_service.id,
                                    target_service.class_name,
                                    call.name,
                                ],
                            ),
                            link_type="service_call",
                            source=OperationLinkEndpoint(
                                operation_id=source_operation.id,
                                service_id=source_service.id,
                                qualified_name=source_operation.qualified_name,
                                class_name=source_service.class_name,
                                method_name=source_operation.method,
                            ),
                            target=target_endpoint,
                            call_name=call.name,
                            variable=variable,
                            resolved=target_operation is not None,
                            confidence=DetectionConfidence.HIGH if target_operation else DetectionConfidence.MEDIUM,
                            source_ref=source_ref,
                            detection=DetectionInfo(
                                method="call_graph",
                                rule="service_instance_method_call",
                                confidence=DetectionConfidence.HIGH if target_operation else DetectionConfidence.MEDIUM,
                                evidence=[
                                    f"source_operation={source_operation.id}",
                                    f"call={call.name}",
                                    f"target_service={target_service.id}",
                                    f"target_method={target_method_name}",
                                ],
                            ),
                            details={
                                "awaited": call.awaited,
                                "nested_in_call": call.nested_in_call,
                                "args": call.args,
                                "kwargs": call.kwargs,
                            },
                        )
                    )

    return sorted(_dedupe_links(links), key=lambda link: link.id)


def _operation_by_qualified_name(
    services: list[ServiceCatalogItem],
) -> dict[str, tuple[ServiceCatalogItem, OperationCatalogItem]]:
    return {
        operation.qualified_name: (service, operation)
        for service in services
        for operation in service.operations
    }


def _service_by_class_name(services: list[ServiceCatalogItem]) -> dict[str, ServiceCatalogItem]:
    return {service.class_name: service for service in services}


def _operation_by_service_and_method(
    services: list[ServiceCatalogItem],
) -> dict[tuple[str, str], OperationCatalogItem]:
    return {
        (service.id, operation.method): operation
        for service in services
        for operation in service.operations
    }


def _class_service_bindings(
    class_fact: ClassFact,
    service_by_class_name: dict[str, ServiceCatalogItem],
) -> dict[str, ServiceCatalogItem]:
    bindings: dict[str, ServiceCatalogItem] = {}

    for method in class_fact.methods:
        if method.name != "__init__":
            continue

        bindings.update(_function_service_bindings(method, service_by_class_name))

    return bindings


def _function_service_bindings(
    function: FunctionFact,
    service_by_class_name: dict[str, ServiceCatalogItem],
) -> dict[str, ServiceCatalogItem]:
    bindings: dict[str, ServiceCatalogItem] = {}

    for assignment in function.assignments:
        service = _service_from_assignment(assignment, service_by_class_name)
        if service is not None:
            bindings[assignment.target] = service

    return bindings


def _service_from_assignment(
    assignment: AssignmentFact,
    service_by_class_name: dict[str, ServiceCatalogItem],
) -> ServiceCatalogItem | None:
    if assignment.value_call and assignment.value_call in service_by_class_name:
        return service_by_class_name[assignment.value_call]

    if assignment.value:
        match = re.match(r"([A-Z][A-Za-z0-9_]*Service)\(", assignment.value)
        if match and match.group(1) in service_by_class_name:
            return service_by_class_name[match.group(1)]

    return None


def _target_from_call(
    call_name: str,
    bindings: dict[str, ServiceCatalogItem],
    service_by_class_name: dict[str, ServiceCatalogItem],
    operation_by_service_and_method: dict[tuple[str, str], OperationCatalogItem],
) -> tuple[ServiceCatalogItem, OperationCatalogItem | None, str | None, str | None] | None:
    parts = call_name.split(".")
    if len(parts) < 2:
        return None

    variable = ".".join(parts[:-1])
    method_name = parts[-1]

    service = bindings.get(variable)
    if service is None and len(parts) >= 3:
        service = bindings.get(".".join(parts[:-2]))

    if service is None and parts[0] in service_by_class_name:
        service = service_by_class_name[parts[0]]

    if service is None:
        return None

    return (
        service,
        operation_by_service_and_method.get((service.id, method_name)),
        variable,
        method_name,
    )


def _dedupe_links(links: list[OperationLinkItem]) -> list[OperationLinkItem]:
    seen: set[tuple[str | None, str | None, str, int]] = set()
    result: list[OperationLinkItem] = []

    for link in links:
        key = (
            link.source.operation_id,
            link.target.operation_id or link.target.service_id,
            link.call_name,
            link.source_ref.line_start,
        )
        if key in seen:
            continue

        seen.add(key)
        result.append(link)

    return result


def _slug(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_.-]+", "-", value).strip("-").lower()
