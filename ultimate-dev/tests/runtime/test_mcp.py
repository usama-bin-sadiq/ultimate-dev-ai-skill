import unittest

from runtime.core.capabilities import CapabilityRegistry
from runtime.core.mcp import MCPAdapter, MCPToolMalformed


class FakeTransport:
    def __init__(self, *, fail=False, result=None):
        self.fail = fail
        self.result = result if result is not None else {"structuredContent": {"value": 42}}
        self.calls = []

    def discover(self):
        if self.fail:
            raise RuntimeError("offline")
        return {"name": "fake", "version": "1"}

    def list_tools(self):
        if self.fail:
            raise RuntimeError("offline")
        return {
            "tools": [
                {
                    "name": "read_value",
                    "capabilityId": "filesystem.read",
                    "description": "Read a value",
                    "inputSchema": {
                        "type": "object",
                        "properties": {"key": {"type": "string"}},
                        "required": ["key"],
                        "additionalProperties": False,
                    },
                    "outputSchema": {
                        "type": "object",
                        "properties": {"value": {"type": "number"}},
                        "required": ["value"],
                    },
                    "trust": "verified",
                    "effects": ["read"],
                }
            ]
        }

    def call_tool(self, name, arguments):
        self.calls.append((name, arguments))
        return self.result


class MCPAdapterTests(unittest.TestCase):
    def test_discovery_and_schema_validated_call(self):
        transport = FakeTransport()
        adapter = MCPAdapter(transport)
        tools = adapter.discover()
        self.assertEqual(tools[0].name, "read_value")
        result = adapter.call_tool("read_value", {"key": "x"})
        self.assertEqual(result.status, "success")
        self.assertEqual(result.result, {"value": 42})
        self.assertEqual(transport.calls, [("read_value", {"key": "x"})])

    def test_invalid_input_fails_before_transport(self):
        transport = FakeTransport()
        adapter = MCPAdapter(transport)
        result = adapter.call_tool("read_value", {"wrong": 1})
        self.assertEqual(result.status, "rejected")
        self.assertEqual(result.error_code, "mcp_input_invalid")
        self.assertEqual(transport.calls, [])

    def test_untrusted_tool_requires_explicit_opt_in(self):
        class UntrustedTransport(FakeTransport):
            def list_tools(self):
                value = super().list_tools()
                value["tools"][0]["trust"] = "untrusted"
                return value

        adapter = MCPAdapter(UntrustedTransport())
        self.assertEqual(adapter.call_tool("read_value", {"key": "x"}).status, "review")
        self.assertEqual(adapter.call_tool("read_value", {"key": "x"}, allow_untrusted=True).status, "success")

    def test_fallback_is_explicit_and_equivalent_only(self):
        calls = []

        class UnavailableCallTransport(FakeTransport):
            def call_tool(self, name, arguments):
                raise RuntimeError("offline call")

        transport = UnavailableCallTransport()
        adapter = MCPAdapter(
            transport,
            fallback=lambda name, args: calls.append((name, args)) or {"value": 7},
            fallback_equivalent=True,
        )
        result = adapter.call_tool("read_value", {"key": "x"}, allow_fallback=True)
        self.assertEqual(result.status, "failed")
        self.assertEqual(calls, [])

        class MCPUnavailableTransport(FakeTransport):
            def call_tool(self, name, arguments):
                from runtime.core.mcp import MCPUnavailable
                raise MCPUnavailable("offline")

        transport = MCPUnavailableTransport()
        result = adapter = MCPAdapter(
            transport,
            fallback=lambda name, args: calls.append((name, args)) or {"value": 7},
            fallback_equivalent=True,
        ).call_tool("read_value", {"key": "x"}, allow_fallback=True)
        self.assertEqual(result.status, "success")
        self.assertTrue(result.provenance["fallback"])
        self.assertEqual(calls, [("read_value", {"key": "x"})])

        def broken_fallback(name, args):
            raise RuntimeError("no fallback")

        no_fallback = MCPAdapter(transport, fallback=broken_fallback)
        self.assertEqual(no_fallback.call_tool("read_value", {"key": "x"}, allow_fallback=True).status, "unavailable")

    def test_explicit_capability_ids_can_feed_the_runtime_registry(self):
        registry = CapabilityRegistry()
        registered = MCPAdapter(FakeTransport()).register_into(registry, allow_untrusted=True)
        self.assertEqual(registered, ["filesystem.read"])
        capability = registry.get("filesystem.read")
        self.assertIsNotNone(capability)
        result = capability.execute(arguments={"key": "x"})
        self.assertTrue(result["success"])
        self.assertEqual(result["result"], {"value": 42})

    def test_health_and_tasks_report_optional_capability(self):
        adapter = MCPAdapter(FakeTransport())
        self.assertTrue(adapter.health()["available"])
        unavailable = adapter.start_task("read_value", {"key": "x"})
        self.assertEqual(unavailable.status, "unavailable")
        self.assertEqual(unavailable.error_code, "mcp_tasks_unavailable")

    def test_malformed_tool_descriptor_fails_closed(self):
        class BadTransport(FakeTransport):
            def list_tools(self):
                return {"tools": [{"name": "bad", "inputSchema": {"type": "string"}, "description": "bad", "effects": []}]}

        with self.assertRaises(MCPToolMalformed):
            MCPAdapter(BadTransport()).discover()


if __name__ == "__main__":
    unittest.main()
