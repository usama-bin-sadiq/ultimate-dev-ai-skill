"""Unified Task Engine: the single orchestrator for every execution mode.

This is deliberately the only place in the runtime that schedules work. A
workflow is a reusable graph template, an agent is a specialised executor, and
an execution mode is a graph shape. None of them may grow a second scheduler.

The engine is dependency-free and deterministic for a given graph: node
completion order is a topological sort, and parallel branches never share
mutable scheduler state.

Honest scope: this engine schedules, validates, retries, gates, and reports. It
does not decide which graph is justified. That is JEV's responsibility, and
``decide_mode`` below only reports the mode a finished graph used.
"""
from __future__ import annotations

import threading
import time
from concurrent.futures import FIRST_COMPLETED, Future, ThreadPoolExecutor, wait
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Iterable, Mapping, Sequence

VALID_TYPES = frozenset({"leaf", "decision", "parallel", "loop", "approval", "terminal"})
VALID_EDGES = frozenset(
    {"dependency", "data", "control", "approval", "verification", "failure", "recovery"}
)
VALID_RISKS = frozenset({"none", "data", "security", "compliance"})
VALID_APPROVALS = frozenset({"not_required", "recommended", "required", "human_review"})


class TaskGraphError(ValueError):
    """The graph is structurally invalid and must not be executed."""


class GraphCancelled(RuntimeError):
    """Execution was cancelled before the graph reached a terminal state."""


class NodeStatus(str, Enum):
    PENDING = "pending"
    BLOCKED = "blocked"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    CANCELLED = "cancelled"


