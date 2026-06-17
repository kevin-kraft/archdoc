from __future__ import annotations

import json
from pathlib import Path

from archdoc.catalog.models import ArchitectureActionItem, EndpointCatalogItem, OperationLinkItem, ServiceCatalogItem
from archdoc.catalog.models import EndpointServiceLinkItem

def write_service_catalog(
    services: list[ServiceCatalogItem],
    catalog_dir: Path,
) -> None:
    services_dir = catalog_dir / "services"
    services_dir.mkdir(parents=True, exist_ok=True)

    for service in services:
        output_path = services_dir / f"{service.id}.json"

        output_path.write_text(
            json.dumps(
                service.model_dump(mode="json"),
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

def write_endpoint_catalog(
    endpoints: list[EndpointCatalogItem],
    catalog_dir: Path,
) -> None:
    endpoints_dir = catalog_dir / "endpoints"
    endpoints_dir.mkdir(parents=True, exist_ok=True)

    grouped: dict[str, list[EndpointCatalogItem]] = {}

    for endpoint in endpoints:
        grouped.setdefault(endpoint.module, []).append(endpoint)

    for module, module_endpoints in grouped.items():
        safe_name = module.replace("/", ".")
        output_path = endpoints_dir / f"{safe_name}.json"

        payload = {
            "id": module,
            "module": module,
            "source_file": module_endpoints[0].source.file,
            "endpoints": [
                endpoint.model_dump(mode="json")
                for endpoint in sorted(module_endpoints, key=lambda item: item.id)
            ],
        }

        output_path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )


def write_endpoint_service_links(
    links: list[EndpointServiceLinkItem],
    catalog_dir: Path,
) -> None:
    links_dir = catalog_dir / "links"
    links_dir.mkdir(parents=True, exist_ok=True)

    output_path = links_dir / "endpoint_service_links.json"

    payload = {
        "id": "endpoint_service_links",
        "links": [
            link.model_dump(mode="json")
            for link in sorted(
                links,
                key=lambda item: (item.endpoint_id, item.operation_id),
            )
        ],
    }

    output_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def write_action_catalog(
    actions: list[ArchitectureActionItem],
    catalog_dir: Path,
) -> None:
    actions_dir = catalog_dir / "actions"
    actions_dir.mkdir(parents=True, exist_ok=True)

    output_path = actions_dir / "architecture_actions.json"
    payload = {
        "id": "architecture_actions",
        "actions": [
            action.model_dump(mode="json")
            for action in sorted(actions, key=lambda item: item.id)
        ],
    }

    output_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def write_operation_link_catalog(
    operation_links: list[OperationLinkItem],
    catalog_dir: Path,
) -> None:
    links_dir = catalog_dir / "links"
    links_dir.mkdir(parents=True, exist_ok=True)

    output_path = links_dir / "operation_links.json"
    payload = {
        "id": "operation_links",
        "links": [
            link.model_dump(mode="json")
            for link in sorted(operation_links, key=lambda item: item.id)
        ],
    }

    output_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
