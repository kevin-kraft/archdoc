from __future__ import annotations

from pathlib import Path
from textwrap import dedent

from archdoc.config.models import ArchdocConfig


def write_file(root: Path, relative_path: str, content: str) -> Path:
    path = root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dedent(content).strip() + "\n", encoding="utf-8")
    return path


def make_config(project_root: Path) -> ArchdocConfig:
    return ArchdocConfig.model_validate(
        {
            "project": {
                "name": "fixture",
                "root": str(project_root),
                "source_root": str(project_root / "app"),
            },
            "scan": {
                "include": ["**/*.py"],
                "exclude": ["**/__pycache__/**", "**/tests/**"],
            },
            "output": {
                "raw_facts": str(project_root / "out" / "raw_code_facts.json"),
                "catalog_dir": str(project_root / "out" / "catalog"),
                "docusaurus_static_dir": str(project_root / "out" / "static"),
            },
            "mapping": {
                "services": {
                    "paths": ["services", "app/services"],
                    "class_suffixes": ["Service"],
                    "exclude_classes": [],
                    "public_methods_as_operations": True,
                    "ignore_method_prefixes": ["_"],
                    "ignore_methods": ["__init__"],
                },
                "endpoints": {
                    "paths": ["routers", "app/routers"],
                    "route_signal_kind": "api_route",
                },
                "actions": {
                    "enabled": True,
                    "include_unmatched_type_usages": True,
                },
                "entities": {
                    "enabled": True,
                    "paths": ["models", "app/models"],
                    "class_base_names": ["Base", "DeclarativeBase"],
                    "field_value_calls": ["Column", "mapped_column", "relationship"],
                    "table_name_fields": ["__tablename__"],
                    "include_pydantic_models": True,
                },
            },
            "naming": {
                "service_id_template": "{domain}.{class_slug}",
                "operation_id_template": "{service_id}.operation.{method_name}",
            },
        }
    )

