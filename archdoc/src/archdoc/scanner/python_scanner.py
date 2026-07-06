# src/archdoc/scanner/python_scanner.py

from __future__ import annotations

import ast
from fnmatch import fnmatch
from pathlib import Path

from archdoc.config.models import ArchdocConfig
from archdoc.facts.models import (
    CallFact,
    ClassFact,
    ClassFieldFact,
    DecoratorFact,
    FileFact,
    FunctionFact,
    ImportFact,
    ImportNameFact,
    ParameterFact,
    RawCodeFacts,
    SignalFact,
    SourceLocation,
    AssignmentFact
)
from archdoc.scanner.ast_utils import (
    ast_to_str,
    get_name,
    literal_or_expr_to_str,
    module_name_from_path,
    source_location,
    visibility_from_name,
    collect_parent_map
)


def scan_project(config: ArchdocConfig) -> RawCodeFacts:
    """
    Layer 1 entrypoint.

    Scans Python files and returns raw syntax-level facts.
    No architecture interpretation happens here.
    """
    source_root = config.project.source_root.resolve()

    python_files = _find_python_files(
        source_root=source_root,
        include_patterns=config.scan.include,
        exclude_patterns=config.scan.exclude,
    )

    files: list[FileFact] = []

    for file_path in python_files:
        files.append(_scan_python_file(file_path, source_root))

    return RawCodeFacts(
        project_name=config.project.name,
        source_root=str(source_root),
        files=files,
    )


def _find_python_files(
    source_root: Path,
    include_patterns: list[str],
    exclude_patterns: list[str],
) -> list[Path]:
    if not source_root.exists():
        raise FileNotFoundError(f"Source root does not exist: {source_root}")

    if not source_root.is_dir():
        raise NotADirectoryError(f"Source root is not a directory: {source_root}")

    candidates: set[Path] = set()

    for pattern in include_patterns:
        for path in source_root.glob(pattern):
            if path.is_file() and path.suffix == ".py":
                candidates.add(path.resolve())

    filtered = []

    for path in candidates:
        relative = path.relative_to(source_root).as_posix()

        if _is_excluded(relative, exclude_patterns):
            continue

        filtered.append(path)

    return sorted(filtered)


def _is_excluded(relative_path: str, exclude_patterns: list[str]) -> bool:
    return any(fnmatch(relative_path, pattern) for pattern in exclude_patterns)


def _scan_python_file(file_path: Path, source_root: Path) -> FileFact:
    relative_path = file_path.relative_to(source_root).as_posix()

    try:
        source = file_path.read_text(encoding="utf-8")
        tree = ast.parse(source)

        module = module_name_from_path(file_path, source_root)

        return FileFact(
            path=relative_path,
            module=module,
            imports=_extract_imports(tree, relative_path),
            assignments=_extract_module_assignments(tree, relative_path),
            classes=_extract_classes(tree, module, relative_path),
            functions=_extract_top_level_functions(tree, module, relative_path),
            signals=_extract_file_signals(tree, relative_path),
            source=SourceLocation(
                file=relative_path,
                line_start=1,
                line_end=len(source.splitlines()),
            ),
        )

    except SyntaxError as exc:
        return FileFact(
            path=relative_path,
            module=module_name_from_path(file_path, source_root),
            error=f"SyntaxError: {exc}",
        )

    except UnicodeDecodeError as exc:
        return FileFact(
            path=relative_path,
            module=module_name_from_path(file_path, source_root),
            error=f"UnicodeDecodeError: {exc}",
        )


def _extract_imports(tree: ast.AST, file_path: str) -> list[ImportFact]:
    imports: list[ImportFact] = []

    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.Import):
            imports.append(
                ImportFact(
                    type="import",
                    module=None,
                    names=[
                        ImportNameFact(name=alias.name, alias=alias.asname)
                        for alias in node.names
                    ],
                    source=source_location(node, file_path),
                )
            )

        elif isinstance(node, ast.ImportFrom):
            imports.append(
                ImportFact(
                    type="from_import",
                    module=node.module,
                    names=[
                        ImportNameFact(name=alias.name, alias=alias.asname)
                        for alias in node.names
                    ],
                    source=source_location(node, file_path),
                )
            )

    return imports


