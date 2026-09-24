"""Optional, dependency-free MCP host seam.

This module does not implement a network transport or install an MCP SDK. A
host injects a transport object, while the adapter owns discovery, schema
checks, trust metadata, result normalization, explicit fallback, and task
handles. MCP remains an optional capability source, never runtime authority.
"""
from __future__ import annotations

import inspect
import re
from dataclasses import dataclass, field
from typing import Any, Callable, Mapping, Protocol

from .contracts import validate_capability_id


class MCPError(RuntimeError):
    """Base error for the optional MCP seam."""


class MCPUnavailable(MCPError):
    pass


class MCPToolNotFound(MCPError):
    pass


class MCPToolMalformed(MCPError):
    pass


class MCPOperationUncertain(MCPError):
    pass


class MCPTransport(Protocol):
    def discover(self) -> Mapping[str, Any]: ...
    def list_tools(self) -> Any: ...
    def call_tool(self, name: str, arguments: Mapping[str, Any]) -> Any: ...


_TOOL_NAME_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_.-]{0,127}$")


@dataclass(frozen=True)
class MCPToolDescriptor:
    name: str
    description: str
    input_schema: Mapping[str, Any]
    output_schema: Mapping[str, Any] | None
    source: str
    server: str
    capability_id: str | None = None
    version: str | None = None
    effects: frozenset[str] = field(default_factory=frozenset)
    available: bool = True
    trust: str = "untrusted"
    annotations: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not _TOOL_NAME_RE.fullmatch(self.name):
            raise MCPToolMalformed(f"invalid MCP tool name: {self.name!r}")
        if self.capability_id is not None:
            try:
                validate_capability_id(self.capability_id)
            except ValueError as exc:
                raise MCPToolMalformed(f"invalid MCP capability id: {self.capability_id!r}") from exc
        if not isinstance(self.description, str):
            raise MCPToolMalformed(f"MCP tool {self.name} has no description")
        if not isinstance(self.input_schema, Mapping):
            raise MCPToolMalformed(f"MCP tool {self.name} inputSchema must be an object")
        if self.output_schema is not None and not isinstance(self.output_schema, Mapping):
            raise MCPToolMalformed(f"MCP tool {self.name} outputSchema must be an object")
        if self.trust not in {"untrusted", "trusted", "verified"}:
            raise MCPToolMalformed(f"MCP tool {self.name} has invalid trust metadata")
        if self.input_schema.get("type") not in {None, "object"}:
            raise MCPToolMalformed(f"MCP tool {self.name} inputSchema must describe an object")
        properties = self.input_schema.get("properties", {})
        if not isinstance(properties, Mapping):
            raise MCPToolMalformed(f"MCP tool {self.name} inputSchema.properties must be an object")
        required = self.input_schema.get("required", [])
        if not isinstance(required, list) or any(not isinstance(item, str) for item in required):
            raise MCPToolMalformed(f"MCP tool {self.name} inputSchema.required must be a string array")

    def capability_descriptor(self) -> dict[str, Any]:
        return {
            "id": self.capability_id or self.name,
            "name": self.name,
            "available": self.available,
            "source": self.source,
            "server": self.server,
            "version": self.version,
            "trust": self.trust,
            "effects": sorted(self.effects),
            "annotations": dict(self.annotations),
        }


def _type_matches(value: Any, expected: str) -> bool:
    return {
        "object": isinstance(value, Mapping),
        "array": isinstance(value, list),
        "string": isinstance(value, str),
        "integer": isinstance(value, int) and not isinstance(value, bool),
        "number": isinstance(value, (int, float)) and not isinstance(value, bool),
        "boolean": isinstance(value, bool),
        "null": value is None,
    }.get(expected, True)


