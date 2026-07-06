from __future__ import annotations

import re

from archdoc.catalog.models import (
    DetectionInfo,
    DetectionConfidence,
    EndpointCatalogItem,
    SourceRef,
    EndpointParameterItem,
    EndpointImplementation,
    EndpointImplementationKind,
)
from archdoc.catalog.identity import build_catalog_identity
from archdoc.config.models import ArchdocConfig
from archdoc.facts.models import AssignmentFact, FileFact, FunctionFact, RawCodeFacts, SignalFact


def map_endpoints(
    facts: RawCodeFacts,
    config: ArchdocConfig,
) -> list[EndpointCatalogItem]:
    endpoints: list[EndpointCatalogItem] = []
    include_prefixes = _router_include_prefixes(facts)

    for file in facts.files:
        if file.error:
            continue

        if not _is_in_endpoint_path(file.path, config.mapping.endpoints.paths):
            continue

        for fn in file.functions:
            route_signals = [
                signal
                for signal in fn.signals
                if signal.kind == config.mapping.endpoints.route_signal_kind
            ]

            for signal in route_signals:
                endpoints.append(_map_endpoint(file, fn, signal, config, include_prefixes))

    return sorted(endpoints, key=lambda endpoint: endpoint.id)


def _is_in_endpoint_path(file_path: str, endpoint_paths: list[str]) -> bool:
    normalized = file_path.replace("\\", "/")

    for endpoint_path in endpoint_paths:
        endpoint_path = endpoint_path.strip("/").replace("\\", "/")

        if normalized.startswith(endpoint_path + "/"):
            return True

        if f"/{endpoint_path}/" in normalized:
            return True

    return False


def _map_endpoint(
    file: FileFact,
    fn: FunctionFact,
    signal: SignalFact,
    config: ArchdocConfig,
    include_prefixes: dict[str, str | None],
) -> EndpointCatalogItem:
    data = signal.data

    http_method = str(data.get("http_method", "UNKNOWN")).upper()
    path = data.get("path")
    router = data.get("router")
    include_prefix = include_prefixes.get(file.module)
    router_prefix = _router_prefix_for_signal(file, router)
    full_path = _join_api_paths(include_prefix, router_prefix, path)
    kwargs = data.get("kwargs") or {}

    endpoint_id = _endpoint_id(
        module=file.module,
        function_name=fn.name,
        http_method=http_method,
        path=full_path or path,
    )

    endpoint_source = SourceRef(
        file=fn.source.file,
        line_start=fn.source.line_start,
        line_end=fn.source.line_end,
    )

    return EndpointCatalogItem(
        id=endpoint_id,
        identity=build_catalog_identity(
            kind="endpoint",
            logical_id=endpoint_id,
            display_name=f"{http_method} {full_path or path or fn.name}",
            source=endpoint_source,
            qualified_name=fn.qualified_name,
            extra_parts=[http_method, include_prefix or "", router_prefix or "", path or "", full_path or "", fn.name],
            aliases=_unique_strings([fn.qualified_name, path or "", router_prefix or "", include_prefix or "", full_path or ""]),
        ),
        module=file.module,
        function_name=fn.name,
        qualified_name=fn.qualified_name,
        implementation=_detect_endpoint_implementation(fn, config, file.assignments),
        http_method=http_method,
        path=path,
        include_prefix=include_prefix,
        router_prefix=router_prefix,
        full_path=full_path,
        router=router,
        kwargs=kwargs,
        source=endpoint_source,
        parameters=[
            EndpointParameterItem(
                name=param.name,
                annotation=param.annotation,
                default=param.default,
                kind=param.kind,
                source=_parameter_source(param.default),
            )
            for param in fn.parameters
        ],
        detection=DetectionInfo(
            method="rule",
            rule="function_with_api_route_signal",
            confidence=DetectionConfidence.EXACT,
            evidence=[
                f"http_method={http_method}",
                f"path={path}",
                f"include_prefix={include_prefix}",
                f"router_prefix={router_prefix}",
                f"full_path={full_path}",
                f"function={fn.qualified_name}",
            ],
        ),
        review_status="generated",
    )


def _router_include_prefixes(facts: RawCodeFacts) -> dict[str, str | None]:
    prefixes: dict[str, str | None] = {}

    for file in facts.files:
        if file.error:
            continue

        import_modules = _router_import_modules(file)

        for fn in file.functions:
            for call in fn.calls:
                if not call.name.endswith(".include_router") or not call.args:
                    continue

                router_ref = call.args[0]
                if not router_ref.endswith(".router"):
                    continue

                imported_name = router_ref.rsplit(".", 1)[0]
                module = import_modules.get(imported_name)
                if not module:
                    continue

                prefix = _clean_prefix_value(call.kwargs.get("prefix"))
                prefixes.setdefault(module, prefix)

    return prefixes


def _router_import_modules(file: FileFact) -> dict[str, str]:
    modules: dict[str, str] = {}

    for import_fact in file.imports:
        if import_fact.type != "from_import":
            continue

        router_module = _normalized_router_module(import_fact.module)
        if router_module is None:
            continue

        for name in import_fact.names:
            local_name = name.alias or name.name
            modules[local_name] = f"{router_module}.{name.name}"

    return modules


