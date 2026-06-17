# src/archdoc/facts/models.py

from __future__ import annotations
from enum import Enum
from pydantic import BaseModel, Field
from typing import TypeAlias

class SourceLocation(BaseModel):
    file: str
    line_start: int
    line_end: int | None = None


class ImportNameFact(BaseModel):
    name: str
    alias: str | None = None


class ImportFact(BaseModel):
    type: str  # "import" | "from_import"
    module: str | None = None
    names: list[ImportNameFact]
    source: SourceLocation


class DecoratorFact(BaseModel):
    name: str
    args: list[str] = Field(default_factory=list)
    kwargs: dict[str, str] = Field(default_factory=dict)
    source: SourceLocation


class ParameterFact(BaseModel):
    name: str
    annotation: str | None = None
    default: str | None = None
    kind: str = "positional_or_keyword"


class CallFact(BaseModel):
    name: str
    args: list[str] = Field(default_factory=list)
    kwargs: dict[str, str] = Field(default_factory=dict)
    awaited: bool = False

    # new fields
    nested_in_call: bool = False
    call_role: str = "unknown"
    root_name: str | None = None

    source: SourceLocation

class SignalFact(BaseModel):
    kind: str
    data: dict = Field(default_factory=dict)
    source: SourceLocation | None = None


class FunctionFact(BaseModel):
    name: str
    qualified_name: str
    kind: str
    is_async: bool
    visibility: str
    docstring: str | None = None
    parameters: list[ParameterFact] = Field(default_factory=list)
    returns: str | None = None
    decorators: list[DecoratorFact] = Field(default_factory=list)
    calls: list[CallFact] = Field(default_factory=list)
    assignments: list[AssignmentFact] = Field(default_factory=list)
    signals: list[SignalFact] = Field(default_factory=list)
    source: SourceLocation

class AssignmentFact(BaseModel):
    target: str
    value: str | None = None
    value_call: str | None = None
    source: SourceLocation


class ClassFieldFact(BaseModel):
    name: str
    annotation: str | None = None
    value: str | None = None
    value_call: str | None = None
    source: SourceLocation


class ClassFact(BaseModel):
    name: str
    qualified_name: str
    bases: list[str] = Field(default_factory=list)
    decorators: list[DecoratorFact] = Field(default_factory=list)
    docstring: str | None = None
    fields: list[ClassFieldFact] = Field(default_factory=list)
    methods: list[FunctionFact] = Field(default_factory=list)
    signals: list[SignalFact] = Field(default_factory=list)
    source: SourceLocation


ClassIndex = dict[str, ClassFact]

class FileFact(BaseModel):
    path: str
    module: str
    imports: list[ImportFact] = Field(default_factory=list)
    assignments: list[AssignmentFact] = Field(default_factory=list)
    classes: list[ClassFact] = Field(default_factory=list)
    functions: list[FunctionFact] = Field(default_factory=list)
    signals: list[SignalFact] = Field(default_factory=list)
    source: SourceLocation | None = None
    error: str | None = None


class RawCodeFacts(BaseModel):
    schema_version: str = "raw-code-facts/v0.1"
    project_name: str
    source_root: str
    files: list[FileFact]

