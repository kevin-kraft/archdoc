from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class OverlayTargetType(StrEnum):
    SERVICE = "service"
    OPERATION = "operation"
    ENDPOINT = "endpoint"
    ENDPOINT_SERVICE_LINK = "endpoint_service_link"
    ARCHITECTURE_ACTION = "architecture_action"
    VALIDATION_ISSUE = "validation_issue"
    USER_STORY = "user_story"
    BPMN_PROCESS = "bpmn_process"
    BPMN_TASK = "bpmn_task"


class OverlayReviewStatus(StrEnum):
    GENERATED = "generated"
    NEEDS_REVIEW = "needs_review"
    REVIEWED = "reviewed"
    ACCEPTED = "accepted"
    NEEDS_REFACTOR = "needs_refactor"
    FALSE_POSITIVE = "false_positive"
    DEPRECATED = "deprecated"


class OverlayTarget(BaseModel):
    type: OverlayTargetType
    id: str
    parent_id: str | None = None
    source_file: str | None = None
    line_start: int | None = None


class OverlayMetadata(BaseModel):
    author: str | None = None
    updated_at: str | None = None
    rationale: str | None = None


class CatalogOverlayItem(BaseModel):
    target: OverlayTarget
    review_status: OverlayReviewStatus | None = None
    labels: list[str] = Field(default_factory=list)
    status_markers: list[str] = Field(default_factory=list)
    owner: str | None = None
    notes: str | None = None
    links: dict[str, list[str]] = Field(default_factory=dict)
    overrides: dict[str, Any] = Field(default_factory=dict)
    metadata: OverlayMetadata = Field(default_factory=OverlayMetadata)


class ArchitectureOverlay(BaseModel):
    schema_version: str = "architecture-overlay/v0.1"
    project_name: str
    catalog_version: str | None = None
    items: list[CatalogOverlayItem] = Field(default_factory=list)


class OverlayUpdate(BaseModel):
    review_status: OverlayReviewStatus | None = None
    labels: list[str] = Field(default_factory=list)
    status_markers: list[str] = Field(default_factory=list)
    owner: str | None = None
    notes: str | None = None
    links: dict[str, list[str]] = Field(default_factory=dict)
    overrides: dict[str, Any] = Field(default_factory=dict)
    metadata: OverlayMetadata = Field(default_factory=OverlayMetadata)


class EffectiveCatalog(BaseModel):
    services: list[dict[str, Any]] = Field(default_factory=list)
    endpoints: list[dict[str, Any]] = Field(default_factory=list)
    links: list[dict[str, Any]] = Field(default_factory=list)
    actions: list[dict[str, Any]] = Field(default_factory=list)
    validation_report: dict[str, Any] | None = None
    overlay: ArchitectureOverlay


class TablePage(BaseModel):
    rows: list[dict[str, Any]] = Field(default_factory=list)
    total: int = 0
    limit: int = 50
    offset: int = 0
