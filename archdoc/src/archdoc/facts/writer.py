# src/archdoc/facts/writer.py

from __future__ import annotations

import json
from pathlib import Path

from archdoc.facts.models import RawCodeFacts


def write_raw_facts(facts: RawCodeFacts, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    output_path.write_text(
        json.dumps(
            facts.model_dump(mode="json"),
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )