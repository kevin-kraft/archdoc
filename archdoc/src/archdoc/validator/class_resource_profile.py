from __future__ import annotations

from dataclasses import dataclass, field

from archdoc.facts.models import AssignmentFact, ClassFact, FunctionFact, RawCodeFacts
from archdoc.utils.class_index import ClassIndex, build_class_index, lookup_class


@dataclass(frozen=True)
class ResourceOrigin:
    attribute: str
    kind: str
    source_class: str
    source_method: str | None = None
    source_file: str | None = None
    line_start: int | None = None
    evidence: list[str] = field(default_factory=list)

    def as_details(self) -> dict[str, object]:
        return {
            "attribute": self.attribute,
            "kind": self.kind,
            "source_class": self.source_class,
            "source_method": self.source_method,
            "source_file": self.source_file,
            "line_start": self.line_start,
            "evidence": self.evidence,
        }


@dataclass
class ClassResourceProfile:
    class_name: str
    qualified_name: str
    origins_by_attribute: dict[str, list[ResourceOrigin]] = field(default_factory=dict)

    def add_origin(self, origin: ResourceOrigin) -> None:
        origins = self.origins_by_attribute.setdefault(origin.attribute, [])
        if origin not in origins:
            origins.append(origin)

    def origins_for(self, attribute: str) -> list[ResourceOrigin]:
        return self.origins_by_attribute.get(attribute, [])

    def has_resource(self, attribute: str) -> bool:
        return bool(self.origins_for(attribute))


SESSION_PARAMETER_NAMES = {"db", "session", "async_session"}
SESSION_ANNOTATION_NAMES = {"Session", "AsyncSession"}


def build_class_resource_profiles(facts: RawCodeFacts) -> dict[str, ClassResourceProfile]:
    class_index = build_class_index(facts)
    profiles: dict[str, ClassResourceProfile] = {}

    for file in facts.files:
        if file.error:
            continue

        for class_fact in file.classes:
            _build_profile_for_class(
                class_fact=class_fact,
                class_index=class_index,
                profiles=profiles,
                seen=set(),
            )

    return profiles


def _build_profile_for_class(
    class_fact: ClassFact,
    class_index: ClassIndex,
    profiles: dict[str, ClassResourceProfile],
    seen: set[str],
) -> ClassResourceProfile:
    cached = profiles.get(class_fact.qualified_name)
    if cached is not None:
        return cached

    if class_fact.qualified_name in seen:
        return ClassResourceProfile(
            class_name=class_fact.name,
            qualified_name=class_fact.qualified_name,
        )

    next_seen = {*seen, class_fact.qualified_name}
    profile = ClassResourceProfile(
        class_name=class_fact.name,
        qualified_name=class_fact.qualified_name,
    )
    profiles[class_fact.qualified_name] = profile

    _add_local_resource_origins(profile, class_fact)
    _add_inherited_resource_origins(profile, class_fact, class_index, profiles, next_seen)
    _add_forwarded_super_resource_origins(profile, class_fact)

    return profile


def _add_local_resource_origins(profile: ClassResourceProfile, class_fact: ClassFact) -> None:
    for method in class_fact.methods:
        if method.name == "__init__":
            constructor_parameters = {
                parameter.name
                for parameter in method.parameters
                if parameter.name != "self"
            }
        else:
            constructor_parameters = set()

        for assignment in method.assignments:
            if not assignment.target.startswith("self."):
                continue

            profile.add_origin(
                ResourceOrigin(
                    attribute=assignment.target,
                    kind=(
                        "constructor_parameter_assignment"
                        if method.name == "__init__" and assignment.value in constructor_parameters
                        else "instance_assignment"
                    ),
                    source_class=class_fact.qualified_name,
                    source_method=method.name,
                    source_file=assignment.source.file,
                    line_start=assignment.source.line_start,
                    evidence=[
                        f"assignment={assignment.target}",
                        f"value={assignment.value}",
                    ],
                )
            )

        if _is_property_method(method):
            profile.add_origin(
                ResourceOrigin(
                    attribute=f"self.{method.name}",
                    kind="property_method",
                    source_class=class_fact.qualified_name,
                    source_method=method.name,
                    source_file=method.source.file,
                    line_start=method.source.line_start,
                    evidence=[f"property={method.name}"],
                )
            )


def _add_inherited_resource_origins(
    profile: ClassResourceProfile,
    class_fact: ClassFact,
    class_index: ClassIndex,
    profiles: dict[str, ClassResourceProfile],
    seen: set[str],
) -> None:
    for base_name in class_fact.bases:
        base_class = lookup_class(base_name, class_index)
        if base_class is None:
            continue

        base_profile = _build_profile_for_class(
            class_fact=base_class,
            class_index=class_index,
            profiles=profiles,
            seen=seen,
        )

        for attribute, origins in base_profile.origins_by_attribute.items():
            for origin in origins:
                profile.add_origin(
                    ResourceOrigin(
                        attribute=attribute,
                        kind="inherited_resource",
                        source_class=origin.source_class,
                        source_method=origin.source_method,
                        source_file=origin.source_file,
                        line_start=origin.line_start,
                        evidence=[
                            f"base={base_class.qualified_name}",
                            *origin.evidence,
                        ],
                    )
                )


def _add_forwarded_super_resource_origins(profile: ClassResourceProfile, class_fact: ClassFact) -> None:
    init_method = next((method for method in class_fact.methods if method.name == "__init__"), None)
    if init_method is None:
        return

    constructor_parameters = {
        parameter.name: parameter.annotation
        for parameter in init_method.parameters
        if parameter.name != "self"
    }

    for call in init_method.calls:
        if not _is_super_init_call(call.name):
            continue

        for arg in call.args:
            if arg not in constructor_parameters:
                continue

            if not _looks_like_resource_parameter(arg, constructor_parameters[arg]):
                continue

            attribute = f"self.{arg}"
            profile.add_origin(
                ResourceOrigin(
                    attribute=attribute,
                    kind="forwarded_to_super_init",
                    source_class=class_fact.qualified_name,
                    source_method=init_method.name,
                    source_file=call.source.file,
                    line_start=call.source.line_start,
                    evidence=[
                        f"call={call.name}",
                        f"parameter={arg}",
                        f"annotation={constructor_parameters[arg]}",
                    ],
                )
            )


def _is_property_method(method: FunctionFact) -> bool:
    return any(decorator.name == "property" for decorator in method.decorators)


def _is_super_init_call(call_name: str) -> bool:
    return call_name == "super.__init__" or call_name.endswith(".__init__")


def _looks_like_resource_parameter(name: str, annotation: str | None) -> bool:
    if name in SESSION_PARAMETER_NAMES:
        return True

    if annotation is None:
        return False

    annotation_name = annotation.replace("'", "").replace('"', "")
    if "." in annotation_name:
        annotation_name = annotation_name.rsplit(".", 1)[-1]

    return annotation_name in SESSION_ANNOTATION_NAMES
