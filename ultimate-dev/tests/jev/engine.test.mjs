import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { decide, validateDecisionPacket, validateDecisionRequest, JEV_SCHEMA_VERSION } from "../../runtime/jev/engine.mjs";

const policy = (overrides = {}) => ({
  policy_version: "test.policy.v1",
  denied_capability_ids: [],
  review_capability_ids: [],
  denied_effects: [],
  approval_required_effects: [],
  isolation_required_effects: ["execute"],
  thresholds: {
    review_risk: 0.8,
    review_confidence: 0.55,
    flagship_load: 0.7,
    high_context_pressure: 0.8,
    deep_complexity: 0.75,
    deep_confidence: 0.8,
  },
  max_capabilities: 8,
  ...overrides,
});

const approvalScope = ({
  taskId = "task-jev-001",
  operation = "write",
  reversibility = "reversible",
  effects = [operation],
  description = "A bounded test scope",
  projectRoot = null,
  targets = ["fixture"],
  policyVersion = "test.policy.v1",
  catalogVersion = "catalog.test.v1",
} = {}) => ({
  task_id: taskId,
  operation,
  policy_version: policyVersion,
  capability_catalog_version: catalogVersion,
  reversibility,
  effects,
  action_scope: {
    description,
    project_root: projectRoot,
    targets,
  },
});

const request = ({
  operation = "read",
  effects = [operation],
  signals = {},
  choice = {},
  scores = {},
  requested = [{ id: "filesystem.read", required: true, reason: "Read the relevant files." }],
  catalog = [{ id: "filesystem.read", available: true, reversible: true, isolation: "host_managed", risk: 0.1, effects: ["read"] }],
  policyOverrides = {},
  approvals = [],
  evidence = ["evidence-1"],
  environment = "development",
  reversibility = "reversible",
  evaluationTime = "2026-09-24T12:00:00Z",
} = {}) => ({
  schema_version: "1.0",
  task_id: "task-jev-001",
  evaluation_time: evaluationTime,
  orchestration_state: {
    state_id: "state-001",
    pattern: "inline",
    phase: "plan",
    environment,
    completed_step_ids: [],
    pending_step_ids: ["decide"],
  },
  model_assessment: {
    signals: {
      urgent: false,
      destructive: false,
      policy_sensitive: false,
      human_approval_required: false,
      evidence_required: false,
      ...signals,
    },
    choice: {
      pattern: "inline",
      task_size: "atomic",
      preferred_path: "lightweight",
      primary_domain: "testing",
      rationale: "The task is a bounded read-only decision.",
      ...choice,
    },
    scores: {
      risk: 0.1,
      complexity: 0.1,
      urgency: 0,
      confidence: 0.9,
      context_pressure: 0.1,
      ...scores,
    },
    proposal: {
      summary: "Evaluate a bounded action.",
      action: {
        operation,
        reversibility,
        scope: {
          description: "A bounded test scope",
          project_root: null,
          targets: ["fixture"],
        },
      },
      requested_capabilities: requested,
      effects,
      evidence_refs: evidence,
    },
  },
  host_facts: {
    capability_catalog_version: "catalog.test.v1",
    capability_catalog: catalog,
    policy: policy(policyOverrides),
    approvals,
  },
});

test("read-only capability is approved and intersection-selected", () => {
  const packet = decide(request());

  assert.equal(packet.ok, true);
  assert.equal(packet.guardrail.action, "approve");
  assert.equal(packet.execution_effect, "execute");
  assert.equal(packet.route.path, "lightweight");
  assert.deepEqual(packet.capability_plan.selected, ["filesystem.read"]);
  assert.deepEqual(packet.capability_plan.missing_capabilities, []);
  assert.equal(packet.context_plan.profile, "standard");
});

