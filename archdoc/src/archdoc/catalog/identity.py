from __future__ import annotations

import hashlib

from archdoc.catalog.models import CatalogIdentity, SourceRef


def build_catalog_identity(
    *,
    kind: str,
    logical_id: str,
    display_name: str,
    source: SourceRef,
    qualified_name: str | None = None,
    extra_parts: list[str] | None = None,
    aliases: list[str] | None = None,
) -> CatalogIdentity:
    source_id = build_source_id(
        kind=kind,
        source=source,
        qualified_name=qualified_name,
        extra_parts=extra_parts or [],
    )

    return CatalogIdentity(
        catalog_id=logical_id,
        logical_id=logical_id,
        source_id=source_id,
        display_name=display_name,
        aliases=_unique_aliases([logical_id, *(aliases or [])]),
    )


def build_source_id(
    *,
    kind: str,
    source: SourceRef,
    qualified_name: str | None = None,
    extra_parts: list[str] | None = None,
) -> str:
    parts = [
        kind,
        source.file,
        str(source.line_start),
        str(source.line_end or ""),
        qualified_name or "",
        *(extra_parts or []),
    ]
    digest = hashlib.sha256()

    for part in parts:
        digest.update(part.encode("utf-8"))
        digest.update(b"\0")

    return f"{kind}:{digest.hexdigest()[:16]}"


def _unique_aliases(values: list[str]) -> list[str]:
    seen: set[str] = set()
    aliases: list[str] = []

    for value in values:
        if not value or value in seen:
            continue

        seen.add(value)
        aliases.append(value)

    return aliases
