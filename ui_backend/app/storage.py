from __future__ import annotations

import hashlib
import json
import sqlite3
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

import yaml

from ui_backend.app.models import (
    ArchitectureOverlay,
    CatalogOverlayItem,
    EffectiveCatalog,
    OverlayMetadata,
    OverlayTarget,
    OverlayTargetType,
    OverlayUpdate,
    TablePage,
)
from ui_backend.app.settings import settings

SCHEMA_VERSION = 7


def initialize_store() -> None:
    settings.db_path.parent.mkdir(parents=True, exist_ok=True)

    with _connect() as conn:
        _create_schema(conn)

    import_generated_if_needed()
    import_user_stories()
    import_overlay_json_if_needed()


def read_generated_catalog() -> dict[str, Any]:
    import_generated_if_needed()

    with _connect() as conn:
        run_id = _active_run_id(conn)
        if run_id is None:
            return {"services": [], "endpoints": [], "links": [], "actions": [], "operation_links": [], "validation_report": None}

        services = _read_services(conn, run_id)
        endpoints = _read_payload_rows(conn, "generated_endpoints", run_id)
        links = _read_payload_rows(conn, "generated_links", run_id)
        actions = _read_payload_rows(conn, "generated_actions", run_id)
        operation_links = _read_payload_rows(conn, "generated_operation_links", run_id)
        validation_report = _read_validation_report(conn, run_id)

    return {
        "services": services,
        "endpoints": endpoints,
        "links": links,
        "actions": actions,
        "operation_links": operation_links,
        "validation_report": validation_report,
    }


def read_overlay() -> ArchitectureOverlay:
    initialize_schema_only()

    with _connect() as conn:
        items = [_overlay_item_from_row(conn, row) for row in _fetch_review_rows(conn)]

    return ArchitectureOverlay(project_name=settings.project_name, items=items)


def write_overlay(overlay: ArchitectureOverlay) -> ArchitectureOverlay:
    initialize_schema_only()

    with _connect() as conn:
        conn.execute("DELETE FROM review_items")
        conn.execute("DELETE FROM review_labels")
        conn.execute("DELETE FROM review_status_markers")

        for item in overlay.items:
            _upsert_review_item(conn, item)

    return mirror_overlay_to_json(read_overlay())


def read_effective_catalog() -> EffectiveCatalog:
    generated = read_generated_catalog()
    overlay = read_overlay()
    overlay_index = _overlay_index(overlay)

    services = [
        _apply_service_overlay(service, overlay_index)
        for service in generated["services"]
    ]
    endpoints = [
        _apply_overlay(endpoint, _overlay_for_item(overlay_index, "endpoint", endpoint))
        for endpoint in generated["endpoints"]
    ]
    links = [
        _apply_overlay(
            link,
            _overlay_for_item(overlay_index, "endpoint_service_link", link, fallback_id=_link_id(link)),
        )
        for link in generated["links"]
    ]
    actions = [
        _apply_overlay(action, _overlay_for_item(overlay_index, "architecture_action", action))
        for action in generated["actions"]
    ]
    validation_report = _apply_validation_overlays(generated["validation_report"], overlay_index)

    return EffectiveCatalog(
        services=services,
        endpoints=endpoints,
        links=links,
        actions=actions,
        validation_report=validation_report,
        overlay=overlay,
    )


def query_user_stories(
    search: str = "",
    area: str = "all",
    status: str = "all",
    linkage: str = "all",
    sort: str = "id",
    direction: str = "asc",
    limit: int = 50,
    offset: int = 0,
) -> TablePage:
    import_generated_if_needed()
    import_user_stories()

    with _connect() as conn:
        run_id = _active_run_id(conn)
        if run_id is None:
            return TablePage()

        overlay = read_overlay()
        overlay_index = _overlay_index(overlay)
        where, params = _user_story_where(search, area, status, linkage)
        order_by = _user_story_order_by(sort, direction)
        safe_limit = max(1, min(limit, 500))
        safe_offset = max(0, offset)
        total = conn.execute(
            f"SELECT COUNT(*) AS count FROM user_stories us {where}",
            params,
        ).fetchone()["count"]
        rows = conn.execute(
            f"""
            SELECT us.*
            FROM user_stories us
            {where}
            {order_by}
            LIMIT ? OFFSET ?
            """,
            [*params, safe_limit, safe_offset],
        ).fetchall()

        stories = []
        for row in rows:
            story = _story_from_row(row)
            _attach_story_link_summary(conn, run_id, story)
            story = _apply_overlay(story, _overlay_for_item(overlay_index, "user_story", story))
            stories.append(story)

        return TablePage(rows=stories, total=total, limit=safe_limit, offset=safe_offset)


def read_user_story_detail(story_id: str) -> dict[str, Any] | None:
    import_generated_if_needed()
    import_user_stories()

    with _connect() as conn:
        run_id = _active_run_id(conn)
        if run_id is None:
            return None

        row = conn.execute(
            "SELECT * FROM user_stories WHERE id = ? LIMIT 1",
            (story_id,),
        ).fetchone()
        if row is None:
            return None

        overlay = read_overlay()
        overlay_index = _overlay_index(overlay)
        story = _story_from_row(row)
        _attach_story_link_summary(conn, run_id, story)
        story = _apply_overlay(story, _overlay_for_item(overlay_index, "user_story", story))
        linked_endpoints = _story_linked_architecture(conn, run_id, story)

    return {
        "story": story,
        "linked_endpoints": linked_endpoints,
    }


def read_user_story_trace(story_id: str) -> dict[str, Any] | None:
    import_generated_if_needed()
    import_user_stories()

    with _connect() as conn:
        run_id = _active_run_id(conn)
        if run_id is None:
            return None

        row = conn.execute(
            "SELECT * FROM user_stories WHERE id = ? LIMIT 1",
            (story_id,),
        ).fetchone()
        if row is None:
            return None

        story = _story_from_row(row)
        _attach_story_link_summary(conn, run_id, story)
        return _build_user_story_trace(conn, run_id, story)


def query_endpoints(
    search: str = "",
    method: str = "all",
    contract: str = "all",
    linkage: str = "all",
    review_status: str = "all",
    sort: str = "path",
    direction: str = "asc",
    limit: int = 50,
    offset: int = 0,
) -> TablePage:
    import_generated_if_needed()

    with _connect() as conn:
        run_id = _active_run_id(conn)
        if run_id is None:
            return TablePage()
        overlay = read_overlay()
        overlay_index = _overlay_index(overlay)
        where, params = _endpoint_where(run_id, search, method, contract, linkage, review_status)
        order_by = _endpoint_order_by(sort, direction)
        safe_limit = max(1, min(limit, 500))
        safe_offset = max(0, offset)
        total = conn.execute(f"SELECT COUNT(*) AS count FROM generated_endpoints ge {where}", params).fetchone()["count"]
        rows = conn.execute(
            f"""
            SELECT ge.id, ge.payload_json,
                   EXISTS (
                     SELECT 1 FROM generated_links gl
                     WHERE gl.import_run_id = ge.import_run_id AND gl.endpoint_id = ge.id
                   ) AS linked
            FROM generated_endpoints ge
            {where}
            {order_by}
            LIMIT ? OFFSET ?
            """,
            [*params, safe_limit, safe_offset],
        ).fetchall()

    effective_rows = []
    for row in rows:
        endpoint_raw = _json_load(row["payload_json"])
        endpoint = _apply_overlay(endpoint_raw, _overlay_for_item(overlay_index, "endpoint", endpoint_raw))
        endpoint["_linked"] = bool(row["linked"])
        effective_rows.append(endpoint)

    return TablePage(rows=effective_rows, total=total, limit=safe_limit, offset=safe_offset)


def query_operations(
    search: str = "",
    coverage: str = "all",
    relation: str = "all",
    review_status: str = "all",
    sort: str = "service",
    direction: str = "asc",
    limit: int = 50,
    offset: int = 0,
) -> TablePage:
    import_generated_if_needed()

    with _connect() as conn:
        run_id = _active_run_id(conn)
        if run_id is None:
            return TablePage()
        overlay = read_overlay()
        overlay_index = _overlay_index(overlay)
        where, params = _operation_where(run_id, search, coverage, relation, review_status)
        order_by = _operation_order_by(sort, direction)
        safe_limit = max(1, min(limit, 500))
        safe_offset = max(0, offset)
        total = conn.execute(
            f"""
            SELECT COUNT(*) AS count
            FROM generated_operations go
            JOIN generated_services gs ON gs.import_run_id = go.import_run_id AND gs.id = go.service_id
            {where}
            """,
            params,
        ).fetchone()["count"]
        operation_rows = conn.execute(
            f"""
            SELECT go.id AS operation_id, go.service_id, go.payload_json AS operation_json, gs.payload_json AS service_json
                 , EXISTS (
                     SELECT 1 FROM generated_links gl
                     WHERE gl.import_run_id = go.import_run_id AND gl.operation_id = go.id
                   ) AS linked
            FROM generated_operations go
            JOIN generated_services gs
              ON gs.import_run_id = go.import_run_id AND gs.id = go.service_id
            {where}
            {order_by}
            LIMIT ? OFFSET ?
            """,
            [*params, safe_limit, safe_offset],
        ).fetchall()
        operation_links_by_id = _operation_links_for_operation_ids(
            conn,
            run_id,
            [str(row["operation_id"]) for row in operation_rows],
        )
        rows = []
        for row in operation_rows:
            service_raw = _json_load(row["service_json"])
            service = _apply_overlay(service_raw, _overlay_for_item(overlay_index, "service", service_raw))
            operation_raw = _json_load(row["operation_json"])
            operation = _apply_overlay(operation_raw, _overlay_for_item(overlay_index, "operation", operation_raw))
            rows.append({
                "service": service,
                "operation": operation,
                "operation_links": operation_links_by_id.get(str(row["operation_id"]), []),
                "_linked": bool(row["linked"]),
            })
    return TablePage(rows=rows, total=total, limit=safe_limit, offset=safe_offset)


def _operation_links_for_operation_ids(
    conn: sqlite3.Connection,
    run_id: str,
    operation_ids: list[str],
) -> dict[str, list[dict[str, Any]]]:
    if not operation_ids:
        return {}

    placeholders = ",".join("?" for _ in operation_ids)
    rows = conn.execute(
        f"""
        SELECT source_operation_id, target_operation_id, payload_json
        FROM generated_operation_links
        WHERE import_run_id = ?
          AND (
            source_operation_id IN ({placeholders})
            OR target_operation_id IN ({placeholders})
          )
        ORDER BY source_operation_id, target_operation_id, ordinal
        """,
        [run_id, *operation_ids, *operation_ids],
    ).fetchall()

    grouped: dict[str, list[dict[str, Any]]] = {operation_id: [] for operation_id in operation_ids}
    for row in rows:
        link = _json_load(row["payload_json"])
        source_operation_id = str(row["source_operation_id"] or "")
        target_operation_id = str(row["target_operation_id"] or "")
        if source_operation_id in grouped:
            grouped[source_operation_id].append(link)
        if target_operation_id in grouped and target_operation_id != source_operation_id:
            grouped[target_operation_id].append(link)

    return grouped


