# src/archdoc/scanner/ast_utils.py

from __future__ import annotations

import ast
from pathlib import Path

from archdoc.facts.models import SourceLocation


def source_location(node: ast.AST, file_path: str) -> SourceLocation:
    return SourceLocation(
        file=file_path,
        line_start=getattr(node, "lineno", 1),
        line_end=getattr(node, "end_lineno", getattr(node, "lineno", 1)),
    )


def module_name_from_path(file_path: Path, source_root: Path) -> str:
    relative = file_path.relative_to(source_root).with_suffix("")
    return ".".join(relative.parts)


def ast_to_str(node: ast.AST | None) -> str | None:
    if node is None:
        return None

    try:
        return ast.unparse(node)
    except Exception:
        return None
    
def collect_parent_map(root: ast.AST) -> dict[int, ast.AST]:
    parent_map: dict[int, ast.AST] = {}

    for parent in ast.walk(root):
        for child in ast.iter_child_nodes(parent):
            parent_map[id(child)] = parent

    return parent_map

def get_name(node: ast.AST) -> str:
    """
    Converts common AST expressions to readable names.

    Examples:
    - Name("select")                  -> "select"
    - Attribute(self.db.execute)      -> "self.db.execute"
    - Call(finance_core())            -> "finance_core"
    - Subscript(list[str])            -> "list[str]"
    """
    if isinstance(node, ast.Name):
        return node.id

    if isinstance(node, ast.Attribute):
        base = get_name(node.value)
        return f"{base}.{node.attr}" if base else node.attr

    if isinstance(node, ast.Call):
        return get_name(node.func)

    if isinstance(node, ast.Subscript):
        return ast_to_str(node) or ""

    if isinstance(node, ast.Constant):
        return repr(node.value)

    return ast_to_str(node) or ""


def visibility_from_name(name: str) -> str:
    if name.startswith("__") and name.endswith("__"):
        return "magic"

    if name.startswith("_"):
        return "private"

    return "public"


def literal_or_expr_to_str(node: ast.AST) -> str:
    """
    For decorator args/kwargs.

    Literal strings become clean values.
    Expressions become source-like strings.
    """
    if isinstance(node, ast.Constant):
        return str(node.value)

    return ast_to_str(node) or ""