/**
 * Ultimate-Dev JEV reference policy kernel.
 *
 * This module is intentionally pure: it does not import a host runtime, call a
 * model, discover tools, install dependencies, execute commands, or persist
 * state. The JSON request schema is the canonical contract. A host may port
 * these rules to its native language without adopting this file.
 */

export const JEV_SCHEMA_VERSION = "1.0";

export const EFFECTS = Object.freeze([
  "read",
  "write",
  "execute",
  "delete",
  "network",
  "communicate",
]);

const PATTERNS = Object.freeze([
  "inline",
  "subagent",
  "handoff",
  "router",
  "compose",
]);

const PATHS = Object.freeze(["lightweight", "flagship", "human_review", "none"]);
const TASK_SIZES = Object.freeze(["atomic", "moderate", "complex"]);
const ISOLATION_LEVELS = Object.freeze(["host_managed", "user_approved", "none"]);
const CAPABILITY_ID = /^[a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_]*)+$/;
const DATE_TIME = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$/;
const THRESHOLD_KEYS = Object.freeze([
  "review_risk",
  "review_confidence",
  "flagship_load",
  "high_context_pressure",
  "deep_complexity",
  "deep_confidence",
]);

const has = (value, key) => Object.prototype.hasOwnProperty.call(value, key);
const isRecord = (value) => value !== null && typeof value === "object" && !Array.isArray(value);
const isFiniteNumber = (value) => typeof value === "number" && Number.isFinite(value);
const nonEmpty = (value) => typeof value === "string" && value.trim().length > 0;
const path = (...parts) => parts.filter(Boolean).join(".");
const unique = (values) => new Set(values).size === values.length;
const clamp = (value) => Math.max(0, Math.min(1, value));
const round = (value) => Math.round(clamp(value) * 10000) / 10000;

function error(code, message, fieldPath, remedy = undefined) {
  const result = { code, message, path: fieldPath };
  if (remedy !== undefined) result.remedy = remedy;
  return result;
}

function checkKeys(value, allowed, required, prefix, errors) {
  for (const key of required) {
    if (!has(value, key)) {
      errors.push(error("missing_field", `Required field is missing: ${key}`, path(prefix, key), "Add the field before evaluating the request."));
    }
  }
  for (const key of Object.keys(value)) {
    if (!allowed.includes(key)) {
      errors.push(error("unknown_field", `Unknown field is not part of the versioned contract: ${key}`, path(prefix, key), "Remove the field or version the contract explicitly."));
    }
  }
}

function objectValue(value, prefix, errors) {
  if (!isRecord(value)) {
    errors.push(error("invalid_type", "Expected an object.", prefix, "Provide a JSON object for this field."));
    return null;
  }
  return value;
}

function stringValue(value, prefix, errors, { max = 10000 } = {}) {
  if (!nonEmpty(value)) {
    errors.push(error("invalid_string", "Expected a non-empty string.", prefix, "Provide a meaningful value."));
    return null;
  }
  if (value.length > max) {
    errors.push(error("invalid_length", `String exceeds the maximum length of ${max}.`, prefix, "Shorten the value."));
  }
  return value;
}

function booleanValue(value, prefix, errors) {
  if (typeof value !== "boolean") {
    errors.push(error("invalid_type", "Expected a boolean.", prefix, "Use true or false."));
    return null;
  }
  return value;
}

function enumValue(value, allowed, prefix, errors) {
  if (!allowed.includes(value)) {
    errors.push(error("invalid_enum", `Expected one of: ${allowed.join(", ")}.`, prefix, "Use a value defined by the versioned contract."));
    return null;
  }
  return value;
}

function unitValue(value, prefix, errors) {
  if (!isFiniteNumber(value) || value < 0 || value > 1) {
    errors.push(error("invalid_range", "Expected a finite number from 0 through 1.", prefix, "Use a normalized score in the inclusive range 0..1."));
    return null;
  }
  return value;
}

function arrayValue(value, prefix, errors) {
  if (!Array.isArray(value)) {
    errors.push(error("invalid_type", "Expected an array.", prefix, "Provide a JSON array."));
    return [];
  }
  return value;
}