def query_interfaces(
    search: str = "",
    confidence: str = "all",
    review_status: str = "all",
    sort: str = "endpoint",
    direction: str = "asc",
    limit: int = 50,
    offset: int = 0,
) -> TablePage:
    import_generated_if_needed()

    with _connect() as conn:
        run_id = _active_run_id(conn)
        if run_id is None:
            return TablePage()
        overlay = read_overlay()
        overlay_index = _overlay_index(overlay)
        where, params = _interface_where(run_id, search, confidence, review_status)
        order_by = _interface_order_by(sort, direction)
        safe_limit = max(1, min(limit, 500))
        safe_offset = max(0, offset)
        total = conn.execute(
            f"""
            SELECT COUNT(*) AS count
            FROM generated_links gl
            LEFT JOIN generated_endpoints ge ON ge.import_run_id = gl.import_run_id AND ge.id = gl.endpoint_id
            {where}
            """,
            params,
        ).fetchone()["count"]
        rows = []
        for row in conn.execute(
            f"""
            SELECT gl.id, gl.payload_json AS link_json, ge.payload_json AS endpoint_json
            FROM generated_links gl
            LEFT JOIN generated_endpoints ge ON ge.import_run_id = gl.import_run_id AND ge.id = gl.endpoint_id
            {where}
            {order_by}
            LIMIT ? OFFSET ?
            """,
            [*params, safe_limit, safe_offset],
        ).fetchall():
            link_raw = _json_load(row["link_json"])
            link = _apply_overlay(link_raw, _overlay_for_item(overlay_index, "endpoint_service_link", link_raw, fallback_id=row["id"]))
            endpoint = _json_load(row["endpoint_json"]) if row["endpoint_json"] else None
            rows.append({"link": link, "endpoint": endpoint})
    return TablePage(rows=rows, total=total, limit=safe_limit, offset=safe_offset)


def query_validation_issues(
    search: str = "",
    severity: str = "all",
    code: str = "all",
    review_status: str = "all",
    sort: str = "severity",
    direction: str = "asc",
    limit: int = 50,
    offset: int = 0,
) -> TablePage:
    import_generated_if_needed()

    with _connect() as conn:
        run_id = _active_run_id(conn)
        if run_id is None:
            return TablePage()

        overlay = read_overlay()
        overlay_index = _overlay_index(overlay)
        where, params = _validation_issue_where(run_id, search, severity, code, review_status)
        order_by = _validation_issue_order_by(sort, direction)
        safe_limit = max(1, min(limit, 500))
        safe_offset = max(0, offset)
        total = conn.execute(
            f"SELECT COUNT(*) AS count FROM generated_validation_issues gvi {where}",
            params,
        ).fetchone()["count"]
        rows = conn.execute(
            f"""
            SELECT gvi.id, gvi.payload_json
            FROM generated_validation_issues gvi
            {where}
            {order_by}
            LIMIT ? OFFSET ?
            """,
            [*params, safe_limit, safe_offset],
        ).fetchall()

    issues = []
    for row in rows:
        issue_raw = _json_load(row["payload_json"])
        issue = _apply_overlay(
            issue_raw,
            _overlay_for_item(
                overlay_index,
                "validation_issue",
                issue_raw,
                fallback_id=row["id"],
            ),
        )
        issues.append(issue)

    return TablePage(rows=issues, total=total, limit=safe_limit, offset=safe_offset)


def read_validation_stats() -> dict[str, Any]:
    import_generated_if_needed()

    with _connect() as conn:
        run_id = _active_run_id(conn)
        if run_id is None:
            return {
                "operations": {
                    "total": 0,
                    "with_endpoint_link": 0,
                    "with_outgoing_service_call": 0,
                    "with_incoming_service_call": 0,
                    "with_any_operation_dependency": 0,
                },
                "operation_links": {
                    "total": 0,
                    "resolved": 0,
                    "unresolved": 0,
                },
                "validation_issue_codes": [],
            }

        total_operations = conn.execute(
            "SELECT COUNT(*) AS count FROM generated_operations WHERE import_run_id = ?",
            (run_id,),
        ).fetchone()["count"]
        endpoint_linked_operations = conn.execute(
            """
            SELECT COUNT(DISTINCT operation_id) AS count
            FROM generated_links
            WHERE import_run_id = ? AND operation_id IS NOT NULL
            """,
            (run_id,),
        ).fetchone()["count"]
        outgoing_operations = conn.execute(
            """
            SELECT COUNT(DISTINCT source_operation_id) AS count
            FROM generated_operation_links
            WHERE import_run_id = ? AND source_operation_id IS NOT NULL
            """,
            (run_id,),
        ).fetchone()["count"]
        incoming_operations = conn.execute(
            """
            SELECT COUNT(DISTINCT target_operation_id) AS count
            FROM generated_operation_links
            WHERE import_run_id = ? AND target_operation_id IS NOT NULL
            """,
            (run_id,),
        ).fetchone()["count"]
        any_dependency_operations = conn.execute(
            """
            SELECT COUNT(DISTINCT operation_id) AS count
            FROM (
                SELECT source_operation_id AS operation_id
                FROM generated_operation_links
                WHERE import_run_id = ? AND source_operation_id IS NOT NULL
                UNION
                SELECT target_operation_id AS operation_id
                FROM generated_operation_links
                WHERE import_run_id = ? AND target_operation_id IS NOT NULL
            )
            """,
            (run_id, run_id),
        ).fetchone()["count"]
        operation_link_counts = conn.execute(
            """
            SELECT COUNT(*) AS total,
                   SUM(CASE WHEN resolved = 1 THEN 1 ELSE 0 END) AS resolved
            FROM generated_operation_links
            WHERE import_run_id = ?
            """,
            (run_id,),
        ).fetchone()
        issue_code_rows = conn.execute(
            """
            SELECT code, severity, COUNT(*) AS count
            FROM generated_validation_issues
            WHERE import_run_id = ?
            GROUP BY code, severity
            ORDER BY count DESC, code
            """,
            (run_id,),
        ).fetchall()

    total_links = int(operation_link_counts["total"] or 0)
    resolved_links = int(operation_link_counts["resolved"] or 0)

    return {
        "operations": {
            "total": int(total_operations or 0),
            "with_endpoint_link": int(endpoint_linked_operations or 0),
            "with_outgoing_service_call": int(outgoing_operations or 0),
            "with_incoming_service_call": int(incoming_operations or 0),
            "with_any_operation_dependency": int(any_dependency_operations or 0),
        },
        "operation_links": {
            "total": total_links,
            "resolved": resolved_links,
            "unresolved": total_links - resolved_links,
        },
        "validation_issue_codes": [
            {
                "code": row["code"],
                "severity": row["severity"],
                "count": row["count"],
            }
            for row in issue_code_rows
        ],
    }


def read_service_action_graph(
    service_id: str | None = None,
    action_kind: str = "all",
    search: str = "",
) -> dict[str, Any]:
    import_generated_if_needed()

    with _connect() as conn:
        run_id = _active_run_id(conn)
        if run_id is None:
            return {
                "services": [],
                "selected_service_id": None,
                "service": None,
                "operations": [],
                "endpoints": [],
                "links": [],
                "actions": [],
                "operation_links": [],
            }

        services = _service_graph_summaries(conn, run_id)
        selected_service_id = service_id or (services[0]["id"] if services else None)

        if selected_service_id is None:
            return {
                "services": services,
                "selected_service_id": None,
                "service": None,
                "operations": [],
                "endpoints": [],
                "links": [],
                "actions": [],
                "operation_links": [],
            }

        service_row = conn.execute(
            """
            SELECT payload_json
            FROM generated_services
            WHERE import_run_id = ? AND id = ?
            LIMIT 1
            """,
            (run_id, selected_service_id),
        ).fetchone()

        if service_row is None:
            return {
                "services": services,
                "selected_service_id": selected_service_id,
                "service": None,
                "operations": [],
                "endpoints": [],
                "links": [],
                "actions": [],
                "operation_links": [],
            }

        operation_rows = conn.execute(
            """
            SELECT id, payload_json
            FROM generated_operations
            WHERE import_run_id = ? AND service_id = ?
            ORDER BY ordinal, id
            """,
            (run_id, selected_service_id),
        ).fetchall()
        operation_ids = [str(row["id"]) for row in operation_rows]
        operations = [_json_load(row["payload_json"]) for row in operation_rows]

        links = _service_graph_links(conn, run_id, selected_service_id)
        endpoint_ids = _unique_strings([str(link.get("endpoint_id")) for link in links if link.get("endpoint_id")])
        endpoints = _service_graph_endpoints(conn, run_id, endpoint_ids)
        actions = _service_graph_actions(conn, run_id, operation_ids, endpoint_ids, action_kind, search)
        operation_links = _service_graph_operation_links(conn, run_id, selected_service_id, operation_ids)

    return {
        "services": services,
        "selected_service_id": selected_service_id,
        "service": _json_load(service_row["payload_json"]),
        "operations": operations,
        "endpoints": endpoints,
        "links": links,
        "actions": actions,
        "operation_links": operation_links,
    }


def upsert_overlay_item(
    target_type: OverlayTargetType,
    target_id: str,
    payload: OverlayUpdate,
) -> CatalogOverlayItem:
    initialize_schema_only()
    target_id = _normalize_overlay_target_id(target_type, target_id)

    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    metadata = payload.metadata.model_copy(
        update={
            "updated_at": payload.metadata.updated_at or now,
        }
    )
    item = CatalogOverlayItem(
        target=OverlayTarget(type=target_type, id=target_id),
        review_status=payload.review_status,
        labels=payload.labels,
        status_markers=payload.status_markers,
        owner=payload.owner,
        notes=payload.notes,
        links=payload.links,
        overrides=payload.overrides,
        metadata=metadata,
    )

    with _connect() as conn:
        _upsert_review_item(conn, item)

    mirror_overlay_to_json(read_overlay())
    return item


def delete_overlay_item(target_type: OverlayTargetType, target_id: str) -> ArchitectureOverlay:
    initialize_schema_only()
    target_id = _normalize_overlay_target_id(target_type, target_id)

    with _connect() as conn:
        conn.execute(
            "DELETE FROM review_items WHERE target_type = ? AND target_id = ?",
            (target_type.value, target_id),
        )
        conn.execute(
            "DELETE FROM review_labels WHERE target_type = ? AND target_id = ?",
            (target_type.value, target_id),
        )
        conn.execute(
            "DELETE FROM review_status_markers WHERE target_type = ? AND target_id = ?",
            (target_type.value, target_id),
        )

    return mirror_overlay_to_json(read_overlay())


def import_generated_if_needed(force: bool = False) -> str | None:
    initialize_schema_only()
    source_hash = _generated_source_hash()

    if source_hash is None:
        return None

    with _connect() as conn:
        active = conn.execute(
            "SELECT id FROM import_runs WHERE active = 1 AND source_hash = ?",
            (source_hash,),
        ).fetchone()

        if active is not None and not force and _generated_identity_ready(conn, str(active["id"])):
            return str(active["id"])

        generated = _read_generated_json_files()
        run_id = str(uuid4())
        now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()

        conn.execute("UPDATE import_runs SET active = 0")
        conn.execute(
            """
            INSERT INTO import_runs (id, source_hash, created_at, active, schema_version)
            VALUES (?, ?, ?, 1, ?)
            """,
            (run_id, source_hash, now, "archdoc-static/v0.1"),
        )

        _clear_generated_tables(conn)
        _insert_services(conn, run_id, generated["services"])
        _insert_endpoints(conn, run_id, generated["endpoints"])
        _insert_links(conn, run_id, generated["links"])
        _insert_actions(conn, run_id, generated["actions"])
        _insert_operation_links(conn, run_id, generated["operation_links"])
        _insert_validation(conn, run_id, generated["validation_report"])

        return run_id


