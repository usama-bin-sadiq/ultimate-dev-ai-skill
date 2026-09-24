"""Bounded sequential execution for validated workflow descriptors.

The executor is host-neutral and dependency-free.  It does not import a
model/provider, perform network I/O, or choose an execution adapter.  A host
injects a callable for each logical step ID and receives a structured,
deterministic result and event stream.  A handler may use the conventional
``context``/``inputs``/``dependencies`` parameter names, or request ``step``,
``results``, or the JSON-shaped ``payload`` explicitly; no host/provider
object is constructed by the executor.
"""
from __future__ import annotations

import inspect
import json
import queue
import threading
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from typing import Any

from .registry import (
    MAX_DEPENDENCIES,
    MAX_JSON_BYTES,
    MAX_WORKFLOW_STEPS,
    AgentDescriptor,
    CapabilityDescriptor,
    CatalogError,
    WorkflowCatalog,
    WorkflowDescriptor,
    WorkflowStepDescriptor,
    _canonical_json,
    _check_json_size,
    _json_copy,
    _normalise_json,
    _require_identifier,
)


class WorkflowExecutionError(CatalogError):
    """Raised for invalid executor configuration or invocation contracts."""


class StepExecutionError(WorkflowExecutionError):
    """Compatibility alias for callers that use a step-specific error name."""


EVENT_TYPES = frozenset({
    "workflow_started",
    "step_started",
    "step_completed",
    "step_failed",
    "step_skipped",
    "workflow_completed",
    "workflow_failed",
})
RESULT_STATUSES = frozenset({"succeeded", "failed", "skipped"})
HANDLER_RESULT_STATUSES = frozenset({"success", "succeeded", "ok", "failed", "failure", "skipped"})
MAX_EXECUTION_BYTES = 4 * MAX_JSON_BYTES
MAX_HANDLERS = MAX_WORKFLOW_STEPS
DEFAULT_STEP_TIMEOUT_SECONDS = 300.0


class WorkflowStepTimeout(WorkflowExecutionError):
    """A handler exceeded its bounded execution deadline."""


def _call_with_timeout(call: Callable[[], Any], timeout_seconds: float) -> Any:
    result_queue: queue.Queue[tuple[bool, Any]] = queue.Queue(maxsize=1)

    def runner() -> None:
        try:
            result_queue.put((True, call()))
        except BaseException as exc:
            result_queue.put((False, exc))

    worker = threading.Thread(target=runner, name="ultimate-workflow-step", daemon=True)
    worker.start()
    try:
        ok, value = result_queue.get(timeout=timeout_seconds)
    except queue.Empty as exc:
        raise WorkflowStepTimeout("workflow step exceeded its deadline") from exc
    if ok:
        return value
    raise value


def _positive_limit(value: Any, label: str) -> int:
    if type(value) is not int or value <= 0:
        raise WorkflowExecutionError(f"{label} must be a positive integer")
    if label == "max_steps" and value > MAX_WORKFLOW_STEPS:
        raise WorkflowExecutionError(f"{label} cannot exceed {MAX_WORKFLOW_STEPS}")
    if label in {"max_result_bytes", "max_context_bytes"} and value > MAX_JSON_BYTES:
        raise WorkflowExecutionError(f"{label} cannot exceed {MAX_JSON_BYTES}")
    if label == "max_total_bytes" and value > MAX_EXECUTION_BYTES:
        raise WorkflowExecutionError(f"{label} cannot exceed {MAX_EXECUTION_BYTES}")
    return value


def _error_value(
    value: Any,
    *,
    default_code: str = "handler_error",
    max_bytes: int = MAX_JSON_BYTES,
) -> dict[str, Any]:
    if value is None:
        return {"code": default_code, "message": "step handler failed"}
    if isinstance(value, Mapping):
        code = value.get("code", default_code)
        message = value.get("message", value.get("error", "step handler failed"))
        error_type = value.get("type")
        if not isinstance(code, str) or not code:
            code = default_code
        try:
            message_text = message if isinstance(message, str) else str(message)
        except Exception:  # pragma: no cover - defensive for hostile objects
            message_text = "step handler failed"
        try:
            type_text = str(error_type)[:128] if error_type is not None else None
        except Exception:  # pragma: no cover - defensive for hostile objects
            type_text = None
        result: dict[str, Any] = {
            "code": code,
            "message": message_text[:4096],
        }
        if type_text is not None:
            result["type"] = type_text
        try:
            for key in sorted(value, key=lambda item: str(item)):
                if not isinstance(key, str):
                    raise CatalogError("step error keys must be strings")
                if key not in {"code", "message", "error", "type"}:
                    result[key] = _normalise_json(value[key], f"error.{key}")
            _check_json_size(result, "step error", max_bytes)
        except (CatalogError, TypeError, ValueError, OverflowError):
            return {"code": code, "message": "step error details are invalid or exceeded the configured bound"}
        return result
    try:
        message = str(value)
    except Exception:  # pragma: no cover - defensive for hostile objects
        message = default_code
    return {"code": default_code, "message": message[:4096]}