test("the packet is complete and contains no ambient timing fields", () => {
  const packet = decide(request());

  assert.deepEqual(Object.keys(packet).sort(), [
    "aggregate",
    "capability_catalog_version",
    "capability_plan",
    "context_plan",
    "errors",
    "execution_effect",
    "guardrail",
    "heads",
    "ok",
    "orchestration_state_id",
    "policy_version",
    "route",
    "schema_version",
    "task_id",
    "trace",
  ].sort());
  assert.equal("generated_at" in packet, false);
  assert.equal("processing_time_ms" in packet, false);
});

test("the same request produces the same logical packet", () => {
  const input = request();
  const before = JSON.stringify(input);
  const first = decide(input);
  const second = decide(input);

  assert.deepEqual(first, second);
  assert.equal(JSON.stringify(input), before);
  assert.equal(first.trace.deterministic, true);
});

test("side effects without scoped approval stop at human review", () => {
  const packet = decide(request({
    operation: "write",
    policyOverrides: { approval_required_effects: ["write"] },
    catalog: [{ id: "filesystem.write", available: true, reversible: true, isolation: "host_managed", risk: 0.4, effects: ["write"] }],
    requested: [{ id: "filesystem.write", required: true, reason: "Write the approved output." }],
  }));

  assert.equal(packet.guardrail.action, "human_review");
  assert.equal(packet.execution_effect, "review");
  assert.deepEqual(packet.capability_plan.selected, []);
  assert.ok(packet.guardrail.reasons.some((item) => item.code === "approval_required"));
});

test("a scoped approval allows a reversible side effect", () => {
  const packet = decide(request({
    operation: "write",
    policyOverrides: { approval_required_effects: ["write"] },
    catalog: [{ id: "filesystem.write", available: true, reversible: true, isolation: "host_managed", risk: 0.4, effects: ["write"] }],
    requested: [{ id: "filesystem.write", required: true, reason: "Write the approved output." }],
    approvals: [{
      capability_id: "filesystem.write",
      effect: "write",
      scope: approvalScope(),
      confirmed_at: "2026-09-24T11:55:00Z",
      expires_at: "2026-09-24T12:05:00Z",
    }],
  }));

  assert.equal(packet.guardrail.action, "approve");
  assert.equal(packet.execution_effect, "execute");
  assert.deepEqual(packet.capability_plan.selected, ["filesystem.write"]);
});

test("a denied effect has deny precedence and exposes no executable capability", () => {
  const packet = decide(request({
    operation: "delete",
    policyOverrides: { denied_effects: ["delete"] },
    catalog: [{ id: "filesystem.delete", available: true, reversible: false, isolation: "host_managed", risk: 0.9, effects: ["delete"] }],
    requested: [{ id: "filesystem.delete", required: true, reason: "Remove the target." }],
  }));

  assert.equal(packet.guardrail.action, "deny");
  assert.equal(packet.execution_effect, "stop");
  assert.deepEqual(packet.capability_plan.selected, []);
  assert.ok(packet.guardrail.reasons.some((item) => item.code === "policy_denied_effect"));
});

test("a missing required capability degrades to review rather than installation", () => {
  const packet = decide(request({
    requested: [{ id: "browser.navigate", required: true, reason: "Inspect the host browser." }],
    catalog: [],
  }));

  assert.equal(packet.guardrail.action, "human_review");
  assert.equal(packet.execution_effect, "review");
  assert.deepEqual(packet.capability_plan.missing_capabilities, ["browser.navigate"]);
  assert.deepEqual(packet.capability_plan.selected, []);
  assert.ok(packet.guardrail.reasons.some((item) => item.code === "required_capability_unavailable"));
});

test("an optional unavailable capability is omitted without blocking the request", () => {
  const packet = decide(request({
    requested: [
      { id: "filesystem.read", required: true, reason: "Read source." },
      { id: "search.web", required: false, reason: "Optional enrichment." },
    ],
    catalog: [{ id: "filesystem.read", available: true, reversible: true, isolation: "host_managed", risk: 0.1, effects: ["read"] }],
  }));

  assert.equal(packet.guardrail.action, "approve");
  assert.deepEqual(packet.capability_plan.selected, ["filesystem.read"]);
  assert.ok(packet.capability_plan.omitted.some((item) => item.id === "search.web" && item.code === "capability_unavailable"));
});

test("low confidence and missing required evidence require review", () => {
  const packet = decide(request({
    signals: { evidence_required: true },
    scores: { confidence: 0.2 },
    evidence: [],
  }));

  assert.equal(packet.guardrail.action, "human_review");
  assert.ok(packet.guardrail.reasons.some((item) => item.code === "missing_required_evidence"));
  assert.ok(packet.guardrail.reasons.some((item) => item.code === "low_confidence"));
});

test("host-declared irreversible side effects require approval even if the model understates them", () => {
  const packet = decide(request({
    operation: "write",
    catalog: [{ id: "filesystem.write", available: true, reversible: false, isolation: "host_managed", risk: 0.4, effects: ["write"] }],
    requested: [{ id: "filesystem.write", required: true, reason: "Write without a model risk signal." }],
    policyOverrides: { approval_required_effects: [] },
  }));

  assert.equal(packet.guardrail.action, "human_review");
  assert.ok(packet.guardrail.reasons.some((item) => item.code === "approval_required"));
});

test("a capability cannot be selected for an undeclared effect", () => {
  const packet = decide(request({
    operation: "read",
    requested: [{ id: "shell.execute", required: true, reason: "Attempt a mismatched capability." }],
    catalog: [{ id: "shell.execute", available: true, reversible: true, isolation: "host_managed", risk: 0.2, effects: ["execute"] }],
  }));

  assert.equal(packet.guardrail.action, "human_review");
  assert.ok(packet.guardrail.reasons.some((item) => item.code === "capability_effect_not_declared"));
});

test("every proposed effect is covered by the selected capability set", () => {
  for (const sideEffect of ["write", "delete", "network"]) {
    const packet = decide(request({
      operation: sideEffect,
      effects: ["read", sideEffect],
      requested: [{ id: "filesystem.read", required: true, reason: "Read the relevant files." }],
      catalog: [{ id: "filesystem.read", available: true, reversible: true, isolation: "host_managed", risk: 0.1, effects: ["read"] }],
    }));

    assert.equal(packet.guardrail.action, "human_review", `${sideEffect} must require review`);
    assert.equal(packet.execution_effect, "review");
    assert.deepEqual(packet.capability_plan.selected, []);
    const coverageReason = packet.guardrail.reasons.find((item) => item.code === "effect_coverage_incomplete");
    assert.ok(coverageReason, `${sideEffect} must expose a coverage reason`);
    assert.equal(coverageReason.path, "model_assessment.proposal.effects");
  }
});

test("a complete requested capability set may execute with scoped approval", () => {
  const packet = decide(request({
    operation: "write",
    effects: ["read", "write"],
    requested: [
      { id: "filesystem.read", required: true, reason: "Read the relevant files." },
      { id: "filesystem.write", required: true, reason: "Write the approved output." },
    ],
    catalog: [
      { id: "filesystem.read", available: true, reversible: true, isolation: "host_managed", risk: 0.1, effects: ["read"] },
      { id: "filesystem.write", available: true, reversible: true, isolation: "host_managed", risk: 0.4, effects: ["write"] },
    ],
    policyOverrides: { approval_required_effects: ["write"] },
    approvals: [{
      capability_id: "filesystem.write",
      effect: "write",
      scope: approvalScope({ effects: ["read", "write"] }),
      confirmed_at: "2026-09-24T11:55:00Z",
      expires_at: "2026-09-24T12:05:00Z",
    }],
  }));

  assert.equal(packet.guardrail.action, "approve");
  assert.equal(packet.execution_effect, "execute");
  assert.deepEqual(packet.capability_plan.selected, ["filesystem.read", "filesystem.write"]);
});

