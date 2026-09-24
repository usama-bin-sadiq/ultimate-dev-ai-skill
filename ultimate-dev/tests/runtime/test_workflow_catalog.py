"""Focused tests for the host-neutral workflow/catalog authority."""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from runtime.core.registry import (
    AgentDescriptor,
    CapabilityDescriptor,
    CatalogError,
    ReferenceError as CatalogReferenceError,
    WorkflowCatalog,
    WorkflowDescriptor,
    WorkflowStepDescriptor,
)
from runtime.core.workflow import WorkflowExecutionError, WorkflowExecutor


class WorkflowCatalogTests(unittest.TestCase):
    def setUp(self) -> None:
        self.capability = CapabilityDescriptor(
            id="tool.read",
            description="Read a value",
            input_schema={"type": "object", "properties": {"path": {"type": "string"}}},
            output_schema={"type": "object"},
            effects=("read",),
        )
        self.agent = AgentDescriptor(
            id="reader",
            description="Reads values",
            capabilities=("tool.read",),
        )
        self.workflow = WorkflowDescriptor(
            id="ordered",
            description="A deterministic ordered workflow",
            steps=(
                WorkflowStepDescriptor(
                    id="finish",
                    description="Use the prepared value",
                    agent="reader",
                    capability="tool.read",
                    depends_on=("prepare",),
                ),
                WorkflowStepDescriptor(
                    id="prepare",
                    description="Prepare the value",
                    agent="reader",
                    capability="tool.read",
                ),
            ),
        )
        self.catalog = WorkflowCatalog(
            capabilities=(self.capability,),
            agents=(self.agent,),
            workflows=(self.workflow,),
        )

    def test_catalog_is_canonical_and_json_round_trippable(self) -> None:
        encoded = self.catalog.to_json()
        restored = WorkflowCatalog.from_json(encoded)
        self.assertEqual(restored.to_json(), encoded)
        self.assertEqual(restored.fingerprint(), self.catalog.fingerprint())
        self.assertEqual([item.id for item in restored.capabilities], ["tool.read"])
        self.assertEqual(restored.get_workflow("ordered").execution_order(), ("prepare", "finish"))
        self.assertEqual(json.loads(encoded)["schema_version"], "1.0")

    def test_invalid_references_fail_closed(self) -> None:
        with self.assertRaises(CatalogReferenceError):
            WorkflowCatalog(
                agents=(AgentDescriptor(id="reader", description="Reader", capabilities=("missing.tool",)),)
            )

        with self.assertRaises(CatalogReferenceError):
            WorkflowCatalog(
                capabilities=(self.capability,),
                workflows=(
                    WorkflowDescriptor(
                        id="bad-agent",
                        description="References an unknown agent",
                        steps=(WorkflowStepDescriptor(id="one", agent="ghost"),),
                    ),
                ),
            )

        with self.assertRaises(CatalogReferenceError):
            WorkflowCatalog(
                workflows=(
                    WorkflowDescriptor(
                        id="bad-capability",
                        description="References an unknown capability",
                        steps=(WorkflowStepDescriptor(id="one", capability="ghost.tool"),),
                    ),
                )
            )

        with self.assertRaises(CatalogError):
            WorkflowCatalog.from_dict(
                {
                    "schema_version": "1.0",
                    "capabilities": [],
                    "agents": [],
                    "workflows": [],
                    "unexpected": True,
                }
            )

    def test_registration_rolls_back_an_unresolved_reference(self) -> None:
        with self.assertRaises(CatalogReferenceError):
            self.catalog.register_agent(
                AgentDescriptor(id="broken", description="Broken", capabilities=("missing.tool",))
            )
        self.assertEqual(self.catalog.agents, (self.agent,))

    def test_standalone_workflow_references_are_checked_by_executor(self) -> None:
        standalone = WorkflowDescriptor(
            id="standalone",
            description="Must not bypass catalog references",
            steps=(WorkflowStepDescriptor(id="one", agent="ghost"),),
        )
        with self.assertRaises(CatalogReferenceError):
            WorkflowExecutor(self.catalog).execute(standalone)

    def test_dependency_order_is_stable_and_dependencies_reach_handlers(self) -> None:
        calls: list[str] = []

        def prepare(context, dependencies):
            calls.append("prepare")
            self.assertEqual(dependencies, {})
            return {"value": 7}

        def finish(context, dependencies):
            calls.append("finish")
            return {"value": dependencies["prepare"]["value"] + 1}

        result = WorkflowExecutor(
            self.catalog,
            handlers={"prepare": prepare, "finish": finish},
        ).execute("ordered", context={"request": "x"})

        self.assertTrue(result.success)
        self.assertEqual(calls, ["prepare", "finish"])
        self.assertEqual(result.output, {"value": 8})
        self.assertEqual(result.steps[0].step_id, "prepare")
        self.assertEqual(result.steps[1].step_id, "finish")

    def test_results_and_events_are_deterministic_across_executions(self) -> None:
        def first():
            return {"b": 2, "a": 1}

        def second():
            return ["done"]

        handlers = {"prepare": first, "finish": second}
        first_result = WorkflowExecutor(self.catalog, handlers=handlers).execute("ordered")
        second_result = WorkflowExecutor(self.catalog, handlers=handlers).execute("ordered")

        self.assertEqual(first_result.to_dict(), second_result.to_dict())
        self.assertEqual(
            [event.to_dict() for event in first_result.events],
            [event.to_dict() for event in second_result.events],
        )
        self.assertEqual(
            [event.sequence for event in first_result.events],
            list(range(len(first_result.events))),
        )
        self.assertEqual(
            [event.type for event in first_result.events],
            [
                "workflow_started",
                "step_started",
                "step_completed",
                "step_started",
                "step_completed",
                "workflow_completed",
            ],
        )

    def test_missing_handler_is_a_structured_fail_closed_result(self) -> None:
        result = WorkflowExecutor(self.catalog).execute("ordered")
        self.assertFalse(result.success)
        self.assertEqual(result.status, "failed")
        self.assertEqual(result.steps[0].status, "failed")
        self.assertEqual(result.steps[0].error["code"], "handler_not_found")
        self.assertEqual(result.steps[1].status, "skipped")
        self.assertEqual(result.events[-1].type, "workflow_failed")

    def test_executor_rejects_workflows_over_its_bound(self) -> None:
        with self.assertRaises(WorkflowExecutionError):
            WorkflowExecutor(self.catalog, max_steps=1).execute("ordered")

    def test_executor_enforces_total_output_bound(self) -> None:
        result = WorkflowExecutor(
            self.catalog,
            handlers={"prepare": lambda: {"value": "x" * 100}, "finish": lambda: {"value": "y" * 100}},
            max_total_bytes=32,
        ).execute("ordered")
        self.assertFalse(result.success)
        self.assertEqual(result.steps[0].error["code"], "execution_budget_exceeded")

    def test_unavailable_capability_does_not_call_handler(self) -> None:
        calls: list[str] = []

        def unavailable_handler():
            calls.append("called")
            return {"ok": True}

        capability = CapabilityDescriptor(
            id="tool.read",
            description="Unavailable",
            available=False,
        )
        workflow = WorkflowDescriptor(
            id="unavailable",
            description="Must fail closed",
            steps=(WorkflowStepDescriptor(id="one", capability="tool.read"),),
        )
        result = WorkflowExecutor(
            WorkflowCatalog(capabilities=(capability,), workflows=(workflow,)),
            handlers={"one": unavailable_handler},
        ).execute("unavailable")
        self.assertFalse(result.success)
        self.assertEqual(result.steps[0].error["code"], "capability_unavailable")
        self.assertEqual(calls, [])

    def test_handler_exception_is_structured(self) -> None:
        def explode():
            raise RuntimeError("host unavailable")

        result = WorkflowExecutor(self.catalog, handlers={"prepare": explode}).execute("ordered")
        self.assertFalse(result.success)
        self.assertEqual(result.steps[0].error["code"], "handler_exception")
        self.assertEqual(result.steps[0].error["type"], "RuntimeError")
        self.assertEqual(result.events[-1].type, "workflow_failed")


if __name__ == "__main__":
    unittest.main()