def _extract_classes(tree: ast.AST, module: str, file_path: str) -> list[ClassFact]:
    classes: list[ClassFact] = []

    for node in ast.iter_child_nodes(tree):
        if not isinstance(node, ast.ClassDef):
            continue

        qualified_name = f"{module}.{node.name}"

        class_fact = ClassFact(
            name=node.name,
            qualified_name=qualified_name,
            bases=[get_name(base) for base in node.bases],
            decorators=_extract_decorators(node.decorator_list, file_path),
            docstring=ast.get_docstring(node),
            fields=_extract_class_fields(node, file_path),
            methods=_extract_methods(node, qualified_name, file_path),
            signals=_extract_class_signals(node, file_path),
            source=source_location(node, file_path),
        )

        classes.append(class_fact)

    return classes


def _extract_class_fields(
    class_node: ast.ClassDef,
    file_path: str,
) -> list[ClassFieldFact]:
    fields: list[ClassFieldFact] = []

    for child in class_node.body:
        if isinstance(child, ast.Assign):
            value = ast_to_str(child.value)
            value_call = get_name(child.value.func) if isinstance(child.value, ast.Call) else None

            for target in child.targets:
                name = get_name(target)
                if not name:
                    continue

                fields.append(
                    ClassFieldFact(
                        name=name,
                        annotation=None,
                        value=value,
                        value_call=value_call,
                        source=source_location(child, file_path),
                    )
                )

        elif isinstance(child, ast.AnnAssign):
            name = get_name(child.target)
            if not name:
                continue

            fields.append(
                ClassFieldFact(
                    name=name,
                    annotation=ast_to_str(child.annotation),
                    value=ast_to_str(child.value),
                    value_call=get_name(child.value.func) if isinstance(child.value, ast.Call) else None,
                    source=source_location(child, file_path),
                )
            )

    return fields


def _extract_methods(
    class_node: ast.ClassDef,
    class_qualified_name: str,
    file_path: str,
) -> list[FunctionFact]:
    methods: list[FunctionFact] = []

    for node in class_node.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            methods.append(
                _extract_function_like(
                    node=node,
                    qualified_name=f"{class_qualified_name}.{node.name}",
                    kind="method",
                    file_path=file_path,
                    assignments=_extract_assignments(node, file_path),
                )
            )

    return methods


