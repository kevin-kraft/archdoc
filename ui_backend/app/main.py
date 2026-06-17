from __future__ import annotations

from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ui_backend.app.models import (
    ArchitectureOverlay,
    CatalogOverlayItem,
    EffectiveCatalog,
    OverlayTargetType,
    OverlayUpdate,
    TablePage,
)
from ui_backend.app.settings import settings
from ui_backend.app.storage import (
    SCHEMA_VERSION,
    delete_overlay_item,
    import_generated_if_needed,
    initialize_store,
    query_endpoints,
    query_interfaces,
    query_operations,
    query_user_stories,
    query_validation_issues,
    read_validation_stats,
    read_user_story_trace,
    read_user_story_detail,
    read_service_action_graph,
    read_effective_catalog,
    read_generated_catalog,
    read_overlay,
    upsert_overlay_item,
)

app = FastAPI(title="Archdoc UI Backend", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8010",
        "http://127.0.0.1:8010",
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup() -> None:
    initialize_store()


@app.get("/health", response_model=dict[str, str])
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "static_dir": str(settings.generated_static_dir),
        "user_stories_dir": str(settings.user_stories_dir),
        "overlay_path": str(settings.overlay_path),
        "db_path": str(settings.db_path),
        "db_schema_version": str(SCHEMA_VERSION),
    }


@app.post("/api/import/generated", response_model=dict[str, str | None])
def import_generated(force: bool = False) -> dict[str, str | None]:
    run_id = import_generated_if_needed(force=force)
    return {"status": "ok", "import_run_id": run_id}


@app.get("/api/catalog/generated", response_model=dict[str, Any])
def get_generated_catalog() -> dict[str, Any]:
    return read_generated_catalog()


@app.get("/api/catalog/effective", response_model=EffectiveCatalog)
def get_effective_catalog() -> EffectiveCatalog:
    return read_effective_catalog()


@app.get("/api/table/endpoints", response_model=TablePage)
def get_endpoint_table(
    search: str = "",
    method: str = "all",
    contract: str = "all",
    linkage: str = "all",
    review_status: str = "all",
    sort: str = "endpoint",
    direction: str = "asc",
    limit: int = 50,
    offset: int = 0,
) -> TablePage:
    return query_endpoints(
        search=search,
        method=method,
        contract=contract,
        linkage=linkage,
        review_status=review_status,
        sort=sort,
        direction=direction,
        limit=limit,
        offset=offset,
    )


@app.get("/api/table/operations", response_model=TablePage)
def get_operation_table(
    search: str = "",
    coverage: str = "all",
    review_status: str = "all",
    sort: str = "service",
    direction: str = "asc",
    limit: int = 50,
    offset: int = 0,
) -> TablePage:
    return query_operations(
        search=search,
        coverage=coverage,
        review_status=review_status,
        sort=sort,
        direction=direction,
        limit=limit,
        offset=offset,
    )


@app.get("/api/table/interfaces", response_model=TablePage)
def get_interface_table(
    search: str = "",
    confidence: str = "all",
    review_status: str = "all",
    sort: str = "endpoint",
    direction: str = "asc",
    limit: int = 50,
    offset: int = 0,
) -> TablePage:
    return query_interfaces(
        search=search,
        confidence=confidence,
        review_status=review_status,
        sort=sort,
        direction=direction,
        limit=limit,
        offset=offset,
    )


@app.get("/api/table/validation-issues", response_model=TablePage)
def get_validation_issue_table(
    search: str = "",
    severity: str = "all",
    code: str = "all",
    review_status: str = "all",
    sort: str = "severity",
    direction: str = "asc",
    limit: int = 50,
    offset: int = 0,
) -> TablePage:
    return query_validation_issues(
        search=search,
        severity=severity,
        code=code,
        review_status=review_status,
        sort=sort,
        direction=direction,
        limit=limit,
        offset=offset,
    )


@app.get("/api/validation/stats", response_model=dict[str, Any])
def get_validation_stats() -> dict[str, Any]:
    return read_validation_stats()


@app.get("/api/table/user-stories", response_model=TablePage)
def get_user_story_table(
    search: str = "",
    area: str = "all",
    status: str = "all",
    linkage: str = "all",
    sort: str = "id",
    direction: str = "asc",
    limit: int = 50,
    offset: int = 0,
) -> TablePage:
    return query_user_stories(
        search=search,
        area=area,
        status=status,
        linkage=linkage,
        sort=sort,
        direction=direction,
        limit=limit,
        offset=offset,
    )


@app.get("/api/user-stories/{story_id:path}/trace", response_model=dict[str, Any] | None)
def get_user_story_trace(story_id: str) -> dict[str, Any] | None:
    return read_user_story_trace(story_id)


@app.get("/api/user-stories/{story_id:path}", response_model=dict[str, Any] | None)
def get_user_story(story_id: str) -> dict[str, Any] | None:
    return read_user_story_detail(story_id)


@app.get("/api/graph/services", response_model=dict[str, Any])
def get_service_action_graph(
    service_id: str | None = None,
    action_kind: str = "all",
    search: str = "",
) -> dict[str, Any]:
    return read_service_action_graph(
        service_id=service_id,
        action_kind=action_kind,
        search=search,
    )


@app.get("/api/overlays", response_model=ArchitectureOverlay)
def get_overlay() -> ArchitectureOverlay:
    return read_overlay()


@app.put(
    "/api/overlays/{target_type}/{target_id:path}",
    response_model=CatalogOverlayItem,
)
def put_overlay_item(
    target_type: OverlayTargetType,
    target_id: str,
    payload: OverlayUpdate,
) -> CatalogOverlayItem:
    return upsert_overlay_item(target_type, target_id, payload)


@app.delete("/api/overlays/{target_type}/{target_id:path}", response_model=ArchitectureOverlay)
def remove_overlay_item(
    target_type: OverlayTargetType,
    target_id: str,
) -> ArchitectureOverlay:
    return delete_overlay_item(target_type, target_id)