function stringArray(value, prefix, errors, { max = 100 } = {}) {
  const values = arrayValue(value, prefix, errors);
  values.forEach((item, index) => stringValue(item, `${prefix}[${index}]`, errors, { max }));
  if (!unique(values)) {
    errors.push(error("duplicate_value", "Array values must be unique.", prefix, "Remove duplicate entries."));
  }
  return values;
}

function capabilityId(value, prefix, errors) {
  if (!nonEmpty(value) || !CAPABILITY_ID.test(value)) {
    errors.push(error("invalid_capability_id", "Expected a canonical dotted capability ID such as filesystem.read.", prefix, "Use a provider-neutral capability ID."));
    return null;
  }
  return value;
}

function capabilityIdArray(value, prefix, errors) {
  const values = arrayValue(value, prefix, errors);
  values.forEach((item, index) => capabilityId(item, `${prefix}[${index}]`, errors));
  if (!unique(values)) {
    errors.push(error("duplicate_value", "Capability IDs must be unique.", prefix, "Remove duplicate entries."));
  }
  return values;
}

function validateOrchestrationState(value, errors) {
  const state = objectValue(value, "orchestration_state", errors);
  if (!state) return null;
  checkKeys(state, ["state_id", "pattern", "phase", "environment", "completed_step_ids", "pending_step_ids"], ["state_id", "pattern", "phase", "environment", "completed_step_ids", "pending_step_ids"], "orchestration_state", errors);
  stringValue(state.state_id, "orchestration_state.state_id", errors, { max: 200 });
  enumValue(state.pattern, ["undecided", ...PATTERNS], "orchestration_state.pattern", errors);
  stringValue(state.phase, "orchestration_state.phase", errors, { max: 100 });
  enumValue(state.environment, ["development", "test", "staging", "production", "unknown"], "orchestration_state.environment", errors);
  stringArray(state.completed_step_ids, "orchestration_state.completed_step_ids", errors);
  stringArray(state.pending_step_ids, "orchestration_state.pending_step_ids", errors);
  return state;
}

function validateSignals(value, errors) {
  const signals = objectValue(value, "model_assessment.signals", errors);
  if (!signals) return null;
  const keys = ["urgent", "destructive", "policy_sensitive", "human_approval_required", "evidence_required"];
  checkKeys(signals, keys, keys, "model_assessment.signals", errors);
  keys.forEach((key) => booleanValue(signals[key], `model_assessment.signals.${key}`, errors));
  return signals;
}

function validateChoice(value, errors) {
  const choice = objectValue(value, "model_assessment.choice", errors);
  if (!choice) return null;
  const keys = ["pattern", "task_size", "preferred_path", "primary_domain", "rationale"];
  checkKeys(choice, keys, keys, "model_assessment.choice", errors);
  enumValue(choice.pattern, PATTERNS, "model_assessment.choice.pattern", errors);
  enumValue(choice.task_size, TASK_SIZES, "model_assessment.choice.task_size", errors);
  enumValue(choice.preferred_path, PATHS, "model_assessment.choice.preferred_path", errors);
  stringValue(choice.primary_domain, "model_assessment.choice.primary_domain", errors, { max: 100 });
  stringValue(choice.rationale, "model_assessment.choice.rationale", errors, { max: 2000 });
  return choice;
}

function validateScores(value, errors) {
  const scores = objectValue(value, "model_assessment.scores", errors);
  if (!scores) return null;
  const keys = ["risk", "complexity", "urgency", "confidence", "context_pressure"];
  checkKeys(scores, keys, keys, "model_assessment.scores", errors);
  keys.forEach((key) => unitValue(scores[key], `model_assessment.scores.${key}`, errors));
  return scores;
}

