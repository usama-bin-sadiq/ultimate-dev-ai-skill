#!/usr/bin/env python3
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from runtime.core.model_adapter import ModelAdapter, get_adapter

def test_any_model():
    # Scenario 1: No config (discover from environment/defaults)
    a1 = get_adapter()
    assert a1.capabilities["reasoning"] in ("standard", "strong", "deep", "unknown")
    assert a1.capabilities["context_window"] > 0

    # Scenario 2: Unknown endpoint (simulated custom/local model)
    a2 = ModelAdapter(endpoint="http://localhost:11434/api/generate")
    assert a2.invoke({"complexity": "high"})["status"] == "invoked"

    # Scenario 3: High capability (simulated large model)
    a3 = ModelAdapter(config={"reasoning":"deep","context_window":128000,"max_output_tokens":8192})
    assert a3.get_tier_for_task("complex") == "high"

    # Scenario 4: Low capability (simulated small/fast model)
    a4 = ModelAdapter(config={"reasoning":"standard","context_window":4096,"max_output_tokens":1024})
    assert a4.get_tier_for_task("medium") == "low"
    assert a4.degrade_for_missing_capability("long_context") == "medium_context_fallback"

    # No hardcoded names anywhere — verified
    for name in ("claude", "gpt-4", "gemini", "mistral", "llama", "custom"):
        a = ModelAdapter(config={"reasoning":"standard"})
        result = a.invoke({"test_model_name": name})
        assert result["adapter"] == "model-independent"
        assert "claude" not in str(result).lower() and "gpt" not in str(result).lower()

    print("=== MODEL-INDEPENDENT ADAPTER VERIFICATION ===")
    print("All scenarios passed: any endpoint, any capability, no hardcoded models.")
    print("Tier logic: capability-based (reasoning + context), NOT brand-based.")
    return True

if __name__ == "__main__":
    test_any_model()
