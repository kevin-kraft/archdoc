from __future__ import annotations

import json
from pathlib import Path

from archdoc.catalog.models import (
    ArchitectureActionItem,
    EndpointCatalogItem,
    EndpointServiceLinkItem,
    OperationLinkItem,
    ServiceCatalogItem,
)
from archdoc.validator.models import ValidationReport


def export_docusaurus_data(
    services: list[ServiceCatalogItem],
    endpoints: list[EndpointCatalogItem],
    links: list[EndpointServiceLinkItem],
    validation_report: ValidationReport,
    output_dir: Path,
    actions: list[ArchitectureActionItem] | None = None,
    operation_links: list[OperationLinkItem] | None = None,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    _write_json(output_dir / "services.json", {
        "services": [service.model_dump(mode="json") for service in services]
    })

    _write_json(output_dir / "endpoints.json", {
        "endpoints": [endpoint.model_dump(mode="json") for endpoint in endpoints]
    })

    _write_json(output_dir / "endpoint_service_links.json", {
        "links": [link.model_dump(mode="json") for link in links]
    })

    _write_json(output_dir / "architecture_actions.json", {
        "actions": [
            action.model_dump(mode="json")
            for action in (actions or [])
        ]
    })

    _write_json(output_dir / "operation_links.json", {
        "links": [
            link.model_dump(mode="json")
            for link in (operation_links or [])
        ]
    })

    _write_json(output_dir / "validation_report.json", validation_report.model_dump(mode="json"))


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