def _extract_top_level_functions(
    tree: ast.AST,
    module: str,
    file_path: str,
) -> list[FunctionFact]:
    functions: list[FunctionFact] = []

    for node in ast.iter_child_nodes(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            functions.append(
                _extract_function_like(
                    node=node,
                    qualified_name=f"{module}.{node.name}",
                    kind="function",
                    file_path=file_path,
                    assignments=_extract_assignments(node, file_path),
                )
            )

    return functions


def _extract_module_assignments(
    tree: ast.AST,
    file_path: str,
) -> list[AssignmentFact]:
    assignments: list[AssignmentFact] = []

    for child in ast.iter_child_nodes(tree):
        if isinstance(child, ast.Assign):
            assignments.extend(_assignment_facts_from_assign(child, file_path))
        elif isinstance(child, ast.AnnAssign):
            assignment = _assignment_fact_from_ann_assign(child, file_path)

            if assignment is not None:
                assignments.append(assignment)

    return assignments


def _extract_assignments(
    node: ast.AST,
    file_path: str,
) -> list[AssignmentFact]:
    assignments: list[AssignmentFact] = []

    for child in _walk_scoped_nodes(node):
        if isinstance(child, ast.Assign):
            assignments.extend(_assignment_facts_from_assign(child, file_path))

        elif isinstance(child, ast.AnnAssign):
            assignment = _assignment_fact_from_ann_assign(child, file_path)

            if assignment is not None:
                assignments.append(assignment)


    return assignments


def _assignment_facts_from_assign(
    node: ast.Assign,
    file_path: str,
) -> list[AssignmentFact]:
    value = ast_to_str(node.value)
    value_call = None
    assignments: list[AssignmentFact] = []

    if isinstance(node.value, ast.Call):
        value_call = get_name(node.value.func)

    for target in node.targets:
        target_name = get_name(target)

        if target_name:
            assignments.append(
                AssignmentFact(
                    target=target_name,
                    value=value,
                    value_call=value_call,
                    source=source_location(node, file_path),
                )
            )

    return assignments


def _assignment_fact_from_ann_assign(
    node: ast.AnnAssign,
    file_path: str,
) -> AssignmentFact | None:
    target_name = get_name(node.target)
    value = ast_to_str(node.value)
    value_call = None

    if isinstance(node.value, ast.Call):
        value_call = get_name(node.value.func)

    if not target_name:
        return None

    return AssignmentFact(
        target=target_name,
        value=value,
        value_call=value_call,
        source=source_location(node, file_path),
    )

def _extract_function_like(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
    qualified_name: str,
    kind: str,
    file_path: str,
    assignments: list[AssignmentFact], 
) -> FunctionFact:
    decorators = _extract_decorators(node.decorator_list, file_path)

    return FunctionFact(
        name=node.name,
        qualified_name=qualified_name,
        kind=kind,
        is_async=isinstance(node, ast.AsyncFunctionDef),
        visibility=visibility_from_name(node.name),
        docstring=ast.get_docstring(node),
        parameters=_extract_parameters(node),
        returns=ast_to_str(node.returns),
        decorators=decorators,
        calls=_extract_calls(node, file_path),
        assignments=assignments, 
        signals=_extract_function_signals(node, decorators, file_path),
        source=source_location(node, file_path),
    )

def _extract_parameters(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
) -> list[ParameterFact]:
    parameters: list[ParameterFact] = []
    args = node.args

    # -----------------------
    # positional-only args
    # -----------------------
    posonly_defaults = _align_defaults(args.posonlyargs, [])
    for arg, default in zip(args.posonlyargs, posonly_defaults):
        parameters.append(
            ParameterFact(
                name=arg.arg,
                annotation=ast_to_str(arg.annotation),
                default=ast_to_str(default),
                kind="positional_only",
            )
        )

    # -----------------------
    # normal args
    # defaults apply to the last N args
    # -----------------------
    normal_defaults = _align_defaults(args.args, args.defaults)

    for arg, default in zip(args.args, normal_defaults):
        parameters.append(
            ParameterFact(
                name=arg.arg,
                annotation=ast_to_str(arg.annotation),
                default=ast_to_str(default),
                kind="positional_or_keyword",
            )
        )

    # -----------------------
    # *args
    # -----------------------
    if args.vararg:
        parameters.append(
            ParameterFact(
                name=args.vararg.arg,
                annotation=ast_to_str(args.vararg.annotation),
                default=None,
                kind="vararg",
            )
        )

    # -----------------------
    # keyword-only args
    # -----------------------
    for arg, default in zip(args.kwonlyargs, args.kw_defaults):
        parameters.append(
            ParameterFact(
                name=arg.arg,
                annotation=ast_to_str(arg.annotation),
                default=ast_to_str(default),
                kind="keyword_only",
            )
        )

    # -----------------------
    # **kwargs
    # -----------------------
    if args.kwarg:
        parameters.append(
            ParameterFact(
                name=args.kwarg.arg,
                annotation=ast_to_str(args.kwarg.annotation),
                default=None,
                kind="kwarg",
            )
        )

    return parameters

def _align_defaults(args: list[ast.arg], defaults: list[ast.expr | None]) -> list[ast.expr | None]:
    missing = len(args) - len(defaults)
    return [None] * missing + list(defaults)

def _extract_decorators(
    decorators: list[ast.expr],
    file_path: str,
) -> list[DecoratorFact]:
    facts: list[DecoratorFact] = []

    for decorator in decorators:
        if isinstance(decorator, ast.Call):
            name = get_name(decorator.func)
            args = [literal_or_expr_to_str(arg) for arg in decorator.args]
            kwargs = {
                kw.arg: literal_or_expr_to_str(kw.value)
                for kw in decorator.keywords
                if kw.arg is not None
            }
        else:
            name = get_name(decorator)
            args = []
            kwargs = {}

        facts.append(
            DecoratorFact(
                name=name,
                args=args,
                kwargs=kwargs,
                source=source_location(decorator, file_path),
            )
        )

    return facts

def _extract_calls(
    node: ast.AST,
    file_path: str,
) -> list[CallFact]:
    calls: list[CallFact] = []

    parent_map = collect_parent_map(node)

    awaited_call_nodes: set[int] = set()

    for child in _walk_scoped_nodes(node):
        if isinstance(child, ast.Await) and isinstance(child.value, ast.Call):
            awaited_call_nodes.add(id(child.value))

    seen: set[tuple[str, int, int, bool]] = set()

    for child in _walk_scoped_nodes(node):
        if not isinstance(child, ast.Call):
            continue

        name = get_name(child.func)

        if not name:
            continue

        location = source_location(child, file_path)
        nested = is_nested_inside_call(child, parent_map)
        root_name = get_root_call_name(name)

        dedupe_key = (
            name,
            location.line_start,
            location.line_end or location.line_start,
            nested,
        )

        if dedupe_key in seen:
            continue

        seen.add(dedupe_key)

        calls.append(
            CallFact(
                name=name,
                args=[ast_to_str(arg) or "" for arg in child.args],
                kwargs={
                    kw.arg: ast_to_str(kw.value) or ""
                    for kw in child.keywords
                    if kw.arg is not None
                },
                awaited=id(child) in awaited_call_nodes,
                nested_in_call=nested,
                root_name=root_name,
                call_role=classify_call(name=name, nested=nested),
                source=location,
            )
        )

    return calls

def _walk_scoped_nodes(root: ast.AST):
    """
    Walk nodes that belong to the current function/class scope.

    ast.walk() descends into nested function and class definitions. For
    architecture mapping that causes false positives: calls inside a local
    helper function can be attributed to the endpoint or service method that
    merely defines it. Decorators are still extracted separately, so nested
    scopes are intentionally treated as their own future facts, not as part of
    the outer implementation body.
    """
    stack = list(reversed(list(ast.iter_child_nodes(root))))

    while stack:
        node = stack.pop()
        yield node

        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)):
            continue

        stack.extend(reversed(list(ast.iter_child_nodes(node))))