function validateAction(value, errors) {
  const action = objectValue(value, "model_assessment.proposal.action", errors);
  if (!action) return null;
  checkKeys(action, ["operation", "reversibility", "scope"], ["operation", "reversibility", "scope"], "model_assessment.proposal.action", errors);
  enumValue(action.operation, EFFECTS, "model_assessment.proposal.action.operation", errors);
  enumValue(action.reversibility, ["reversible", "partially_reversible", "irreversible", "unknown"], "model_assessment.proposal.action.reversibility", errors);
  const scope = objectValue(action.scope, "model_assessment.proposal.action.scope", errors);
  if (scope) {
    checkKeys(scope, ["description", "project_root", "targets"], ["description", "project_root", "targets"], "model_assessment.proposal.action.scope", errors);
    stringValue(scope.description, "model_assessment.proposal.action.scope.description", errors, { max: 2000 });
    if (scope.project_root !== null && !nonEmpty(scope.project_root)) {
      errors.push(error("invalid_string", "project_root must be a non-empty string or null.", "model_assessment.proposal.action.scope.project_root", "Use null when the action is not project-scoped."));
    }
    stringArray(scope.targets, "model_assessment.proposal.action.scope.targets", errors);
  }
  return action;
}

function validateProposal(value, errors) {
  const proposal = objectValue(value, "model_assessment.proposal", errors);
  if (!proposal) return null;
  const keys = ["summary", "action", "requested_capabilities", "effects", "evidence_refs"];
  checkKeys(proposal, keys, keys, "model_assessment.proposal", errors);
  stringValue(proposal.summary, "model_assessment.proposal.summary", errors, { max: 4000 });
  const action = validateAction(proposal.action, errors);
  const requested = arrayValue(proposal.requested_capabilities, "model_assessment.proposal.requested_capabilities", errors);
  const ids = [];
  requested.forEach((item, index) => {
    const request = objectValue(item, `model_assessment.proposal.requested_capabilities[${index}]`, errors);
    if (!request) return;
    checkKeys(request, ["id", "required", "reason"], ["id", "required", "reason"], `model_assessment.proposal.requested_capabilities[${index}]`, errors);
    const id = capabilityId(request.id, `model_assessment.proposal.requested_capabilities[${index}].id`, errors);
    if (id) ids.push(id);
    booleanValue(request.required, `model_assessment.proposal.requested_capabilities[${index}].required`, errors);
    stringValue(request.reason, `model_assessment.proposal.requested_capabilities[${index}].reason`, errors, { max: 1000 });
  });
  if (!unique(ids)) {
    errors.push(error("duplicate_value", "Requested capability IDs must be unique.", "model_assessment.proposal.requested_capabilities", "Remove duplicate capability entries."));
  }
  const effects = arrayValue(proposal.effects, "model_assessment.proposal.effects", errors);
  effects.forEach((item, index) => enumValue(item, EFFECTS, `model_assessment.proposal.effects[${index}]`, errors));
  if (!unique(effects)) {
    errors.push(error("duplicate_value", "Effects must be unique.", "model_assessment.proposal.effects", "Remove duplicate effects."));
  }
  stringArray(proposal.evidence_refs, "model_assessment.proposal.evidence_refs", errors);
  if (action && !effects.includes(action.operation)) {
    errors.push(error("action_effect_mismatch", "The action operation must be included in the declared effects.", "model_assessment.proposal.action.operation", "Include the operation in proposal.effects."));
  }
  return proposal;
}

function validateCapabilityDescriptor(value, prefix, errors) {
  const descriptor = objectValue(value, prefix, errors);
  if (!descriptor) return null;
  const keys = ["id", "available", "reversible", "isolation", "risk", "effects"];
  checkKeys(descriptor, keys, keys, prefix, errors);
  capabilityId(descriptor.id, `${prefix}.id`, errors);
  booleanValue(descriptor.available, `${prefix}.available`, errors);
  booleanValue(descriptor.reversible, `${prefix}.reversible`, errors);
  enumValue(descriptor.isolation, ISOLATION_LEVELS, `${prefix}.isolation`, errors);
  unitValue(descriptor.risk, `${prefix}.risk`, errors);
  const effects = arrayValue(descriptor.effects, `${prefix}.effects`, errors);
  if (effects.length === 0) errors.push(error("empty_effects", "A capability must declare at least one effect.", `${prefix}.effects`, "Declare the effects the host capability can perform."));
  effects.forEach((item, index) => enumValue(item, EFFECTS, `${prefix}.effects[${index}]`, errors));
  if (!unique(effects)) errors.push(error("duplicate_value", "Capability effects must be unique.", `${prefix}.effects`, "Remove duplicate effects."));
  return descriptor;
}