def _normalized_router_module(module: str | None) -> str | None:
    if module in {"routers", "app.routers"}:
        return "routers"

    return None


def _clean_prefix_value(value: str | None) -> str | None:
    if value is None:
        return None

    cleaned = value.strip()
    if len(cleaned) >= 2 and cleaned[0] == cleaned[-1] and cleaned[0] in {"'", '"'}:
        cleaned = cleaned[1:-1]

    return cleaned or None


def _router_prefix_for_signal(file: FileFact, router: str | None) -> str | None:
    if not router:
        return None

    for signal in file.signals:
        if signal.kind != "fastapi_router_instance":
            continue

        targets = signal.data.get("targets") or []
        if router not in targets:
            continue

        prefix = signal.data.get("prefix")
        if prefix is None:
            return None

        return str(prefix)

    return None


def _join_api_paths(*parts: str | None) -> str | None:
    values = [
        part.strip()
        for part in parts
        if part is not None and part.strip()
    ]

    if not values:
        return parts[-1] if parts else None

    joined = "/".join(
        part.strip("/")
        for part in values
        if part.strip("/")
    )

    return f"/{joined}" if joined else "/"


def _unique_strings(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []

    for value in values:
        if not value or value in seen:
            continue

        seen.add(value)
        result.append(value)

    return result


def _detect_endpoint_implementation(
    fn: FunctionFact,
    config: ArchdocConfig,
    module_assignments: list[AssignmentFact] | None = None,
) -> EndpointImplementation:
    signals: list[str] = []

    call_names = [call.name for call in fn.calls]
    top_level_calls = [
        call for call in fn.calls
        if not getattr(call, "nested_in_call", False)
    ]

    call_roles = {
        getattr(call, "call_role", "unknown")
        for call in fn.calls
    }

    # -----------------------
    # DB direct access
    # -----------------------
    if "db_call" in call_roles or "sqlalchemy_query_call" in call_roles:
        signals.append("db_or_sqlalchemy_call")

    # -----------------------
    # Service candidate by assignment or parameter
    # service = FinancialService(db)
    # service: FinancialService = ...
    # -----------------------
    service_variables = _infer_service_variables(fn, module_assignments)

    if service_variables:
        signals.append("service_variable_detected")

    service_method_calls = _find_service_method_calls(fn, service_variables)

    if service_method_calls:
        signals.append("service_method_call_detected")
        return EndpointImplementation(
            kind=EndpointImplementationKind.SERVICE_CANDIDATE,
            confidence=DetectionConfidence.HIGH,
            reason="Endpoint contains a typed or assigned service variable and calls a method on it.",
            signals=signals,
        )

    # -----------------------
    # Direct service class calls
    # FinancialService(...).method()
    # _finance_core().FinancialService(...).method()
    # -----------------------
    if _has_direct_service_class_call(call_names):
        signals.append("direct_service_class_call")
        return EndpointImplementation(
            kind=EndpointImplementationKind.SERVICE_CANDIDATE,
            confidence=DetectionConfidence.MEDIUM,
            reason="Endpoint appears to call a service class directly, but no service variable was inferred.",
            signals=signals,
        )

    # -----------------------
    # Direct DB access in router
    # -----------------------
    if "db_or_sqlalchemy_call" in signals:
        return EndpointImplementation(
            kind=EndpointImplementationKind.DIRECT_DB_ACCESS,
            confidence=DetectionConfidence.HIGH,
            reason="Endpoint directly uses database/session or SQLAlchemy calls.",
            signals=signals,
        )

    # -----------------------
    # External calls
    # -----------------------
    if _has_external_call(call_names):
        signals.append("external_call")
        return EndpointImplementation(
            kind=EndpointImplementationKind.EXTERNAL_CALL,
            confidence=DetectionConfidence.MEDIUM,
            reason="Endpoint appears to call an external HTTP/client/provider API.",
            signals=signals,
        )

    # -----------------------
    # Passthrough / helper delegation
    # -----------------------
    meaningful_calls = [
        call for call in top_level_calls
        if getattr(call, "call_role", "unknown") not in {
            "builtin_or_utility_call",
            "nested_call",
        }
    ]

    if len(meaningful_calls) == 1:
        signals.append("single_meaningful_call")
        return EndpointImplementation(
            kind=EndpointImplementationKind.PASSTHROUGH,
            confidence=DetectionConfidence.MEDIUM,
            reason="Endpoint mostly delegates to a single helper/function call.",
            signals=signals,
        )

    # -----------------------
    # Static/trivial endpoint
    # -----------------------
    if len(fn.calls) <= 1 and len(fn.assignments) <= 1:
        signals.append("few_calls_or_assignments")
        return EndpointImplementation(
            kind=EndpointImplementationKind.STATIC_OR_TRIVIAL,
            confidence=DetectionConfidence.LOW,
            reason="Endpoint contains very little detected logic.",
            signals=signals,
        )

    # -----------------------
    # Fallback: likely router-local implementation
    # -----------------------
    if fn.calls or fn.assignments:
        signals.append("local_logic_detected")
        return EndpointImplementation(
            kind=EndpointImplementationKind.ROUTER_INTERNAL,
            confidence=DetectionConfidence.MEDIUM,
            reason="Endpoint contains local logic, but no service operation link was detected at mapping time.",
            signals=signals,
        )

    return EndpointImplementation(
        kind=EndpointImplementationKind.UNKNOWN,
        confidence=DetectionConfidence.UNKNOWN,
        reason="No implementation pattern could be classified.",
        signals=signals,
    )

    


def _parameter_source(default: str | None) -> str:
    if not default:
        return "body_or_positional"

    if default.startswith("Depends("):
        return "dependency"

    if default.startswith("Query("):
        return "query"

    if default.startswith("Path("):
        return "path"

    if default.startswith("Body("):
        return "body"

    if default.startswith("Header("):
        return "header"

    if default.startswith("Cookie("):
        return "cookie"

    return "default"

def _endpoint_id(
    module: str,
    function_name: str,
    http_method: str,
    path: str | None,
) -> str:
    """
    Stable enough for now.

    Example:
    module = "routers.financial"
    method = "POST"
    path = "/payouts/{payout_id}/approve"
    function = "approve_payout"

    -> routers.financial.post.payouts.payout-id.approve.approve-payout
    """
    module_slug = module.replace(".", ".")
    method_slug = http_method.lower()
    path_slug = _path_to_slug(path)
    function_slug = _slugify(function_name)

    if path_slug:
        return f"{module_slug}.{method_slug}.{path_slug}.{function_slug}"

    return f"{module_slug}.{method_slug}.{function_slug}"


def _path_to_slug(path: str | None) -> str:
    if not path:
        return ""

    cleaned = path.strip("")

    if not cleaned:
        return "root"
    if cleaned == "/": 
        return "root"


    # /payouts/{payout_id}/approve -> payouts.payout-id.approve
    # cleaned = cleaned.replace("{", "").replace("}", "")
    # cleaned = cleaned.replace("_", "-")
    # cleaned = cleaned.replace("/", ".")

    # Important: preserve path style differences
    # "/count"  -> "count"
    # ":count"  -> "colon-count"
    # "{id}"    -> "param-id"
    # "/x/{id}" -> "x.param-id"

    cleaned = cleaned.strip("/")

    if not cleaned:
        return cleaned
    
    parts = cleaned.split("/")
    slug_parts: list[str] = []

    for part in parts:
        if not part:
            continue

        if part.startswith(":"):
            slug_parts.append("colon-" + _slugify(part[1:]))
            continue

        if part.startswith("{") and part.endswith("}"):
            slug_parts.append("param-" + _slugify(part[1:-1]))
            continue

        slug_parts.append(_slugify(part))


    # cleaned = re.sub(r"[^a-zA-Z0-9.-]+", "-", cleaned)
    # cleaned = re.sub(r"-+", "-", cleaned)
    # cleaned = cleaned.strip(".-")

    return ".".join(slug_parts)


def _slugify(value: str) -> str:
    value = value.replace("_", "-")
    value = re.sub(r"[^a-zA-Z0-9.-]+", "-", value)
    value = re.sub(r"-+", "-", value)
    return value.strip("-").lower()

def _infer_service_variables(
    fn: FunctionFact,
    module_assignments: list[AssignmentFact] | None = None,
) -> dict[str, str]:
    variable_types: dict[str, str] = {}

    # Parameter-based, e.g. service: FinancialService = Depends(...)
    for param in fn.parameters:
        if param.annotation and param.annotation.endswith("Service"):
            variable_types[param.name] = param.annotation

    # Assignment-based, e.g. service = FinancialService(db)
    for assignment in [*(module_assignments or []), *fn.assignments]:
        if assignment.value_call and assignment.value_call.endswith("Service"):
            variable_types[assignment.target] = assignment.value_call

    return variable_types


def _find_service_method_calls(
    fn: FunctionFact,
    service_variables: dict[str, str],
) -> list[str]:
    result: list[str] = []

    for call in fn.calls:
        if getattr(call, "nested_in_call", False):
            continue

        parts = call.name.split(".")

        if len(parts) < 2:
            continue

        variable_name = parts[-2]

        if variable_name in service_variables:
            result.append(call.name)

    return result


def _has_direct_service_class_call(call_names: list[str]) -> bool:
    for call_name in call_names:
        parts = call_name.split(".")

        # catches:
        # FinancialService.create_x
        # _finance_core.FinancialService.create_x
        if len(parts) >= 2 and parts[-2].endswith("Service"):
            return True

    return False


def _has_external_call(call_names: list[str]) -> bool:
    external_markers = [
        "httpx.",
        "requests.",
        "client.",
        "provider.",
        "stripe.",
        "paypal.",
        "sendgrid.",
        "smtp.",
    ]

    return any(
        any(marker in call_name for marker in external_markers)
        for call_name in call_names
    )