def _canonical_value(value: Any, label: str, *, max_bytes: int) -> Any:
    normalised = _normalise_json(value, label)
    _check_json_size(normalised, label, max_bytes)
    # Round-tripping through the canonical encoder makes nested mapping order
    # deterministic even when a handler built a dict from unordered input.
    return json.loads(_canonical_json(normalised))


@dataclass(frozen=True)
class WorkflowEvent:
    """One deterministic executor event; no wall-clock or random IDs."""

    sequence: int
    type: str
    workflow_id: str
    step_id: str | None = None
    status: str | None = None
    details: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if type(self.sequence) is not int or self.sequence < 0:
            raise WorkflowExecutionError("workflow event sequence must be a non-negative integer")
        if self.type not in EVENT_TYPES:
            raise WorkflowExecutionError(f"unsupported workflow event type: {self.type!r}")
        object.__setattr__(self, "workflow_id", _require_identifier(self.workflow_id, "workflow event workflow_id"))
        if self.step_id is not None:
            object.__setattr__(self, "step_id", _require_identifier(self.step_id, "workflow event step_id"))
        if self.status is not None and not isinstance(self.status, str):
            raise WorkflowExecutionError("workflow event status must be a string or null")
        object.__setattr__(self, "details", _normalise_json(self.details, "workflow event details"))

    @property
    def event_type(self) -> str:
        return self.type

    def to_dict(self) -> dict[str, Any]:
        return {
            "sequence": self.sequence,
            "type": self.type,
            "workflow_id": self.workflow_id,
            "step_id": self.step_id,
            "status": self.status,
            "details": _json_value(self.details),
        }

    as_dict = to_dict

    def to_json(self) -> str:
        return _canonical_json(self.to_dict())


@dataclass(frozen=True)
class StepResult:
    """Structured result for one planned workflow step."""

    step_id: str
    status: str
    output: Any = None
    error: Mapping[str, Any] | None = None
    dependencies: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "step_id", _require_identifier(self.step_id, "step result step_id"))
        if self.status not in RESULT_STATUSES:
            raise WorkflowExecutionError(f"unsupported step result status: {self.status!r}")
        object.__setattr__(self, "output", _normalise_json(self.output, "step result output"))
        if self.error is not None:
            object.__setattr__(self, "error", _error_value(self.error))
        if not isinstance(self.dependencies, (list, tuple)):
            raise WorkflowExecutionError("step result dependencies must be an array")
        dependencies = tuple(
            _require_identifier(item, f"step result dependency[{index}]")
            for index, item in enumerate(self.dependencies)
        )
        if len(dependencies) > MAX_DEPENDENCIES:
            raise WorkflowExecutionError(
                f"step result exceeds maximum of {MAX_DEPENDENCIES} dependencies"
            )
        if len(dependencies) != len(set(dependencies)):
            raise WorkflowExecutionError("step result dependencies must not contain duplicates")
        object.__setattr__(self, "dependencies", tuple(sorted(dependencies)))

    @property
    def success(self) -> bool:
        return self.status == "succeeded"

    @property
    def ok(self) -> bool:
        return self.success

    def to_dict(self) -> dict[str, Any]:
        return {
            "step_id": self.step_id,
            "status": self.status,
            "output": _json_value(self.output),
            "error": _json_value(self.error) if self.error is not None else None,
            "dependencies": list(self.dependencies),
        }

    as_dict = to_dict

    def to_json(self) -> str:
        return _canonical_json(self.to_dict())

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "StepResult":
        if not isinstance(value, Mapping):
            raise WorkflowExecutionError("step result must be an object")
        allowed = {"step_id", "status", "output", "error", "dependencies"}
        unknown = set(value) - allowed
        if unknown:
            raise WorkflowExecutionError(f"step result contains unknown fields: {', '.join(sorted(unknown))}")
        return cls(
            step_id=value.get("step_id"),
            status=value.get("status"),
            output=value.get("output"),
            error=value.get("error"),
            dependencies=tuple(value.get("dependencies", ())),
        )


