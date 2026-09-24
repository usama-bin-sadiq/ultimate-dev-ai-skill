"""Typed, dependency-free capability, agent, and workflow catalog primitives.

The catalog is deliberately a small compatibility/runtime surface.  It owns
metadata and referential integrity only; it does not discover tools, import a
provider, read YAML, or execute host actions.  Workflow execution is provided
by :mod:`runtime.core.workflow`, which consumes this module's validated
objects.

All values accepted by the JSON boundary are ordinary JSON values.  The
validators reject unknown fields, duplicate IDs, unresolved references,
cycles, non-finite numbers, and excessively large/deep values.  Descriptors
serialize in a canonical order so the same logical catalog has the same JSON
representation regardless of registration order.
"""
from __future__ import annotations

import hashlib
import json
import math
import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, ClassVar, TypeVar


SCHEMA_VERSION = "1.0"
MAX_CATALOG_ITEMS = 1024
MAX_WORKFLOW_STEPS = 256
MAX_DEPENDENCIES = 128
MAX_GRAPH_DEPTH = 256
MAX_JSON_DEPTH = 32
MAX_JSON_NODES = 10_000
MAX_JSON_BYTES = 1_048_576
MAX_CATALOG_BYTES = 4 * MAX_JSON_BYTES
MAX_WORKFLOW_BYTES = 2 * MAX_JSON_BYTES
MAX_STEP_BYTES = 2 * MAX_JSON_BYTES

_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")


class CatalogError(ValueError):
    """Base error for an invalid catalog or descriptor."""


class DescriptorError(CatalogError):
    """A descriptor is malformed or violates the bounded JSON contract."""


class ReferenceError(CatalogError):
    """A descriptor contains a reference that cannot be resolved."""


class WorkflowValidationError(CatalogError):
    """A workflow graph is invalid or cyclic."""


# Friendly aliases for callers that use more specific terminology.
RegistryError = CatalogError
DescriptorValidationError = DescriptorError
InvalidReferenceError = ReferenceError


T = TypeVar("T")


def _require_mapping(value: Any, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise DescriptorError(f"{label} must be an object")
    for key in value:
        if not isinstance(key, str):
            raise DescriptorError(f"{label} keys must be strings")
    return value


def _require_list(value: Any, label: str) -> list[Any]:
    if not isinstance(value, list):
        raise DescriptorError(f"{label} must be an array")
    return value


def _require_identifier(value: Any, label: str) -> str:
    if not isinstance(value, str) or _IDENTIFIER_RE.fullmatch(value) is None:
        raise DescriptorError(f"{label} must match {_IDENTIFIER_RE.pattern}")
    return value


def _require_text(value: Any, label: str, *, allow_empty: bool = False) -> str:
    if not isinstance(value, str):
        raise DescriptorError(f"{label} must be a string")
    if not allow_empty and not value.strip():
        raise DescriptorError(f"{label} must not be empty")
    if len(value) > 16_384:
        raise DescriptorError(f"{label} is too long")
    return value


def _normalise_json(
    value: Any,
    label: str,
    *,
    depth: int = 0,
    nodes: list[int] | None = None,
    ancestors: set[int] | None = None,
) -> Any:
    """Copy a bounded JSON value and reject non-JSON/cyclic input."""
    if depth > MAX_JSON_DEPTH:
        raise DescriptorError(f"{label} exceeds maximum nesting depth")
    if nodes is None:
        nodes = [0]
    if ancestors is None:
        ancestors = set()
    nodes[0] += 1
    if nodes[0] > MAX_JSON_NODES:
        raise DescriptorError(f"{label} exceeds maximum value count")

    if value is None or type(value) is bool or type(value) is int:
        return value
    if type(value) is float:
        if not math.isfinite(value):
            raise DescriptorError(f"{label} contains a non-finite number")
        return value
    if isinstance(value, str):
        if len(value) > 16_384:
            raise DescriptorError(f"{label} contains an oversized string")
        return value
    if isinstance(value, Mapping):
        marker = id(value)
        if marker in ancestors:
            raise DescriptorError(f"{label} contains a cycle")
        ancestors.add(marker)
        try:
            result: dict[str, Any] = {}
            for key, child in value.items():
                if not isinstance(key, str):
                    raise DescriptorError(f"{label} keys must be strings")
                if len(key) > 512:
                    raise DescriptorError(f"{label} contains an oversized key")
                result[key] = _normalise_json(
                    child,
                    f"{label}.{key}",
                    depth=depth + 1,
                    nodes=nodes,
                    ancestors=ancestors,
                )
            return result
        finally:
            ancestors.remove(marker)
    if isinstance(value, (list, tuple)):
        marker = id(value)
        if marker in ancestors:
            raise DescriptorError(f"{label} contains a cycle")
        ancestors.add(marker)
        try:
            return [
                _normalise_json(
                    child,
                    f"{label}[{index}]",
                    depth=depth + 1,
                    nodes=nodes,
                    ancestors=ancestors,
                )
                for index, child in enumerate(value)
            ]
        finally:
            ancestors.remove(marker)
    raise DescriptorError(f"{label} contains a non-JSON value of type {type(value).__name__}")


def _canonical_json(value: Any) -> str:
    try:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
    except (TypeError, ValueError, OverflowError) as exc:
        raise DescriptorError(f"value is not canonical JSON: {exc}") from exc


def _check_json_size(value: Any, label: str, limit: int = MAX_JSON_BYTES) -> None:
    try:
        size = len(_canonical_json(value).encode("utf-8"))
    except DescriptorError:
        raise
    except (TypeError, ValueError, OverflowError) as exc:
        raise DescriptorError(f"{label} is not JSON serializable: {exc}") from exc
    if size > limit:
        raise DescriptorError(f"{label} exceeds maximum JSON size of {limit} bytes")


def _json_copy(value: Any) -> Any:
    """Return a detached, recursively key-sorted JSON value."""
    if isinstance(value, Mapping):
        return {key: _json_copy(value[key]) for key in sorted(value)}
    if isinstance(value, list):
        return [_json_copy(child) for child in value]
    return value


def _parse_json(text: str, label: str = "JSON") -> Any:
    if not isinstance(text, str):
        raise DescriptorError(f"{label} must be a string")

    def reject_constant(value: str) -> Any:
        raise DescriptorError(f"{label} contains non-finite constant {value}")

    def reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise DescriptorError(f"{label} contains duplicate key {key!r}")
            result[key] = value
        return result

    try:
        return json.loads(
            text,
            object_pairs_hook=reject_duplicate_keys,
            parse_constant=reject_constant,
        )
    except DescriptorError:
        raise
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise DescriptorError(f"invalid {label}: {exc}") from exc


def _id_tuple(value: Any, label: str) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple)):
        raise DescriptorError(f"{label} must be an array of identifiers")
    values = tuple(
        _require_identifier(item, f"{label}[{index}]")
        for index, item in enumerate(value)
    )
    if len(values) != len(set(values)):
        raise DescriptorError(f"{label} must not contain duplicates")
    return tuple(sorted(values))