def import_user_stories() -> int:
    initialize_schema_only()
    stories = _read_user_story_markdown_files()

    with _connect() as conn:
        conn.execute("DELETE FROM user_stories")

        for story in stories:
            conn.execute(
                """
                INSERT INTO user_stories (
                    id, title, area, status, owner, roles_json, endpoints_json,
                    body_markdown, source_file, payload_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    story["id"],
                    story.get("title"),
                    story.get("area"),
                    story.get("status"),
                    story.get("owner"),
                    _json_dump(story.get("roles", [])),
                    _json_dump(story.get("endpoints", [])),
                    story.get("body_markdown", ""),
                    story.get("source_file"),
                    _json_dump(story),
                ),
            )

    return len(stories)


def _read_user_story_markdown_files() -> list[dict[str, Any]]:
    if not settings.user_stories_dir.exists():
        return []

    stories: list[dict[str, Any]] = []
    for path in sorted(settings.user_stories_dir.glob("*.md")):
        parsed = _parse_user_story_markdown(path)
        if parsed is not None:
            stories.append(parsed)

    return stories


def _parse_user_story_markdown(path: Path) -> dict[str, Any] | None:
    raw = path.read_text(encoding="utf-8")
    frontmatter: dict[str, Any] = {}
    body = raw

    if raw.startswith("---"):
        parts = raw.split("---", 2)
        if len(parts) == 3:
            frontmatter = yaml.safe_load(parts[1]) or {}
            body = parts[2].lstrip()

    story_id = str(frontmatter.get("id") or path.stem).strip()
    if not story_id:
        return None

    endpoints = [
        {
            "method": str(endpoint.get("method", "")).upper(),
            "path": str(endpoint.get("path", "")),
            "purpose": endpoint.get("purpose") or endpoint.get("zweck"),
        }
        for endpoint in frontmatter.get("endpoints", []) or []
        if isinstance(endpoint, dict)
    ]

    return {
        "id": story_id,
        "title": frontmatter.get("title") or _heading_title(body) or story_id,
        "area": frontmatter.get("area") or "unknown",
        "status": frontmatter.get("status") or "draft",
        "owner": frontmatter.get("owner"),
        "roles": _normalized_string_list(frontmatter.get("roles")),
        "endpoints": endpoints,
        "body_markdown": body,
        "source_file": str(path.relative_to(settings.user_stories_dir.parent)),
        "linkage": "unmapped",
    }


def _generated_identity_ready(conn: sqlite3.Connection, run_id: str) -> bool:
    checks = [
        ("generated_services", "catalog_id"),
        ("generated_operations", "catalog_id"),
        ("generated_endpoints", "catalog_id"),
        ("generated_links", "catalog_id"),
        ("generated_actions", "catalog_id"),
    ]

    for table, column in checks:
        missing = conn.execute(
            f"""
            SELECT COUNT(*) AS count
            FROM {table}
            WHERE import_run_id = ? AND ({column} IS NULL OR {column} = '')
            """,
            (run_id,),
        ).fetchone()["count"]

        if missing:
            return False

    return True


def import_overlay_json_if_needed() -> None:
    initialize_schema_only()
    if not settings.overlay_path.exists():
        return

    with _connect() as conn:
        count = conn.execute("SELECT COUNT(*) AS count FROM review_items").fetchone()["count"]

    if count > 0:
        return

    overlay = ArchitectureOverlay.model_validate_json(settings.overlay_path.read_text(encoding="utf-8"))
    write_overlay(overlay)


def mirror_overlay_to_json(overlay: ArchitectureOverlay) -> ArchitectureOverlay:
    settings.overlay_path.parent.mkdir(parents=True, exist_ok=True)
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
    settings.overlay_path.write_text(
        json.dumps(
            sorted_overlay.model_dump(mode="json", exclude_none=True),
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    return sorted_overlay


def initialize_schema_only() -> None:
    settings.db_path.parent.mkdir(parents=True, exist_ok=True)
    with _connect() as conn:
        _create_schema(conn)


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(settings.db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _create_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS import_runs (
            id TEXT PRIMARY KEY,
            source_hash TEXT NOT NULL,
            created_at TEXT NOT NULL,
            active INTEGER NOT NULL DEFAULT 0,
            schema_version TEXT
        );

        CREATE TABLE IF NOT EXISTS schema_meta (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS generated_services (
            generated_pk TEXT PRIMARY KEY,
            import_run_id TEXT NOT NULL,
            id TEXT NOT NULL,
            catalog_id TEXT,
            logical_id TEXT,
            source_id TEXT,
            display_name TEXT,
            aliases_json TEXT NOT NULL DEFAULT '[]',
            module TEXT,
            class_name TEXT,
            qualified_name TEXT,
            source_file TEXT,
            source_line INTEGER,
            payload_json TEXT NOT NULL,
            FOREIGN KEY (import_run_id) REFERENCES import_runs(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS generated_operations (
            generated_pk TEXT PRIMARY KEY,
            import_run_id TEXT NOT NULL,
            id TEXT NOT NULL,
            catalog_id TEXT,
            logical_id TEXT,
            source_id TEXT,
            display_name TEXT,
            aliases_json TEXT NOT NULL DEFAULT '[]',
            service_id TEXT NOT NULL,
            method TEXT,
            qualified_name TEXT,
            source_file TEXT,
            source_line INTEGER,
            payload_json TEXT NOT NULL,
            ordinal INTEGER NOT NULL,
            FOREIGN KEY (import_run_id) REFERENCES import_runs(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS generated_endpoints (
            generated_pk TEXT PRIMARY KEY,
            import_run_id TEXT NOT NULL,
            id TEXT NOT NULL,
            catalog_id TEXT,
            logical_id TEXT,
            source_id TEXT,
            display_name TEXT,
            aliases_json TEXT NOT NULL DEFAULT '[]',
            http_method TEXT,
            path TEXT,
            include_prefix TEXT,
            router_prefix TEXT,
            full_path TEXT,
            module TEXT,
            function_name TEXT,
            source_file TEXT,
            source_line INTEGER,
            payload_json TEXT NOT NULL,
            ordinal INTEGER NOT NULL,
            FOREIGN KEY (import_run_id) REFERENCES import_runs(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS generated_links (
            generated_pk TEXT PRIMARY KEY,
            import_run_id TEXT NOT NULL,
            id TEXT NOT NULL,
            catalog_id TEXT,
            logical_id TEXT,
            source_id TEXT,
            display_name TEXT,
            aliases_json TEXT NOT NULL DEFAULT '[]',
            endpoint_id TEXT,
            service_id TEXT,
            operation_id TEXT,
            source_file TEXT,
            source_line INTEGER,
            payload_json TEXT NOT NULL,
            ordinal INTEGER NOT NULL,
            FOREIGN KEY (import_run_id) REFERENCES import_runs(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS generated_validation_issues (
            generated_pk TEXT PRIMARY KEY,
            import_run_id TEXT NOT NULL,
            id TEXT NOT NULL,
            code TEXT,
            severity TEXT,
            item_id TEXT,
            source_file TEXT,
            source_line INTEGER,
            payload_json TEXT NOT NULL,
            ordinal INTEGER NOT NULL,
            FOREIGN KEY (import_run_id) REFERENCES import_runs(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS generated_actions (
            generated_pk TEXT PRIMARY KEY,
            import_run_id TEXT NOT NULL,
            id TEXT NOT NULL,
            catalog_id TEXT,
            logical_id TEXT,
            source_id TEXT,
            display_name TEXT,
            aliases_json TEXT NOT NULL DEFAULT '[]',
            kind TEXT,
            action TEXT,
            access TEXT,
            owner_type TEXT,
            owner_id TEXT,
            owner_qualified_name TEXT,
            owner_class_name TEXT,
            owner_module TEXT,
            call_name TEXT,
            resource TEXT,
            entity TEXT,
            source_file TEXT,
            source_line INTEGER,
            payload_json TEXT NOT NULL,
            ordinal INTEGER NOT NULL,
            FOREIGN KEY (import_run_id) REFERENCES import_runs(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS generated_operation_links (
            generated_pk TEXT PRIMARY KEY,
            import_run_id TEXT NOT NULL,
            id TEXT NOT NULL,
            catalog_id TEXT,
            logical_id TEXT,
            source_id TEXT,
            display_name TEXT,
            aliases_json TEXT NOT NULL DEFAULT '[]',
            link_type TEXT,
            source_operation_id TEXT,
            source_service_id TEXT,
            target_operation_id TEXT,
            target_service_id TEXT,
            target_class_name TEXT,
            target_method_name TEXT,
            call_name TEXT,
            variable TEXT,
            resolved INTEGER NOT NULL DEFAULT 0,
            source_file TEXT,
            source_line INTEGER,
            payload_json TEXT NOT NULL,
            ordinal INTEGER NOT NULL,
            FOREIGN KEY (import_run_id) REFERENCES import_runs(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS generated_validation_reports (
            import_run_id TEXT PRIMARY KEY,
            summary_json TEXT NOT NULL,
            schema_version TEXT,
            FOREIGN KEY (import_run_id) REFERENCES import_runs(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS user_stories (
            id TEXT PRIMARY KEY,
            title TEXT,
            area TEXT,
            status TEXT,
            owner TEXT,
            roles_json TEXT NOT NULL DEFAULT '[]',
            endpoints_json TEXT NOT NULL DEFAULT '[]',
            body_markdown TEXT NOT NULL DEFAULT '',
            source_file TEXT,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS review_items (
            target_type TEXT NOT NULL,
            target_id TEXT NOT NULL,
            parent_id TEXT,
            source_file TEXT,
            source_line INTEGER,
            review_status TEXT,
            owner TEXT,
            notes TEXT,
            links_json TEXT NOT NULL DEFAULT '{}',
            overrides_json TEXT NOT NULL DEFAULT '{}',
            metadata_json TEXT NOT NULL DEFAULT '{}',
            updated_at TEXT,
            PRIMARY KEY (target_type, target_id)
        );

        CREATE TABLE IF NOT EXISTS review_labels (
            target_type TEXT NOT NULL,
            target_id TEXT NOT NULL,
            label TEXT NOT NULL,
            PRIMARY KEY (target_type, target_id, label),
            FOREIGN KEY (target_type, target_id) REFERENCES review_items(target_type, target_id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS review_status_markers (
            target_type TEXT NOT NULL,
            target_id TEXT NOT NULL,
            marker TEXT NOT NULL,
            PRIMARY KEY (target_type, target_id, marker),
            FOREIGN KEY (target_type, target_id) REFERENCES review_items(target_type, target_id) ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS idx_generated_endpoints_lookup
            ON generated_endpoints(import_run_id, id, http_method, path, module);
        CREATE INDEX IF NOT EXISTS idx_generated_operations_lookup
            ON generated_operations(import_run_id, id, service_id, method);
        CREATE INDEX IF NOT EXISTS idx_generated_links_lookup
            ON generated_links(import_run_id, endpoint_id, service_id, operation_id);
        CREATE INDEX IF NOT EXISTS idx_generated_actions_lookup
            ON generated_actions(import_run_id, kind, owner_type, owner_id, entity, resource);
        CREATE INDEX IF NOT EXISTS idx_generated_operation_links_lookup
            ON generated_operation_links(import_run_id, source_service_id, source_operation_id, target_service_id, target_operation_id);
        CREATE INDEX IF NOT EXISTS idx_generated_validation_issues_lookup
            ON generated_validation_issues(import_run_id, code, severity, item_id);
        CREATE INDEX IF NOT EXISTS idx_user_stories_lookup
            ON user_stories(area, status, id);
        CREATE INDEX IF NOT EXISTS idx_review_items_lookup
            ON review_items(target_type, target_id);
        """
    )
    _ensure_identity_columns(conn)
    _ensure_endpoint_route_columns(conn)
    conn.executescript(
        """
        CREATE INDEX IF NOT EXISTS idx_generated_endpoints_route_lookup
            ON generated_endpoints(import_run_id, http_method, full_path, path);
        CREATE INDEX IF NOT EXISTS idx_generated_endpoints_identity
            ON generated_endpoints(import_run_id, catalog_id, logical_id, source_id);
        CREATE INDEX IF NOT EXISTS idx_generated_operations_identity
            ON generated_operations(import_run_id, catalog_id, logical_id, source_id);
        CREATE INDEX IF NOT EXISTS idx_generated_links_identity
            ON generated_links(import_run_id, catalog_id, logical_id, source_id);
        CREATE INDEX IF NOT EXISTS idx_generated_services_identity
            ON generated_services(import_run_id, catalog_id, logical_id, source_id);
        CREATE INDEX IF NOT EXISTS idx_generated_actions_identity
            ON generated_actions(import_run_id, catalog_id, logical_id, source_id);
        CREATE INDEX IF NOT EXISTS idx_generated_operation_links_identity
            ON generated_operation_links(import_run_id, catalog_id, logical_id, source_id);
        """
    )
    conn.execute(
        """
        INSERT INTO schema_meta (key, value)
        VALUES ('schema_version', ?)
        ON CONFLICT(key) DO UPDATE SET value = excluded.value
        """,
        (str(SCHEMA_VERSION),),
    )