function validatePolicy(value, errors) {
  const policy = objectValue(value, "host_facts.policy", errors);
  if (!policy) return null;
  const keys = ["policy_version", "denied_capability_ids", "review_capability_ids", "denied_effects", "approval_required_effects", "isolation_required_effects", "thresholds", "max_capabilities"];
  checkKeys(policy, keys, keys, "host_facts.policy", errors);
  stringValue(policy.policy_version, "host_facts.policy.policy_version", errors, { max: 200 });
  capabilityIdArray(policy.denied_capability_ids, "host_facts.policy.denied_capability_ids", errors);
  capabilityIdArray(policy.review_capability_ids, "host_facts.policy.review_capability_ids", errors);
  ["denied_effects", "approval_required_effects", "isolation_required_effects"].forEach((key) => {
    const values = arrayValue(policy[key], `host_facts.policy.${key}`, errors);
    values.forEach((item, index) => enumValue(item, EFFECTS, `host_facts.policy.${key}[${index}]`, errors));
    if (!unique(values)) errors.push(error("duplicate_value", "Policy values must be unique.", `host_facts.policy.${key}`, "Remove duplicate values."));
  });
  const thresholds = objectValue(policy.thresholds, "host_facts.policy.thresholds", errors);
  if (thresholds) {
    checkKeys(thresholds, THRESHOLD_KEYS, THRESHOLD_KEYS, "host_facts.policy.thresholds", errors);
    THRESHOLD_KEYS.forEach((key) => unitValue(thresholds[key], `host_facts.policy.thresholds.${key}`, errors));
  }
  if (!Number.isInteger(policy.max_capabilities) || policy.max_capabilities < 1 || policy.max_capabilities > 64) {
    errors.push(error("invalid_range", "max_capabilities must be an integer from 1 through 64.", "host_facts.policy.max_capabilities", "Set a bounded host capability budget."));
  }
  return policy;
}

function validateApproval(value, prefix, errors) {
  const approval = objectValue(value, prefix, errors);
  if (!approval) return null;
  const keys = ["capability_id", "effect", "scope", "confirmed_at"];
  checkKeys(approval, keys, keys, prefix, errors);
  capabilityId(approval.capability_id, `${prefix}.capability_id`, errors);
  enumValue(approval.effect, EFFECTS, `${prefix}.effect`, errors);
  stringValue(approval.scope, `${prefix}.scope`, errors, { max: 2000 });
  if (!nonEmpty(approval.confirmed_at) || !DATE_TIME.test(approval.confirmed_at)) {
    errors.push(error("invalid_format", "confirmed_at must be an ISO-8601 date-time string.", `${prefix}.confirmed_at`, "Use a value such as 2026-09-24T00:00:00Z."));
  }
  return approval;
}

function validateHostFacts(value, errors) {
  const host = objectValue(value, "host_facts", errors);
  if (!host) return null;
  const keys = ["capability_catalog_version", "capability_catalog", "policy", "approvals"];
  checkKeys(host, keys, keys, "host_facts", errors);
  stringValue(host.capability_catalog_version, "host_facts.capability_catalog_version", errors, { max: 200 });
  const catalog = arrayValue(host.capability_catalog, "host_facts.capability_catalog", errors);
  const ids = [];
  catalog.forEach((item, index) => {
    const descriptor = validateCapabilityDescriptor(item, `host_facts.capability_catalog[${index}]`, errors);
    if (descriptor && nonEmpty(descriptor.id)) ids.push(descriptor.id);
  });
  if (!unique(ids)) errors.push(error("duplicate_value", "Capability catalog IDs must be unique.", "host_facts.capability_catalog", "Keep one descriptor per capability ID."));
  validatePolicy(host.policy, errors);
  arrayValue(host.approvals, "host_facts.approvals", errors).forEach((item, index) => validateApproval(item, `host_facts.approvals[${index}]`, errors));
  return host;
}