def classify_call(name: str, nested: bool) -> str:
    db_calls = {
        "self.db.add",
        "self.db.flush",
        "self.db.commit",
        "self.db.refresh",
        "self.db.get",
        "self.db.execute",
        "db.add",
        "db.flush",
        "db.commit",
        "db.refresh",
        "db.get",
        "db.execute",
        "session.add",
        "session.execute",
        "session.commit",
        "session.refresh",
        "session.get",
    }

    builtins_or_utility = {
        "str",
        "int",
        "float",
        "bool",
        "type",
        "isinstance",
        "setattr",
        "getattr",
        "len",
        "print",
    }

    if name in db_calls:
        return "db_call"

    if name in {"select", "insert", "update", "delete"}:
        return "sqlalchemy_query_call"

    if name.startswith("select."):
        return "sqlalchemy_query_call"

    if name.startswith("insert."):
        return "sqlalchemy_query_call"

    if name.startswith("update."):
        return "sqlalchemy_query_call"

    if name.startswith("delete."):
        return "sqlalchemy_query_call"

    if name.endswith(".log_event") or "AuditService" in name:
        return "audit_call"

    if name in builtins_or_utility:
        return "builtin_or_utility_call"

    if nested:
        return "nested_call"

    if name and name[0].isupper():
        return "constructor_call"

    return "top_level_call"

def get_root_call_name(name: str) -> str:
    if not name:
        return ""

    return name.split(".")[0]

def is_nested_inside_call(call_node: ast.Call, parent_map: dict[int, ast.AST]) -> bool:
    current = parent_map.get(id(call_node))

    while current is not None:
        if isinstance(current, ast.Call):
            return True

        current = parent_map.get(id(current))

    return False

