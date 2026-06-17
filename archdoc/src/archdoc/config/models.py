# src/archdoc/config/models.py

from pathlib import Path
from pydantic import BaseModel, Field


class ProjectConfig(BaseModel):
    name: str
    root: Path = Path(".")
    source_root: Path


class OutputConfig(BaseModel):
    raw_facts: Path
    catalog_dir: Path | None = None
    docs_dir: Path | None = None
    docusaurus_static_dir: Path | None = None
    overlays_dir: Path | None = None
    schema_dir: Path | None = None


class ScanConfig(BaseModel):
    include: list[str] = ["**/*.py"]
    exclude: list[str] = []


class ServiceMappingConfig(BaseModel):
    paths: list[str] = Field(default_factory=lambda: ["services"])
    class_suffixes: list[str] = Field(default_factory=lambda: ["Service"])
    exclude_classes: list[str] = Field(default_factory=list)
    public_methods_as_operations: bool = True
    ignore_method_prefixes: list[str] = Field(default_factory=lambda: ["_"])
    ignore_methods: list[str] = Field(default_factory=lambda: ["__init__"])


class FastApiEndpointConfig(BaseModel):
    route_decorators: list[str] = ["get", "post", "put", "patch", "delete"]
    router_names: list[str] = ["router"]


class EndpointMappingConfig(BaseModel):
    paths: list[str] = Field(default_factory=lambda: ["routers", "api"])
    route_signal_kind: str = "api_route"


class ActionPatternConfig(BaseModel):
    name: str
    kind: str
    action: str | None = None
    access: str | None = None
    call_roles: list[str] = Field(default_factory=list)
    call_names: list[str] = Field(default_factory=list)
    call_prefixes: list[str] = Field(default_factory=list)
    call_suffixes: list[str] = Field(default_factory=list)
    call_contains: list[str] = Field(default_factory=list)
    include_nested_calls: bool = False
    confidence: str = "medium"


def _default_action_patterns() -> list[ActionPatternConfig]:
    return [
        ActionPatternConfig(
            name="database_session_call",
            kind="database_action",
            call_roles=["db_call"],
            confidence="high",
        ),
        ActionPatternConfig(
            name="permission_dependency",
            kind="permission_action",
            action="check",
            call_names=["require_permission", "require_any_permission", "has_permission"],
            call_contains=["require_permission", "require_any_permission", "has_permission"],
            include_nested_calls=True,
            confidence="high",
        ),
        ActionPatternConfig(
            name="org_context_dependency",
            kind="permission_action",
            action="tenant_context",
            call_names=["require_org_context"],
            call_contains=["require_org_context"],
            include_nested_calls=True,
            confidence="high",
        ),
        ActionPatternConfig(
            name="audit_event",
            kind="audit_action",
            action="log",
            call_suffixes=[".log_event"],
            call_contains=["AuditService"],
            confidence="high",
        ),
        ActionPatternConfig(
            name="worker_dispatch",
            kind="worker_action",
            action="dispatch",
            call_suffixes=[".delay", ".apply_async", ".enqueue", ".send_task"],
            confidence="medium",
        ),
        ActionPatternConfig(
            name="external_http",
            kind="external_action",
            action="request",
            call_contains=["httpx", "requests.", "resilient_httpx_request"],
            confidence="medium",
        ),
    ]


class ActionMappingConfig(BaseModel):
    enabled: bool = True
    include_unmatched_type_usages: bool = True
    patterns: list[ActionPatternConfig] = Field(default_factory=_default_action_patterns)


class EntityMappingConfig(BaseModel):
    enabled: bool = True
    paths: list[str] = Field(default_factory=lambda: ["models", "app/models"])
    class_base_names: list[str] = Field(default_factory=lambda: ["Base", "DeclarativeBase"])
    field_value_calls: list[str] = Field(default_factory=lambda: ["Column", "mapped_column", "relationship"])
    table_name_fields: list[str] = Field(default_factory=lambda: ["__tablename__"])
    include_pydantic_models: bool = True


class WorkerDispatchCallConfig(BaseModel):
    name: str
    job_type_arg: str = "job_type"
    payload_arg: str = "payload"
    schedule_arg: str | None = "run_at"
    priority_arg: str | None = "priority"
    org_arg: str | None = "org_id"


class WorkerJobModelConfig(BaseModel):
    class_name: str = "Job"
    job_type_kwarg: str = "job_type"
    payload_kwarg: str = "payload"
    schedule_kwarg: str | None = "scheduled_at"
    priority_kwarg: str | None = "priority"
    org_kwarg: str | None = "org_id"


class WorkerMappingConfig(BaseModel):
    enabled: bool = True
    worker_classes: list[str] = Field(default_factory=lambda: ["Worker"])
    dispatch_calls: list[WorkerDispatchCallConfig] = Field(
        default_factory=lambda: [WorkerDispatchCallConfig(name="enqueue_job")]
    )
    job_model_constructors: list[WorkerJobModelConfig] = Field(
        default_factory=lambda: [WorkerJobModelConfig()]
    )
    queue_method_suffixes: list[str] = Field(
        default_factory=lambda: [".delay", ".apply_async", ".enqueue", ".send_task"]
    )
    injected_attribute_names: list[str] = Field(default_factory=lambda: ["worker"])


class OperationLinkMappingConfig(BaseModel):
    enabled: bool = True


class MappingConfig(BaseModel):
    services: ServiceMappingConfig = Field(default_factory=ServiceMappingConfig)
    endpoints: EndpointMappingConfig = Field(default_factory=EndpointMappingConfig)
    actions: ActionMappingConfig = Field(default_factory=ActionMappingConfig)
    entities: EntityMappingConfig = Field(default_factory=EntityMappingConfig)
    workers: WorkerMappingConfig = Field(default_factory=WorkerMappingConfig)
    operation_links: OperationLinkMappingConfig = Field(default_factory=OperationLinkMappingConfig)

class NamingConfig(BaseModel):
    service_id_template: str = "{domain}.{class_slug}"
    operation_id_template: str = "{service_id}.operation.{method_name}"


class ArchdocConfig(BaseModel):
    project: ProjectConfig
    scan: ScanConfig = Field(default_factory=ScanConfig)
    output: OutputConfig
    mapping: MappingConfig = Field(default_factory=MappingConfig)
    naming: NamingConfig = Field(default_factory=NamingConfig)
