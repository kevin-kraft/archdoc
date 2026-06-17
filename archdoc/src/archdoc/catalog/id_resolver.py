from __future__ import annotations

from collections import defaultdict
from typing import Protocol, TypeVar

from archdoc.catalog.identity import build_source_id
from archdoc.catalog.models import (
    CatalogIdentity,
    EndpointCatalogItem,
    EndpointServiceLinkItem,
    OperationCatalogItem,
    ServiceCatalogItem,
)


class CatalogItemWithIdentity(Protocol):
    id: str
    identity: CatalogIdentity


TItem = TypeVar("TItem", bound=CatalogItemWithIdentity)


def resolve_catalog_id_collisions(
    services: list[ServiceCatalogItem],
    endpoints: list[EndpointCatalogItem],
) -> tuple[list[ServiceCatalogItem], list[EndpointCatalogItem]]:
    _resolve_items(_service_items(services))
    _rebase_operation_ids_to_resolved_services(services)
    _resolve_items(_operation_items(services))
    _resolve_items(endpoints)

    return services, endpoints


def resolve_link_id_collisions(
    links: list[EndpointServiceLinkItem],
) -> list[EndpointServiceLinkItem]:
    _resolve_items(links)
    return links


def _service_items(services: list[ServiceCatalogItem]) -> list[ServiceCatalogItem]:
    return services


def _operation_items(services: list[ServiceCatalogItem]) -> list[OperationCatalogItem]:
    return [
        operation
        for service in services
        for operation in service.operations
    ]


def _rebase_operation_ids_to_resolved_services(services: list[ServiceCatalogItem]) -> None:
    for service in services:
        original_service_id = service.identity.logical_id

        if service.id == original_service_id:
            continue

        original_prefix = f"{original_service_id}.operation."
        resolved_prefix = f"{service.id}.operation."

        for operation in service.operations:
            if not operation.id.startswith(original_prefix):
                continue

            original_operation_id = operation.id
            operation.id = f"{resolved_prefix}{operation.id[len(original_prefix):]}"
            operation.identity.catalog_id = operation.id
            operation.identity.source_id = build_source_id(
                kind="operation",
                source=operation.source,
                qualified_name=operation.qualified_name,
                extra_parts=[service.id, operation.method],
            )
            operation.identity.aliases = _with_alias(
                operation.identity.aliases,
                original_operation_id,
            )


def _resolve_items(items: list[TItem]) -> None:
    groups: dict[str, list[TItem]] = defaultdict(list)

    for item in items:
        groups[item.id].append(item)

    for original_id, duplicates in sorted(groups.items()):
        if len(duplicates) <= 1:
            _sync_identity(duplicates[0], original_id)
            continue

        for item in sorted(duplicates, key=_collision_sort_key):
            unique_id = f"{original_id}--{_source_suffix(item)}"
            _set_resolved_id(item, unique_id, original_id)


def _sync_identity(item: TItem, item_id: str) -> None:
    item.identity.catalog_id = item_id

    if item.identity.logical_id != item_id:
        item.identity.aliases = _with_alias(item.identity.aliases, item.identity.logical_id)


def _set_resolved_id(item: TItem, unique_id: str, original_id: str) -> None:
    item.id = unique_id
    item.identity.catalog_id = unique_id

    if item.identity.logical_id == original_id:
        item.identity.logical_id = original_id

    item.identity.aliases = _with_alias(item.identity.aliases, original_id)


def _collision_sort_key(item: CatalogItemWithIdentity) -> tuple[str, str]:
    return (
        item.identity.source_id,
        item.identity.display_name,
    )


def _source_suffix(item: CatalogItemWithIdentity) -> str:
    return item.identity.source_id.rsplit(":", 1)[-1][:10]


def _with_alias(aliases: list[str], value: str) -> list[str]:
    if value in aliases:
        return aliases

    return [*aliases, value]
