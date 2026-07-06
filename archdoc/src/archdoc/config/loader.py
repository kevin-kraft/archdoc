# src/archdoc/config/loader.py

from __future__ import annotations

from pathlib import Path

import yaml

from archdoc.config.models import ArchdocConfig


def load_config(path: Path) -> ArchdocConfig:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))

    cfg = ArchdocConfig.model_validate(raw)

    config_dir = path.parent.resolve()
    project_root = (config_dir / cfg.project.root).resolve()

    cfg.project.root = project_root
    cfg.project.source_root = (project_root / cfg.project.source_root).resolve()
    cfg.output.raw_facts = (project_root / cfg.output.raw_facts).resolve()

    if cfg.output.catalog_dir is not None:
        cfg.output.catalog_dir = (
            project_root / cfg.output.catalog_dir
        ).resolve()

    if cfg.output.docusaurus_static_dir is not None:
        cfg.output.docusaurus_static_dir = (
            project_root / cfg.output.docusaurus_static_dir
        ).resolve()

    if cfg.output.overlays_dir is not None:
        cfg.output.overlays_dir = (
            project_root / cfg.output.overlays_dir
        ).resolve()

    if cfg.output.schema_dir is not None:
        cfg.output.schema_dir = (
            project_root / cfg.output.schema_dir
        ).resolve()

    return cfg