def _metadata(value: Any, label: str) -> dict[str, Any]:
    mapping = _require_mapping(value, label)
    normalised = _normalise_json(mapping, label)
    _check_json_size(normalised, label)
    return normalised


def _schema(value: Any, label: str) -> dict[str, Any]:
    mapping = _require_mapping(value, label)
    normalised = _normalise_json(mapping, label)
    _check_json_size(normalised, label)
    return normalised


def _alias_map(value: Mapping[str, Any], aliases: Mapping[str, str]) -> dict[str, Any]:
    """Copy a mapping while accepting a small set of explicit field aliases."""
    result = dict(value)
    for alias, canonical in aliases.items():
        if alias in result:
            if canonical in result:
                raise DescriptorError(f"provide only one of {alias!r} and {canonical!r}")
            result[canonical] = result.pop(alias)
    return result


@dataclass(frozen=True)
class CapabilityDescriptor:
    """Metadata describing one host-provided capability.

    ``input_schema`` and ``output_schema`` are intentionally opaque JSON
    objects.  The catalog does not attempt to execute or interpret a provider.
    """

    id: str
    description: str
    input_schema: Mapping[str, Any] = field(default_factory=dict)
    output_schema: Mapping[str, Any] | None = None
    effects: tuple[str, ...] = ()
    available: bool = True
    metadata: Mapping[str, Any] = field(default_factory=dict)
    risk: float = 0.0
    reversible: bool = True
    isolation: str = "host_managed"

    _ALLOWED: ClassVar[frozenset[str]] = frozenset({
        "id", "name", "capability_id", "description", "input_schema", "inputSchema",
        "output_schema", "outputSchema", "effects", "available", "metadata", "risk",
        "reversible", "isolation",
    })

    def __post_init__(self) -> None:
        object.__setattr__(self, "id", _require_identifier(self.id, "capability id"))
        object.__setattr__(self, "description", _require_text(self.description, "capability description"))
        object.__setattr__(self, "input_schema", _schema(self.input_schema, "capability input_schema"))
        if self.output_schema is not None:
            object.__setattr__(self, "output_schema", _schema(self.output_schema, "capability output_schema"))
        object.__setattr__(self, "effects", _id_tuple(self.effects, "capability effects"))
        if type(self.available) is not bool:
            raise DescriptorError("capability available must be boolean")
        object.__setattr__(self, "metadata", _metadata(self.metadata, "capability metadata"))
        if type(self.risk) not in {int, float}:
            raise DescriptorError("capability risk must be a finite number between 0 and 1")
        try:
            risk = float(self.risk)
        except (OverflowError, TypeError, ValueError) as exc:
            raise DescriptorError("capability risk must be a finite number between 0 and 1") from exc
        if not math.isfinite(risk) or not 0.0 <= risk <= 1.0:
            raise DescriptorError("capability risk must be a finite number between 0 and 1")
        object.__setattr__(self, "risk", risk)
        if type(self.reversible) is not bool:
            raise DescriptorError("capability reversible must be boolean")
        object.__setattr__(self, "isolation", _require_identifier(self.isolation, "capability isolation"))

    def validate(self) -> "CapabilityDescriptor":
        """Revalidate the bounded descriptor and return it."""
        # Dataclass construction performs the authoritative checks.  This
        # method keeps descriptor/catalog validation interfaces uniform.
        return self

    @property
    def name(self) -> str:
        return self.id

    @property
    def capability_id(self) -> str:
        return self.id

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "description": self.description,
            "input_schema": _json_copy(self.input_schema),
            "output_schema": _json_copy(self.output_schema) if self.output_schema is not None else None,
            "effects": list(self.effects),
            "available": self.available,
            "metadata": _json_copy(self.metadata),
            "risk": self.risk,
            "reversible": self.reversible,
            "isolation": self.isolation,
        }

    as_dict = to_dict

    def capability_descriptor(self) -> dict[str, Any]:
        """Return the compact capability fact projection used by hosts."""
        return {
            "id": self.id,
            "available": self.available,
            "risk": self.risk,
            "reversible": self.reversible,
            "isolation": self.isolation,
            "effects": list(self.effects),
        }

    jev_descriptor = capability_descriptor

    def to_json(self) -> str:
        return _canonical_json(self.to_dict())

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "CapabilityDescriptor":
        raw = _require_mapping(value, "capability")
        unknown = set(raw) - cls._ALLOWED
        if unknown:
            raise DescriptorError(f"capability contains unknown fields: {', '.join(sorted(unknown))}")
        raw = _alias_map(
            raw,
            {
                "name": "id",
                "capability_id": "id",
                "inputSchema": "input_schema",
                "outputSchema": "output_schema",
            },
        )
        if "id" not in raw or "description" not in raw:
            raise DescriptorError("capability requires id and description")
        return cls(
            id=raw["id"],
            description=raw["description"],
            input_schema=raw.get("input_schema", {}),
            output_schema=raw.get("output_schema"),
            effects=raw.get("effects", ()),
            available=raw.get("available", True),
            metadata=raw.get("metadata", {}),
            risk=raw.get("risk", 0.0),
            reversible=raw.get("reversible", True),
            isolation=raw.get("isolation", "host_managed"),
        )

    @classmethod
    def from_json(cls, text: str) -> "CapabilityDescriptor":
        return cls.from_dict(_require_mapping(_parse_json(text, "capability JSON"), "capability"))