/** Validate a request without evaluating it. */
export function validateDecisionRequest(input) {
  const errors = [];
  if (!isRecord(input)) {
    errors.push(error("invalid_type", "The decision request must be an object.", "$", "Provide an object matching jev-decision-request.schema.json."));
    return { ok: false, errors };
  }
  const allowed = ["schema_version", "task_id", "orchestration_state", "model_assessment", "host_facts"];
  const required = ["schema_version", "task_id", "orchestration_state", "model_assessment", "host_facts"];
  checkKeys(input, allowed, required, "$", errors);
  if (input.schema_version !== JEV_SCHEMA_VERSION) {
    errors.push(error("unsupported_schema_version", `Expected schema_version ${JEV_SCHEMA_VERSION}.`, "schema_version", "Use the version supported by this host adapter."));
  }
  stringValue(input.task_id, "task_id", errors, { max: 200 });
  const orchestration = validateOrchestrationState(input.orchestration_state, errors);
  const model = objectValue(input.model_assessment, "model_assessment", errors);
  let signals = null;
  let choice = null;
  let scores = null;
  let proposal = null;
  if (model) {
    checkKeys(model, ["signals", "choice", "scores", "proposal"], ["signals", "choice", "scores", "proposal"], "model_assessment", errors);
    signals = validateSignals(model.signals, errors);
    choice = validateChoice(model.choice, errors);
    scores = validateScores(model.scores, errors);
    proposal = validateProposal(model.proposal, errors);
  }
  const host = validateHostFacts(input.host_facts, errors);
  if (orchestration && choice && orchestration.pattern !== "undecided" && orchestration.pattern !== choice.pattern) {
    errors.push(error("orchestration_pattern_conflict", "The orchestration state pattern conflicts with the model choice pattern.", "orchestration_state.pattern", "Align the state transition and the model proposal, or set the state pattern to undecided."));
  }
  return { ok: errors.length === 0, errors, normalized: { orchestration, signals, choice, scores, proposal, host } };
}

function reason(code, message, capabilityIds = []) {
  return { code, message, capability_ids: [...new Set(capabilityIds)] };
}

function neutralHeads() {
  return {
    noul: { urgent: false, destructive: false, policy_sensitive: false, human_approval_required: false, evidence_required: false },
    choice: { pattern: "inline", task_size: "atomic", preferred_path: "none", primary_domain: "unknown" },
    score: { risk: 0, complexity: 0, urgency: 0, confidence: 0, context_pressure: 0 },
  };
}

function invalidPacket(request, validation) {
  const root = isRecord(request) ? request : {};
  const orchestration = isRecord(root.orchestration_state) ? root.orchestration_state : null;
  const host = isRecord(root.host_facts) ? root.host_facts : null;
  const policy = host && isRecord(host.policy) ? host.policy : null;
  const errors = validation.errors.map((item) => reason(item.code, item.message, []));
  return {
    schema_version: JEV_SCHEMA_VERSION,
    task_id: typeof root.task_id === "string" ? root.task_id : "",
    orchestration_state_id: orchestration && typeof orchestration.state_id === "string" ? orchestration.state_id : null,
    capability_catalog_version: host && typeof host.capability_catalog_version === "string" ? host.capability_catalog_version : null,
    policy_version: policy && typeof policy.policy_version === "string" ? policy.policy_version : null,
    ok: false,
    execution_effect: "stop",
    errors,
    heads: neutralHeads(),
    aggregate: { risk: 0, complexity: 0, urgency: 0, confidence: 0, context_pressure: 0, load: 0 },
    guardrail: { action: "deny", reasons: [reason("invalid_request", "The request could not be safely evaluated.", [])] },
    route: { pattern: "inline", path: "none", task_size: "atomic", primary_domain: "unknown", reasons: ["invalid_request"], authority: "recommendation" },
    capability_plan: { selected: [], omitted: [], missing_capabilities: [] },
    context_plan: { profile: "minimal", reasons: ["invalid_request"], authority: "recommendation" },
    trace: { rules_applied: ["validate_request"], deterministic: true },
  };
}

function sideEffects(effects) {
  return effects.filter((effect) => effect !== "read");
}

