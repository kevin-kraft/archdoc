from __future__ import annotations

import json
from pathlib import Path

from archdoc.facts.models import RawCodeFacts


def load_raw_facts(path: Path) -> RawCodeFacts:
    data = json.loads(path.read_text(encoding="utf-8"))
    return RawCodeFacts.model_validate(data)