def validate_schema(value: Any, schema: Mapping[str, Any], path: str = "$") -> None:
    """Validate the dependency-free subset of JSON Schema used by MCP tools."""
    if not isinstance(schema, Mapping):
        raise MCPToolMalformed(f"{path} schema must be an object")
    expected = schema.get("type")
    if expected is not None:
        choices = expected if isinstance(expected, list) else [expected]
        if not any(_type_matches(value, choice) for choice in choices):
            raise MCPToolMalformed(f"{path} does not match schema type {expected!r}")
    if "enum" in schema and value not in schema["enum"]:
        raise MCPToolMalformed(f"{path} is not one of the allowed enum values")
    if isinstance(value, str):
        if "minLength" in schema and len(value) < schema["minLength"]:
            raise MCPToolMalformed(f"{path} is shorter than minLength")
        if "pattern" in schema:
            try:
                matches = re.search(schema["pattern"], value) is not None
            except (re.error, TypeError) as exc:
                raise MCPToolMalformed(f"{path} has an invalid pattern") from exc
            if not matches:
                raise MCPToolMalformed(f"{path} does not match pattern")
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if "minimum" in schema and value < schema["minimum"]:
            raise MCPToolMalformed(f"{path} is below minimum")
        if "maximum" in schema and value > schema["maximum"]:
            raise MCPToolMalformed(f"{path} is above maximum")
    if isinstance(value, Mapping):
        required = schema.get("required", [])
        if not isinstance(required, list):
            raise MCPToolMalformed(f"{path}.required must be an array")
        for key in required:
            if key not in value:
                raise MCPToolMalformed(f"{path} is missing required property {key}")
        properties = schema.get("properties", {})
        if not isinstance(properties, Mapping):
            raise MCPToolMalformed(f"{path}.properties must be an object")
        if schema.get("additionalProperties") is False:
            extras = set(value) - set(properties)
            if extras:
                raise MCPToolMalformed(f"{path} contains undeclared properties: {sorted(extras)}")
        for key, child in value.items():
            if key in properties:
                validate_schema(child, properties[key], f"{path}.{key}")
    if isinstance(value, list):
        items = schema.get("items")
        if isinstance(items, Mapping):
            for index, child in enumerate(value):
                validate_schema(child, items, f"{path}[{index}]")


def _maybe_await(value: Any) -> Any:
    if inspect.isawaitable(value):
        raise MCPUnavailable("async MCP transports require an async host adapter")
    return value


@dataclass
class MCPToolResult:
    tool: str
    server: str
    status: str
    result: Any = None
    error_code: str | None = None
    provenance: Mapping[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "tool": self.tool,
            "server": self.server,
            "status": self.status,
            "result": self.result,
            "error_code": self.error_code,
            "provenance": dict(self.provenance),
        }