def _clear_generated_tables(conn: sqlite3.Connection) -> None:
    conn.execute("DELETE FROM generated_validation_reports")
    conn.execute("DELETE FROM generated_validation_issues")
    conn.execute("DELETE FROM generated_operation_links")
    conn.execute("DELETE FROM generated_actions")
    conn.execute("DELETE FROM generated_links")
    conn.execute("DELETE FROM generated_endpoints")
    conn.execute("DELETE FROM generated_operations")
    conn.execute("DELETE FROM generated_services")


def _ensure_identity_columns(conn: sqlite3.Connection) -> None:
    identity_columns = {
        "catalog_id": "TEXT",
        "logical_id": "TEXT",
        "source_id": "TEXT",
        "display_name": "TEXT",
        "aliases_json": "TEXT NOT NULL DEFAULT '[]'",
    }

    for table in (
        "generated_services",
        "generated_operations",
        "generated_endpoints",
        "generated_links",
        "generated_actions",
    ):
        existing = {
            row["name"]
            for row in conn.execute(f"PRAGMA table_info({table})").fetchall()
        }

        for column, definition in identity_columns.items():
            if column in existing:
                continue

            conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")


def _ensure_endpoint_route_columns(conn: sqlite3.Connection) -> None:
    existing = {
        row["name"]
        for row in conn.execute("PRAGMA table_info(generated_endpoints)").fetchall()
    }

    for column in ("include_prefix", "router_prefix", "full_path"):
        if column not in existing:
            conn.execute(f"ALTER TABLE generated_endpoints ADD COLUMN {column} TEXT")


def _insert_services(conn: sqlite3.Connection, run_id: str, services: list[dict[str, Any]]) -> None:
    for index, service in enumerate(services):
        service_identity = _identity_values(service, fallback_display=service.get("class_name"))
        service_pk = _generated_pk(run_id, "service", service.get("id"), service.get("qualified_name"), index)
        conn.execute(
            """
            INSERT INTO generated_services (
                generated_pk, import_run_id, id, catalog_id, logical_id, source_id,
                display_name, aliases_json, module, class_name, qualified_name,
                source_file, source_line, payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                service_pk,
                run_id,
                service.get("id"),
                service_identity["catalog_id"],
                service_identity["logical_id"],
                service_identity["source_id"],
                service_identity["display_name"],
                _json_dump(service_identity["aliases"]),
                service.get("module"),
                service.get("class_name"),
                service.get("qualified_name"),
                service.get("source", {}).get("file"),
                service.get("source", {}).get("line_start"),
                _json_dump(service),
            ),
        )

        for operation_index, operation in enumerate(service.get("operations", [])):
            operation_identity = _identity_values(operation, fallback_display=operation.get("method"))
            operation_pk = _generated_pk(
                run_id,
                "operation",
                operation.get("id"),
                operation.get("qualified_name"),
                operation.get("source", {}).get("file"),
                operation.get("source", {}).get("line_start"),
                index,
                operation_index,
            )
            conn.execute(
                """
                INSERT INTO generated_operations (
                    generated_pk, import_run_id, id, catalog_id, logical_id, source_id,
                    display_name, aliases_json, service_id, method, qualified_name,
                    source_file, source_line, payload_json, ordinal
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    operation_pk,
                    run_id,
                    operation.get("id"),
                    operation_identity["catalog_id"],
                    operation_identity["logical_id"],
                    operation_identity["source_id"],
                    operation_identity["display_name"],
                    _json_dump(operation_identity["aliases"]),
                    service.get("id"),
                    operation.get("method"),
                    operation.get("qualified_name"),
                    operation.get("source", {}).get("file"),
                    operation.get("source", {}).get("line_start"),
                    _json_dump(operation),
                    operation_index,
                ),
            )


def _insert_endpoints(conn: sqlite3.Connection, run_id: str, endpoints: list[dict[str, Any]]) -> None:
    for index, endpoint in enumerate(endpoints):
        endpoint_identity = _identity_values(
            endpoint,
            fallback_display=endpoint.get("full_path") or endpoint.get("path") or endpoint.get("function_name"),
        )
        endpoint_pk = _generated_pk(
            run_id,
            "endpoint",
            endpoint.get("id"),
            endpoint.get("qualified_name"),
            endpoint.get("source", {}).get("file"),
            endpoint.get("source", {}).get("line_start"),
            index,
        )
        conn.execute(
            """
            INSERT INTO generated_endpoints (
                generated_pk, import_run_id, id, catalog_id, logical_id, source_id,
                display_name, aliases_json, http_method, path, include_prefix, router_prefix, full_path, module,
                function_name, source_file, source_line, payload_json, ordinal
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                endpoint_pk,
                run_id,
                endpoint.get("id"),
                endpoint_identity["catalog_id"],
                endpoint_identity["logical_id"],
                endpoint_identity["source_id"],
                endpoint_identity["display_name"],
                _json_dump(endpoint_identity["aliases"]),
                endpoint.get("http_method"),
                endpoint.get("path"),
                endpoint.get("include_prefix"),
                endpoint.get("router_prefix"),
                endpoint.get("full_path") or endpoint.get("path"),
                endpoint.get("module"),
                endpoint.get("function_name"),
                endpoint.get("source", {}).get("file"),
                endpoint.get("source", {}).get("line_start"),
                _json_dump(endpoint),
                index,
            ),
        )


def _insert_links(conn: sqlite3.Connection, run_id: str, links: list[dict[str, Any]]) -> None:
    for index, link in enumerate(links):
        link_id = _link_id(link)
        link_identity = _identity_values(link, fallback_id=link_id, fallback_display=link.get("call_name"))
        link_pk = _generated_pk(run_id, "endpoint_service_link", link_id, index)
        conn.execute(
            """
            INSERT INTO generated_links (
                generated_pk, import_run_id, id, catalog_id, logical_id, source_id,
                display_name, aliases_json, endpoint_id, service_id,
                operation_id, source_file, source_line, payload_json, ordinal
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                link_pk,
                run_id,
                link_id,
                link_identity["catalog_id"],
                link_identity["logical_id"],
                link_identity["source_id"],
                link_identity["display_name"],
                _json_dump(link_identity["aliases"]),
                link.get("endpoint_id"),
                link.get("service_id"),
                link.get("operation_id"),
                link.get("source", {}).get("file"),
                link.get("source", {}).get("line_start"),
                _json_dump(link),
                index,
            ),
        )


def _insert_actions(conn: sqlite3.Connection, run_id: str, actions: list[dict[str, Any]]) -> None:
    for index, action in enumerate(actions):
        action_identity = _identity_values(action, fallback_display=action.get("call_name") or action.get("kind"))
        owner = action.get("owner") or {}
        action_pk = _generated_pk(
            run_id,
            "architecture_action",
            action.get("id"),
            owner.get("id"),
            action.get("kind"),
            action.get("source", {}).get("file"),
            action.get("source", {}).get("line_start"),
            index,
        )
        conn.execute(
            """
            INSERT INTO generated_actions (
                generated_pk, import_run_id, id, catalog_id, logical_id, source_id,
                display_name, aliases_json, kind, action, access, owner_type,
                owner_id, owner_qualified_name, owner_class_name, owner_module,
                call_name, resource, entity, source_file, source_line,
                payload_json, ordinal
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                action_pk,
                run_id,
                action.get("id"),
                action_identity["catalog_id"],
                action_identity["logical_id"],
                action_identity["source_id"],
                action_identity["display_name"],
                _json_dump(action_identity["aliases"]),
                action.get("kind"),
                action.get("action"),
                action.get("access"),
                owner.get("type"),
                owner.get("id"),
                owner.get("qualified_name"),
                owner.get("class_name"),
                owner.get("module"),
                action.get("call_name"),
                action.get("resource"),
                action.get("entity"),
                action.get("source", {}).get("file"),
                action.get("source", {}).get("line_start"),
                _json_dump(action),
                index,
            ),
        )


def _insert_operation_links(conn: sqlite3.Connection, run_id: str, links: list[dict[str, Any]]) -> None:
    for index, link in enumerate(links):
        link_identity = _identity_values(link, fallback_display=link.get("call_name") or link.get("link_type"))
        source = link.get("source") or {}
        target = link.get("target") or {}
        source_ref = link.get("source_ref") or {}
        link_pk = _generated_pk(
            run_id,
            "operation_link",
            link.get("id"),
            source.get("operation_id"),
            target.get("operation_id") or target.get("service_id"),
            source_ref.get("file"),
            source_ref.get("line_start"),
            index,
        )
        conn.execute(
            """
            INSERT INTO generated_operation_links (
                generated_pk, import_run_id, id, catalog_id, logical_id, source_id,
                display_name, aliases_json, link_type, source_operation_id,
                source_service_id, target_operation_id, target_service_id,
                target_class_name, target_method_name, call_name, variable, resolved,
                source_file, source_line, payload_json, ordinal
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                link_pk,
                run_id,
                link.get("id"),
                link_identity["catalog_id"],
                link_identity["logical_id"],
                link_identity["source_id"],
                link_identity["display_name"],
                _json_dump(link_identity["aliases"]),
                link.get("link_type"),
                source.get("operation_id"),
                source.get("service_id"),
                target.get("operation_id"),
                target.get("service_id"),
                target.get("class_name"),
                target.get("method_name"),
                link.get("call_name"),
                link.get("variable"),
                1 if link.get("resolved") else 0,
                source_ref.get("file"),
                source_ref.get("line_start"),
                _json_dump(link),
                index,
            ),
        )