@dataclass(frozen=True)
class WorkflowResult:
    """Complete result for one bounded workflow execution."""

    workflow_id: str
    status: str
    output: Any = None
    steps: tuple[StepResult, ...] = ()
    events: tuple[WorkflowEvent, ...] = ()
    error: Mapping[str, Any] | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "workflow_id", _require_identifier(self.workflow_id, "workflow result workflow_id"))
        if self.status not in {"succeeded", "failed"}:
            raise WorkflowExecutionError(f"unsupported workflow result status: {self.status!r}")
        object.__setattr__(self, "output", _normalise_json(self.output, "workflow result output"))
        steps = tuple(self.steps)
        if any(not isinstance(item, StepResult) for item in steps):
            raise WorkflowExecutionError("workflow result steps must contain StepResult values")
        step_ids = [item.step_id for item in steps]
        if len(step_ids) != len(set(step_ids)):
            raise WorkflowExecutionError("workflow result step IDs must be unique")
        object.__setattr__(self, "steps", steps)
        events = tuple(self.events)
        if any(not isinstance(item, WorkflowEvent) for item in events):
            raise WorkflowExecutionError("workflow result events must contain WorkflowEvent values")
        for expected, event in enumerate(events):
            if event.sequence != expected:
                raise WorkflowExecutionError("workflow event sequences must be contiguous from zero")
            if event.workflow_id != self.workflow_id:
                raise WorkflowExecutionError("workflow result events must match workflow_id")
        object.__setattr__(self, "events", events)
        if self.error is not None:
            object.__setattr__(self, "error", _error_value(self.error))

    @property
    def success(self) -> bool:
        return self.status == "succeeded"

    @property
    def ok(self) -> bool:
        return self.success

    @property
    def step_results(self) -> tuple[StepResult, ...]:
        return self.steps

    @property
    def result_by_step(self) -> dict[str, StepResult]:
        return {step.step_id: step for step in self.steps}

    def to_dict(self) -> dict[str, Any]:
        return {
            "workflow_id": self.workflow_id,
            "status": self.status,
            "success": self.success,
            "output": _json_value(self.output),
            "steps": [step.to_dict() for step in self.steps],
            "events": [event.to_dict() for event in self.events],
            "error": _json_value(self.error) if self.error is not None else None,
        }

    as_dict = to_dict

    def to_json(self) -> str:
        return _canonical_json(self.to_dict())


# Explicit names reduce ambiguity for callers that use both result classes.
WorkflowStepResult = StepResult
WorkflowExecutionResult = WorkflowResult
WorkflowExecutionEvent = WorkflowEvent


