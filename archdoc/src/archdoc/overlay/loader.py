from __future__ import annotations

from pathlib import Path

from archdoc.overlay.models import ArchitectureOverlay


def load_architecture_overlay(path: Path) -> ArchitectureOverlay:
    return ArchitectureOverlay.model_validate_json(path.read_text(encoding="utf-8"))
