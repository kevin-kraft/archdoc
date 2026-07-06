from __future__ import annotations

import re
from pathlib import Path

from archdoc.catalog.models import (
    DetectionInfo,
    OperationCatalogItem,
    ServiceCatalogItem,
    SourceRef,
    DetectionConfidence
)
from archdoc.catalog.identity import build_catalog_identity
from archdoc.facts.models import ClassIndex
from archdoc.utils.class_index import (
    build_class_index,
    collect_inherited_methods_for_service,
)

from archdoc.config.models import ArchdocConfig
from archdoc.facts.models import ClassFact, FileFact, FunctionFact, RawCodeFacts


def map_services(
    facts: RawCodeFacts,
    config: ArchdocConfig,
) -> list[ServiceCatalogItem]:
    services: list[ServiceCatalogItem] = []
    class_index = build_class_index(facts)

    for file in facts.files:
        if file.error:
            continue

        if not _is_in_service_path(file.path, config.mapping.services.paths):
            continue

        for cls in file.classes:
            if not _is_service_class(cls, config.mapping.services.class_suffixes):
                continue

            if _is_excluded_service_class(cls, config):
                continue

            service = _map_service(file, cls, config, class_index)
            services.append(service)

    return sorted(services, key=lambda service: service.id)


def _is_in_service_path(file_path: str, service_paths: list[str]) -> bool:
    normalized = file_path.replace("\\", "/")

    for service_path in service_paths:
        service_path = service_path.strip("/").replace("\\", "/")

        if normalized.startswith(service_path + "/"):
            return True

        if f"/{service_path}/" in normalized:
            return True

    return False


def _is_service_class(cls: ClassFact, suffixes: list[str]) -> bool:
    return any(cls.name.endswith(suffix) for suffix in suffixes)


def _is_excluded_service_class(cls: ClassFact, config: ArchdocConfig) -> bool:
    excluded = set(config.mapping.services.exclude_classes)
    return cls.name in excluded or cls.qualified_name in excluded


def _map_service(
    file: FileFact,
    cls: ClassFact,
    config: ArchdocConfig,
    class_index: ClassIndex
) -> ServiceCatalogItem:
    domain = _domain_from_path(file.path, config.mapping.services.paths)
    class_slug = _class_name_to_slug(cls.name)

    service_id = config.naming.service_id_template.format(
        domain=domain,
        class_slug=class_slug,
        class_name=cls.name,
        module=file.module,
    )

    method_entries = collect_inherited_methods_for_service(
    class_name=cls.name,
    class_index=class_index,
)

    operations = [
        _map_operation(
            service_id=service_id,
            method=method,
            config=config,
            owner_class=owner_cls,
            service_class=cls,
        )
        for owner_cls, method in method_entries
        if _is_operation_method(method, config)
    ]
    
    def _dedupe_operations_by_id(
        operations: list[OperationCatalogItem],
    ) -> list[OperationCatalogItem]:
        seen: dict[str, OperationCatalogItem] = {}
        result: list[OperationCatalogItem] = []

        for operation in operations:
            existing = seen.get(operation.id)

            if existing is not None:
                continue

            seen[operation.id] = operation
            result.append(operation)

        return result
    
    operations = _dedupe_operations_by_id(operations)

    service_source = SourceRef(
        file=cls.source.file,
        line_start=cls.source.line_start,
        line_end=cls.source.line_end,
    )

    return ServiceCatalogItem(
        id=service_id,
        identity=build_catalog_identity(
            kind="service",
            logical_id=service_id,
            display_name=cls.name,
            source=service_source,
            qualified_name=cls.qualified_name,
            aliases=[cls.qualified_name],
        ),
        module=file.module,
        class_name=cls.name,
        qualified_name=cls.qualified_name,
        description=_docstring_summary(cls.docstring),
        docstring=cls.docstring,
        source=service_source,
        operations=operations,
        detection=DetectionInfo(
            method="rule",
            rule="class_suffix_and_service_path",
            confidence=DetectionConfidence.HIGH,
            evidence=[
                f"class_name={cls.name}",
                f"source_path={file.path}",
            ],
        ),
        review_status="generated",
    )