def _insert_validation(conn: sqlite3.Connection, run_id: str, report: dict[str, Any] | None) -> None:
    if report is None:
        return

    conn.execute(
        """
        INSERT INTO generated_validation_reports (import_run_id, summary_json, schema_version)
        VALUES (?, ?, ?)
        """,
        (run_id, _json_dump(report.get("summary", {})), report.get("schema_version")),
    )

    for index, issue in enumerate(report.get("issues", [])):
        issue_id = _validation_issue_id(issue)
        issue_pk = _generated_pk(run_id, "validation_issue", issue_id, index)
        conn.execute(
            """
            INSERT INTO generated_validation_issues (
                generated_pk, import_run_id, id, code, severity, item_id,
                source_file, source_line, payload_json, ordinal
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                issue_pk,
                run_id,
                issue_id,
                issue.get("code"),
                issue.get("severity"),
                issue.get("item_id"),
                issue.get("source_file"),
                issue.get("line_start"),
                _json_dump(issue),
                index,
            ),
        )


def _story_from_row(row: sqlite3.Row) -> dict[str, Any]:
    story = _json_load(row["payload_json"])
    story["roles"] = _json_load(row["roles_json"]) or []
    story["endpoints"] = _json_load(row["endpoints_json"]) or []
    story["_link_summary"] = _story_link_summary(story)
    return story


def _story_link_summary(story: dict[str, Any]) -> dict[str, Any]:
    endpoints = story.get("endpoints") or []
    return {
        "declared_endpoints": len(endpoints),
        "linked_endpoints": int(story.get("_linked_endpoint_count", 0)),
        "status": story.get("_linkage") or "unmapped",
    }


def _story_linked_architecture(
    conn: sqlite3.Connection,
    run_id: str,
    story: dict[str, Any],
) -> list[dict[str, Any]]:
    linked: list[dict[str, Any]] = []

    for endpoint_ref in story.get("endpoints", []):
        endpoint_row = _find_endpoint_for_story_ref(conn, run_id, endpoint_ref)
        entry: dict[str, Any] = {
            "ref": endpoint_ref,
            "match_status": "missing",
            "endpoint": None,
            "links": [],
        }

        if endpoint_row is None:
            linked.append(entry)
            continue

        endpoint = _json_load(endpoint_row["payload_json"])
        entry["match_status"] = "linked"
        entry["endpoint"] = endpoint
        entry["links"] = _architecture_for_endpoint(conn, run_id, endpoint["id"])
        linked.append(entry)

    return linked


def _build_user_story_trace(
    conn: sqlite3.Connection,
    run_id: str,
    story: dict[str, Any],
) -> dict[str, Any]:
    nodes: dict[str, dict[str, Any]] = {}
    edges: dict[str, dict[str, Any]] = {}
    unresolved_refs: list[dict[str, Any]] = []

    story_node_id = f"story:{story['id']}"
    _add_trace_node(
        nodes,
        story_node_id,
        "user_story",
        story["id"],
        story.get("title") or story["id"],
        story,
    )

    operation_ids: set[str] = set()

    for endpoint_ref in story.get("endpoints", []):
        endpoint_row = _find_endpoint_for_story_ref(conn, run_id, endpoint_ref)
        if endpoint_row is None:
            unresolved_refs.append(endpoint_ref)
            continue

        endpoint = _json_load(endpoint_row["payload_json"])
        endpoint_node_id = f"endpoint:{endpoint['id']}"
        endpoint_label = f"{endpoint.get('http_method')} {endpoint.get('full_path') or endpoint.get('path') or endpoint.get('id')}"
        _add_trace_node(nodes, endpoint_node_id, "endpoint", endpoint.get("id"), endpoint_label, endpoint)
        _add_trace_edge(edges, story_node_id, endpoint_node_id, "declares")

        for link_entry in _architecture_for_endpoint(conn, run_id, endpoint["id"]):
            service = link_entry.get("service")
            operation = link_entry.get("operation")
            link = link_entry.get("link")

            if service:
                service_node_id = f"service:{service['id']}"
                _add_trace_node(nodes, service_node_id, "service", service.get("id"), service.get("class_name") or service.get("id"), service)
                _add_trace_edge(edges, endpoint_node_id, service_node_id, "routes_to")

            if operation:
                operation_node_id = f"operation:{operation['id']}"
                operation_ids.add(operation["id"])
                _add_trace_node(nodes, operation_node_id, "operation", operation.get("id"), operation.get("method") or operation.get("id"), operation)
                _add_trace_edge(edges, endpoint_node_id, operation_node_id, "calls")
                if service:
                    _add_trace_edge(edges, f"service:{service['id']}", operation_node_id, "owns")
                if link:
                    nodes[operation_node_id]["link"] = link

                _attach_operation_actions_to_trace(nodes, edges, operation_node_id, link_entry.get("actions") or [])

    _attach_operation_dependencies_to_trace(conn, run_id, nodes, edges, operation_ids)

    summary = _trace_summary(nodes, edges, unresolved_refs)
    return {
        "story": story,
        "nodes": list(nodes.values()),
        "edges": list(edges.values()),
        "unresolved_refs": unresolved_refs,
        "summary": summary,
    }


def _attach_operation_actions_to_trace(
    nodes: dict[str, dict[str, Any]],
    edges: dict[str, dict[str, Any]],
    operation_node_id: str,
    actions: list[dict[str, Any]],
) -> None:
    for action in actions:
        action_node_id = f"action:{action.get('id')}"
        label = _action_trace_label(action)
        _add_trace_node(nodes, action_node_id, action.get("kind") or "action", action.get("id"), label, action)
        _add_trace_edge(edges, operation_node_id, action_node_id, "does")

        entity = action.get("entity")
        if not entity and isinstance(action.get("query"), dict):
            entities = action["query"].get("entities") or []
            entity = entities[0] if entities else None

        if entity:
            entity_node_id = f"entity:{entity}"
            _add_trace_node(nodes, entity_node_id, "entity", entity, entity, {"name": entity})
            _add_trace_edge(edges, action_node_id, entity_node_id, "touches")


def _attach_operation_dependencies_to_trace(
    conn: sqlite3.Connection,
    run_id: str,
    nodes: dict[str, dict[str, Any]],
    edges: dict[str, dict[str, Any]],
    operation_ids: set[str],
) -> None:
    if not operation_ids:
        return

    placeholders = ",".join("?" for _ in operation_ids)
    rows = conn.execute(
        f"""
        SELECT payload_json
        FROM generated_operation_links
        WHERE import_run_id = ?
          AND source_operation_id IN ({placeholders})
        ORDER BY source_operation_id, target_service_id, target_operation_id
        LIMIT 200
        """,
        [run_id, *sorted(operation_ids)],
    ).fetchall()

    for row in rows:
        operation_link = _json_load(row["payload_json"])
        source_operation_id = operation_link.get("source", {}).get("operation_id")
        target_operation_id = operation_link.get("target", {}).get("operation_id")
        target_service_id = operation_link.get("target", {}).get("service_id")

        if target_service_id:
            service = _read_service_by_id(conn, run_id, target_service_id)
            service_node_id = f"service:{target_service_id}"
            _add_trace_node(nodes, service_node_id, "service", target_service_id, service.get("class_name") if service else target_service_id, service or operation_link.get("target", {}))

        if source_operation_id and target_operation_id:
            operation = _read_operation_by_id(conn, run_id, target_operation_id)
            operation_node_id = f"operation:{target_operation_id}"
            _add_trace_node(nodes, operation_node_id, "operation", target_operation_id, operation.get("method") if operation else target_operation_id, operation or operation_link.get("target", {}))
            _add_trace_edge(edges, f"operation:{source_operation_id}", operation_node_id, "calls_service")
            if target_service_id:
                _add_trace_edge(edges, f"service:{target_service_id}", operation_node_id, "owns")
            _attach_operation_actions_to_trace(nodes, edges, operation_node_id, _actions_for_operation(conn, run_id, target_operation_id))


def _read_service_by_id(conn: sqlite3.Connection, run_id: str, service_id: str) -> dict[str, Any] | None:
    row = conn.execute(
        "SELECT payload_json FROM generated_services WHERE import_run_id = ? AND id = ? LIMIT 1",
        (run_id, service_id),
    ).fetchone()
    return _json_load(row["payload_json"]) if row else None


def _read_operation_by_id(conn: sqlite3.Connection, run_id: str, operation_id: str) -> dict[str, Any] | None:
    row = conn.execute(
        "SELECT payload_json FROM generated_operations WHERE import_run_id = ? AND id = ? LIMIT 1",
        (run_id, operation_id),
    ).fetchone()
    return _json_load(row["payload_json"]) if row else None


def _add_trace_node(
    nodes: dict[str, dict[str, Any]],
    node_id: str,
    kind: str,
    target_id: str | None,
    label: str | None,
    payload: dict[str, Any],
) -> None:
    if node_id in nodes:
        return

    nodes[node_id] = {
        "id": node_id,
        "kind": kind,
        "target_id": target_id,
        "label": label or target_id or node_id,
        "payload": payload,
    }


def _add_trace_edge(
    edges: dict[str, dict[str, Any]],
    source: str,
    target: str,
    label: str,
) -> None:
    edge_id = f"{source}->{label}->{target}"
    edges.setdefault(
        edge_id,
        {
            "id": edge_id,
            "source": source,
            "target": target,
            "label": label,
        },
    )


def _action_trace_label(action: dict[str, Any]) -> str:
    if action.get("resource"):
        return str(action["resource"])
    if action.get("entity"):
        return str(action["entity"])
    if action.get("call_name"):
        return str(action["call_name"])
    return str(action.get("kind") or action.get("id") or "action")


def _trace_summary(
    nodes: dict[str, dict[str, Any]],
    edges: dict[str, dict[str, Any]],
    unresolved_refs: list[dict[str, Any]],
) -> dict[str, Any]:
    counts: dict[str, int] = {}
    for node in nodes.values():
        kind = str(node.get("kind") or "unknown")
        counts[kind] = counts.get(kind, 0) + 1

    return {
        "nodes": len(nodes),
        "edges": len(edges),
        "unresolved_refs": len(unresolved_refs),
        "by_kind": counts,
    }


def _architecture_for_endpoint(
    conn: sqlite3.Connection,
    run_id: str,
    endpoint_id: str,
) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT gl.payload_json AS link_json,
               gs.payload_json AS service_json,
               go.payload_json AS operation_json
        FROM generated_links gl
        LEFT JOIN generated_services gs
          ON gs.import_run_id = gl.import_run_id AND gs.id = gl.service_id
        LEFT JOIN generated_operations go
          ON go.import_run_id = gl.import_run_id AND go.id = gl.operation_id
        WHERE gl.import_run_id = ? AND gl.endpoint_id = ?
        ORDER BY gl.service_id, gl.operation_id
        """,
        (run_id, endpoint_id),
    ).fetchall()

    result = []
    for row in rows:
        link = _json_load(row["link_json"])
        operation = _json_load(row["operation_json"])
        result.append(
            {
                "link": link,
                "service": _json_load(row["service_json"]),
                "operation": operation,
                "actions": _actions_for_operation(conn, run_id, operation.get("id") if operation else None),
            }
        )

    return result