@dataclass(frozen=True)
class AgentDescriptor:
    """Metadata describing an agent role and the capabilities it may use."""

    id: str
    description: str
    capabilities: tuple[str, ...] = ()
    instructions: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    _ALLOWED: ClassVar[frozenset[str]] = frozenset({
        "id", "name", "agent_id", "description", "capabilities", "instructions", "metadata",
    })

    def __post_init__(self) -> None:
        object.__setattr__(self, "id", _require_identifier(self.id, "agent id"))
        object.__setattr__(self, "description", _require_text(self.description, "agent description"))
        object.__setattr__(self, "capabilities", _id_tuple(self.capabilities, "agent capabilities"))
        if self.instructions is not None:
            object.__setattr__(self, "instructions", _require_text(self.instructions, "agent instructions"))
        object.__setattr__(self, "metadata", _metadata(self.metadata, "agent metadata"))

    def validate(self) -> "AgentDescriptor":
        """Revalidate the bounded descriptor and return it."""
        return self

    @property
    def name(self) -> str:
        return self.id

    @property
    def agent_id(self) -> str:
        return self.id

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "description": self.description,
            "capabilities": list(self.capabilities),
            "instructions": self.instructions,
            "metadata": _json_copy(self.metadata),
        }

    as_dict = to_dict

    def to_json(self) -> str:
        return _canonical_json(self.to_dict())

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "AgentDescriptor":
        raw = _require_mapping(value, "agent")
        unknown = set(raw) - cls._ALLOWED
        if unknown:
            raise DescriptorError(f"agent contains unknown fields: {', '.join(sorted(unknown))}")
        raw = _alias_map(raw, {"name": "id", "agent_id": "id"})
        if "id" not in raw or "description" not in raw:
            raise DescriptorError("agent requires id and description")
        return cls(
            id=raw["id"],
            description=raw["description"],
            capabilities=raw.get("capabilities", ()),
            instructions=raw.get("instructions"),
            metadata=raw.get("metadata", {}),
        )

    @classmethod
    def from_json(cls, text: str) -> "AgentDescriptor":
        return cls.from_dict(_require_mapping(_parse_json(text, "agent JSON"), "agent"))