test("an approval must bind the task and exact action scope", () => {
  const packet = decide(request({
    operation: "write",
    policyOverrides: { approval_required_effects: ["write"] },
    catalog: [{ id: "filesystem.write", available: true, reversible: true, isolation: "host_managed", risk: 0.4, effects: ["write"] }],
    requested: [{ id: "filesystem.write", required: true, reason: "Write the approved output." }],
    approvals: [{
      capability_id: "filesystem.write",
      effect: "write",
      scope: approvalScope({ taskId: "another-task" }),
      confirmed_at: "2026-09-24T11:55:00Z",
      expires_at: "2026-09-24T12:05:00Z",
    }],
  }));

  assert.equal(packet.guardrail.action, "human_review");
  assert.equal(packet.execution_effect, "review");
  assert.deepEqual(packet.capability_plan.selected, []);
  assert.ok(packet.guardrail.reasons.some((item) => item.code === "approval_scope_mismatch"));
});

test("approval freshness fails closed without an explicit evaluation time", () => {
  const input = request({
    operation: "write",
    policyOverrides: { approval_required_effects: ["write"] },
    catalog: [{ id: "filesystem.write", available: true, reversible: true, isolation: "host_managed", risk: 0.4, effects: ["write"] }],
    requested: [{ id: "filesystem.write", required: true, reason: "Write the approved output." }],
    approvals: [{
      capability_id: "filesystem.write",
      effect: "write",
      scope: approvalScope(),
      confirmed_at: "2026-09-24T11:55:00Z",
      expires_at: "2026-09-24T12:05:00Z",
    }],
  });
  delete input.evaluation_time;

  const packet = decide(input);
  assert.equal(packet.execution_effect, "review");
  assert.deepEqual(packet.capability_plan.selected, []);
  assert.ok(packet.guardrail.reasons.some((item) => item.code === "evaluation_time_required"));

  const sideEffectWithoutTime = request({
    operation: "write",
    policyOverrides: { approval_required_effects: [] },
    catalog: [{ id: "filesystem.write", available: true, reversible: true, isolation: "host_managed", risk: 0.1, effects: ["write"] }],
    requested: [{ id: "filesystem.write", required: true, reason: "Write a bounded result." }],
  });
  delete sideEffectWithoutTime.evaluation_time;
  const sideEffectPacket = decide(sideEffectWithoutTime);
  assert.equal(sideEffectPacket.execution_effect, "review");
  assert.ok(sideEffectPacket.guardrail.reasons.some((item) => item.code === "evaluation_time_required"));

  const explicitlyTimed = decide(input, { evaluation_time: "2026-09-24T12:00:00Z" });
  assert.equal(explicitlyTimed.execution_effect, "execute");
});

test("expired, stale, and future approvals are never executable", () => {
  const cases = [
    ["2026-09-24T10:00:00Z", "2026-09-24T11:00:00Z", "approval_expired"],
    ["2026-09-24T00:00:00Z", "2026-09-24T13:00:00Z", "approval_stale"],
    ["2026-09-24T12:01:00Z", "2026-09-24T12:05:00Z", "approval_future_dated"],
  ];
  for (const [confirmedAt, expiresAt, code] of cases) {
    const packet = decide(request({
      operation: "write",
      policyOverrides: { approval_required_effects: ["write"] },
      catalog: [{ id: "filesystem.write", available: true, reversible: true, isolation: "host_managed", risk: 0.4, effects: ["write"] }],
      requested: [{ id: "filesystem.write", required: true, reason: "Write the approved output." }],
      approvals: [{ capability_id: "filesystem.write", effect: "write", scope: approvalScope(), confirmed_at: confirmedAt, expires_at: expiresAt }],
    }));
    assert.equal(packet.execution_effect, "review", code);
    assert.deepEqual(packet.capability_plan.selected, [], code);
    assert.ok(packet.guardrail.reasons.some((item) => item.code === code), code);
  }
});