function hasApproval(approvals, capability, effect) {
  return approvals.some((approval) => approval.capability_id === capability && approval.effect === effect);
}

function addOmission(omitted, id, code, message) {
  if (!omitted.some((item) => item.id === id && item.code === code)) {
    omitted.push({ id, code, message });
  }
}

function buildPacket(request) {
  const { orchestration, signals, choice, scores, proposal, host } = validateDecisionRequest(request).normalized;
  const policy = host.policy;
  const catalog = new Map(host.capability_catalog.map((descriptor) => [descriptor.id, descriptor]));
  const requested = proposal.requested_capabilities;
  const missing = [];
  const missingSet = new Set();
  for (const requestItem of requested) {
    const descriptor = catalog.get(requestItem.id);
    if (requestItem.required && (!descriptor || !descriptor.available)) {
      missing.push(requestItem.id);
      missingSet.add(requestItem.id);
    }
  }

  const deniedEffects = proposal.effects.filter((effect) => policy.denied_effects.includes(effect));
  const deniedCapabilities = requested.filter((item) => policy.denied_capability_ids.includes(item.id)).map((item) => item.id);
  const denied = deniedEffects.length > 0 || deniedCapabilities.length > 0;
  const denyReasons = [];
  if (deniedEffects.length > 0) {
    denyReasons.push(reason("policy_denied_effect", `The requested effects are forbidden by host policy: ${deniedEffects.join(", ")}.`, requested.map((item) => item.id)));
  }
  if (deniedCapabilities.length > 0) {
    denyReasons.push(reason("policy_denied_capability", "One or more requested capabilities are forbidden by host policy.", deniedCapabilities));
  }

  const available = requested.filter((item) => {
    const descriptor = catalog.get(item.id);
    return descriptor && descriptor.available;
  });
  const reviewReasons = [];
  if (missing.length > 0) {
    reviewReasons.push(reason("required_capability_unavailable", "A required capability is not available from the host; no tool was installed or substituted.", missing));
  }
  for (const item of requested) {
    const descriptor = catalog.get(item.id);
    if (descriptor && policy.review_capability_ids.includes(item.id)) {
      reviewReasons.push(reason("policy_review_capability", "The host policy requires human review for this capability.", [item.id]));
    }
    if (descriptor && descriptor.effects.some((effect) => policy.isolation_required_effects.includes(effect)) && descriptor.isolation === "none") {
      reviewReasons.push(reason("missing_isolation", "The requested effect requires a host-managed or user-approved isolation boundary.", [item.id]));
    }
    if (descriptor && !descriptor.effects.some((effect) => proposal.effects.includes(effect))) {
      reviewReasons.push(reason("capability_effect_not_declared", "The requested capability does not advertise any of the proposed effects.", [item.id]));
    }
  }

  const approvalEffects = new Set(policy.approval_required_effects);
  available.filter((item) => !catalog.get(item.id).reversible).forEach((item) => {
    catalog.get(item.id).effects.filter((effect) => effect !== "read").forEach((effect) => approvalEffects.add(effect));
  });
  const approvalCandidates = available.filter((item) => {
    const descriptor = catalog.get(item.id);
    return descriptor.effects.some((effect) => approvalEffects.has(effect) && proposal.effects.includes(effect));
  });
  const unapproved = [];
  for (const item of approvalCandidates) {
    const descriptor = catalog.get(item.id);
    for (const effect of descriptor.effects.filter((value) => approvalEffects.has(value) && proposal.effects.includes(value))) {
      if (!hasApproval(host.approvals, item.id, effect)) unapproved.push({ id: item.id, effect });
    }
  }
  if (unapproved.length > 0) {
    reviewReasons.push(reason("approval_required", "Scoped host approval is missing for one or more side effects.", unapproved.map((item) => item.id)));
  }
  if (signals.human_approval_required) {
    const effectsToApprove = sideEffects(proposal.effects).length > 0 ? sideEffects(proposal.effects) : [proposal.action.operation];
    const humanApproved = available.length > 0 && requested.every((item) => {
      const descriptor = catalog.get(item.id);
      return descriptor && effectsToApprove.every((effect) => descriptor.effects.includes(effect) && hasApproval(host.approvals, item.id, effect));
    });
    if (!humanApproved) {
      reviewReasons.push(reason("human_approval_required", "The model marked this action as requiring human approval.", requested.map((item) => item.id)));
    }
  }
  if (signals.policy_sensitive) {
    reviewReasons.push(reason("policy_sensitive", "The action is marked policy-sensitive and cannot be silently approved.", requested.map((item) => item.id)));
  }
  if (orchestration.environment === "production" && sideEffects(proposal.effects).length > 0) {
    reviewReasons.push(reason("production_side_effect", "Production side effects require explicit host review.", requested.map((item) => item.id)));
  }
  if (proposal.action.reversibility === "irreversible" || proposal.action.reversibility === "unknown") {
    reviewReasons.push(reason("irreversible_or_unknown", "The action reversibility is irreversible or unknown.", requested.map((item) => item.id)));
  }
  if (signals.evidence_required && proposal.evidence_refs.length === 0) {
    reviewReasons.push(reason("missing_required_evidence", "The action requires evidence references, but none were supplied.", requested.map((item) => item.id)));
  }

  const hardRisk = Math.max(
    signals.destructive ? 0.9 : 0,
    signals.policy_sensitive ? 0.8 : 0,
    orchestration.environment === "production" && sideEffects(proposal.effects).length > 0 ? 0.8 : 0,
    proposal.action.reversibility === "irreversible" ? 0.9 : proposal.action.reversibility === "unknown" ? 0.7 : 0,
    ...available.map((item) => catalog.get(item.id).risk),
    ...available.filter((item) => !catalog.get(item.id).reversible && sideEffects(proposal.effects).length > 0).map(() => 0.75),
  );
  const aggregate = {
    risk: round(Math.max(scores.risk, hardRisk)),
    complexity: round(scores.complexity),
    urgency: round(Math.max(scores.urgency, signals.urgent ? 0.8 : 0)),
    confidence: round(Math.min(0.99, signals.evidence_required && proposal.evidence_refs.length === 0 ? Math.min(scores.confidence, 0.49) : scores.confidence)),
    context_pressure: round(scores.context_pressure),
  };
  aggregate.load = round(Math.max(aggregate.risk, aggregate.complexity, aggregate.context_pressure));

  if (aggregate.risk >= policy.thresholds.review_risk && unapproved.length > 0) {
    reviewReasons.push(reason("high_risk", "The aggregate risk exceeds the host review threshold while approval is incomplete.", requested.map((item) => item.id)));
  }
  if (aggregate.confidence < policy.thresholds.review_confidence) {
    reviewReasons.push(reason("low_confidence", "The model confidence is below the host review threshold.", requested.map((item) => item.id)));
  }
  if (choice.preferred_path === "human_review") {
    reviewReasons.push(reason("model_requested_review", "The model requested the human-review path.", requested.map((item) => item.id)));
  }
  if (requiredCount(requested) > policy.max_capabilities) {
    reviewReasons.push(reason("capability_budget_insufficient", "The required capability set exceeds the host capability budget.", requested.filter((item) => item.required).map((item) => item.id)));
  }

  const guardrailAction = denied ? "deny" : reviewReasons.length > 0 ? "human_review" : "approve";
  const guardrailReasons = denied ? denyReasons : reviewReasons.length > 0 ? reviewReasons : [reason("guardrails_passed", "The request passed the deterministic host policy checks.", [])];
  const pathRecommendation = denied ? "none" : guardrailAction === "human_review" ? "human_review" : choice.preferred_path === "none" ? "none" : (choice.preferred_path === "flagship" || aggregate.load >= policy.thresholds.flagship_load || choice.pattern !== "inline" || choice.task_size === "complex") ? "flagship" : "lightweight";
  const routeReasons = [];
  if (denied) routeReasons.push("guardrail_deny");
  else if (guardrailAction === "human_review") routeReasons.push("guardrail_human_review");
  else if (pathRecommendation === "none") routeReasons.push("model_requested_no_execution");
  else if (pathRecommendation === "flagship") routeReasons.push("high_capability_or_complex_path");
  else routeReasons.push("lightweight_path");

  const executionEffect = denied ? "stop" : guardrailAction === "human_review" ? "review" : pathRecommendation === "none" ? "clarify" : "execute";
  const selected = [];
  const omitted = [];
  const candidate = executionEffect === "execute"
    ? [...requested].sort((left, right) => Number(right.required) - Number(left.required))
    : [];
  for (const item of candidate) {
    const descriptor = catalog.get(item.id);
    if (!descriptor) {
      addOmission(omitted, item.id, "capability_unavailable", "The host did not advertise this capability.");
    } else if (!descriptor.available) {
      addOmission(omitted, item.id, "capability_unavailable", "The host advertised this capability as unavailable.");
    } else if (denied || guardrailAction === "human_review") {
      addOmission(omitted, item.id, guardrailAction === "deny" ? "guardrail_deny" : "guardrail_human_review", "No executable capability is exposed until the guardrail is resolved.");
    } else if (selected.length >= policy.max_capabilities) {
      addOmission(omitted, item.id, "capability_budget_exhausted", "The host capability budget was exhausted; the request remains available for a later decision.");
    } else {
      selected.push(item.id);
    }
  }
  if (executionEffect !== "execute") {
    requested.forEach((item) => addOmission(omitted, item.id, executionEffect === "review" ? "guardrail_human_review" : "execution_stopped", "No executable capability is exposed by this decision packet."));
  }

  const contextProfile = executionEffect !== "execute" || aggregate.context_pressure >= policy.thresholds.high_context_pressure ? "minimal" : (pathRecommendation === "flagship" && aggregate.complexity >= policy.thresholds.deep_complexity && aggregate.confidence >= policy.thresholds.deep_confidence && aggregate.context_pressure < policy.thresholds.high_context_pressure) ? "deep" : "standard";
  const contextReasons = [executionEffect !== "execute" ? "execution_blocked" : aggregate.context_pressure >= policy.thresholds.high_context_pressure ? "high_context_pressure" : contextProfile === "deep" ? "deep_complexity_with_capacity" : "standard_context_budget"];

  const rules = ["validate_request", "evaluate_heads", "aggregate_hard_floors", "evaluate_policy", "select_capabilities", "choose_context_profile"];
  if (denied) rules.push("deny_precedence");
  else if (guardrailAction === "human_review") rules.push("review_precedence");
  else rules.push("approve_precedence");
  if (missing.length > 0) rules.push("missing_capability_degrades_to_review");
  if (approvalEffects.size > 0) rules.push("approval_check");
  if (available.some((item) => catalog.get(item.id).isolation === "none")) rules.push("isolation_check");

  return {
    schema_version: JEV_SCHEMA_VERSION,
    task_id: request.task_id,
    orchestration_state_id: orchestration.state_id,
    capability_catalog_version: host.capability_catalog_version,
    policy_version: policy.policy_version,
    ok: true,
    execution_effect: executionEffect,
    errors: [],
    heads: {
      noul: { ...signals },
      choice: { pattern: choice.pattern, task_size: choice.task_size, preferred_path: choice.preferred_path, primary_domain: choice.primary_domain },
      score: { ...scores },
    },
    aggregate,
    guardrail: { action: guardrailAction, reasons: guardrailReasons },
    route: { pattern: choice.pattern, path: pathRecommendation, task_size: choice.task_size, primary_domain: choice.primary_domain, reasons: routeReasons, authority: "recommendation" },
    capability_plan: { selected, omitted, missing_capabilities: missing.filter((id) => missingSet.has(id)) },
    context_plan: { profile: contextProfile, reasons: contextReasons, authority: "recommendation" },
    trace: { rules_applied: rules, deterministic: true },
  };
}

function requiredCount(requested) {
  return requested.filter((item) => item.required).length;
}

/** Evaluate a request and return a deterministic, side-effect-free decision packet. */
export function decide(request) {
  const validation = validateDecisionRequest(request);
  if (!validation.ok) return invalidPacket(request, validation);
  return buildPacket(request);
}