@dataclass(frozen=True)
class WorkflowStepDescriptor:
    """One bounded workflow step.

    A step may identify an agent, a capability, or neither when a host injects
    a handler by step ID.  ``handler`` is a logical injection key, not a
    Python callable, so a workflow remains JSON serializable.
    """

    id: str
    description: str = ""
    agent: str | None = None
    capability: str | None = None
    handler: str | None = None
    depends_on: tuple[str, ...] = ()
    inputs: Mapping[str, Any] = field(default_factory=dict)
    outputs: tuple[str, ...] = ()
    metadata: Mapping[str, Any] = field(default_factory=dict)

    _ALLOWED: ClassVar[frozenset[str]] = frozenset({
        "id", "name", "description", "agent", "agent_id", "capability", "capability_id",
        "tool", "tool_id", "handler", "handler_id", "depends_on", "dependsOn", "dependencies", "inputs", "input",
        "outputs", "metadata",
    })

    def __post_init__(self) -> None:
        object.__setattr__(self, "id", _require_identifier(self.id, "workflow step id"))
        object.__setattr__(self, "description", _require_text(self.description, "workflow step description", allow_empty=True))
        if self.agent is not None:
            object.__setattr__(self, "agent", _require_identifier(self.agent, "workflow step agent"))
        if self.capability is not None:
            object.__setattr__(self, "capability", _require_identifier(self.capability, "workflow step capability"))
        if self.handler is not None:
            object.__setattr__(self, "handler", _require_identifier(self.handler, "workflow step handler"))
        dependencies = _id_tuple(self.depends_on, "workflow step depends_on")
        if len(dependencies) > MAX_DEPENDENCIES:
            raise WorkflowValidationError(
                f"workflow step {self.id!r} exceeds maximum of {MAX_DEPENDENCIES} dependencies"
            )
        if self.id in dependencies:
            raise WorkflowValidationError(f"workflow step {self.id!r} cannot depend on itself")
        object.__setattr__(self, "depends_on", dependencies)
        object.__setattr__(self, "inputs", _metadata(self.inputs, "workflow step inputs"))
        object.__setattr__(self, "outputs", _id_tuple(self.outputs, "workflow step outputs"))
        object.__setattr__(self, "metadata", _metadata(self.metadata, "workflow step metadata"))

    def validate(self) -> "WorkflowStepDescriptor":
        """Revalidate the bounded step contract and return it."""
        return self

    @property
    def name(self) -> str:
        return self.id

    @property
    def agent_id(self) -> str | None:
        return self.agent

    @property
    def capability_id(self) -> str | None:
        return self.capability

    @property
    def dependencies(self) -> tuple[str, ...]:
        return self.depends_on

    def to_dict(self) -> dict[str, Any]:
        value = {
            "id": self.id,
            "description": self.description,
            "agent": self.agent,
            "capability": self.capability,
            "handler": self.handler,
            "depends_on": list(self.depends_on),
            "inputs": _json_copy(self.inputs),
            "outputs": list(self.outputs),
            "metadata": _json_copy(self.metadata),
        }
        _check_json_size(value, "workflow step", MAX_STEP_BYTES)
        return value

    as_dict = to_dict

    def to_json(self) -> str:
        return _canonical_json(self.to_dict())

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "WorkflowStepDescriptor":
        raw = _require_mapping(value, "workflow step")
        unknown = set(raw) - cls._ALLOWED
        if unknown:
            raise DescriptorError(f"workflow step contains unknown fields: {', '.join(sorted(unknown))}")
        raw = _alias_map(
            raw,
            {
                "name": "description",
                "agent_id": "agent",
                "capability_id": "capability",
                "tool": "capability",
                "tool_id": "capability",
                "handler_id": "handler",
                "dependsOn": "depends_on",
                "dependencies": "depends_on",
                "input": "inputs",
            },
        )
        if "id" not in raw:
            raise DescriptorError("workflow step requires id")
        return cls(
            id=raw["id"],
            description=raw.get("description", ""),
            agent=raw.get("agent"),
            capability=raw.get("capability"),
            handler=raw.get("handler"),
            depends_on=raw.get("depends_on", ()),
            inputs=raw.get("inputs", {}),
            outputs=raw.get("outputs", ()),
            metadata=raw.get("metadata", {}),
        )

    @classmethod
    def from_json(cls, text: str) -> "WorkflowStepDescriptor":
        return cls.from_dict(_require_mapping(_parse_json(text, "workflow step JSON"), "workflow step"))