def _json_value(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {key: _json_value(value[key]) for key in sorted(value)}
    if isinstance(value, (list, tuple)):
        return [_json_value(item) for item in value]
    return value


@dataclass(frozen=True)
class StepInvocation:
    """JSON-shaped payload available to handlers that request ``payload``."""

    workflow_id: str
    step_id: str
    step: Mapping[str, Any]
    context: Mapping[str, Any]
    results: Mapping[str, Any]
    dependencies: Mapping[str, Any]
    dependency_results: Mapping[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "workflow_id": self.workflow_id,
            "step_id": self.step_id,
            "step": _json_value(self.step),
            "inputs": _json_value(self.step.get("inputs", {})),
            "context": _json_value(self.context),
            "results": _json_value(self.results),
            "dependencies": _json_value(self.dependencies),
            "dependency_results": _json_value(self.dependency_results),
        }


StepHandler = Callable[..., Any]
StepContext = StepInvocation
WorkflowContext = StepInvocation


class WorkflowExecutor:
    """Execute one catalog workflow sequentially through injected handlers."""

    def __init__(
        self,
        catalog: WorkflowCatalog,
        handlers: Mapping[str, StepHandler] | None = None,
        *,
        max_steps: int = MAX_WORKFLOW_STEPS,
        max_result_bytes: int = MAX_JSON_BYTES,
        max_context_bytes: int = MAX_JSON_BYTES,
        max_total_bytes: int = MAX_EXECUTION_BYTES,
        step_timeout_seconds: float = DEFAULT_STEP_TIMEOUT_SECONDS,
    ) -> None:
        if not isinstance(catalog, WorkflowCatalog):
            raise WorkflowExecutionError("catalog must be a WorkflowCatalog")
        catalog.validate()
        self.catalog = catalog
        self.max_steps = _positive_limit(max_steps, "max_steps")
        self.max_result_bytes = _positive_limit(max_result_bytes, "max_result_bytes")
        self.max_context_bytes = _positive_limit(max_context_bytes, "max_context_bytes")
        self.max_total_bytes = _positive_limit(max_total_bytes, "max_total_bytes")
        if isinstance(step_timeout_seconds, bool) or not isinstance(step_timeout_seconds, (int, float)) or step_timeout_seconds <= 0:
            raise WorkflowExecutionError("step_timeout_seconds must be positive")
        self.step_timeout_seconds = float(step_timeout_seconds)
        self.handlers: dict[str, StepHandler] = {}
        if handlers is not None:
            self._set_handlers(handlers)

    def _copy_handlers(self, handlers: Mapping[str, StepHandler]) -> dict[str, StepHandler]:
        if not isinstance(handlers, Mapping):
            raise WorkflowExecutionError("handlers must be a mapping")
        if len(handlers) > MAX_HANDLERS:
            raise WorkflowExecutionError(f"handlers cannot exceed {MAX_HANDLERS} entries")
        copied: dict[str, StepHandler] = {}
        for key, handler in handlers.items():
            if not isinstance(key, str) or not key or len(key) > 256:
                raise WorkflowExecutionError("handler keys must be non-empty strings")
            if not callable(handler):
                raise WorkflowExecutionError(f"handler for {key!r} must be callable")
            copied[key] = handler
        return copied

    def _set_handlers(self, handlers: Mapping[str, StepHandler]) -> None:
        self.handlers = self._copy_handlers(handlers)

    def register_handler(
        self,
        key: str | WorkflowStepDescriptor,
        handler: StepHandler,
        *,
        replace: bool = True,
    ) -> StepHandler:
        if isinstance(key, WorkflowStepDescriptor):
            key = key.id
        if not isinstance(key, str) or not key or len(key) > 256:
            raise WorkflowExecutionError("handler key must be a non-empty string")
        if not callable(handler):
            raise WorkflowExecutionError("step handler must be callable")
        if key in self.handlers and not replace:
            raise WorkflowExecutionError(f"handler already registered: {key}")
        self.handlers[key] = handler
        return handler

    add_handler = register_handler

    def _resolve_handler(
        self,
        workflow: WorkflowDescriptor,
        step: WorkflowStepDescriptor,
        handlers: Mapping[str, StepHandler],
    ) -> StepHandler | None:
        keys = []
        if step.handler is not None:
            keys.append(step.handler)
        keys.extend((f"{workflow.id}:{step.id}", step.id))
        if step.capability is not None:
            keys.extend((f"{step.capability}:{step.id}", step.capability))
        if step.agent is not None:
            keys.extend((f"{step.agent}:{step.id}", step.agent))
        # Explicit step handler wins, followed by workflow/step, step ID,
        # and finally referenced capability/agent keys.
        for key in keys:
            if key in handlers:
                return handlers[key]
        return None

    @staticmethod
    def _parameter_value(
        name: str,
        ordinal: int,
        *,
        payload: StepInvocation,
        step: WorkflowStepDescriptor,
        workflow: WorkflowDescriptor,
        context: Mapping[str, Any],
        dependency_values: Mapping[str, Any],
        result_values: Mapping[str, Any],
        canonical: tuple[Any, ...],
    ) -> Any:
        lowered = name.lower()
        if lowered in {"step", "step_descriptor", "descriptor"}:
            return step
        if lowered in {"step_id", "step_name"}:
            return step.id
        if lowered in {"workflow", "workflow_descriptor"}:
            return workflow
        if lowered in {"context", "ctx", "state", "input"}:
            return context
        if lowered == "inputs":
            return _json_copy(step.inputs)
        if lowered in {"dependencies", "dependency_values", "deps"}:
            return dependency_values
        if lowered in {"results", "step_results", "result_values", "outputs", "prior", "prior_results", "previous", "previous_results"}:
            return result_values
        if lowered in {"payload", "invocation", "step_context", "invocation_context"}:
            return payload.to_dict()
        if ordinal < len(canonical):
            return canonical[ordinal]
        return None

    def _invoke_handler(
        self,
        handler: StepHandler,
        *,
        workflow: WorkflowDescriptor,
        step: WorkflowStepDescriptor,
        context: Mapping[str, Any],
        results: Mapping[str, StepResult],
    ) -> Any:
        result_values = {key: value.output for key, value in sorted(results.items())}
        dependency_values = {
            dependency: result_values.get(dependency)
            for dependency in step.depends_on
        }
        dependency_result_dicts = {
            dependency: results[dependency].to_dict()
            for dependency in step.depends_on
            if dependency in results
        }
        payload = StepInvocation(
            workflow_id=workflow.id,
            step_id=step.id,
            step=step.to_dict(),
            context=context,
            results=result_values,
            dependencies=dependency_values,
            dependency_results=dependency_result_dicts,
        )
        canonical = (context, dependency_values, step, payload.to_dict())
        try:
            signature = inspect.signature(handler)
        except (TypeError, ValueError):
            return _call_with_timeout(lambda: handler(context), self.step_timeout_seconds)

        positional: list[Any] = []
        keyword: dict[str, Any] = {}
        ordinal = 0
        has_varargs = False
        has_varkw = False
        for parameter in signature.parameters.values():
            if parameter.kind is inspect.Parameter.VAR_POSITIONAL:
                has_varargs = True
                continue
            if parameter.kind is inspect.Parameter.VAR_KEYWORD:
                has_varkw = True
                continue
            value = self._parameter_value(
                parameter.name,
                ordinal,
                payload=payload,
                step=step,
                workflow=workflow,
                context=context,
                dependency_values=dependency_values,
                result_values=result_values,
                canonical=canonical,
            )
            if parameter.kind is inspect.Parameter.KEYWORD_ONLY:
                if parameter.default is inspect.Parameter.empty:
                    keyword[parameter.name] = value
            else:
                positional.append(value)
                ordinal += 1
        if has_varargs:
            positional.append(payload.to_dict())
        if has_varkw:
            for key, value in payload.to_dict().items():
                keyword.setdefault(key, value)
        return _call_with_timeout(lambda: handler(*positional, **keyword), self.step_timeout_seconds)

    def _normalise_handler_result(
        self,
        value: Any,
        *,
        step: WorkflowStepDescriptor,
    ) -> tuple[str, Any, Mapping[str, Any] | None]:
        if inspect.isawaitable(value):
            close = getattr(value, "close", None)
            if callable(close):
                close()
            return "failed", None, {
                "code": "async_handler_unsupported",
                "message": "workflow handlers must be synchronous",
            }
        if value is False:
            return "failed", None, {
                "code": "handler_reported_failure",
                "message": "step handler returned false",
            }
        if isinstance(value, StepResult):
            status = "succeeded" if value.status == "succeeded" else value.status
            if status == "succeeded":
                try:
                    output = _canonical_value(
                        value.output,
                        f"step {step.id} output",
                        max_bytes=self.max_result_bytes,
                    )
                except CatalogError as exc:
                    return "failed", None, {"code": "invalid_handler_result", "message": str(exc)}
            else:
                output = value.output
            return status, output, _error_value(value.error, max_bytes=self.max_result_bytes)
        if isinstance(value, Mapping) and (
            ("status" in value and value.get("status") in HANDLER_RESULT_STATUSES)
            or ("success" in value and type(value.get("success")) is bool)
            or ("ok" in value and type(value.get("ok")) is bool)
        ):
            raw_status = value.get(
                "status",
                "success" if value.get("success", value.get("ok")) else "failed",
            )
            if raw_status in {"success", "succeeded", "ok"}:
                status = "succeeded"
            elif raw_status in {"failed", "failure"}:
                status = "failed"
            else:
                status = "skipped"
            output = value.get("output")
            if status == "succeeded" and "output" not in value:
                if "result" in value:
                    output = value["result"]
                else:
                    output = {
                        key: item
                        for key, item in value.items()
                        if key not in {"status", "success", "ok"}
                    }
            error = value.get("error", value.get("message"))
            if status == "failed":
                return status, None, _error_value(
                    error,
                    default_code="handler_failed",
                    max_bytes=self.max_result_bytes,
                )
            if status == "succeeded":
                try:
                    output = _canonical_value(
                        output,
                        f"step {step.id} output",
                        max_bytes=self.max_result_bytes,
                    )
                except CatalogError as exc:
                    return "failed", None, {"code": "invalid_handler_result", "message": str(exc)}
            return status, output, None
        try:
            output = _canonical_value(value, f"step {step.id} output", max_bytes=self.max_result_bytes)
        except CatalogError as exc:
            return "failed", None, {"code": "invalid_handler_result", "message": str(exc)}
        return "succeeded", output, None

    def execute(
        self,
        workflow: str | WorkflowDescriptor,
        context: Mapping[str, Any] | None = None,
        handlers: Mapping[str, StepHandler] | None = None,
        *,
        initial_context: Mapping[str, Any] | None = None,
        max_steps: int | None = None,
    ) -> WorkflowResult:
        """Execute ``workflow`` once and return a structured result.

        The executor is deliberately fail-fast: after a failed step, later
        steps receive ``skipped`` results and no handler is called.  This keeps
        side effects bounded and makes the event stream deterministic.
        """
        if context is not None and initial_context is not None:
            raise WorkflowExecutionError("provide context or initial_context, not both")
        if context is None:
            context = initial_context
        self.catalog.validate()
        if isinstance(workflow, WorkflowDescriptor):
            definition = self.catalog.validate_workflow_references(workflow)
        else:
            definition = self.catalog.get_workflow(workflow)

        limit = self.max_steps if max_steps is None else _positive_limit(max_steps, "max_steps")
        if len(definition.steps) > limit:
            raise WorkflowExecutionError(
                f"workflow {definition.id!r} has {len(definition.steps)} steps, exceeding limit {limit}"
            )

        if context is None:
            context_value: dict[str, Any] = {}
        else:
            if not isinstance(context, Mapping):
                raise WorkflowExecutionError("workflow context must be an object")
            try:
                context_value = _canonical_value(context, "workflow context", max_bytes=self.max_context_bytes)
            except CatalogError as exc:
                raise WorkflowExecutionError(str(exc)) from exc

        effective_handlers = dict(self.handlers)
        if handlers is not None:
            # Per-call handlers overlay the injected registry without mutating
            # executor state, so separate calls cannot cross-talk.
            effective_handlers.update(self._copy_handlers(handlers))
        if len(effective_handlers) > MAX_HANDLERS:
            raise WorkflowExecutionError(f"effective handlers cannot exceed {MAX_HANDLERS} entries")
        return self._execute_with_handlers(definition, context_value, limit, effective_handlers)

    def _execute_with_handlers(
        self,
        workflow: WorkflowDescriptor,
        context: Mapping[str, Any],
        limit: int,
        handlers: Mapping[str, StepHandler],
    ) -> WorkflowResult:
        events: list[WorkflowEvent] = []

        def emit(
            event_type: str,
            *,
            step_id: str | None = None,
            status: str | None = None,
            details: Mapping[str, Any] | None = None,
        ) -> None:
            event = WorkflowEvent(
                sequence=len(events),
                type=event_type,
                workflow_id=workflow.id,
                step_id=step_id,
                status=status,
                details=details or {},
            )
            events.append(event)

        emit("workflow_started", details={"step_count": len(workflow.steps)})
        results: dict[str, StepResult] = {}
        step_results: list[StepResult] = []
        failed_step: str | None = None
        failure_error: Mapping[str, Any] | None = None
        final_output: Any = None
        total_output_bytes = 0

        for step in workflow.ordered_steps:
            if failed_step is not None:
                skipped = StepResult(
                    step_id=step.id,
                    status="skipped",
                    output=None,
                    error={"code": "blocked_by_failure", "message": f"blocked by failed step {failed_step}"},
                    dependencies=step.depends_on,
                )
                step_results.append(skipped)
                emit("step_skipped", step_id=step.id, status="skipped", details={"blocked_by": failed_step})
                continue

            emit(
                "step_started",
                step_id=step.id,
                status="running",
                details={
                    "handler": step.handler or step.id,
                    "dependencies": list(step.depends_on),
                },
            )
            handler = self._resolve_handler(workflow, step, handlers)
            if step.capability is not None and not self.catalog.get_capability(step.capability).available:
                status = "failed"
                output = None
                error: Mapping[str, Any] | None = {
                    "code": "capability_unavailable",
                    "message": f"capability {step.capability!r} is unavailable",
                }
            elif handler is None:
                status = "failed"
                output = None
                error = {
                    "code": "handler_not_found",
                    "message": f"no handler registered for step {step.id!r}",
                }
            else:
                try:
                    raw_result = self._invoke_handler(
                        handler,
                        workflow=workflow,
                        step=step,
                        context=dict(context),
                        results=dict(results),
                    )
                except WorkflowStepTimeout as exc:
                    status = "failed"
                    output = None
                    error = {
                        "code": "handler_timeout",
                        "type": type(exc).__name__,
                        "message": str(exc)[:4096],
                        "uncertain": True,
                    }
                except Exception as exc:  # handlers are an injected boundary
                    status = "failed"
                    output = None
                    error = {
                        "code": "handler_exception",
                        "type": type(exc).__name__,
                        "message": str(exc)[:4096],
                    }
                else:
                    status, output, error = self._normalise_handler_result(raw_result, step=step)

            if status == "succeeded":
                try:
                    output_size = len(_canonical_json({"output": output}).encode("utf-8"))
                except CatalogError as exc:
                    status = "failed"
                    output = None
                    error = {"code": "invalid_handler_result", "message": str(exc)}
                else:
                    total_output_bytes += output_size
                    if total_output_bytes > self.max_total_bytes:
                        status = "failed"
                        output = None
                        error = {
                            "code": "execution_budget_exceeded",
                            "message": "workflow output exceeds the configured total bound",
                        }
            if status == "succeeded":
                result = StepResult(
                    step_id=step.id,
                    status="succeeded",
                    output=output,
                    dependencies=step.depends_on,
                )
                results[step.id] = result
                step_results.append(result)
                final_output = output
                emit(
                    "step_completed",
                    step_id=step.id,
                    status="succeeded",
                    details={"output": output},
                )
            elif status == "skipped":
                result = StepResult(
                    step_id=step.id,
                    status="skipped",
                    output=None,
                    error=error,
                    dependencies=step.depends_on,
                )
                step_results.append(result)
                emit("step_skipped", step_id=step.id, status="skipped", details={"reason": "handler_skipped"})
                if failed_step is None:
                    failed_step = step.id
                    failure_error = error or {"code": "step_skipped", "message": "step was skipped"}
            else:
                result = StepResult(
                    step_id=step.id,
                    status="failed",
                    output=None,
                    error=error,
                    dependencies=step.depends_on,
                )
                step_results.append(result)
                if failed_step is None:
                    failed_step = step.id
                    failure_error = error
                emit("step_failed", step_id=step.id, status="failed", details={"error": error or {}})

        if failed_step is not None:
            emit(
                "workflow_failed",
                status="failed",
                details={"failed_step": failed_step, "error": failure_error or {}},
            )
            return WorkflowResult(
                workflow_id=workflow.id,
                status="failed",
                output=None,
                steps=tuple(step_results),
                events=tuple(events),
                error=failure_error or {"code": "workflow_failed", "message": "workflow failed"},
            )

        emit("workflow_completed", status="succeeded", details={"output": final_output})
        return WorkflowResult(
            workflow_id=workflow.id,
            status="succeeded",
            output=final_output,
            steps=tuple(step_results),
            events=tuple(events),
        )

    # Natural aliases for hosts and older experimental callers.
    run = execute
    execute_workflow = execute


SequentialWorkflowExecutor = WorkflowExecutor
BoundedWorkflowExecutor = WorkflowExecutor


__all__ = [
    "EVENT_TYPES",
    "RESULT_STATUSES",
    "MAX_EXECUTION_BYTES",
    "MAX_HANDLERS",
    "WorkflowExecutionError",
    "StepExecutionError",
    "WorkflowCatalog",
    "CapabilityDescriptor",
    "AgentDescriptor",
    "WorkflowDescriptor",
    "WorkflowStepDescriptor",
    "WorkflowEvent",
    "StepResult",
    "WorkflowStepResult",
    "WorkflowResult",
    "WorkflowExecutionResult",
    "WorkflowExecutionEvent",
    "StepInvocation",
    "StepContext",
    "WorkflowContext",
    "StepHandler",
    "WorkflowExecutor",
    "SequentialWorkflowExecutor",
    "BoundedWorkflowExecutor",
]
