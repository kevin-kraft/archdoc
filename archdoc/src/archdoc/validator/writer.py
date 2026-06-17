from __future__ import annotations

import json
from pathlib import Path

from archdoc.validator.models import ValidationReport


def write_validation_report(report: ValidationReport, catalog_dir: Path) -> None:
    reports_dir = catalog_dir / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)

    output_path = reports_dir / "validation_report.json"

    output_path.write_text(
        json.dumps(report.model_dump(mode="json"), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )