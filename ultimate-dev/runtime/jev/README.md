# JEV Host-Native Decision Kernel

JEV is the deterministic policy boundary used by Ultimate-Dev between model
intent and host capability execution.

It is **not** a model, orchestrator, sandbox, browser, installer, or service.
It accepts a structured request, evaluates the NOUL/CHOICE/SCORE heads, and
returns a decision packet. The Ultimate-Dev Runtime persists the packet and
remains responsible for state, confirmation, execution, evidence, and recovery.

## Contract

| Artifact | Purpose |
|---|---|
| `../schemas/jev-decision-request.schema.json` | Versioned request contract |
| `../schemas/jev-decision-packet.schema.json` | Versioned result contract |
| `../jev-policy.json` | Example host policy snapshot |
| `engine.mjs` | Dependency-free reference implementation |

The JSON Schemas are canonical. `engine.mjs` is a portable reference for hosts
that already have a JavaScript runtime; another host may implement the same
rules in its native language. Neither path requires a package manager.

## Request shape

The model supplies an assessment and a capability proposal:

```json
{
  "schema_version": "1.0",
  "task_id": "task-123",
  "orchestration_state": {
    "state_id": "state-1",
    "pattern": "inline",
    "phase": "plan",
    "environment": "development",
    "completed_step_ids": [],
    "pending_step_ids": ["inspect"]
  },
  "model_assessment": {
    "signals": {
      "urgent": false,
      "destructive": false,
      "policy_sensitive": false,
      "human_approval_required": false,
      "evidence_required": false
    },
    "choice": {
      "pattern": "inline",
      "task_size": "atomic",
      "preferred_path": "lightweight",
      "primary_domain": "testing",
      "rationale": "A bounded read-only inspection."
    },
    "scores": {
      "risk": 0.1,
      "complexity": 0.1,
      "urgency": 0,
      "confidence": 0.9,
      "context_pressure": 0.1
    },
    "proposal": {
      "summary": "Read the relevant source file.",
      "action": {
        "operation": "read",
        "reversibility": "reversible",
        "scope": {
          "description": "One source file",
          "project_root": null,
          "targets": ["src/example.ts"]
        }
      },
      "requested_capabilities": [
        {
          "id": "filesystem.read",
          "required": true,
          "reason": "Inspect the implementation."
        }
      ],
      "effects": ["read"],
      "evidence_refs": ["file:src/example.ts"]
    }
  },
  "host_facts": {
    "capability_catalog_version": "host-1",
    "capability_catalog": [
      {
        "id": "filesystem.read",
        "available": true,
        "reversible": true,
        "isolation": "host_managed",
        "risk": 0.1,
        "effects": ["read"]
      }
    ],
    "policy": {
      "policy_version": "host-policy-1",
      "denied_capability_ids": [],
      "review_capability_ids": [],
      "denied_effects": [],
      "approval_required_effects": ["write", "delete", "network"],
      "isolation_required_effects": ["execute"],
      "thresholds": {
        "review_risk": 0.8,
        "review_confidence": 0.55,
        "flagship_load": 0.7,
        "high_context_pressure": 0.8,
        "deep_complexity": 0.75,
        "deep_confidence": 0.8
      },
      "max_capabilities": 8
    },
    "approvals": []
  }
}
```

`model_assessment` is advisory. `host_facts` is the authority for capability
availability, reversibility, isolation, policy, and approvals. The model must
not mark a capability as available or approved by itself.

## Evaluation order

The reference implementation applies rules in this order:

1. Validate the versioned request and host facts.
2. Reject malformed input with `deny`.
3. Apply forbidden effects/capabilities with `deny` precedence.
4. Report missing required capabilities as `human_review`; never install or
   substitute a provider.
5. Require scoped approval for side effects and review for irreversible,
   policy-sensitive, production, low-confidence, or insufficiently isolated
   actions.
6. Aggregate normalized scores with hard safety floors. Scores are confidence
   and support values, not probabilities.
7. Recommend a lightweight, flagship, human-review, or no-execution path.
8. Select the intersection of requested, available, and policy-allowed
   capability IDs, prioritizing required capabilities within the host budget.
9. Recommend a minimal, standard, or deep context profile.

Precedence is always:

```text
deny > human_review > approve
```

`human_review` is a stop state. It must not be converted into a model-tier
upgrade or an execution fallback.

## Host adapter contract

A host adapter performs the following sequence:

```text
discover native capabilities
  -> build host_facts and policy snapshot
  -> ask the model for model_assessment
  -> call the host's JEV implementation
  -> persist the returned packet
  -> only if execution_effect == "execute", map selected IDs to native tools
  -> verify the result and persist evidence
```

Canonical IDs such as `filesystem.read`, `shell.execute`, and
`browser.navigate` are contracts, not vendor tool names. The adapter owns the
mapping to whatever native tools the host provides.

If the host cannot discover capabilities, validate the contract, or provide an
approved isolation boundary, it must not execute the action. Report
`unavailable`, `review`, or `stop` honestly.

## Safety and degradation

- JEV never calls an LLM or changes durable state.
- JEV never runs a subprocess, starts a browser, contacts a model provider, or
  installs dependencies.
- Missing capabilities are explicit; there is no Docker/Podman/Playwright or
  other provider fallback in this kernel.
- A `reversible`/`host_managed` descriptor is a host assertion, not a security
  guarantee created by JEV.
- The Runtime remains the final policy enforcement point and must re-check the
  actual action, scope, and confirmation before invoking a capability.

## Migration

The old `runtime/core/jev/` Python package is legacy compatibility material,
not the canonical decision path. It is not imported by the Runtime or
SessionManager. New hosts should use the JSON contract and either the reference
engine or a native implementation. The old package must not be treated as a
safe behavior baseline because its public classification path and policy
helpers are broken.