test("destructive signals force human review even with a permissive policy", () => {
  const packet = decide(request({
    operation: "write",
    signals: { destructive: true },
    policyOverrides: { approval_required_effects: [] },
    catalog: [{ id: "filesystem.write", available: true, reversible: true, isolation: "host_managed", risk: 0.1, effects: ["write"] }],
    requested: [{ id: "filesystem.write", required: true, reason: "Write a bounded result." }],
  }));

  assert.equal(packet.guardrail.action, "human_review");
  assert.equal(packet.execution_effect, "review");
  assert.deepEqual(packet.capability_plan.selected, []);
  assert.ok(packet.guardrail.reasons.some((item) => item.code === "destructive_signal"));

  const coveredDelete = decide(request({
    operation: "delete",
    catalog: [{ id: "filesystem.delete", available: true, reversible: true, isolation: "host_managed", risk: 0.1, effects: ["delete"] }],
    requested: [{ id: "filesystem.delete", required: true, reason: "Remove the target." }],
  }));
  assert.equal(coveredDelete.guardrail.action, "human_review");
  assert.equal(coveredDelete.execution_effect, "review");
  assert.ok(coveredDelete.guardrail.reasons.some((item) => item.code === "destructive_effect"));
});

test("packet semantic validation rejects contradictory executable coverage", () => {
  const input = request({
    operation: "write",
    effects: ["read", "write"],
    requested: [
      { id: "filesystem.read", required: true, reason: "Read the relevant files." },
      { id: "filesystem.write", required: true, reason: "Write the approved output." },
    ],
    catalog: [
      { id: "filesystem.read", available: true, reversible: true, isolation: "host_managed", risk: 0.1, effects: ["read"] },
      { id: "filesystem.write", available: true, reversible: true, isolation: "host_managed", risk: 0.4, effects: ["write"] },
    ],
    policyOverrides: { approval_required_effects: ["write"] },
    approvals: [{
      capability_id: "filesystem.write",
      effect: "write",
      scope: approvalScope({ effects: ["read", "write"] }),
      confirmed_at: "2026-09-24T11:55:00Z",
      expires_at: "2026-09-24T12:05:00Z",
    }],
  });
  const packet = decide(input);
  assert.equal(validateDecisionPacket(packet, input).ok, true);

  const uncovered = JSON.parse(JSON.stringify(packet));
  uncovered.capability_plan.selected = ["filesystem.read"];
  const uncoveredResult = validateDecisionPacket(uncovered, input);
  assert.equal(uncoveredResult.ok, false);
  assert.ok(uncoveredResult.errors.some((item) => item.code === "effect_coverage_incomplete"));

  const contradictory = JSON.parse(JSON.stringify(packet));
  contradictory.capability_plan.missing_capabilities = ["filesystem.write"];
  const contradictoryResult = validateDecisionPacket(contradictory, input);
  assert.equal(contradictoryResult.ok, false);
  assert.ok(contradictoryResult.errors.some((item) => item.code === "executable_packet_has_missing_capabilities"));

  const failed = JSON.parse(JSON.stringify(packet));
  failed.ok = false;
  const failedResult = validateDecisionPacket(failed, input);
  assert.equal(failedResult.ok, false);
  assert.ok(failedResult.errors.some((item) => item.code === "executable_packet_not_ok"));
});

test("unisolated execution is not treated as a secure sandbox", () => {
  const packet = decide(request({
    operation: "execute",
    catalog: [{ id: "shell.execute", available: true, reversible: false, isolation: "none", risk: 0.8, effects: ["execute"] }],
    requested: [{ id: "shell.execute", required: true, reason: "Run a bounded command." }],
  }));

  assert.equal(packet.guardrail.action, "human_review");
  assert.equal(packet.execution_effect, "review");
  assert.ok(packet.guardrail.reasons.some((item) => item.code === "missing_isolation"));
});