class Verdict(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    INCONCLUSIVE = "INCONCLUSIVE"


@dataclass(frozen=True)
class TaskNode:
    """One unit of work. The objective is what makes the node verifiable."""

    id: str
    objective: str
    type: str = "leaf"
    dependencies: tuple[str, ...] = ()
    skill: str | None = None
    subskills: tuple[str, ...] = ()
    agent: str | None = None
    capabilities: tuple[str, ...] = ()
    inputs: Mapping[str, Any] = field(default_factory=dict)
    outputs: Mapping[str, Any] = field(default_factory=dict)
    risk: str = "none"
    approval: str = "not_required"
    verification: tuple[str, ...] = ()
    evidence: tuple[str, ...] = ()
    retry: Mapping[str, Any] = field(default_factory=lambda: {"max_attempts": 1, "idempotent": True})
    rollback: str | None = None
    timeout: float | None = None
    checkpoint: bool = False

    def validate(self) -> list[str]:
        problems: list[str] = []
        if not self.id.strip():
            problems.append("node id must be non-empty")
        if not self.objective.strip():
            problems.append(f"{self.id}: objective is required so the node can be verified")
        if self.type not in VALID_TYPES:
            problems.append(f"{self.id}: unknown type {self.type!r}")
        if self.risk not in VALID_RISKS:
            problems.append(f"{self.id}: unknown risk {self.risk!r}")
        if self.approval not in VALID_APPROVALS:
            problems.append(f"{self.id}: unknown approval {self.approval!r}")
        if not self.retry.get("idempotent", False) and int(self.retry.get("max_attempts", 1)) > 1:
            problems.append(
                f"{self.id}: retry is only permitted when the node is idempotent or declares a rollback"
            )
        return problems


@dataclass(frozen=True)
class TaskEdge:
    source: str
    target: str
    type: str = "dependency"
    condition: Callable[[Mapping[str, Any]], bool] | None = None

    def validate(self) -> list[str]:
        if self.type not in VALID_EDGES:
            return [f"edge {self.source}->{self.target}: unknown edge type {self.type!r}"]
        if self.type == "control" and self.condition is None:
            return [f"edge {self.source}->{self.target}: a control edge requires a condition"]
        return []


class TaskGraph:
    """An acyclic graph of :class:`TaskNode` with typed edges."""

    def __init__(self, name: str = "graph", parallelism: int = 4) -> None:
        self.name = name
        self.parallelism = max(1, int(parallelism))
        self._nodes: dict[str, TaskNode] = {}
        self._edges: list[TaskEdge] = []
        self._lock = threading.Lock()

    # ---------------------------------------------------------------- building
    def add_node(self, node: TaskNode) -> "TaskGraph":
        problems = node.validate()
        if problems:
            raise TaskGraphError("; ".join(problems))
        with self._lock:
            if node.id in self._nodes:
                raise TaskGraphError(f"duplicate node id {node.id!r}")
            self._nodes[node.id] = node
        return self

    def add_edge(self, edge: TaskEdge) -> "TaskGraph":
        problems = edge.validate()
        if problems:
            raise TaskGraphError("; ".join(problems))
        self._edges.append(edge)
        return self

    def chain(self, *node_ids: str, edge_type: str = "dependency") -> "TaskGraph":
        """Link nodes in order. Convenience for the common linear case."""
        for source, target in zip(node_ids, node_ids[1:]):
            self.add_edge(TaskEdge(source, target, edge_type))
        return self

    @property
    def nodes(self) -> Mapping[str, TaskNode]:
        return dict(self._nodes)

    @property
    def edges(self) -> Sequence[TaskEdge]:
        return tuple(self._edges)

    # ------------------------------------------------------------- validation
    def validate(self) -> None:
        """Raise :class:`TaskGraphError` if the graph must not be executed."""
        problems: list[str] = []
        for node in self._nodes.values():
            problems.extend(node.validate())
        for edge in self._edges:
            problems.extend(edge.validate())
            if edge.source not in self._nodes:
                problems.append(f"edge references unknown source {edge.source!r}")
            if edge.target not in self._nodes:
                problems.append(f"edge references unknown target {edge.target!r}")
        for node in self._nodes.values():
            for dependency in node.dependencies:
                if dependency not in self._nodes:
                    problems.append(f"{node.id}: unknown dependency {dependency!r}")
                if dependency == node.id:
                    problems.append(f"{node.id}: cannot depend on itself")
        order = self._topological_order(problems)
        if order is None:
            problems.append("graph contains a cycle")
        if problems:
            raise TaskGraphError("; ".join(problems))

    def _topological_order(self, sink: list[str]) -> list[str] | None:
        """Kahn's algorithm. Returns None when a cycle remains."""
        indegree: dict[str, int] = {node_id: 0 for node_id in self._nodes}
        for node in self._nodes.values():
            for dependency in node.dependencies:
                if dependency in indegree:
                    indegree[node.id] += 1
        for edge in self._edges:
            if edge.type in {"dependency", "data", "verification"} and edge.target in indegree:
                indegree[edge.target] += 1
        ready = sorted(node_id for node_id, count in indegree.items() if count == 0)
        order: list[str] = []
        while ready:
            current = ready.pop(0)
            order.append(current)
            for node_id in sorted(self._nodes):
                blocked = set(self._nodes[node_id].dependencies)
                blocked |= {e.source for e in self._edges if e.type in {"dependency", "data", "verification"} and e.target == node_id}
                if current in blocked and node_id in indegree:
                    indegree[node_id] -= 1
                    if indegree[node_id] == 0:
                        ready.append(node_id)
                        ready.sort()
        if len(order) != len(self._nodes):
            sink.append("graph contains a cycle")
            return None
        return order

    def execution_order(self) -> list[str]:
        self.validate()
        order = self._topological_order([])
        assert order is not None
        return order

    # ----------------------------------------------------------------- running
    def _blocked_by(self, node_id: str) -> set[str]:
        blocked = set(self._nodes[node_id].dependencies)
        for edge in self._edges:
            if edge.target == node_id and edge.type in {"dependency", "data", "verification"}:
                blocked.add(edge.source)
        return blocked

    def run(
        self,
        execute: Callable[[TaskNode, Mapping[str, Any]], Any],
        verify: Callable[[TaskNode, Any, str], Verdict] | None = None,
        approve: Callable[[TaskNode], str] | None = None,
        recover: Callable[[TaskNode, BaseException], Any] | None = None,
        checkpoint: Callable[[TaskNode, str], None] | None = None,
        context: Mapping[str, Any] | None = None,
        on_event: Callable[[str, TaskNode, str], None] | None = None,
    ) -> dict[str, Any]:
        """Execute the graph and return an auditable result.

        Returns a mapping with ``status`` (completed | partial | failed |
        cancelled), per-node statuses, the evidence trail, and the approval
        decisions that were actually taken. A node is only ``completed`` when
        its executable ran and its verifier passed; an ``INCONCLUSIVE`` verdict
        never completes a node.
        """
        self.validate()
        base_context = dict(context or {})
        status: dict[str, str] = {node_id: NodeStatus.PENDING.value for node_id in self._nodes}
        results: dict[str, Any] = {}
        trail: list[dict[str, Any]] = []
        approvals: dict[str, str] = {}
        remaining = set(self._nodes)
        cancel = threading.Event()
        clock = threading.local()
        # Futures still in flight across scheduling iterations. A node already
        # RUNNING must never be submitted again: it has no unmet dependencies
        # (`all([])` is True), so dropping this map would re-run it.
        inflight: dict[Future, TaskNode] = {}

        def emit(event: str, node: TaskNode, note: str = "") -> None:
            if on_event is not None:
                on_event(event, node, note)

        def run_node(node: TaskNode) -> tuple[str, Any, list[dict[str, Any]]]:
            """Run one node to a terminal-ish status. Never raises."""
            notes: list[dict[str, Any]] = []
            if node.approval in {"required", "human_review"}:
                if approve is None:
                    notes.append({"type": "approval", "decision": "unavailable", "blocking": True})
                    return NodeStatus.FAILED.value, None, notes
                decision = approve(node)
                approvals[node.id] = decision
                notes.append({"type": "approval", "decision": decision, "blocking": False})
                if decision not in {"approved", "allow"}:
                    return NodeStatus.SKIPPED.value, None, notes

            payload: dict[str, Any] = dict(base_context)
            for name, source in node.inputs.items():
                if source in results:
                    payload[name] = results[source]

            attempts = int(node.retry.get("max_attempts", 1))
            backoff = float(node.retry.get("backoff_seconds", 0))
            last: BaseException | None = None
            for attempt in range(1, attempts + 1):
                if cancel.is_set():
                    return NodeStatus.CANCELLED.value, None, notes
                try:
                    value = execute(node, payload)
                except BaseException as exc:  # noqa: BLE001 - recorded, not swallowed
                    last = exc
                    notes.append({"type": "attempt", "n": attempt, "error": repr(exc)})
                    if recover is not None and attempt == attempts:
                        try:
                            value = recover(node, exc)
                            notes.append({"type": "recovery", "applied": True})
                            last = None
                        except BaseException as recovery_error:  # noqa: BLE001
                            notes.append({"type": "recovery", "applied": False, "error": repr(recovery_error)})
                            return NodeStatus.FAILED.value, None, notes
                    if attempt < attempts and backoff:
                        time.sleep(backoff)
                    continue

                if verify is not None:
                    for verifier in node.verification or ("default",):
                        verdict = verify(node, value, verifier)
                        notes.append({"type": "verification", "verifier": verifier, "verdict": verdict.value})
                        if verdict is Verdict.FAIL:
                            return NodeStatus.FAILED.value, value, notes
                        if verdict is Verdict.INCONCLUSIVE:
                            return NodeStatus.BLOCKED.value, value, notes
                return NodeStatus.COMPLETED.value, value, notes

            if last is not None and recover is not None:
                try:
                    value = recover(node, last)
                    notes.append({"type": "recovery", "applied": True})
                    return NodeStatus.COMPLETED.value, value, notes
                except BaseException as recovery_error:  # noqa: BLE001
                    notes.append({"type": "recovery", "applied": False, "error": repr(recovery_error)})
            return NodeStatus.FAILED.value, None, notes

        pool = ThreadPoolExecutor(max_workers=self.parallelism, thread_name_prefix="taskgraph")
        try:
            while remaining:
                if cancel.is_set():
                    for node_id in sorted(remaining):
                        if status[node_id] == NodeStatus.PENDING.value:
                            status[node_id] = NodeStatus.CANCELLED.value
                    break

                failed_deps: set[str] = set()
                for node_id, value in status.items():
                    if value in {NodeStatus.FAILED.value, NodeStatus.CANCELLED.value, NodeStatus.SKIPPED.value}:
                        failed_deps |= self._downstream(node_id)

                runnable: list[TaskNode] = []
                for node_id in sorted(remaining):
                    if status[node_id] != NodeStatus.PENDING.value:
                        continue  # already running, done, or resolved
                    node = self._nodes[node_id]
                    blocked = self._blocked_by(node_id)
                    if any(status.get(b) in {NodeStatus.FAILED.value, NodeStatus.SKIPPED.value} for b in blocked):
                        status[node_id] = NodeStatus.SKIPPED.value
                        emit("skipped", node, "upstream did not complete")
                        remaining.discard(node_id)
                        continue
                    if node_id in failed_deps and status[node_id] == NodeStatus.PENDING.value:
                        if not any(e.type == "failure" and e.source in self._nodes for e in self._edges if e.target == node_id):
                            pass
                    if all(status.get(b) == NodeStatus.COMPLETED.value for b in blocked):
                        if not self._conditions_hold(node_id, results, base_context):
                            if any(e.type == "control" and e.target == node_id for e in self._edges):
                                status[node_id] = NodeStatus.SKIPPED.value
                                emit("skipped", node, "control condition not met")
                                remaining.discard(node_id)
                                continue
                        runnable.append(node)
                        status[node_id] = NodeStatus.RUNNING.value

                if not runnable and not inflight:
                    for node_id in sorted(remaining):
                        if status[node_id] == NodeStatus.PENDING.value:
                            status[node_id] = NodeStatus.BLOCKED.value
                            emit("blocked", self._nodes[node_id], "unresolvable dependencies")
                    break

                for node in runnable:
                    inflight[pool.submit(run_node, node)] = node
                done, _ = wait(inflight, return_when=FIRST_COMPLETED)
                for future in done:
                    node = inflight.pop(future)
                    try:
                        node_status, value, notes = future.result()
                    except BaseException as exc:  # noqa: BLE001
                        node_status, value, notes = NodeStatus.FAILED.value, None, [{"type": "error", "error": repr(exc)}]
                    status[node.id] = node_status
                    remaining.discard(node.id)
                    if value is not None:
                        results[node.id] = value
                    trail.extend({"node": node.id, **note} for note in notes)
                    emit(node_status, node)
                    if checkpoint is not None and node_status in {
                        NodeStatus.COMPLETED.value,
                        NodeStatus.FAILED.value,
                    }:
                        checkpoint(node, node_status)
        finally:
            pool.shutdown(wait=True)

        return summarise(self.name, status, results, trail, approvals, cancel.is_set())


# --------------------------------------------------------------------- helpers
def _downstream(graph: TaskGraph, node_id: str) -> set[str]:
    """Every node transitively waiting on ``node_id``."""
    seen: set[str] = set()
    frontier = [node_id]
    while frontier:
        current = frontier.pop()
        for edge in graph.edges:
            if edge.source == current and edge.target not in seen:
                seen.add(edge.target)
                frontier.append(edge.target)
    return seen


def _conditions(graph: TaskGraph, node_id: str, results: Mapping[str, Any], context: Mapping[str, Any]) -> bool:
    for edge in graph.edges:
        if edge.target == node_id and edge.type == "control" and edge.condition is not None:
            if not edge.condition({**context, **results}):
                return False
    return True


TaskGraph._downstream = lambda self, node_id: _downstream(self, node_id)  # type: ignore[attr-defined]
TaskGraph._conditions_hold = (  # type: ignore[attr-defined]
    lambda self, node_id, results, context: _conditions(self, node_id, results, context)
)


def summarise(
    name: str,
    status: Mapping[str, str],
    results: Mapping[str, Any],
    trail: Sequence[Mapping[str, Any]],
    approvals: Mapping[str, str],
    cancelled: bool,
) -> dict[str, Any]:
    """Reduce per-node status to one auditable result. Never reports success for work that did not run."""
    completed = [node_id for node_id, value in status.items() if value == NodeStatus.COMPLETED.value]
    failed = [node_id for node_id, value in status.items() if value == NodeStatus.FAILED.value]
    blocked = [node_id for node_id, value in status.items() if value == NodeStatus.BLOCKED.value]
    skipped = [node_id for node_id, value in status.items() if value == NodeStatus.SKIPPED.value]
    cancelled_nodes = [node_id for node_id, value in status.items() if value == NodeStatus.CANCELLED.value]

    if cancelled or cancelled_nodes:
        overall = "cancelled"
    elif failed:
        overall = "failed"
    elif blocked or skipped:
        overall = "partial" if completed else "not_run"
    else:
        overall = "completed" if completed else "not_run"

    verifications = [note for note in trail if note.get("type") == "verification"]
    inconclusive = [note for note in verifications if note.get("verdict") == Verdict.INCONCLUSIVE.value]

    return {
        "graph": name,
        "status": overall,
        "node_status": dict(status),
        "completed": sorted(completed),
        "failed": sorted(failed),
        "blocked": sorted(blocked),
        "skipped": sorted(skipped),
        "cancelled_nodes": sorted(cancelled_nodes),
        "results": dict(results),
        "trail": [dict(note) for note in trail],
        "approvals": dict(approvals),
        "verification_counts": {
            Verdict.PASS.value: sum(1 for note in verifications if note.get("verdict") == Verdict.PASS.value),
            Verdict.FAIL.value: sum(1 for note in verifications if note.get("verdict") == Verdict.FAIL.value),
            Verdict.INCONCLUSIVE.value: len(inconclusive),
        },
    }
