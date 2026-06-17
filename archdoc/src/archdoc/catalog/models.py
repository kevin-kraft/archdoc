from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, StrEnum
from typing import TypeAlias

from pydantic import BaseModel, Field


class SourceRef(BaseModel):
    file: str
    line_start: int
    line_end: int | None = None


class CatalogIdentity(BaseModel):
    catalog_id: str
    logical_id: str
    source_id: str
    display_name: str
    aliases: list[str] = Field(default_factory=list)

class DetectionConfidence(str, Enum): 
    EXACT = "exact"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNKNOWN = "unknown"

class DetectionInfo(BaseModel):
    method: str
    rule: str
    confidence: DetectionConfidence = DetectionConfidence.UNKNOWN
    evidence: list[str] = Field(default_factory=list)


class OperationCatalogItem(BaseModel):
    id: str
    identity: CatalogIdentity
    method: str
    qualified_name: str
    parameters: list[dict[str, str | None]] = Field(default_factory=list)
    returns: str | None = None
    description: str | None = None
    docstring: str | None = None
    source: SourceRef
    detection: DetectionInfo
    review_status: str = "generated"


class ServiceCatalogItem(BaseModel):
    id: str
    identity: CatalogIdentity
    module: str
    class_name: str
    qualified_name: str
    description: str | None = None
    docstring: str | None = None
    source: SourceRef
    operations: list[OperationCatalogItem] = Field(default_factory=list)
    detection: DetectionInfo
    review_status: str = "generated"

class EndpointParameterItem(BaseModel): 
    name: str
    annotation: str | None = None 
    default: str | None = None
    kind: str | None = None
    source: str | None = None

class EndpointImplementationKind(str, Enum):
    SERVICE_OPERATION = "service_operation"
    SERVICE_CANDIDATE = "service_candidate"
    ROUTER_INTERNAL = "router_internal"
    DIRECT_DB_ACCESS = "direct_db_access"
    PASSTHROUGH = "passthrough"
    EXTERNAL_CALL = "external_call"
    STATIC_OR_TRIVIAL = "static_or_trivial"
    UNKNOWN = "unknown"

class EndpointImplementation(BaseModel): 
    kind: EndpointImplementationKind = EndpointImplementationKind.UNKNOWN
    confidence: DetectionConfidence = DetectionConfidence.UNKNOWN
    reason: str | None = None
    signals: list[str] = Field(default_factory=list)

class EndpointCatalogItem(BaseModel):
    id: str
    identity: CatalogIdentity
    module: str
    function_name: str
    qualified_name: str

   
    implementation: EndpointImplementation = Field(default_factory=EndpointImplementation)

    http_method: str
    path: str | None = None
    include_prefix: str | None = None
    router_prefix: str | None = None
    full_path: str | None = None
    router: str | None = None
    kwargs: dict[str, str] = Field(default_factory=dict)
    parameters: list[EndpointParameterItem] = Field(default_factory=list)
    source: SourceRef
    detection: DetectionInfo
    review_status: str = "generated"
    
    
class EndpointGroupCatalogItem(BaseModel):
    id: str
    module: str
    source_file: str
    endpoints: list[EndpointCatalogItem] = Field(default_factory=list)

class EndpointServiceLinkItem(BaseModel):
    id: str
    identity: CatalogIdentity

    endpoint_id: str
    endpoint_qualified_name: str

    service_id: str
    service_class: str

    operation_id: str
    operation_method: str

    call_name: str

    source: SourceRef
    detection: DetectionInfo
    review_status: str = "generated"


class ActionOwnerRef(BaseModel):
    type: str
    id: str
    qualified_name: str
    class_name: str | None = None
    module: str | None = None


class EntityFieldInfo(BaseModel):
    name: str
    annotation: str | None = None
    value: str | None = None
    value_call: str | None = None
    source: SourceRef


class EntityTypeInfo(BaseModel):
    name: str
    qualified_name: str
    module: str
    kind: str
    table_name: str | None = None
    source: SourceRef
    fields: list[EntityFieldInfo] = Field(default_factory=list)


class QueryInfo(BaseModel):
    variable: str | None = None
    expression: str
    operation: str | None = None
    entities: list[str] = Field(default_factory=list)
    filters: list[str] = Field(default_factory=list)
    joins: list[str] = Field(default_factory=list)
    ordering: list[str] = Field(default_factory=list)
    limit: str | None = None
    entity_details: list[EntityTypeInfo] = Field(default_factory=list)


class ArchitectureActionItem(BaseModel):
    id: str
    identity: CatalogIdentity
    kind: str
    action: str | None = None
    access: str | None = None
    owner: ActionOwnerRef
    call_name: str | None = None
    resource: str | None = None
    entity: str | None = None
    query: QueryInfo | None = None
    source: SourceRef
    detection: DetectionInfo
    details: dict = Field(default_factory=dict)
    review_status: str = "generated"


class OperationLinkEndpoint(BaseModel):
    operation_id: str | None = None
    service_id: str | None = None
    qualified_name: str | None = None
    class_name: str | None = None
    method_name: str | None = None


class OperationLinkItem(BaseModel):
    id: str
    identity: CatalogIdentity
    link_type: str
    source: OperationLinkEndpoint
    target: OperationLinkEndpoint
    call_name: str
    variable: str | None = None
    resolved: bool = False
    confidence: DetectionConfidence = DetectionConfidence.MEDIUM
    source_ref: SourceRef
    detection: DetectionInfo
    details: dict = Field(default_factory=dict)
    review_status: str = "generated"


OperationIndex: TypeAlias = dict[
    tuple[str, str],
    tuple[ServiceCatalogItem, OperationCatalogItem],
]

VariableTypeMap: TypeAlias = dict[str, str]

class ServiceResolutionRule(StrEnum):
    TYPED_OR_ASSIGNED_SERVICE_VARIABLE_METHOD_CALL = (
        "typed_or_assigned_service_variable_method_call"
    )
    RECURSIVE_INHERITED_SERVICE_METHOD_CALL_SERVICE_PREFERRED = (
        "recursive_inherited_service_method_call_service_preferred"
    )
    RECURSIVE_INHERITED_SERVICE_METHOD_CALL_OWNER_FALLBACK = (
        "recursive_inherited_service_method_call_owner_fallback"
    )
    DIRECT_SERVICE_CLASS_METHOD_CALL = "direct_service_class_method_call"
    SERVICE_VARIABLE_FORWARDED_TO_TYPED_HELPER = "service_variable_forwarded_to_typed_helper"

class IgnoredCallRole(StrEnum):
    DB_CALL = "db_call"
    SQLALCHEMY_QUERY_CALL = "sqlalchemy_query_call"
    BUILTIN_OR_UTILITY_CALL = "builtin_or_utility_call"
    CONSTRUCTOR_CALL = "constructor_call"
    NESTED_CALL = "nested_call"


@dataclass(frozen=True)
class ServiceCallMatch:
    service: ServiceCatalogItem
    operation: OperationCatalogItem
    confidence: DetectionConfidence
    rule: ServiceResolutionRule