test("human approval is a stop state even when no capability is requested", () => {
  const packet = decide(request({ signals: { human_approval_required: true }, requested: [], catalog: [] }));

  assert.equal(packet.guardrail.action, "human_review");
  assert.equal(packet.execution_effect, "review");
  assert.deepEqual(packet.capability_plan.selected, []);
});

test("required capabilities are selected before optional capabilities under a budget", () => {
  const packet = decide(request({
    requested: [
      { id: "search.web", required: false, reason: "Optional first." },
      { id: "filesystem.read", required: true, reason: "Required second." },
    ],
    catalog: [
      { id: "search.web", available: true, reversible: true, isolation: "host_managed", risk: 0.1, effects: ["read"] },
      { id: "filesystem.read", available: true, reversible: true, isolation: "host_managed", risk: 0.1, effects: ["read"] },
    ],
    policyOverrides: { max_capabilities: 1 },
  }));

  assert.deepEqual(packet.capability_plan.selected, ["filesystem.read"]);
  assert.ok(packet.capability_plan.omitted.some((item) => item.id === "search.web" && item.code === "capability_budget_exhausted"));
});

test("malformed payloads fail closed", () => {
  const packet = decide({ schema_version: "1.0", task_id: "bad" });

  assert.equal(packet.ok, false);
  assert.equal(packet.guardrail.action, "deny");
  assert.equal(packet.execution_effect, "stop");
  assert.ok(packet.errors.length > 0);
});

test("the reference engine has no host/runtime side-effect imports", async () => {
  const source = await readFile(new URL("../../runtime/jev/engine.mjs", import.meta.url), "utf8");
  assert.doesNotMatch(source, /^\s*import\s/m);
  assert.doesNotMatch(source, /\b(fetch|XMLHttpRequest|child_process|execSync|spawnSync)\b/);
});

test("the schema version and contract files are stable", async () => {
  const requestSchema = JSON.parse(await readFile(new URL("../../runtime/schemas/jev-decision-request.schema.json", import.meta.url)));
  const packetSchema = JSON.parse(await readFile(new URL("../../runtime/schemas/jev-decision-packet.schema.json", import.meta.url)));
  const policyFile = JSON.parse(await readFile(new URL("../../runtime/jev-policy.json", import.meta.url)));

  assert.equal(JEV_SCHEMA_VERSION, "1.0");
  assert.equal(requestSchema.properties.schema_version.const, "1.0");
  assert.equal(packetSchema.properties.schema_version.const, "1.0");
  assert.ok(requestSchema.required.includes("host_facts"));
  assert.ok(packetSchema.required.includes("execution_effect"));
  assert.ok(requestSchema.$defs.approvalScope);
  assert.ok(requestSchema.$defs.approval.required.includes("expires_at"));
  assert.equal(requestSchema.$defs.approval.properties.scope.$ref, "#/$defs/approvalScope");
  assert.ok(Array.isArray(packetSchema.allOf) && packetSchema.allOf.length >= 3);
  assert.equal(policyFile.max_capabilities, 8);
});

test("validation is available independently of evaluation", () => {
  const valid = validateDecisionRequest(request());
  assert.equal(valid.ok, true);
  assert.deepEqual(valid.errors, []);

  const invalid = validateDecisionRequest({ ...request(), schema_version: "2.0" });
  assert.equal(invalid.ok, false);
  assert.ok(invalid.errors.some((item) => item.code === "unsupported_schema_version"));

  const legacyScope = request({
    operation: "write",
    approvals: [{ capability_id: "filesystem.write", effect: "write", scope: "fixture", confirmed_at: "2026-09-24T11:55:00Z", expires_at: "2026-09-24T12:05:00Z" }],
  });
  const legacyValidation = validateDecisionRequest(legacyScope);
  assert.equal(legacyValidation.ok, false);
  assert.ok(legacyValidation.errors.some((item) => item.code === "invalid_type"));
});
