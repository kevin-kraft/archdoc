# src/archdoc/semantic/class_index.py

from __future__ import annotations

from archdoc.facts.models import ClassFact, RawCodeFacts, FunctionFact

from archdoc.facts.models import ClassIndex 


def short_name(name: str | None) -> str:
    if not name:
        return ""
    return name.split(".")[-1]

# from archdoc.facts.models import ClassFact, FunctionFact


def collect_inherited_methods_for_service(
    class_name: str,
    class_index: ClassIndex,
    seen: set[str] | None = None,
) -> list[tuple[ClassFact, FunctionFact]]:
    if seen is None:
        seen = set()

    cls = lookup_class(class_name, class_index)

    if cls is None:
        return []

    if cls.name in seen:
        return []

    seen.add(cls.name)

    result: list[tuple[ClassFact, FunctionFact]] = []

    for method in cls.methods:
        result.append((cls, method))

    for base in cls.bases:
        result.extend(
            collect_inherited_methods_for_service(
                class_name=base,
                class_index=class_index,
                seen=seen,
            )
        )

    return result

def build_class_index(facts: RawCodeFacts) -> ClassIndex:
    index: ClassIndex = {}

    for file in facts.files:
        if file.error:
            continue

        for cls in file.classes:
            # Short name: FinancialService
            index[cls.name] = cls

            # Qualified name: app.services.finance.FinancialService
            index[cls.qualified_name] = cls

    return index


def lookup_class(class_name: str, class_index: ClassIndex) -> ClassFact | None:
    return (
        class_index.get(class_name)
        or class_index.get(short_name(class_name))
    )


def class_has_method(cls: ClassFact, method_name: str) -> bool:
    return any(method.name == method_name for method in cls.methods)
from archdoc.facts.models import ClassFact


def resolve_method_owner_path(
    class_name: str,
    method_name: str,
    class_index: ClassIndex,
    seen: set[str] | None = None,
) -> list[ClassFact] | None:
    if seen is None:
        seen = set()

    lookup_name = short_name(class_name)

    if lookup_name in seen:
        return None

    seen.add(lookup_name)

    cls = lookup_class(lookup_name, class_index)

    if cls is None:
        return None

    if class_has_method(cls, method_name):
        return [cls]

    for base in cls.bases:
        base_path = resolve_method_owner_path(
            class_name=base,
            method_name=method_name,
            class_index=class_index,
            seen=seen.copy(),
        )

        if base_path is not None:
            return [cls] + base_path

    return None

def resolve_method_owner(
    class_name: str,
    method_name: str,
    class_index: ClassIndex,
    seen: set[str] | None = None,
) -> ClassFact | None:
    if seen is None:
        seen = set()

    lookup_name = short_name(class_name)

    if lookup_name in seen:
        return None

    seen.add(lookup_name)

    cls = lookup_class(lookup_name, class_index)

    if cls is None:
        return None

    if class_has_method(cls, method_name):
        return cls

    for base in cls.bases:
        owner = resolve_method_owner(
            class_name=base,
            method_name=method_name,
            class_index=class_index,
            seen=seen,
        )

        if owner is not None:
            return owner

    return None