def _ordered_steps(steps: tuple[WorkflowStepDescriptor, ...]) -> tuple[WorkflowStepDescriptor, ...]:
    """Return a stable topological order, breaking ties by declaration order."""
    by_id = {step.id: step for step in steps}
    if len(by_id) != len(steps):
        raise WorkflowValidationError("workflow step ids must be unique")
    for step in steps:
        missing = sorted(set(step.depends_on) - set(by_id))
        if missing:
            raise WorkflowValidationError(
                f"workflow step {step.id!r} references missing dependencies: {', '.join(missing)}"
            )

    indegree = {step.id: len(step.depends_on) for step in steps}
    depth = {step.id: 0 for step in steps}
    dependents: dict[str, list[str]] = {step.id: [] for step in steps}
    declaration_index = {step.id: index for index, step in enumerate(steps)}
    for step in steps:
        for dependency in step.depends_on:
            dependents[dependency].append(step.id)

    ready = [step.id for step in steps if indegree[step.id] == 0]
    ready.sort(key=declaration_index.__getitem__)
    result: list[WorkflowStepDescriptor] = []
    while ready:
        current_id = ready.pop(0)
        current = by_id[current_id]
        result.append(current)
        for dependent_id in dependents[current_id]:
            depth[dependent_id] = max(depth[dependent_id], depth[current_id] + 1)
            if depth[dependent_id] > MAX_GRAPH_DEPTH:
                raise WorkflowValidationError(
                    f"workflow dependency graph exceeds maximum depth of {MAX_GRAPH_DEPTH}"
                )
            indegree[dependent_id] -= 1
            if indegree[dependent_id] == 0:
                ready.append(dependent_id)
        ready.sort(key=declaration_index.__getitem__)

    if len(result) != len(steps):
        cycle_nodes = sorted(step_id for step_id, degree in indegree.items() if degree > 0)
        raise WorkflowValidationError(
            f"workflow dependency graph contains a cycle involving: {', '.join(cycle_nodes)}"
        )
    return tuple(result)


@dataclass(frozen=True)
class WorkflowDescriptor:
    """A bounded, deterministic sequential workflow definition."""

    id: str
    description: str
    steps: tuple[WorkflowStepDescriptor, ...] = ()
    metadata: Mapping[str, Any] = field(default_factory=dict)

    _ALLOWED: ClassVar[frozenset[str]] = frozenset({"id", "name", "workflow_id", "description", "steps", "metadata"})

    def __post_init__(self) -> None:
        object.__setattr__(self, "id", _require_identifier(self.id, "workflow id"))
        object.__setattr__(self, "description", _require_text(self.description, "workflow description"))
        if not isinstance(self.steps, (list, tuple)):
            raise DescriptorError("workflow steps must be an array")
        if not self.steps:
            raise WorkflowValidationError("workflow must contain at least one step")
        if len(self.steps) > MAX_WORKFLOW_STEPS:
            raise WorkflowValidationError(f"workflow exceeds maximum of {MAX_WORKFLOW_STEPS} steps")
        converted: list[WorkflowStepDescriptor] = []
        for index, step in enumerate(self.steps):
            if isinstance(step, WorkflowStepDescriptor):
                converted.append(step)
            elif isinstance(step, Mapping):
                converted.append(WorkflowStepDescriptor.from_dict(step))
            else:
                raise DescriptorError(f"workflow steps[{index}] must be a step descriptor or object")
        object.__setattr__(self, "steps", tuple(converted))
        object.__setattr__(self, "metadata", _metadata(self.metadata, "workflow metadata"))
        self.validate()

    @property
    def name(self) -> str:
        return self.id

    def validate(self) -> "WorkflowDescriptor":
        _ordered_steps(self.steps)
        self.to_dict()
        return self

    @property
    def ordered_steps(self) -> tuple[WorkflowStepDescriptor, ...]:
        return _ordered_steps(self.steps)

    def execution_order(self) -> tuple[str, ...]:
        return tuple(step.id for step in self.ordered_steps)

    @property
    def step_order(self) -> tuple[str, ...]:
        return self.execution_order()

    @property
    def topological_steps(self) -> tuple[WorkflowStepDescriptor, ...]:
        return self.ordered_steps

    def to_dict(self) -> dict[str, Any]:
        value = {
            "id": self.id,
            "description": self.description,
            "steps": [step.to_dict() for step in self.steps],
            "metadata": _json_copy(self.metadata),
        }
        _check_json_size(value, "workflow", MAX_WORKFLOW_BYTES)
        return value

    as_dict = to_dict

    def to_json(self) -> str:
        return _canonical_json(self.to_dict())

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "WorkflowDescriptor":
        raw = _require_mapping(value, "workflow")
        unknown = set(raw) - cls._ALLOWED
        if unknown:
            raise DescriptorError(f"workflow contains unknown fields: {', '.join(sorted(unknown))}")
        raw = _alias_map(raw, {"name": "id", "workflow_id": "id"})
        if "id" not in raw or "description" not in raw or "steps" not in raw:
            raise DescriptorError("workflow requires id, description, and steps")
        steps = _require_list(raw["steps"], "workflow steps")
        return cls(
            id=raw["id"],
            description=raw["description"],
            steps=tuple(steps),
            metadata=raw.get("metadata", {}),
        )

    @classmethod
    def from_json(cls, text: str) -> "WorkflowDescriptor":
        return cls.from_dict(_require_mapping(_parse_json(text, "workflow JSON"), "workflow"))