class MCPAdapter:
    """Capability-oriented adapter around an injected MCP transport."""

    def __init__(
        self,
        transport: MCPTransport,
        *,
        source: str = "injected-mcp",
        fallback: Callable[[str, Mapping[str, Any]], Any] | None = None,
        fallback_equivalent: bool = False,
    ) -> None:
        if transport is None:
            raise MCPUnavailable("an injected MCP transport is required")
        self.transport = transport
        self.source = source
        self.fallback = fallback
        self.fallback_equivalent = fallback_equivalent
        self._tools: dict[str, MCPToolDescriptor] = {}
        self._server_info: dict[str, Any] = {}

    def discover(self) -> list[MCPToolDescriptor]:
        discover = getattr(self.transport, "discover", None)
        if callable(discover):
            info = _maybe_await(discover())
            if not isinstance(info, Mapping):
                raise MCPToolMalformed("MCP discovery response must be an object")
            self._server_info = dict(info)
        list_tools = getattr(self.transport, "list_tools", None)
        if not callable(list_tools):
            raise MCPUnavailable("MCP transport does not support tool discovery")
        response = _maybe_await(list_tools())
        if isinstance(response, Mapping):
            raw_tools = response.get("tools", [])
        else:
            raw_tools = response
        if not isinstance(raw_tools, list):
            raise MCPToolMalformed("MCP tools/list response must contain an array")
        discovered: dict[str, MCPToolDescriptor] = {}
        server = str(self._server_info.get("name", self.source))
        for index, raw in enumerate(raw_tools):
            if not isinstance(raw, Mapping):
                raise MCPToolMalformed(f"tools[{index}] must be an object")
            name = raw.get("name")
            description = raw.get("description", "")
            capability_id = raw.get("capabilityId", raw.get("capability_id"))
            input_schema = raw.get("inputSchema", raw.get("input_schema"))
            output_schema = raw.get("outputSchema", raw.get("output_schema"))
            if not isinstance(name, str) or input_schema is None:
                raise MCPToolMalformed(f"tools[{index}] is missing name or inputSchema")
            annotations = raw.get("annotations") or {}
            effects = raw.get("effects") or annotations.get("effects") or []
            if isinstance(effects, str):
                effects = [effects]
            if not isinstance(effects, list):
                raise MCPToolMalformed(f"MCP tool {name} effects must be an array")
            descriptor = MCPToolDescriptor(
                name=name,
                description=description,
                input_schema=input_schema,
                output_schema=output_schema,
                source=self.source,
                server=server,
                capability_id=capability_id,
                version=raw.get("version") or self._server_info.get("version"),
                effects=frozenset(str(effect) for effect in effects),
                available=bool(raw.get("available", True)),
                trust=str(raw.get("trust", annotations.get("trust", "untrusted"))),
                annotations=dict(annotations) if isinstance(annotations, Mapping) else {},
            )
            if name in discovered:
                raise MCPToolMalformed(f"duplicate MCP tool name: {name}")
            discovered[name] = descriptor
        self._tools = discovered
        return list(discovered.values())

    def catalog(self) -> list[dict[str, Any]]:
        if not self._tools:
            self.discover()
        return [descriptor.capability_descriptor() for descriptor in self._tools.values()]

    def register_into(self, registry, *, replace: bool = False, allow_untrusted: bool = False, argument_mapper=None) -> list[str]:
        """Register explicitly identified MCP tools in a capability registry."""
        from .capabilities import Capability

        if argument_mapper is not None and not callable(argument_mapper):
            raise TypeError("argument_mapper must be callable")
        registered: list[str] = []
        for descriptor in self.catalog():
            capability_id = descriptor.get("id")
            if not isinstance(capability_id, str) or capability_id == descriptor.get("name"):
                continue

            def execute(_descriptor=descriptor, **kwargs):
                if argument_mapper:
                    arguments = argument_mapper(kwargs)
                elif "arguments" in kwargs and isinstance(kwargs["arguments"], Mapping):
                    arguments = kwargs["arguments"]
                else:
                    arguments = kwargs
                if not isinstance(arguments, Mapping):
                    raise MCPToolMalformed("MCP arguments mapper must return an object")
                result = self.call_tool(
                    _descriptor["name"],
                    arguments,
                    allow_untrusted=allow_untrusted,
                )
                return {
                    "success": result.status == "success",
                    "result": result.result,
                    "code": result.error_code,
                    "status": result.status,
                    "provenance": dict(result.provenance),
                    "stdout": "",
                    "stderr": "",
                    "exit_code": 0 if result.status == "success" else -1,
                }

            registry.register(
                Capability(
                    name=capability_id,
                    description=f"MCP tool {descriptor['name']}",
                    execute=execute,
                    effects=set(descriptor.get("effects", [])),
                    available=bool(descriptor.get("available", True)),
                    isolation="host_managed",
                ),
                replace=replace,
            )
            registered.append(capability_id)
        return registered

    def health(self) -> dict[str, Any]:
        try:
            tools = self.discover()
        except (MCPError, OSError, ValueError) as exc:
            return {"available": False, "error_code": "mcp_discovery_failed", "error_type": type(exc).__name__}
        return {"available": True, "server": self._server_info, "tool_count": len(tools)}

    def _descriptor(self, name: str) -> MCPToolDescriptor:
        if not self._tools:
            self.discover()
        descriptor = self._tools.get(name)
        if descriptor is None:
            raise MCPToolNotFound(name)
        return descriptor

    def _fallback_result(
        self,
        descriptor: MCPToolDescriptor,
        arguments: Mapping[str, Any],
        *,
        allow_fallback: bool,
    ) -> MCPToolResult | None:
        if not allow_fallback or not self.fallback_equivalent or self.fallback is None:
            return None
        try:
            value = _maybe_await(self.fallback(descriptor.name, dict(arguments)))
            if descriptor.output_schema is not None:
                validate_schema(value, descriptor.output_schema, "fallback_result")
            return MCPToolResult(
                descriptor.name,
                descriptor.server,
                "success",
                value,
                provenance={
                    "source": descriptor.source,
                    "server": descriptor.server,
                    "tool": descriptor.name,
                    "trust": descriptor.trust,
                    "fallback": True,
                },
            )
        except Exception as exc:
            return MCPToolResult(
                descriptor.name,
                descriptor.server,
                "failed",
                error_code="mcp_fallback_failed",
                result=type(exc).__name__,
            )

    def call_tool(
        self,
        name: str,
        arguments: Mapping[str, Any],
        *,
        allow_untrusted: bool = False,
        allow_fallback: bool = False,
    ) -> MCPToolResult:
        descriptor = self._descriptor(name)
        if not descriptor.available:
            return MCPToolResult(name, descriptor.server, "unavailable", error_code="mcp_tool_unavailable")
        if descriptor.trust == "untrusted" and not allow_untrusted:
            return MCPToolResult(name, descriptor.server, "review", error_code="mcp_tool_untrusted")
        try:
            validate_schema(dict(arguments), descriptor.input_schema, "arguments")
        except MCPToolMalformed as exc:
            return MCPToolResult(name, descriptor.server, "rejected", error_code="mcp_input_invalid", result=str(exc))
        call = getattr(self.transport, "call_tool", None)
        if not callable(call):
            fallback = self._fallback_result(descriptor, arguments, allow_fallback=allow_fallback)
            return fallback or MCPToolResult(name, descriptor.server, "unavailable", error_code="mcp_call_unavailable")
        try:
            raw = _maybe_await(call(name, dict(arguments)))
        except TimeoutError as exc:
            return MCPToolResult(name, descriptor.server, "uncertain", error_code="mcp_call_uncertain", result=type(exc).__name__)
        except MCPUnavailable:
            fallback = self._fallback_result(descriptor, arguments, allow_fallback=allow_fallback)
            return fallback or MCPToolResult(name, descriptor.server, "unavailable", error_code="mcp_unavailable")
        except Exception as exc:
            return MCPToolResult(name, descriptor.server, "failed", error_code="mcp_tool_error", result=type(exc).__name__)
        if not isinstance(raw, Mapping):
            return MCPToolResult(name, descriptor.server, "failed", error_code="mcp_malformed_result")
        if raw.get("isError") is True or raw.get("is_error") is True:
            return MCPToolResult(name, descriptor.server, "failed", error_code="mcp_tool_error", result=raw.get("content"))
        value = raw.get("structuredContent", raw.get("structured_content", raw.get("content")))
        if descriptor.output_schema is not None:
            try:
                validate_schema(value, descriptor.output_schema, "result")
            except MCPToolMalformed as exc:
                return MCPToolResult(name, descriptor.server, "failed", error_code="mcp_output_invalid", result=str(exc))
        provenance = {"source": descriptor.source, "server": descriptor.server, "tool": name, "trust": descriptor.trust}
        return MCPToolResult(name, descriptor.server, "success", value, provenance=provenance)

    def start_task(self, name: str, arguments: Mapping[str, Any]) -> MCPToolResult:
        try:
            descriptor = self._descriptor(name)
        except MCPError as exc:
            return MCPToolResult(name, self.source, "failed", error_code="mcp_tool_unavailable", result=type(exc).__name__)
        if not descriptor.available:
            return MCPToolResult(name, descriptor.server, "unavailable", error_code="mcp_tool_unavailable")
        if descriptor.trust == "untrusted":
            return MCPToolResult(name, descriptor.server, "review", error_code="mcp_tool_untrusted")
        try:
            validate_schema(dict(arguments), descriptor.input_schema, "arguments")
        except (MCPToolMalformed, TypeError, ValueError) as exc:
            return MCPToolResult(name, descriptor.server, "rejected", error_code="mcp_input_invalid", result=str(exc))
        create = getattr(self.transport, "create_task", None)
        if not callable(create):
            return MCPToolResult(name, self.source, "unavailable", error_code="mcp_tasks_unavailable")
        try:
            raw = _maybe_await(create(name, dict(arguments)))
        except Exception as exc:
            return MCPToolResult(name, self.source, "failed", error_code="mcp_task_create_failed", result=type(exc).__name__)
        if not isinstance(raw, Mapping) or not raw.get("task_id"):
            return MCPToolResult(name, self.source, "failed", error_code="mcp_task_handle_missing")
        return MCPToolResult(name, self.source, "accepted", dict(raw), provenance={"task_id": raw["task_id"]})

    def get_task(self, task_id: str) -> MCPToolResult:
        get = getattr(self.transport, "get_task", None)
        if not callable(get):
            return MCPToolResult(task_id, self.source, "unavailable", error_code="mcp_tasks_unavailable")
        try:
            raw = _maybe_await(get(task_id))
        except Exception as exc:
            return MCPToolResult(task_id, self.source, "failed", error_code="mcp_task_read_failed", result=type(exc).__name__)
        return MCPToolResult(task_id, self.source, "success", raw, provenance={"task_id": task_id})

    def cancel_task(self, task_id: str) -> MCPToolResult:
        cancel = getattr(self.transport, "cancel_task", None)
        if not callable(cancel):
            return MCPToolResult(task_id, self.source, "unavailable", error_code="mcp_tasks_unavailable")
        try:
            raw = _maybe_await(cancel(task_id))
        except Exception as exc:
            return MCPToolResult(task_id, self.source, "failed", error_code="mcp_task_cancel_failed", result=type(exc).__name__)
        return MCPToolResult(task_id, self.source, "success", raw, provenance={"task_id": task_id})
