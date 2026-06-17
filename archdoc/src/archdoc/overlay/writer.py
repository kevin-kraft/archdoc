from __future__ import annotations

import json
from pathlib import Path

from archdoc.overlay.models import ArchitectureOverlay


def write_architecture_overlay(
    overlay: ArchitectureOverlay,
    output_path: Path,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    sorted_overlay = overlay.model_copy(
        update={
            "items": sorted(
                overlay.items,
                key=lambda item: (
                    item.target.type,
                    item.target.id,
                    item.target.parent_id or "",
                ),
            )
        }
    )

    output_path.write_text(
        json.dumps(
            sorted_overlay.model_dump(mode="json", exclude_none=True),
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