def _extract_file_signals(tree: ast.AST, file_path: str) -> list[SignalFact]:
    signals: list[SignalFact] = []

    for node in ast.iter_child_nodes(tree):
        # router = APIRouter(...)
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Call):
            call_name = get_name(node.value.func)

            if call_name == "APIRouter":
                targets = [get_name(target) for target in node.targets]
                kwargs = {
                    kw.arg: literal_or_expr_to_str(kw.value)
                    for kw in node.value.keywords
                    if kw.arg is not None
                }

                signals.append(
                    SignalFact(
                        kind="fastapi_router_instance",
                        data={
                            "targets": targets,
                            "call": call_name,
                            "prefix": kwargs.get("prefix"),
                            "kwargs": kwargs,
                        },
                        source=source_location(node, file_path),
                    )
                )

    return signals


def _extract_class_signals(node: ast.ClassDef, file_path: str) -> list[SignalFact]:
    signals: list[SignalFact] = []

    if node.name.endswith("Service"):
        signals.append(
            SignalFact(
                kind="class_name_suffix",
                data={"suffix": "Service"},
                source=source_location(node, file_path),
            )
        )

    # Mixin-ish class ( Mixin class = Reusable class of )
    if node.name.endswith("Mixin"):
        signals.append(
            SignalFact(
                kind="class_name_suffix",
                data={"suffix": "Mixin"},
                source=source_location(node, file_path),
            )
        )

    base_names = [get_name(base) for base in node.bases] # Bases = Superklasse

    # SQLAlchemy declarative model-ish class
    if "Base" in base_names:
        signals.append(
            SignalFact(
                kind="sqlalchemy_model_base",
                data={"base": "Base"},
                source=source_location(node, file_path),
            )
        )

    # Common ORM base variants
    for base in base_names:
        if base in {"Base", "DeclarativeBase"} or base.endswith(".Base"):
            signals.append(
                SignalFact(
                    kind="orm_model_base",
                    data={"base": base},
                    source=source_location(node, file_path),
                )
            )

    # Pydantic model-ish class
    for base in base_names:
        if base in {"BaseModel"} or base.endswith(".BaseModel"):
            signals.append(
                SignalFact(
                    kind="pydantic_model_base",
                    data={"base": base},
                    source=source_location(node, file_path),
                )
            )

    return signals


def _extract_function_signals(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
    decorators: list[DecoratorFact],
    file_path: str,
) -> list[SignalFact]:
    signals: list[SignalFact] = []

    for decorator in decorators:
        route_signal = _route_signal_from_decorator(decorator)

        if route_signal:
            signals.append(
                SignalFact(
                    kind="api_route",
                    data=route_signal,
                    source=decorator.source,
                )
            )

    db_call_names = {"db.execute", "self.db.execute", "session.execute"}
    db_add_names = {"db.add", "self.db.add", "session.add"}

    for call in _extract_calls(node, file_path):
        if call.name in db_call_names:
            signals.append(
                SignalFact(
                    kind="db_execute",
                    data={"call": call.name},
                    source=call.source,
                )
            )

        if call.name in db_add_names:
            signals.append(
                SignalFact(
                    kind="db_add",
                    data={"call": call.name},
                    source=call.source,
                )
            )

        if call.name in {"select", "insert", "update", "delete"}:
            signals.append(
                SignalFact(
                    kind=f"sqlalchemy_{call.name}",
                    data={"call": call.name},
                    source=call.source,
                )
            )

    return signals


def _route_signal_from_decorator(decorator: DecoratorFact) -> dict | None:
    """
    Detects FastAPI style route decorators:

    @router.get("/x")
    @router.post("/x")
    @api_router.delete("/x")
    """
    parts = decorator.name.split(".")

    if len(parts) < 2:
        return None

    http_method = parts[-1].lower()

    if http_method not in {"get", "post", "put", "patch", "delete", "options", "head"}:
        return None

    router_name = ".".join(parts[:-1])
    path = decorator.args[0] if decorator.args else None

    return {
        "router": router_name,
        "http_method": http_method.upper(),
        "path": path,
        "kwargs": decorator.kwargs,
    }


