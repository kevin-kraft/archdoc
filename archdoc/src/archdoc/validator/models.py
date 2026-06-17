from __future__ import annotations

from pydantic import BaseModel, Field


class ValidationIssue(BaseModel):
    code: str
    severity: str  # "info" | "warning" | "error"
    message: str
    item_id: str | None = None
    source_file: str | None = None
    line_start: int | None = None
    line_end: int | None = None
    details: dict = Field(default_factory=dict)


class ValidationSummary(BaseModel):
    services: int = 0
    operations: int = 0
    endpoints: int = 0
    endpoint_service_links: int = 0
    linked_endpoints: int = 0
    unlinked_endpoints: int = 0
    unreferenced_operations: int = 0
    errors: int = 0
    warnings: int = 0
    infos: int = 0


class ValidationReport(BaseModel):
    schema_version: str = "validation-report/v0.1"
    summary: ValidationSummary
    issues: list[ValidationIssue] = Field(default_factory=list)