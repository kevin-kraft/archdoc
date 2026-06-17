from __future__ import annotations

import json
from pathlib import Path
from typing import Type

from pydantic import BaseModel, Field

from archdoc.catalog.models import (
    ArchitectureActionItem,
    EndpointCatalogItem,
    EndpointGroupCatalogItem,
    EndpointServiceLinkItem,
    OperationLinkItem,
    ServiceCatalogItem,
)
from archdoc.config.models import ArchdocConfig
from archdoc.facts.models import RawCodeFacts
from archdoc.overlay.models import ArchitectureOverlay
from archdoc.validator.models import ValidationReport


class ServicesPayload(BaseModel):
    services: list[ServiceCatalogItem] = Field(default_factory=list)


class EndpointsPayload(BaseModel):
    endpoints: list[EndpointCatalogItem] = Field(default_factory=list)


class EndpointServiceLinksPayload(BaseModel):
    links: list[EndpointServiceLinkItem] = Field(default_factory=list)


class ArchitectureActionsPayload(BaseModel):
    actions: list[ArchitectureActionItem] = Field(default_factory=list)


class OperationLinksPayload(BaseModel):
    links: list[OperationLinkItem] = Field(default_factory=list)


SCHEMA_MODELS: dict[str, Type[BaseModel]] = {
    "archdoc-config": ArchdocConfig,
    "raw-code-facts": RawCodeFacts,
    "architecture-action-item": ArchitectureActionItem,
    "operation-link-item": OperationLinkItem,
    "service-catalog-item": ServiceCatalogItem,
    "endpoint-catalog-item": EndpointCatalogItem,
    "endpoint-group-catalog-item": EndpointGroupCatalogItem,
    "endpoint-service-link-item": EndpointServiceLinkItem,
    "validation-report": ValidationReport,
    "architecture-overlay": ArchitectureOverlay,
    "static-services-payload": ServicesPayload,
    "static-endpoints-payload": EndpointsPayload,
    "static-endpoint-service-links-payload": EndpointServiceLinksPayload,
    "static-architecture-actions-payload": ArchitectureActionsPayload,
    "static-operation-links-payload": OperationLinksPayload,
}


def export_json_schemas(output_dir: Path) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)

    written_paths: list[Path] = []

    for schema_name, model in sorted(SCHEMA_MODELS.items()):
        schema = model.model_json_schema()
        schema["$id"] = f"https://utilis.local/archdoc/schemas/{schema_name}.schema.json"

        output_path = output_dir / f"{schema_name}.schema.json"
        output_path.write_text(
            json.dumps(schema, indent=2, ensure_ascii=False, sort_keys=True),
            encoding="utf-8",
        )
        written_paths.append(output_path)

    return written_paths