# Short aliases are useful when the descriptor type is already clear from
# context, while the *Descriptor names remain the canonical public API.
Capability = CapabilityDescriptor
Agent = AgentDescriptor
WorkflowStep = WorkflowStepDescriptor
Workflow = WorkflowDescriptor


def _coerce_items(value: Any, label: str, expected: type[T]) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, Mapping):
        # A keyed mapping is a convenience for programmatic construction; the
        # canonical JSON form remains an array and is used by to_dict().
        if len(value) > MAX_CATALOG_ITEMS:
            raise CatalogError(f"{label} exceeds maximum of {MAX_CATALOG_ITEMS} items")
        return list(value.values())
    if isinstance(value, (str, bytes)) or not isinstance(value, Iterable):
        raise DescriptorError(f"{label} must be an iterable of descriptors")
    if isinstance(value, (list, tuple)) and len(value) > MAX_CATALOG_ITEMS:
        raise CatalogError(f"{label} exceeds maximum of {MAX_CATALOG_ITEMS} items")
    items = list(value)
    if len(items) > MAX_CATALOG_ITEMS:
        raise CatalogError(f"{label} exceeds maximum of {MAX_CATALOG_ITEMS} items")
    return items


class WorkflowCatalog:
    """Validated in-memory catalog with deterministic JSON persistence.

    Registration is atomic: if adding an item would introduce a duplicate or
    unresolved reference, the catalog is restored to its prior state.
    """

    def __init__(
        self,
        capabilities: Any = (),
        agents: Any = (),
        workflows: Any = (),
        *,
        schema_version: str = SCHEMA_VERSION,
    ) -> None:
        if schema_version != SCHEMA_VERSION:
            raise CatalogError(f"unsupported catalog schema version: {schema_version!r}")
        self.schema_version = schema_version
        self._capabilities: dict[str, CapabilityDescriptor] = {}
        self._agents: dict[str, AgentDescriptor] = {}
        self._workflows: dict[str, WorkflowDescriptor] = {}
        for item in _coerce_items(capabilities, "capabilities", CapabilityDescriptor):
            descriptor = self._coerce(item, CapabilityDescriptor, "capability")
            if descriptor.id in self._capabilities:
                raise CatalogError(f"capability already registered: {descriptor.id}")
            self._capabilities[descriptor.id] = descriptor
        for item in _coerce_items(agents, "agents", AgentDescriptor):
            descriptor = self._coerce(item, AgentDescriptor, "agent")
            if descriptor.id in self._agents:
                raise CatalogError(f"agent already registered: {descriptor.id}")
            self._agents[descriptor.id] = descriptor
        for item in _coerce_items(workflows, "workflows", WorkflowDescriptor):
            descriptor = self._coerce(item, WorkflowDescriptor, "workflow")
            if descriptor.id in self._workflows:
                raise CatalogError(f"workflow already registered: {descriptor.id}")
            self._workflows[descriptor.id] = descriptor
        self.validate()

    def _coerce(self, value: Any, expected: type[T], label: str) -> T:
        if isinstance(value, expected):
            return value
        if isinstance(value, Mapping):
            try:
                return expected.from_dict(value)  # type: ignore[attr-defined]
            except (TypeError, AttributeError) as exc:
                raise DescriptorError(f"{label} cannot be constructed from object") from exc
        raise DescriptorError(f"{label} must be a {expected.__name__} or object")

    @staticmethod
    def _insert(
        target: dict[str, T],
        descriptor: T,
        *,
        kind: str,
        replace: bool,
    ) -> T | None:
        identifier = descriptor.id  # type: ignore[attr-defined]
        if identifier in target and not replace:
            raise CatalogError(f"{kind} already registered: {identifier}")
        previous = target.get(identifier)
        target[identifier] = descriptor
        return previous

    def _register(self, kind: str, value: Any, *, replace: bool = False) -> Any:
        if kind == "capability":
            descriptor = self._coerce(value, CapabilityDescriptor, kind)
            target = self._capabilities
        elif kind == "agent":
            descriptor = self._coerce(value, AgentDescriptor, kind)
            target = self._agents
        elif kind == "workflow":
            descriptor = self._coerce(value, WorkflowDescriptor, kind)
            target = self._workflows
        else:  # pragma: no cover - guarded by public methods
            raise CatalogError(f"unsupported descriptor kind: {kind}")

        previous = self._insert(target, descriptor, kind=kind, replace=replace)
        try:
            self.validate()
        except Exception:
            if previous is None:
                target.pop(descriptor.id, None)
            else:
                target[descriptor.id] = previous
            raise
        return descriptor

    def register_capability(self, capability: Any, *, replace: bool = False) -> CapabilityDescriptor:
        return self._register("capability", capability, replace=replace)

    def register_agent(self, agent: Any, *, replace: bool = False) -> AgentDescriptor:
        return self._register("agent", agent, replace=replace)

    def register_workflow(self, workflow: Any, *, replace: bool = False) -> WorkflowDescriptor:
        return self._register("workflow", workflow, replace=replace)

    # Short registration aliases are useful for small host integrations.
    add_capability = register_capability
    add_agent = register_agent
    add_workflow = register_workflow

    def add(self, descriptor: Any, *, kind: str | None = None, replace: bool = False) -> Any:
        return self.register(descriptor, kind=kind, replace=replace)

    def register(self, descriptor: Any, *, kind: str | None = None, replace: bool = False) -> Any:
        if kind is None:
            if isinstance(descriptor, CapabilityDescriptor):
                kind = "capability"
            elif isinstance(descriptor, AgentDescriptor):
                kind = "agent"
            elif isinstance(descriptor, WorkflowDescriptor):
                kind = "workflow"
            else:
                raise CatalogError("descriptor kind is required for object registration")
        return self._register(kind, descriptor, replace=replace)

    def validate(self) -> "WorkflowCatalog":
        if self.schema_version != SCHEMA_VERSION:
            raise CatalogError(f"unsupported catalog schema version: {self.schema_version!r}")
        if len(self._capabilities) > MAX_CATALOG_ITEMS:
            raise CatalogError(f"catalog exceeds maximum of {MAX_CATALOG_ITEMS} capabilities")
        if len(self._agents) > MAX_CATALOG_ITEMS:
            raise CatalogError(f"catalog exceeds maximum of {MAX_CATALOG_ITEMS} agents")
        if len(self._workflows) > MAX_CATALOG_ITEMS:
            raise CatalogError(f"catalog exceeds maximum of {MAX_CATALOG_ITEMS} workflows")

        for capability in self._capabilities.values():
            capability.validate()
        for agent in self._agents.values():
            missing = sorted(set(agent.capabilities) - set(self._capabilities))
            if missing:
                raise ReferenceError(
                    f"agent {agent.id!r} references unknown capabilities: {', '.join(missing)}"
                )

        for workflow in self._workflows.values():
            self.validate_workflow_references(workflow)
        _check_json_size(self.to_dict(), "catalog", MAX_CATALOG_BYTES)
        return self

    def validate_workflow_references(self, workflow: WorkflowDescriptor) -> WorkflowDescriptor:
        """Validate a workflow against the current catalog namespaces."""
        if not isinstance(workflow, WorkflowDescriptor):
            raise DescriptorError("workflow must be a WorkflowDescriptor")
        workflow.validate()
        for step in workflow.steps:
            step.validate()
            if step.agent is not None and step.agent not in self._agents:
                raise ReferenceError(
                    f"workflow {workflow.id!r} step {step.id!r} references unknown agent {step.agent!r}"
                )
            if step.capability is not None and step.capability not in self._capabilities:
                raise ReferenceError(
                    f"workflow {workflow.id!r} step {step.id!r} references unknown capability {step.capability!r}"
                )
        return workflow

    def get_capability(self, identifier: str) -> CapabilityDescriptor:
        _require_identifier(identifier, "capability id")
        try:
            return self._capabilities[identifier]
        except KeyError as exc:
            raise ReferenceError(f"unknown capability: {identifier}") from exc

    def get_agent(self, identifier: str) -> AgentDescriptor:
        _require_identifier(identifier, "agent id")
        try:
            return self._agents[identifier]
        except KeyError as exc:
            raise ReferenceError(f"unknown agent: {identifier}") from exc

    def get_workflow(self, identifier: str) -> WorkflowDescriptor:
        _require_identifier(identifier, "workflow id")
        try:
            return self._workflows[identifier]
        except KeyError as exc:
            raise ReferenceError(f"unknown workflow: {identifier}") from exc

    def capability(self, identifier: str) -> CapabilityDescriptor:
        return self.get_capability(identifier)

    def agent(self, identifier: str) -> AgentDescriptor:
        return self.get_agent(identifier)

    def workflow(self, identifier: str) -> WorkflowDescriptor:
        return self.get_workflow(identifier)

    def get(self, kind: str, identifier: str) -> Any:
        if kind == "capability":
            return self.get_capability(identifier)
        if kind == "agent":
            return self.get_agent(identifier)
        if kind == "workflow":
            return self.get_workflow(identifier)
        raise CatalogError(f"unknown descriptor kind: {kind!r}")

    # Non-raising lookup helpers complement the fail-closed ``get_*`` methods.
    def find_capability(self, identifier: str) -> CapabilityDescriptor | None:
        try:
            return self.get_capability(identifier)
        except ReferenceError:
            return None

    def find_agent(self, identifier: str) -> AgentDescriptor | None:
        try:
            return self.get_agent(identifier)
        except ReferenceError:
            return None

    def find_workflow(self, identifier: str) -> WorkflowDescriptor | None:
        try:
            return self.get_workflow(identifier)
        except ReferenceError:
            return None

    @property
    def capabilities(self) -> tuple[CapabilityDescriptor, ...]:
        return tuple(self._capabilities[key] for key in sorted(self._capabilities))

    @property
    def agents(self) -> tuple[AgentDescriptor, ...]:
        return tuple(self._agents[key] for key in sorted(self._agents))

    @property
    def workflows(self) -> tuple[WorkflowDescriptor, ...]:
        return tuple(self._workflows[key] for key in sorted(self._workflows))

    def capability_catalog(self) -> list[dict[str, Any]]:
        return [item.capability_descriptor() for item in self.capabilities]

    def jev_catalog(self) -> list[dict[str, Any]]:
        return [item.capability_descriptor() for item in self.capabilities if item.available]

    def catalog(self) -> list[dict[str, Any]]:
        return self.capability_catalog()

    def to_dict(self) -> dict[str, Any]:
        value = {
            "schema_version": self.schema_version,
            "capabilities": [item.to_dict() for item in self.capabilities],
            "agents": [item.to_dict() for item in self.agents],
            "workflows": [item.to_dict() for item in self.workflows],
        }
        _check_json_size(value, "catalog", MAX_CATALOG_BYTES)
        return value

    as_dict = to_dict

    def to_json(self) -> str:
        return _canonical_json(self.to_dict())

    def fingerprint(self) -> str:
        return hashlib.sha256(self.to_json().encode("utf-8")).hexdigest()

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "WorkflowCatalog":
        raw = _require_mapping(value, "catalog")
        allowed = {"schema_version", "capabilities", "agents", "workflows"}
        unknown = set(raw) - allowed
        if unknown:
            raise DescriptorError(f"catalog contains unknown fields: {', '.join(sorted(unknown))}")
        missing = allowed - set(raw)
        if missing:
            raise DescriptorError(f"catalog is missing required fields: {', '.join(sorted(missing))}")
        if raw["schema_version"] != SCHEMA_VERSION:
            raise CatalogError(f"unsupported catalog schema version: {raw['schema_version']!r}")
        capabilities = _require_list(raw["capabilities"], "catalog capabilities")
        agents = _require_list(raw["agents"], "catalog agents")
        workflows = _require_list(raw["workflows"], "catalog workflows")
        return cls(capabilities, agents, workflows, schema_version=raw["schema_version"])

    @classmethod
    def from_json(cls, text: str) -> "WorkflowCatalog":
        return cls.from_dict(_require_mapping(_parse_json(text, "catalog JSON"), "catalog"))

    load_json = from_json

    @classmethod
    def from_file(cls, path: str | Path) -> "WorkflowCatalog":
        try:
            text = Path(path).read_text(encoding="utf-8")
        except OSError as exc:
            raise CatalogError(f"unable to read catalog file: {exc}") from exc
        return cls.from_json(text)

    load = from_file

    def to_file(self, path: str | Path) -> Path:
        target = Path(path)
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(self.to_json() + "\n", encoding="utf-8")
        except OSError as exc:
            raise CatalogError(f"unable to write catalog file: {exc}") from exc
        return target

    save = to_file
    dump = to_file
    write = to_file

    def __len__(self) -> int:
        return len(self._capabilities) + len(self._agents) + len(self._workflows)

    def __contains__(self, identifier: object) -> bool:
        return isinstance(identifier, str) and (
            identifier in self._capabilities or identifier in self._agents or identifier in self._workflows
        )


# Concise aliases for hosts that call the authority simply a Registry.
Registry = WorkflowCatalog
Catalog = WorkflowCatalog


__all__ = [
    "SCHEMA_VERSION",
    "MAX_CATALOG_ITEMS",
    "MAX_WORKFLOW_STEPS",
    "MAX_DEPENDENCIES",
    "MAX_GRAPH_DEPTH",
    "MAX_JSON_DEPTH",
    "MAX_JSON_NODES",
    "MAX_JSON_BYTES",
    "MAX_CATALOG_BYTES",
    "MAX_WORKFLOW_BYTES",
    "MAX_STEP_BYTES",
    "CatalogError",
    "DescriptorError",
    "ReferenceError",
    "WorkflowValidationError",
    "RegistryError",
    "DescriptorValidationError",
    "InvalidReferenceError",
    "CapabilityDescriptor",
    "AgentDescriptor",
    "WorkflowStepDescriptor",
    "WorkflowDescriptor",
    "Capability",
    "Agent",
    "WorkflowStep",
    "Workflow",
    "WorkflowCatalog",
    "Registry",
    "Catalog",
]