def _actions_for_operation(
    conn: sqlite3.Connection,
    run_id: str,
    operation_id: str | None,
) -> list[dict[str, Any]]:
    if not operation_id:
        return []

    rows = conn.execute(
        """
        SELECT payload_json
        FROM generated_actions
        WHERE import_run_id = ? AND owner_type = 'operation' AND owner_id = ?
        ORDER BY kind, resource, id
        """,
        (run_id, operation_id),
    ).fetchall()
    return [_json_load(row["payload_json"]) for row in rows]


def _find_endpoint_for_story_ref(
    conn: sqlite3.Connection,
    run_id: str,
    endpoint_ref: dict[str, Any],
) -> sqlite3.Row | None:
    method = str(endpoint_ref.get("method") or "").upper()
    path = str(endpoint_ref.get("path") or "")
    paths = _endpoint_path_candidates(path)

    for candidate in paths:
        row = conn.execute(
            """
            SELECT *
            FROM generated_endpoints
            WHERE import_run_id = ? AND UPPER(http_method) = ?
              AND (full_path = ? OR path = ?)
            LIMIT 1
            """,
            (run_id, method, candidate, candidate),
        ).fetchone()
        if row is not None:
            return row

    return None


def _read_services(conn: sqlite3.Connection, run_id: str) -> list[dict[str, Any]]:
    service_rows = conn.execute(
        """
        SELECT payload_json
        FROM generated_services
        WHERE import_run_id = ?
        ORDER BY id
        """,
        (run_id,),
    ).fetchall()
    services = [_json_load(row["payload_json"]) for row in service_rows]

    operations_by_service: dict[str, list[dict[str, Any]]] = {}
    operation_rows = conn.execute(
        """
        SELECT service_id, payload_json
        FROM generated_operations
        WHERE import_run_id = ?
        ORDER BY service_id, ordinal, generated_pk
        """,
        (run_id,),
    ).fetchall()

    for row in operation_rows:
        operations_by_service.setdefault(row["service_id"], []).append(_json_load(row["payload_json"]))

    for service in services:
        service["operations"] = operations_by_service.get(service.get("id"), [])

    return services


def _read_payload_rows(conn: sqlite3.Connection, table: str, run_id: str) -> list[dict[str, Any]]:
    rows = conn.execute(
        f"""
        SELECT payload_json
        FROM {table}
        WHERE import_run_id = ?
        ORDER BY ordinal, generated_pk
        """,
        (run_id,),
    ).fetchall()
    return [_json_load(row["payload_json"]) for row in rows]


def _read_validation_report(conn: sqlite3.Connection, run_id: str) -> dict[str, Any] | None:
    report_row = conn.execute(
        "SELECT summary_json, schema_version FROM generated_validation_reports WHERE import_run_id = ?",
        (run_id,),
    ).fetchone()

    if report_row is None:
        return None

    issues = _read_payload_rows(conn, "generated_validation_issues", run_id)

    return {
        "schema_version": report_row["schema_version"],
        "summary": _json_load(report_row["summary_json"]),
        "issues": issues,
    }


def _service_graph_summaries(conn: sqlite3.Connection, run_id: str) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT gs.id, gs.class_name, gs.module, gs.display_name,
               COALESCE(op_counts.operation_count, 0) AS operation_count,
               COALESCE(endpoint_counts.endpoint_count, 0) AS endpoint_count,
               COALESCE(action_counts.action_count, 0) AS action_count
        FROM generated_services gs
        LEFT JOIN (
            SELECT service_id, COUNT(*) AS operation_count
            FROM generated_operations
            WHERE import_run_id = ?
            GROUP BY service_id
        ) op_counts ON op_counts.service_id = gs.id
        LEFT JOIN (
            SELECT service_id, COUNT(DISTINCT endpoint_id) AS endpoint_count
            FROM generated_links
            WHERE import_run_id = ?
            GROUP BY service_id
        ) endpoint_counts ON endpoint_counts.service_id = gs.id
        LEFT JOIN (
            SELECT go.service_id, COUNT(ga.id) AS action_count
            FROM generated_operations go
            JOIN generated_actions ga
              ON ga.import_run_id = go.import_run_id AND ga.owner_id = go.id
            WHERE go.import_run_id = ?
            GROUP BY go.service_id
        ) action_counts ON action_counts.service_id = gs.id
        WHERE gs.import_run_id = ?
        ORDER BY gs.id
        """,
        (run_id, run_id, run_id, run_id),
    ).fetchall()

    return [
        {
            "id": row["id"],
            "class_name": row["class_name"],
            "module": row["module"],
            "display_name": row["display_name"],
            "operation_count": row["operation_count"],
            "endpoint_count": row["endpoint_count"],
            "action_count": row["action_count"],
        }
        for row in rows
    ]


def _service_graph_links(conn: sqlite3.Connection, run_id: str, service_id: str) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT payload_json
        FROM generated_links
        WHERE import_run_id = ? AND service_id = ?
        ORDER BY endpoint_id, operation_id, ordinal
        """,
        (run_id, service_id),
    ).fetchall()
    return [_json_load(row["payload_json"]) for row in rows]


def _service_graph_endpoints(
    conn: sqlite3.Connection,
    run_id: str,
    endpoint_ids: list[str],
) -> list[dict[str, Any]]:
    if not endpoint_ids:
        return []

    placeholders = ",".join("?" for _ in endpoint_ids)
    rows = conn.execute(
        f"""
        SELECT payload_json
        FROM generated_endpoints
        WHERE import_run_id = ? AND id IN ({placeholders})
        ORDER BY module, path, id
        """,
        [run_id, *endpoint_ids],
    ).fetchall()
    return [_json_load(row["payload_json"]) for row in rows]


def _service_graph_actions(
    conn: sqlite3.Connection,
    run_id: str,
    operation_ids: list[str],
    endpoint_ids: list[str],
    action_kind: str,
    search: str,
) -> list[dict[str, Any]]:
    owner_ids = _unique_strings([*operation_ids, *endpoint_ids])
    if not owner_ids:
        return []

    placeholders = ",".join("?" for _ in owner_ids)
    where = [f"import_run_id = ? AND owner_id IN ({placeholders})"]
    params: list[Any] = [run_id, *owner_ids]

    if action_kind != "all":
        where.append("kind = ?")
        params.append(action_kind)

    search_value = search.strip()
    if search_value:
        like = f"%{search_value}%"
        where.append(
            """
            (
              id LIKE ? OR kind LIKE ? OR action LIKE ? OR access LIKE ? OR
              call_name LIKE ? OR resource LIKE ? OR entity LIKE ? OR
              owner_id LIKE ? OR owner_qualified_name LIKE ?
            )
            """
        )
        params.extend([like] * 9)

    rows = conn.execute(
        f"""
        SELECT payload_json
        FROM generated_actions
        WHERE {' AND '.join(where)}
        ORDER BY owner_id, kind, ordinal
        LIMIT 1000
        """,
        params,
    ).fetchall()
    return [_json_load(row["payload_json"]) for row in rows]


def _service_graph_operation_links(
    conn: sqlite3.Connection,
    run_id: str,
    service_id: str,
    operation_ids: list[str],
) -> list[dict[str, Any]]:
    if not operation_ids:
        return []

    placeholders = ",".join("?" for _ in operation_ids)
    rows = conn.execute(
        f"""
        SELECT payload_json
        FROM generated_operation_links
        WHERE import_run_id = ?
          AND (
            source_service_id = ?
            OR target_service_id = ?
            OR source_operation_id IN ({placeholders})
            OR target_operation_id IN ({placeholders})
          )
        ORDER BY source_operation_id, target_service_id, target_operation_id, ordinal
        LIMIT 1000
        """,
        [run_id, service_id, service_id, *operation_ids, *operation_ids],
    ).fetchall()
    return [_json_load(row["payload_json"]) for row in rows]


def _fetch_review_rows(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    return conn.execute(
        """
        SELECT *
        FROM review_items
        ORDER BY target_type, target_id
        """
    ).fetchall()


def _overlay_item_from_row(conn: sqlite3.Connection, row: sqlite3.Row) -> CatalogOverlayItem:
    label_rows = conn.execute(
        """
        SELECT label
        FROM review_labels
        WHERE target_type = ? AND target_id = ?
        ORDER BY label
        """,
        (row["target_type"], row["target_id"]),
    ).fetchall()
    marker_rows = conn.execute(
        """
        SELECT marker
        FROM review_status_markers
        WHERE target_type = ? AND target_id = ?
        ORDER BY marker
        """,
        (row["target_type"], row["target_id"]),
    ).fetchall()

    return CatalogOverlayItem(
        target=OverlayTarget(
            type=OverlayTargetType(row["target_type"]),
            id=row["target_id"],
            parent_id=row["parent_id"],
            source_file=row["source_file"],
            line_start=row["source_line"],
        ),
        review_status=row["review_status"],
        labels=[item["label"] for item in label_rows],
        status_markers=[item["marker"] for item in marker_rows],
        owner=row["owner"],
        notes=row["notes"],
        links=_json_load(row["links_json"]),
        overrides=_json_load(row["overrides_json"]),
        metadata=OverlayMetadata.model_validate(_json_load(row["metadata_json"])),
    )


def _upsert_review_item(conn: sqlite3.Connection, item: CatalogOverlayItem) -> None:
    metadata = item.metadata.model_dump(mode="json", exclude_none=True)
    updated_at = metadata.get("updated_at") or datetime.now(timezone.utc).replace(microsecond=0).isoformat()

    conn.execute(
        """
        INSERT INTO review_items (
            target_type, target_id, parent_id, source_file, source_line,
            review_status, owner, notes, links_json, overrides_json, metadata_json, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(target_type, target_id) DO UPDATE SET
            parent_id = excluded.parent_id,
            source_file = excluded.source_file,
            source_line = excluded.source_line,
            review_status = excluded.review_status,
            owner = excluded.owner,
            notes = excluded.notes,
            links_json = excluded.links_json,
            overrides_json = excluded.overrides_json,
            metadata_json = excluded.metadata_json,
            updated_at = excluded.updated_at
        """,
        (
            item.target.type.value,
            item.target.id,
            item.target.parent_id,
            item.target.source_file,
            item.target.line_start,
            item.review_status,
            item.owner,
            item.notes,
            _json_dump(item.links),
            _json_dump(item.overrides),
            _json_dump(metadata),
            updated_at,
        ),
    )
    conn.execute(
        "DELETE FROM review_labels WHERE target_type = ? AND target_id = ?",
        (item.target.type.value, item.target.id),
    )
    conn.execute(
        "DELETE FROM review_status_markers WHERE target_type = ? AND target_id = ?",
        (item.target.type.value, item.target.id),
    )

    for label in item.labels:
        conn.execute(
            "INSERT OR IGNORE INTO review_labels (target_type, target_id, label) VALUES (?, ?, ?)",
            (item.target.type.value, item.target.id, label),
        )

    for marker in item.status_markers:
        conn.execute(
            "INSERT OR IGNORE INTO review_status_markers (target_type, target_id, marker) VALUES (?, ?, ?)",
            (item.target.type.value, item.target.id, marker),
        )


def _active_run_id(conn: sqlite3.Connection) -> str | None:
    row = conn.execute("SELECT id FROM import_runs WHERE active = 1").fetchone()
    return None if row is None else str(row["id"])


def _read_generated_json_files() -> dict[str, Any]:
    static_dir = settings.generated_static_dir
    return {
        "services": _read_json(static_dir / "services.json").get("services", []),
        "endpoints": _read_json(static_dir / "endpoints.json").get("endpoints", []),
        "links": _read_json(static_dir / "endpoint_service_links.json").get("links", []),
        "actions": _read_json(static_dir / "architecture_actions.json").get("actions", []),
        "operation_links": _read_json(static_dir / "operation_links.json").get("links", []),
        "validation_report": _read_json(static_dir / "validation_report.json"),
    }


def _generated_source_hash() -> str | None:
    paths = [
        settings.generated_static_dir / "services.json",
        settings.generated_static_dir / "endpoints.json",
        settings.generated_static_dir / "endpoint_service_links.json",
        settings.generated_static_dir / "architecture_actions.json",
        settings.generated_static_dir / "operation_links.json",
        settings.generated_static_dir / "validation_report.json",
    ]

    if not all(path.exists() for path in paths):
        return None

    digest = hashlib.sha256()
    for path in paths:
        digest.update(path.name.encode("utf-8"))
        digest.update(path.read_bytes())

    return digest.hexdigest()


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}

    return json.loads(path.read_text(encoding="utf-8"))


