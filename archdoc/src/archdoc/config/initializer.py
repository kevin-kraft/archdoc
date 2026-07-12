from __future__ import annotations

from importlib.resources import files
from pathlib import Path


TEMPLATE_PACKAGE = "archdoc.templates"
TEMPLATE_NAME = "archdoc.example.yml"


def read_default_config_template() -> str:
    template = files(TEMPLATE_PACKAGE).joinpath(TEMPLATE_NAME)
    return template.read_text(encoding="utf-8")


def initialize_config(output_path: Path, *, force: bool = False) -> Path:
    destination = output_path.expanduser()
    destination.parent.mkdir(parents=True, exist_ok=True)

    mode = "w" if force else "x"
    with destination.open(mode, encoding="utf-8", newline="\n") as output:
        output.write(read_default_config_template())

    return destination.resolve()