def _map_operation(
    service_id: str,
    method: FunctionFact,
    config: ArchdocConfig,
    owner_class: ClassFact | None = None,
    service_class: ClassFact | None = None,
) -> OperationCatalogItem:
    operation_id = config.naming.operation_id_template.format(
        service_id=service_id,
        method_name=method.name,
    )

    rule = "public_method_in_service_class"

    if owner_class is not None and service_class is not None:
        if owner_class.name != service_class.name:
            rule = f"inherited_public_method_from_{owner_class.name}"

    operation_source = SourceRef(
        file=method.source.file,
        line_start=method.source.line_start,
        line_end=method.source.line_end,
    )

    return OperationCatalogItem(
        id=operation_id,
        identity=build_catalog_identity(
            kind="operation",
            logical_id=operation_id,
            display_name=f"{service_class.name if service_class else service_id}.{method.name}",
            source=operation_source,
            qualified_name=method.qualified_name,
            extra_parts=[service_id, method.name],
            aliases=[method.qualified_name],
        ),
        method=method.name,
        qualified_name=method.qualified_name,
        parameters=[
            {
                "name": parameter.name,
                "annotation": parameter.annotation,
                "default": parameter.default,
                "kind": parameter.kind,
            }
            for parameter in method.parameters
            if parameter.name != "self"
        ],
        returns=method.returns,
        description=_docstring_summary(method.docstring),
        docstring=method.docstring,
        source=operation_source,
        detection=DetectionInfo(
            method=rule,
            rule=rule,
            confidence=DetectionConfidence.HIGH,
            evidence=[
                f"method_name={method.name}",
                f"qualified_name={method.qualified_name}",
            ],
        ),
        review_status="generated",
    )


def _docstring_summary(docstring: str | None) -> str | None:
    if not docstring:
        return None

    for line in docstring.splitlines():
        stripped = line.strip()
        if stripped:
            return stripped

    return None


def _is_operation_method(
    method: FunctionFact,
    config: ArchdocConfig,
) -> bool:
    service_cfg = config.mapping.services

    if method.name in service_cfg.ignore_methods:
        return False

    if any(method.name.startswith(prefix) for prefix in service_cfg.ignore_method_prefixes):
        return False

    if service_cfg.public_methods_as_operations and method.visibility != "public":
        return False

    return True


def _domain_from_path(file_path: str, service_paths: list[str]) -> str:
    """
    Example:
    file_path = "services/finance/budget.py"
    service_path = "services"
    domain = "finance"

    file_path = "app/services/finance/budget.py"
    service_path = "app/services"
    domain = "finance"
    """
    normalized = file_path.replace("\\", "/")
    parts = normalized.split("/")

    for service_path in service_paths:
        service_parts = service_path.strip("/").replace("\\", "/").split("/")

        idx = _find_subsequence(parts, service_parts)

        if idx is None:
            continue

        domain_index = idx + len(service_parts)

        if domain_index < len(parts) - 1:
            return _slugify(parts[domain_index])

    return "unknown"


def _find_subsequence(parts: list[str], needle: list[str]) -> int | None:
    if not needle:
        return None

    for i in range(0, len(parts) - len(needle) + 1):
        if parts[i : i + len(needle)] == needle:
            return i

    return None


def _class_name_to_slug(class_name: str) -> str:
    name = class_name

    if name.endswith("Service"):
        name = name[: -len("Service")]

    return _camel_to_snake(name).replace("_", "-")


def _camel_to_snake(value: str) -> str:
    value = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", value)
    value = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", value)
    return value.lower()


def _slugify(value: str) -> str:
    return value.lower().replace("_", "-")