def _overlay_index(overlay: ArchitectureOverlay) -> dict[tuple[str, str], CatalogOverlayItem]:
    return {
        (str(item.target.type), item.target.id): item
        for item in overlay.items
    }


def _apply_overlay(item: dict[str, Any], overlay: CatalogOverlayItem | None) -> dict[str, Any]:
    effective = deepcopy(item)
    effective["_generated"] = deepcopy(item)

    if overlay is None:
        effective["_overlay"] = None
        return effective

    for key, value in overlay.overrides.items():
        effective[key] = value

    if overlay.review_status is not None:
        effective["review_status"] = overlay.review_status

    effective["_overlay"] = overlay.model_dump(mode="json", exclude_none=True)
    return effective


def _apply_service_overlay(
    service: dict[str, Any],
    overlay_index: dict[tuple[str, str], CatalogOverlayItem],
) -> dict[str, Any]:
    effective_service = _apply_overlay(
        service,
        _overlay_for_item(overlay_index, "service", service),
    )
    effective_service["operations"] = [
        _apply_overlay(
            operation,
            _overlay_for_item(overlay_index, "operation", operation),
        )
        for operation in service.get("operations", [])
    ]
    return effective_service


def _overlay_for_item(
    overlay_index: dict[tuple[str, str], CatalogOverlayItem],
    target_type: str,
    item: dict[str, Any],
    fallback_id: str | None = None,
) -> CatalogOverlayItem | None:
    for target_id in _identity_target_ids(item, fallback_id=fallback_id):
        overlay = overlay_index.get((target_type, target_id))

        if overlay is not None:
            return overlay

    return None


def _identity_target_ids(item: dict[str, Any], fallback_id: str | None = None) -> list[str]:
    identity = item.get("identity") or {}
    aliases = identity.get("aliases") or []

    if not isinstance(aliases, list):
        aliases = []

    candidates = [
        str(item.get("id") or ""),
        str(identity.get("catalog_id") or ""),
        str(identity.get("logical_id") or ""),
        str(fallback_id or ""),
        *[str(alias) for alias in aliases if alias],
    ]

    return _unique_strings([candidate for candidate in candidates if candidate])


def _normalize_overlay_target_id(target_type: OverlayTargetType, target_id: str) -> str:
    table = {
        OverlayTargetType.SERVICE: "generated_services",
        OverlayTargetType.OPERATION: "generated_operations",
        OverlayTargetType.ENDPOINT: "generated_endpoints",
        OverlayTargetType.ENDPOINT_SERVICE_LINK: "generated_links",
        OverlayTargetType.ARCHITECTURE_ACTION: "generated_actions",
    }.get(target_type)

    if table is None:
        return target_id

    with _connect() as conn:
        run_id = _active_run_id(conn)

        if run_id is None:
            return target_id

        row = conn.execute(
            f"""
            SELECT catalog_id
            FROM {table}
            WHERE import_run_id = ?
              AND (
                id = ? OR
                catalog_id = ? OR
                logical_id = ? OR
                aliases_json LIKE '%"' || ? || '"%'
              )
            ORDER BY CASE WHEN catalog_id = ? THEN 0 ELSE 1 END, generated_pk
            LIMIT 1
            """,
            (run_id, target_id, target_id, target_id, target_id, target_id),
        ).fetchone()

    if row is None or not row["catalog_id"]:
        return target_id

    return str(row["catalog_id"])


def _apply_validation_overlays(
    validation_report: dict[str, Any] | None,
    overlay_index: dict[tuple[str, str], CatalogOverlayItem],
) -> dict[str, Any] | None:
    if validation_report is None:
        return None

    effective_report = deepcopy(validation_report)
    issues = effective_report.get("issues", [])

    for issue in issues:
        issue_id = _validation_issue_id(issue)
        issue["_overlay"] = None
        overlay = overlay_index.get(("validation_issue", issue_id))

        if overlay is None:
            continue

        for key, value in overlay.overrides.items():
            issue[key] = value

        if overlay.review_status is not None:
            issue["review_status"] = overlay.review_status

        issue["_overlay"] = overlay.model_dump(mode="json", exclude_none=True)

    return effective_report


def _link_id(link: dict[str, Any]) -> str:
    if link.get("id"):
        return str(link["id"])

    return "|".join(
        [
            str(link.get("endpoint_id", "")),
            str(link.get("operation_id", "")),
            str(link.get("source", {}).get("line_start", "")),
        ]
    )


def _identity_values(
    item: dict[str, Any],
    fallback_id: str | None = None,
    fallback_display: str | None = None,
) -> dict[str, Any]:
    item_id = str(fallback_id or item.get("id") or "")
    identity = item.get("identity") or {}
    aliases = identity.get("aliases") or []

    if not isinstance(aliases, list):
        aliases = []

    return {
        "catalog_id": identity.get("catalog_id") or item_id,
        "logical_id": identity.get("logical_id") or item_id,
        "source_id": identity.get("source_id") or "",
        "display_name": identity.get("display_name") or fallback_display or item_id,
        "aliases": _unique_strings([str(alias) for alias in aliases if alias]),
    }


def _unique_strings(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []

    for value in values:
        if value in seen:
            continue

        seen.add(value)
        result.append(value)

    return result


def _validation_issue_id(issue: dict[str, Any]) -> str:
    return "|".join(
        [
            str(issue.get("code", "")),
            str(issue.get("item_id", "")),
            str(issue.get("source_file", "")),
            str(issue.get("line_start", "")),
        ]
    )


def _generated_pk(*parts: object) -> str:
    digest = hashlib.sha256()
    for part in parts:
        digest.update(str(part).encode("utf-8"))
        digest.update(b"\0")
    return digest.hexdigest()


def _json_dump(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def _json_load(value: str | None) -> Any:
    if value is None or value == "":
        return {}

    return json.loads(value)


def _page(rows: list[dict[str, Any]], limit: int, offset: int) -> TablePage:
    safe_limit = max(1, min(limit, 500))
    safe_offset = max(0, offset)
    return TablePage(
        rows=rows[safe_offset : safe_offset + safe_limit],
        total=len(rows),
        limit=safe_limit,
        offset=safe_offset,
    )


def _attach_story_link_summary(
    conn: sqlite3.Connection,
    run_id: str,
    story: dict[str, Any],
) -> None:
    declared = story.get("endpoints") or []
    linked = sum(
        1
        for endpoint_ref in declared
        if _find_endpoint_for_story_ref(conn, run_id, endpoint_ref) is not None
    )

    if not declared:
        status = "unmapped"
    elif linked == len(declared):
        status = "linked"
    elif linked > 0:
        status = "partial"
    else:
        status = "missing"

    story["_linked_endpoint_count"] = linked
    story["_linkage"] = status
    story["_link_summary"] = {
        "declared_endpoints": len(declared),
        "linked_endpoints": linked,
        "status": status,
    }


def _user_story_where(
    search: str,
    area: str,
    status: str,
    linkage: str,
) -> tuple[str, list[Any]]:
    clauses: list[str] = []
    params: list[Any] = []

    if search.strip():
        token = f"%{search.strip().lower()}%"
        clauses.append(
            """
            (
                lower(us.id) LIKE ? OR lower(us.title) LIKE ? OR
                lower(us.area) LIKE ? OR lower(us.body_markdown) LIKE ?
            )
            """
        )
        params.extend([token, token, token, token])

    if area != "all":
        clauses.append("us.area = ?")
        params.append(area)

    if status != "all":
        clauses.append("us.status = ?")
        params.append(status)

    _ = linkage

    if not clauses:
        return "", params

    return "WHERE " + " AND ".join(clauses), params


def _user_story_order_by(sort: str, direction: str) -> str:
    allowed = {
        "id": "us.id",
        "title": "us.title",
        "area": "us.area",
        "status": "us.status",
        "owner": "us.owner",
    }
    column = allowed.get(sort, "us.id")
    sql_direction = "DESC" if direction.lower() == "desc" else "ASC"
    return f"ORDER BY {column} {sql_direction}"


def _endpoint_path_candidates(path: str) -> list[str]:
    stripped = path.strip()
    normalized = stripped if stripped.startswith("/") else f"/{stripped}"
    normalized = normalized.replace("//", "/")
    candidates = [normalized]

    if normalized.startswith("/api/"):
        candidates.append(normalized[4:])
    else:
        candidates.append(f"/api{normalized}")

    return _unique_strings(candidates)


def _heading_title(body: str) -> str | None:
    for line in body.splitlines():
        stripped = line.strip()
        if stripped.startswith("# "):
            return stripped[2:].strip()

    return None


def _normalized_string_list(value: Any) -> list[str]:
    if value is None:
        return []

    if isinstance(value, str):
        return [value]

    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]

    return []


def _endpoint_where(
    run_id: str,
    search: str,
    method: str,
    contract: str,
    linkage: str,
    review_status: str,
) -> tuple[str, list[Any]]:
    clauses = ["ge.import_run_id = ?"]
    params: list[Any] = [run_id]
    q = f"%{search.strip().lower()}%"

    if search.strip():
        clauses.append(
            """
            (
                lower(ge.id) LIKE ? OR lower(ge.http_method) LIKE ? OR
                lower(ge.path) LIKE ? OR lower(ge.include_prefix) LIKE ? OR lower(ge.full_path) LIKE ? OR
                lower(ge.router_prefix) LIKE ? OR lower(ge.module) LIKE ? OR
                lower(ge.function_name) LIKE ? OR lower(ge.catalog_id) LIKE ? OR
                lower(ge.logical_id) LIKE ? OR lower(ge.source_id) LIKE ? OR
                lower(ge.display_name) LIKE ? OR lower(ge.aliases_json) LIKE ? OR
                lower(ge.payload_json) LIKE ?
            )
            """
        )
        params.extend([q, q, q, q, q, q, q, q, q, q, q, q, q, q])
    if method != "all":
        clauses.append("ge.http_method = ?")
        params.append(method)
    if contract == "has_response_model":
        clauses.append("ge.payload_json LIKE '%response_model%'")
    elif contract == "missing_response_model":
        clauses.append("ge.payload_json NOT LIKE '%response_model%'")
    elif contract == "has_parameters":
        clauses.append("ge.payload_json NOT LIKE '%\"parameters\": []%'")
    elif contract == "no_parameters":
        clauses.append("ge.payload_json LIKE '%\"parameters\": []%'")
    if linkage == "linked":
        clauses.append("EXISTS (SELECT 1 FROM generated_links gl WHERE gl.import_run_id = ge.import_run_id AND gl.endpoint_id = ge.id)")
    elif linkage == "open":
        clauses.append("NOT EXISTS (SELECT 1 FROM generated_links gl WHERE gl.import_run_id = ge.import_run_id AND gl.endpoint_id = ge.id)")
    if review_status != "all":
        clauses.append(
            """
            EXISTS (
                SELECT 1 FROM review_items ri
                WHERE ri.target_type = 'endpoint'
                  AND ri.review_status = ?
                  AND (
                    ri.target_id = ge.id OR
                    ri.target_id = ge.catalog_id OR
                    ri.target_id = ge.logical_id OR
                    ge.aliases_json LIKE '%"' || ri.target_id || '"%'
                  )
            )
            """
        )
        params.append(review_status)

    return "WHERE " + " AND ".join(clauses), params


def _operation_where(
    run_id: str,
    search: str,
    coverage: str,
    relation: str,
    review_status: str,
) -> tuple[str, list[Any]]:
    clauses = ["go.import_run_id = ?"]
    params: list[Any] = [run_id]
    q = f"%{search.strip().lower()}%"

    if search.strip():
        clauses.append(
            """
            (
                lower(go.id) LIKE ? OR lower(go.service_id) LIKE ? OR
                lower(go.method) LIKE ? OR lower(go.qualified_name) LIKE ? OR
                lower(gs.class_name) LIKE ? OR lower(go.catalog_id) LIKE ? OR
                lower(go.logical_id) LIKE ? OR lower(go.source_id) LIKE ? OR
                lower(go.display_name) LIKE ? OR lower(go.aliases_json) LIKE ? OR
                lower(gs.catalog_id) LIKE ? OR lower(gs.logical_id) LIKE ? OR
                lower(gs.display_name) LIKE ? OR lower(go.payload_json) LIKE ?
            )
            """
        )
        params.extend([q, q, q, q, q, q, q, q, q, q, q, q, q, q])
    if coverage == "linked":
        clauses.append("EXISTS (SELECT 1 FROM generated_links gl WHERE gl.import_run_id = go.import_run_id AND gl.operation_id = go.id)")
    elif coverage == "open":
        clauses.append("NOT EXISTS (SELECT 1 FROM generated_links gl WHERE gl.import_run_id = go.import_run_id AND gl.operation_id = go.id)")
    if relation == "none":
        clauses.append("NOT EXISTS (SELECT 1 FROM generated_operation_links gol WHERE gol.import_run_id = go.import_run_id AND (gol.source_operation_id = go.id OR gol.target_operation_id = go.id))")
    elif relation != "all":
        clauses.append("EXISTS (SELECT 1 FROM generated_operation_links gol WHERE gol.import_run_id = go.import_run_id AND (gol.source_operation_id = go.id OR gol.target_operation_id = go.id) AND gol.link_type = ?)")
        params.append(relation)
    if review_status != "all":
        clauses.append(
            """
            EXISTS (
                SELECT 1 FROM review_items ri
                WHERE ri.target_type = 'operation'
                  AND ri.review_status = ?
                  AND (
                    ri.target_id = go.id OR
                    ri.target_id = go.catalog_id OR
                    ri.target_id = go.logical_id OR
                    go.aliases_json LIKE '%"' || ri.target_id || '"%'
                  )
            )
            """
        )
        params.append(review_status)

    return "WHERE " + " AND ".join(clauses), params


def _interface_where(
    run_id: str,
    search: str,
    confidence: str,
    review_status: str,
) -> tuple[str, list[Any]]:
    clauses = ["gl.import_run_id = ?"]
    params: list[Any] = [run_id]
    q = f"%{search.strip().lower()}%"

    if search.strip():
        clauses.append(
            """
            (
                lower(gl.endpoint_id) LIKE ? OR lower(gl.service_id) LIKE ? OR
                lower(gl.operation_id) LIKE ? OR lower(gl.payload_json) LIKE ? OR
                lower(ge.path) LIKE ? OR lower(ge.function_name) LIKE ? OR
                lower(gl.catalog_id) LIKE ? OR lower(gl.logical_id) LIKE ? OR
                lower(gl.source_id) LIKE ? OR lower(gl.display_name) LIKE ? OR
                lower(gl.aliases_json) LIKE ? OR lower(ge.catalog_id) LIKE ? OR
                lower(ge.logical_id) LIKE ? OR lower(ge.display_name) LIKE ?
            )
            """
        )
        params.extend([q, q, q, q, q, q, q, q, q, q, q, q, q, q])
    if confidence != "all":
        clauses.append("lower(gl.payload_json) LIKE ?")
        params.append(f"%\"confidence\": \"{confidence}\"%")
    if review_status != "all":
        clauses.append(
            """
            EXISTS (
                SELECT 1 FROM review_items ri
                WHERE ri.target_type = 'endpoint_service_link'
                  AND ri.review_status = ?
                  AND (
                    ri.target_id = gl.id OR
                    ri.target_id = gl.catalog_id OR
                    ri.target_id = gl.logical_id OR
                    gl.aliases_json LIKE '%"' || ri.target_id || '"%'
                  )
            )
            """
        )
        params.append(review_status)

    return "WHERE " + " AND ".join(clauses), params


def _validation_issue_where(
    run_id: str,
    search: str,
    severity: str,
    code: str,
    review_status: str,
) -> tuple[str, list[Any]]:
    clauses = ["gvi.import_run_id = ?"]
    params: list[Any] = [run_id]
    q = f"%{search.strip().lower()}%"

    if search.strip():
        clauses.append(
            """
            (
                lower(gvi.id) LIKE ? OR lower(gvi.code) LIKE ? OR
                lower(gvi.severity) LIKE ? OR lower(gvi.item_id) LIKE ? OR
                lower(gvi.source_file) LIKE ? OR lower(gvi.payload_json) LIKE ?
            )
            """
        )
        params.extend([q, q, q, q, q, q])
    if severity != "all":
        clauses.append("gvi.severity = ?")
        params.append(severity)
    if code == "resolved_collisions":
        clauses.append("gvi.code LIKE 'resolved_%_logical_id_collision'")
    elif code == "identity":
        clauses.append("(gvi.code LIKE '%identity%' OR gvi.code = 'service_class_name_reused')")
    elif code == "endpoint_mapping_open":
        clauses.append("gvi.code IN ('endpoint_without_service_link', 'endpoint_service_candidate_not_linked')")
    elif code == "operation_mapping_open":
        clauses.append("gvi.code = 'operation_without_endpoint_link'")
    elif code == "service_linkage_open":
        clauses.append(
            "gvi.code IN ('endpoint_without_service_link', 'endpoint_service_candidate_not_linked', 'operation_without_endpoint_link')"
        )
    elif code != "all":
        clauses.append("gvi.code = ?")
        params.append(code)
    if review_status != "all":
        clauses.append(
            """
            EXISTS (
                SELECT 1 FROM review_items ri
                WHERE ri.target_type = 'validation_issue'
                  AND ri.review_status = ?
                  AND ri.target_id = gvi.id
            )
            """
        )
        params.append(review_status)

    return "WHERE " + " AND ".join(clauses), params


def _endpoint_order_by(sort: str, direction: str) -> str:
    columns = {
        "method": "ge.http_method",
        "endpoint": "ge.path",
        "implementation": "ge.function_name",
        "contract": "ge.payload_json",
        "linkage": "linked",
        "source": "ge.source_file",
        "review": "ge.id",
    }
    return _order_by(columns.get(sort, "ge.path"), direction)


def _operation_order_by(sort: str, direction: str) -> str:
    columns = {
        "service": "go.service_id",
        "operation": "go.method",
        "coverage": "linked",
        "source": "go.source_file",
        "review": "go.id",
    }
    return _order_by(columns.get(sort, "go.service_id"), direction)


def _interface_order_by(sort: str, direction: str) -> str:
    columns = {
        "endpoint": "ge.path",
        "service": "gl.service_id",
        "confidence": "gl.payload_json",
        "source": "gl.source_file",
        "review": "gl.id",
    }
    return _order_by(columns.get(sort, "ge.path"), direction)


def _validation_issue_order_by(sort: str, direction: str) -> str:
    columns = {
        "severity": "CASE gvi.severity WHEN 'error' THEN 0 WHEN 'warning' THEN 1 ELSE 2 END",
        "code": "gvi.code",
        "item": "gvi.item_id",
        "source": "gvi.source_file",
        "review": "gvi.id",
    }
    return _order_by(columns.get(sort, columns["severity"]), direction)


def _order_by(column: str, direction: str) -> str:
    sql_direction = "DESC" if direction == "desc" else "ASC"
    return f"ORDER BY {column} {sql_direction}"


def _search_matches(row: Any, search: str, fields: list[str]) -> bool:
    q = search.strip().lower()
    if not q:
        return True

    values: list[str] = []

    if isinstance(row, dict):
        for field in fields:
            values.append(str(row.get(field, "")))
        values.append(json.dumps(row, ensure_ascii=False, sort_keys=True))

    return q in " ".join(values).lower()


def _sort_dict_rows(
    rows: list[dict[str, Any]],
    sort: str,
    direction: str,
    value_getter,
    context: Any = None,
) -> list[dict[str, Any]]:
    reverse = direction == "desc"
    return sorted(
        rows,
        key=lambda row: str(value_getter(row, sort, context) or "").lower(),
        reverse=reverse,
    )


def _endpoint_sort_value(row: dict[str, Any], sort: str, linked_endpoint_ids: set[str]) -> Any:
    allowed = {
        "method": row.get("http_method"),
        "endpoint": row.get("path") or row.get("id"),
        "implementation": row.get("function_name"),
        "contract": row.get("kwargs", {}).get("response_model") or "",
        "linkage": "linked" if row.get("id") in linked_endpoint_ids else "open",
        "source": row.get("source", {}).get("file"),
        "review": row.get("review_status"),
    }
    return allowed.get(sort, allowed["endpoint"])


def _operation_sort_value(row: dict[str, Any], sort: str, linked_operation_ids: set[str]) -> Any:
    service = row["service"]
    operation = row["operation"]
    allowed = {
        "service": service.get("id"),
        "operation": operation.get("method"),
        "coverage": "linked" if operation.get("id") in linked_operation_ids else "open",
        "source": operation.get("source", {}).get("file"),
        "review": operation.get("review_status"),
    }
    return allowed.get(sort, allowed["service"])


def _interface_sort_value(row: dict[str, Any], sort: str, context: Any = None) -> Any:
    link = row["link"]
    endpoint = row.get("endpoint") or {}
    allowed = {
        "endpoint": endpoint.get("path") or link.get("endpoint_id"),
        "service": link.get("service_id"),
        "confidence": link.get("detection", {}).get("confidence"),
        "source": link.get("source", {}).get("file"),
        "review": link.get("review_status"),
    }
    return allowed.get(sort, allowed["endpoint"])
