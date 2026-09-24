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
const REVERSIBILITIES = Object.freeze(["reversible", "partially_reversible", "irreversible", "unknown"]);
const APPROVAL_SCOPE_REQUIRED_KEYS = Object.freeze(["task_id", "operation", "reversibility", "effects", "action_scope"]);
const APPROVAL_SCOPE_OPTIONAL_KEYS = Object.freeze(["policy_version", "capability_catalog_version"]);
const APPROVAL_SCOPE_KEYS = Object.freeze([...APPROVAL_SCOPE_REQUIRED_KEYS, ...APPROVAL_SCOPE_OPTIONAL_KEYS]);
const ACTION_SCOPE_KEYS = Object.freeze(["description", "project_root", "targets"]);
const CAPABILITY_ID = /^[a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_]*)+$/;
const DATE_TIME = /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})(?:\.\d+)?(Z|[+-]\d{2}:\d{2})$/;
const DEFAULT_APPROVAL_MAX_AGE_SECONDS = 15 * 60;
const MAX_APPROVAL_MAX_AGE_SECONDS = 24 * 60 * 60;
const MAX_APPROVAL_LIFETIME_SECONDS = 24 * 60 * 60;
const THRESHOLD_KEYS = Object.freeze([
  "review_risk",
  "review_confidence",
  "flagship_load",
  "high_context_pressure",
  "deep_complexity",
  "deep_confidence",
]);
const BLOCKING_REASON_CODES = new Set([
  "approval_required",
  "approval_expired",
  "approval_future_dated",
  "approval_invalid",
  "approval_scope_mismatch",
  "approval_stale",
  "approval_window_too_long",
  "evaluation_time_required",
  "capability_budget_insufficient",
  "capability_effect_not_declared",
  "destructive_effect",
  "destructive_signal",
  "effect_coverage_incomplete",
  "high_risk",
  "human_approval_required",
  "irreversible_or_unknown",
  "low_confidence",
  "missing_isolation",
  "missing_required_evidence",
  "model_requested_review",
  "policy_review_capability",
  "policy_denied_capability",
  "policy_denied_effect",
  "policy_sensitive",
  "production_side_effect",
  "required_capability_unavailable",
  "invalid_request",
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

function validateActionScope(value, prefix, errors) {
  const scope = objectValue(value, prefix, errors);
  if (!scope) return null;
  checkKeys(scope, ACTION_SCOPE_KEYS, ACTION_SCOPE_KEYS, prefix, errors);
  stringValue(scope.description, `${prefix}.description`, errors, { max: 2000 });
  if (scope.project_root !== null && !nonEmpty(scope.project_root)) {
    errors.push(error("invalid_string", "project_root must be a non-empty string or null.", `${prefix}.project_root`, "Use null when the action is not project-scoped."));
  }
  stringArray(scope.targets, `${prefix}.targets`, errors);
  return scope;
}

function validateAction(value, errors) {
  const action = objectValue(value, "model_assessment.proposal.action", errors);
  if (!action) return null;
  checkKeys(action, ["operation", "reversibility", "scope"], ["operation", "reversibility", "scope"], "model_assessment.proposal.action", errors);
  enumValue(action.operation, EFFECTS, "model_assessment.proposal.action.operation", errors);
  enumValue(action.reversibility, REVERSIBILITIES, "model_assessment.proposal.action.reversibility", errors);
  validateActionScope(action.scope, "model_assessment.proposal.action.scope", errors);
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
  const keys = ["policy_version", "denied_capability_ids", "review_capability_ids", "denied_effects", "approval_required_effects", "isolation_required_effects", "thresholds", "max_capabilities", "approval_max_age_seconds"];
  checkKeys(policy, keys, keys.filter((key) => key !== "approval_max_age_seconds"), "host_facts.policy", errors);
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
  if (has(policy, "approval_max_age_seconds") && (!Number.isInteger(policy.approval_max_age_seconds) || policy.approval_max_age_seconds < 1 || policy.approval_max_age_seconds > MAX_APPROVAL_MAX_AGE_SECONDS)) {
    errors.push(error("invalid_range", `approval_max_age_seconds must be an integer from 1 through ${MAX_APPROVAL_MAX_AGE_SECONDS}.`, "host_facts.policy.approval_max_age_seconds", "Set a bounded approval freshness window."));
  }
  return policy;
}

// Parse only caller-supplied timestamps. The reference kernel never reads the
// ambient clock; evaluation time is an explicit input.
function timestampMilliseconds(value) {
  if (typeof value !== "string") return null;
  const match = DATE_TIME.exec(value);
  if (!match) return null;
  const year = Number(match[1]);
  const month = Number(match[2]);
  const day = Number(match[3]);
  const hour = Number(match[4]);
  const minute = Number(match[5]);
  const second = Number(match[6]);
  const zone = match[7];
  const leapYear = year % 4 === 0 && (year % 100 !== 0 || year % 400 === 0);
  const daysInMonth = [31, leapYear ? 29 : 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];
  if (month < 1 || month > 12 || day < 1 || day > daysInMonth[month - 1] || hour > 23 || minute > 59 || second > 59) return null;
  if (zone !== "Z") {
    const offsetHour = Number(zone.slice(1, 3));
    const offsetMinute = Number(zone.slice(4, 6));
    if (offsetHour > 23 || offsetMinute > 59) return null;
  }
  const milliseconds = Date.parse(value);
  return Number.isFinite(milliseconds) ? milliseconds : null;
}

function validateTimestamp(value, prefix, errors) {
  const milliseconds = timestampMilliseconds(value);
  if (milliseconds === null) {
    errors.push(error("invalid_format", "Expected a valid ISO-8601 date-time string.", prefix, "Use a value such as 2026-09-24T00:00:00Z."));
  }
  return milliseconds;
}

function validateApprovalScope(value, prefix, errors) {
  const scope = objectValue(value, prefix, errors);
  if (!scope) return null;
  checkKeys(scope, APPROVAL_SCOPE_KEYS, APPROVAL_SCOPE_REQUIRED_KEYS, prefix, errors);
  stringValue(scope.task_id, `${prefix}.task_id`, errors, { max: 200 });
  if (has(scope, "policy_version")) stringValue(scope.policy_version, `${prefix}.policy_version`, errors, { max: 200 });
  if (has(scope, "capability_catalog_version")) stringValue(scope.capability_catalog_version, `${prefix}.capability_catalog_version`, errors, { max: 200 });
  enumValue(scope.operation, EFFECTS, `${prefix}.operation`, errors);
  enumValue(scope.reversibility, REVERSIBILITIES, `${prefix}.reversibility`, errors);
  const effects = arrayValue(scope.effects, `${prefix}.effects`, errors);
  if (effects.length === 0) errors.push(error("empty_effects", "An approval scope must declare at least one effect.", `${prefix}.effects`, "Bind the approval to the complete proposed effect set."));
  effects.forEach((item, index) => enumValue(item, EFFECTS, `${prefix}.effects[${index}]`, errors));
  if (!unique(effects)) errors.push(error("duplicate_value", "Approval scope effects must be unique.", `${prefix}.effects`, "Remove duplicate effects."));
  if (effects.length > 0 && !effects.includes(scope.operation)) {
    errors.push(error("approval_scope_effect_mismatch", "The approval scope operation must be included in its effects.", `${prefix}.operation`, "Include the operation in scope.effects."));
  }
  validateActionScope(scope.action_scope, `${prefix}.action_scope`, errors);
  return scope;
}

function validateApproval(value, prefix, errors) {
  const approval = objectValue(value, prefix, errors);
  if (!approval) return null;
  const keys = ["capability_id", "effect", "scope", "confirmed_at", "expires_at"];
  checkKeys(approval, keys, keys, prefix, errors);
  capabilityId(approval.capability_id, `${prefix}.capability_id`, errors);
  enumValue(approval.effect, EFFECTS, `${prefix}.effect`, errors);
  const scope = validateApprovalScope(approval.scope, `${prefix}.scope`, errors);
  if (scope && Array.isArray(scope.effects) && scope.effects.length > 0 && !scope.effects.includes(approval.effect)) {
    errors.push(error("approval_effect_not_in_scope", "The approved effect must be included in the canonical action scope.", `${prefix}.effect`, "Issue an approval for an effect declared by the action scope."));
  }
  const confirmedAt = validateTimestamp(approval.confirmed_at, `${prefix}.confirmed_at`, errors);
  const expiresAt = validateTimestamp(approval.expires_at, `${prefix}.expires_at`, errors);
  if (confirmedAt !== null && expiresAt !== null && confirmedAt >= expiresAt) {
    errors.push(error("approval_window_invalid", "confirmed_at must be earlier than expires_at.", prefix, "Use a bounded approval window with confirmed_at before expires_at."));
  }
  return approval;
}

function resolveEvaluationTime(input, override, errors) {
  const candidates = [];
  const add = (value, fieldPath) => {
    if (value === undefined) return;
    const milliseconds = timestampMilliseconds(value);
    if (milliseconds === null) {
      errors.push(error("invalid_format", "Evaluation time must be a valid ISO-8601 date-time string.", fieldPath, "Pass an explicit evaluation time; the kernel never reads an ambient clock."));
      return;
    }
    candidates.push({ value, milliseconds });
  };

  if (isRecord(input)) {
    add(input.evaluation_time, "evaluation_time");
    add(input.evaluated_at, "evaluated_at");
    if (isRecord(input.host_facts)) {
      add(input.host_facts.evaluation_time, "host_facts.evaluation_time");
      add(input.host_facts.evaluated_at, "host_facts.evaluated_at");
    }
  }
  if (override !== undefined && override !== null) {
    if (isRecord(override)) {
      add(override.evaluation_time, "options.evaluation_time");
      add(override.evaluated_at, "options.evaluated_at");
      add(override.evaluationTime, "options.evaluationTime");
      add(override.now, "options.now");
    } else {
      add(override, "options.evaluation_time");
    }
  }
  if (candidates.length === 0) return null;
  const first = candidates[0];
  if (candidates.some((candidate) => candidate.milliseconds !== first.milliseconds)) {
    errors.push(error("conflicting_evaluation_time", "All supplied evaluation-time values must agree.", "evaluation_time", "Use one explicit evaluation time for the request and evaluation call."));
  }
  return first.milliseconds;
}

function validateHostFacts(value, errors) {
  const host = objectValue(value, "host_facts", errors);
  if (!host) return null;
  const keys = ["capability_catalog_version", "capability_catalog", "policy", "approvals", "evaluation_time", "evaluated_at"];
  checkKeys(host, keys, keys.filter((key) => !["evaluation_time", "evaluated_at"].includes(key)), "host_facts", errors);
  stringValue(host.capability_catalog_version, "host_facts.capability_catalog_version", errors, { max: 200 });
  if (has(host, "evaluation_time")) validateTimestamp(host.evaluation_time, "host_facts.evaluation_time", errors);
  if (has(host, "evaluated_at")) validateTimestamp(host.evaluated_at, "host_facts.evaluated_at", errors);
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
export function validateDecisionRequest(input, evaluationTime = undefined) {
  const errors = [];
  if (!isRecord(input)) {
    errors.push(error("invalid_type", "The decision request must be an object.", "$", "Provide an object matching jev-decision-request.schema.json."));
    return { ok: false, errors, normalized: null };
  }
  const allowed = ["schema_version", "task_id", "evaluation_time", "evaluated_at", "orchestration_state", "model_assessment", "host_facts"];
  const required = ["schema_version", "task_id", "orchestration_state", "model_assessment", "host_facts"];
  checkKeys(input, allowed, required, "$", errors);
  if (input.schema_version !== JEV_SCHEMA_VERSION) {
    errors.push(error("unsupported_schema_version", `Expected schema_version ${JEV_SCHEMA_VERSION}.`, "schema_version", "Use the version supported by this host adapter."));
  }
  stringValue(input.task_id, "task_id", errors, { max: 200 });
  if (has(input, "evaluation_time")) validateTimestamp(input.evaluation_time, "evaluation_time", errors);
  if (has(input, "evaluated_at")) validateTimestamp(input.evaluated_at, "evaluated_at", errors);
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
  const evaluationTimeMs = resolveEvaluationTime(input, evaluationTime, errors);
  return { ok: errors.length === 0, errors, normalized: { orchestration, signals, choice, scores, proposal, host, evaluationTimeMs } };
}

function reason(code, message, capabilityIds = [], remedy = undefined, fieldPath = undefined) {
  const result = { code, message, capability_ids: [...new Set(capabilityIds)] };
  if (remedy !== undefined) result.remedy = remedy;
  if (fieldPath !== undefined) result.path = fieldPath;
  return result;
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
  const errors = validation.errors.map((item) => {
    const result = reason(item.code, item.message, []);
    if (item.path !== undefined) result.path = item.path;
    if (item.remedy !== undefined) result.remedy = item.remedy;
    return result;
  });
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

function sortedUnique(values) {
  return [...new Set(values)].sort();
}

function sameStringSet(left, right) {
  const normalizedLeft = sortedUnique(left);
  const normalizedRight = sortedUnique(right);
  return normalizedLeft.length === normalizedRight.length && normalizedLeft.every((value, index) => value === normalizedRight[index]);
}

function approvalScopeMatches(approval, request) {
  const scope = approval?.scope;
  const action = request?.model_assessment?.proposal?.action;
  const proposal = request?.model_assessment?.proposal;
  if (!isRecord(scope) || !isRecord(action) || !isRecord(action.scope) || !isRecord(scope.action_scope) || !Array.isArray(scope.effects) || !Array.isArray(proposal?.effects)) return false;
  return scope.task_id === request.task_id
    && (scope.policy_version === undefined || scope.policy_version === request.host_facts.policy.policy_version)
    && (scope.capability_catalog_version === undefined || scope.capability_catalog_version === request.host_facts.capability_catalog_version)
    && scope.operation === action.operation
    && scope.reversibility === action.reversibility
    && sameStringSet(scope.effects, proposal.effects)
    && scope.action_scope.description === action.scope.description
    && scope.action_scope.project_root === action.scope.project_root
    && sameStringSet(scope.action_scope.targets, action.scope.targets);
}

function approvalStatus(approvals, request, capability, effect, evaluationTimeMs, policy) {
  const candidates = approvals.filter((approval) => approval.capability_id === capability && approval.effect === effect);
  if (candidates.length === 0) {
    return {
      approved: false,
      code: "approval_required",
      message: "Scoped host approval is missing for this capability and effect.",
    };
  }
  if (evaluationTimeMs === null || evaluationTimeMs === undefined) {
    return {
      approved: false,
      code: "evaluation_time_required",
      message: "An explicit evaluation time is required before an approval can be used.",
    };
  }
  const maxAgeSeconds = Number.isInteger(policy.approval_max_age_seconds) ? policy.approval_max_age_seconds : DEFAULT_APPROVAL_MAX_AGE_SECONDS;
  let issue = null;
  for (const approval of candidates) {
    const confirmedAt = timestampMilliseconds(approval.confirmed_at);
    const expiresAt = timestampMilliseconds(approval.expires_at);
    if (confirmedAt === null || expiresAt === null) {
      issue = { code: "approval_invalid", message: "The approval does not contain a valid bounded time window." };
      continue;
    }
    if (!approvalScopeMatches(approval, request)) {
      issue = { code: "approval_scope_mismatch", message: "The approval is not bound to this task, action, and effect set." };
      continue;
    }
    if (confirmedAt > evaluationTimeMs) {
      issue = { code: "approval_future_dated", message: "The approval confirmation is later than the evaluation time." };
      continue;
    }
    if (expiresAt <= evaluationTimeMs) {
      issue = { code: "approval_expired", message: "The approval is expired at the evaluation time." };
      continue;
    }
    if (evaluationTimeMs - confirmedAt > maxAgeSeconds * 1000) {
      issue = { code: "approval_stale", message: "The approval is older than the host freshness window." };
      continue;
    }
    if (expiresAt - confirmedAt > MAX_APPROVAL_LIFETIME_SECONDS * 1000) {
      issue = { code: "approval_window_too_long", message: "The approval lifetime exceeds the host's bounded confirmation window." };
      continue;
    }
    return { approved: true, code: "approval_valid", message: "The approval is fresh and bound to the requested action." };
  }
  return issue || { code: "approval_required", message: "Scoped host approval is missing for this capability and effect." };
}

function effectCoverage(proposal, requested, catalog, selectedIds = null) {
  const covered = new Set();
  for (const item of requested) {
    if (selectedIds && !selectedIds.has(item.id)) continue;
    const descriptor = catalog.get(item.id);
    if (!descriptor || !descriptor.available) continue;
    for (const effect of descriptor.effects) {
      if (proposal.effects.includes(effect)) covered.add(effect);
    }
  }
  return {
    covered: [...covered].sort(),
    uncovered: proposal.effects.filter((effect) => !covered.has(effect)).sort(),
  };
}

function addOmission(omitted, id, code, message) {
  if (!omitted.some((item) => item.id === id && item.code === code)) {
    omitted.push({ id, code, message });
  }
}

function orderedRequested(requested) {
  return requested
    .map((item, index) => ({ item, index }))
    .sort((left, right) => Number(right.item.required) - Number(left.item.required) || left.index - right.index)
    .map(({ item }) => item);
}

function buildPacket(request, validation = validateDecisionRequest(request), evaluationTime = undefined) {
  const normalized = validation.normalized || validateDecisionRequest(request, evaluationTime).normalized;
  const { orchestration, signals, choice, scores, proposal, host, evaluationTimeMs } = normalized;
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
  if (sideEffects(proposal.effects).length > 0 && (evaluationTimeMs === null || evaluationTimeMs === undefined)) {
    reviewReasons.push(reason("evaluation_time_required", "Side effects cannot be evaluated without an explicit evaluation time.", requested.map((item) => item.id)));
  }
  if (host.approvals.length > 0 && (evaluationTimeMs === null || evaluationTimeMs === undefined)) {
    reviewReasons.push(reason("evaluation_time_required", "Approvals cannot be evaluated without an explicit evaluation time.", host.approvals.map((approval) => approval.capability_id).filter((id, index, ids) => ids.indexOf(id) === index)));
  }
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
  const approvalIssues = new Map();
  for (const item of approvalCandidates) {
    const descriptor = catalog.get(item.id);
    for (const effect of descriptor.effects.filter((value) => approvalEffects.has(value) && proposal.effects.includes(value))) {
      const status = approvalStatus(host.approvals, request, item.id, effect, evaluationTimeMs, policy);
      if (!status.approved) {
        unapproved.push({ id: item.id, effect });
        if (!approvalIssues.has(status.code)) approvalIssues.set(status.code, { message: status.message, ids: new Set() });
        approvalIssues.get(status.code).ids.add(item.id);
      }
    }
  }
  for (const [code, issue] of approvalIssues) {
    reviewReasons.push(reason(code, issue.message, [...issue.ids].sort()));
  }
  if (unapproved.length > 0 && !reviewReasons.some((item) => item.code === "approval_required")) {
    reviewReasons.push(reason("approval_required", "Scoped host approval is missing, invalid, or not fresh for one or more side effects.", unapproved.map((item) => item.id)));
  }
  if (signals.human_approval_required) {
    const effectsToApprove = sideEffects(proposal.effects).length > 0 ? sideEffects(proposal.effects) : [proposal.action.operation];
    const humanApproved = available.length > 0 && requested.every((item) => {
      const descriptor = catalog.get(item.id);
      return descriptor && effectsToApprove.every((effect) => descriptor.effects.includes(effect) && approvalStatus(host.approvals, request, item.id, effect, evaluationTimeMs, policy).approved);
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
  if (signals.destructive) {
    reviewReasons.push(reason("destructive_signal", "A destructive signal always requires human review; risk scoring cannot authorize the action.", requested.map((item) => item.id)));
  }
  if (proposal.action.operation === "delete" || proposal.effects.includes("delete")) {
    reviewReasons.push(reason("destructive_effect", "Delete effects always require human review.", requested.map((item) => item.id)));
  }
  if (signals.evidence_required && proposal.evidence_refs.length === 0) {
    reviewReasons.push(reason("missing_required_evidence", "The action requires evidence references, but none were supplied.", requested.map((item) => item.id)));
  }

  const hardRisk = Math.max(
    signals.destructive || proposal.effects.includes("delete") ? 0.9 : 0,
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

  const ordered = orderedRequested(requested);
  const plannedSelected = [];
  for (const item of ordered) {
    const descriptor = catalog.get(item.id);
    if (!descriptor || !descriptor.available) continue;
    if (!descriptor.effects.some((effect) => proposal.effects.includes(effect))) continue;
    if (plannedSelected.length >= policy.max_capabilities) break;
    plannedSelected.push(item.id);
  }
  const coverage = effectCoverage(proposal, requested, catalog, new Set(plannedSelected));
  if (coverage.uncovered.length > 0) {
    reviewReasons.push(reason("effect_coverage_incomplete", `The selected capability set does not cover every proposed effect: ${coverage.uncovered.join(", ")}.`, plannedSelected, "Select descriptors covering every proposed effect before execution.", "model_assessment.proposal.effects"));
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
  const selected = executionEffect === "execute" ? plannedSelected : [];
  const omitted = [];
  if (executionEffect === "execute") {
    for (const item of ordered) {
      const descriptor = catalog.get(item.id);
      if (!descriptor) {
        addOmission(omitted, item.id, "capability_unavailable", "The host did not advertise this capability.");
      } else if (!descriptor.available) {
        addOmission(omitted, item.id, "capability_unavailable", "The host advertised this capability as unavailable.");
      } else if (!selected.includes(item.id)) {
        addOmission(omitted, item.id, "capability_budget_exhausted", "The host capability budget was exhausted; the request remains available for a later decision.");
      }
    }
  } else {
    requested.forEach((item) => addOmission(omitted, item.id, executionEffect === "review" ? "guardrail_human_review" : "execution_stopped", "No executable capability is exposed by this decision packet."));
  }

  const contextProfile = executionEffect !== "execute" || aggregate.context_pressure >= policy.thresholds.high_context_pressure ? "minimal" : (pathRecommendation === "flagship" && aggregate.complexity >= policy.thresholds.deep_complexity && aggregate.confidence >= policy.thresholds.deep_confidence && aggregate.context_pressure < policy.thresholds.high_context_pressure) ? "deep" : "standard";
  const contextReasons = [executionEffect !== "execute" ? "execution_blocked" : aggregate.context_pressure >= policy.thresholds.high_context_pressure ? "high_context_pressure" : contextProfile === "deep" ? "deep_complexity_with_capacity" : "standard_context_budget"];

  const rules = ["validate_request", "evaluate_heads", "aggregate_hard_floors", "evaluate_policy", "select_capabilities", "effect_coverage_check", "choose_context_profile"];
  if (denied) rules.push("deny_precedence");
  else if (guardrailAction === "human_review") rules.push("review_precedence");
  else rules.push("approve_precedence");
  if (missing.length > 0) rules.push("missing_capability_degrades_to_review");
  if (approvalCandidates.length > 0) rules.push("approval_check");
  if (coverage.uncovered.length > 0) rules.push("effect_coverage_incomplete");
  if (signals.destructive || proposal.effects.includes("delete")) rules.push("destructive_review_floor");
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

function packetIssue(code, message, fieldPath, remedy = undefined) {
  return error(code, message, fieldPath, remedy);
}

function validatePacketReasons(value, fieldPath, errors) {
  if (!Array.isArray(value)) {
    errors.push(packetIssue("invalid_type", "Packet reason lists must be arrays.", fieldPath));
    return [];
  }
  value.forEach((item, index) => {
    if (!isRecord(item) || !nonEmpty(item.code) || !nonEmpty(item.message) || !Array.isArray(item.capability_ids)) {
      errors.push(packetIssue("invalid_reason", "Each packet reason must contain code, message, and capability_ids.", `${fieldPath}[${index}]`));
    }
  });
  return value;
}

/**
 * Validate packet-level invariants and, when the originating request is
 * supplied, prove that every proposed effect is covered by selected,
 * available, policy-allowed requested descriptors.
 */
export function validateDecisionPacket(packet, request = undefined, evaluationTime = undefined) {
  const errors = [];
  if (!isRecord(packet)) {
    errors.push(packetIssue("invalid_type", "The decision packet must be an object.", "$", "Provide a packet matching jev-decision-packet.schema.json."));
    return { ok: false, errors };
  }
  if (packet.schema_version !== JEV_SCHEMA_VERSION) {
    errors.push(packetIssue("unsupported_schema_version", `Expected schema_version ${JEV_SCHEMA_VERSION}.`, "schema_version", "Use the version supported by this host adapter."));
  }
  if (!["execute", "review", "clarify", "stop"].includes(packet.execution_effect)) {
    errors.push(packetIssue("invalid_execution_effect", "Packet execution_effect is not a versioned JEV outcome.", "execution_effect", "Use execute, review, clarify, or stop."));
  }
  if (!nonEmpty(packet.task_id)) errors.push(packetIssue("invalid_string", "Packet task_id must be a non-empty string.", "task_id", "Bind the packet to the evaluated task."));
  if (typeof packet.ok !== "boolean") errors.push(packetIssue("invalid_type", "Packet ok must be a boolean.", "ok"));
  validatePacketReasons(packet.errors, "errors", errors);
  if (!isRecord(packet.guardrail) || !["approve", "human_review", "deny"].includes(packet.guardrail.action)) {
    errors.push(packetIssue("invalid_guardrail", "Packet guardrail.action is invalid.", "guardrail.action", "Use approve, human_review, or deny."));
  } else {
    validatePacketReasons(packet.guardrail.reasons, "guardrail.reasons", errors);
  }
  if (!isRecord(packet.route) || !["lightweight", "flagship", "human_review", "none"].includes(packet.route.path)) {
    errors.push(packetIssue("invalid_route", "Packet route.path is invalid.", "route.path", "Use a versioned route path."));
  }
  if (!isRecord(packet.trace) || packet.trace.deterministic !== true) {
    errors.push(packetIssue("non_deterministic_packet", "Packet trace must explicitly be deterministic.", "trace.deterministic"));
  }
  if (packet.heads?.noul?.destructive === true && packet.execution_effect === "execute") {
    errors.push(packetIssue("destructive_signal", "Destructive signals cannot appear in an executable packet.", "heads.noul.destructive"));
  }
  const plan = isRecord(packet.capability_plan) ? packet.capability_plan : null;
  const selected = plan && Array.isArray(plan.selected) ? plan.selected : [];
  const missing = plan && Array.isArray(plan.missing_capabilities) ? plan.missing_capabilities : [];
  const omitted = plan && Array.isArray(plan.omitted) ? plan.omitted : [];
  if (!plan || !Array.isArray(plan.selected) || !Array.isArray(plan.missing_capabilities) || !Array.isArray(plan.omitted)) {
    errors.push(packetIssue("invalid_capability_plan", "Packet capability_plan has an invalid shape.", "capability_plan", "Provide selected, omitted, and missing_capabilities arrays."));
  }
  if (selected.length > 0 && new Set(selected).size !== selected.length) {
    errors.push(packetIssue("duplicate_value", "Packet selected capability IDs must be unique.", "capability_plan.selected"));
  }
  if (missing.length > 0 && new Set(missing).size !== missing.length) {
    errors.push(packetIssue("duplicate_value", "Packet missing capability IDs must be unique.", "capability_plan.missing_capabilities"));
  }
  for (const [index, item] of omitted.entries()) {
    if (!isRecord(item) || !nonEmpty(item.id) || !nonEmpty(item.code) || !nonEmpty(item.message)) {
      errors.push(packetIssue("invalid_omission", "Packet capability_plan.omitted entries must contain id, code, and message strings.", `capability_plan.omitted[${index}]`));
    }
  }
  for (const [index, id] of selected.entries()) {
    if (typeof id !== "string" || !CAPABILITY_ID.test(id)) errors.push(packetIssue("invalid_capability_id", "Packet selected capability IDs must be canonical strings.", `capability_plan.selected[${index}]`));
  }
  for (const [index, id] of missing.entries()) {
    if (typeof id !== "string" || !CAPABILITY_ID.test(id)) errors.push(packetIssue("invalid_capability_id", "Packet missing capability IDs must be canonical strings.", `capability_plan.missing_capabilities[${index}]`));
  }
  if (packet.execution_effect === "execute") {
    if (packet.ok !== true) errors.push(packetIssue("executable_packet_not_ok", "Executable packets must set ok=true.", "ok"));
    if (!Array.isArray(packet.errors) || packet.errors.length !== 0) errors.push(packetIssue("executable_packet_has_errors", "Executable packets cannot contain errors.", "errors"));
    if (packet.guardrail?.action !== "approve") errors.push(packetIssue("executable_packet_not_approved", "Executable packets require an approve guardrail.", "guardrail.action"));
    if (selected.length === 0) errors.push(packetIssue("executable_packet_without_selection", "Executable packets must select at least one capability.", "capability_plan.selected"));
    if (missing.length > 0) errors.push(packetIssue("executable_packet_has_missing_capabilities", "Executable packets cannot contain missing capabilities.", "capability_plan.missing_capabilities"));
    for (const id of missing) {
      if (selected.includes(id)) errors.push(packetIssue("contradictory_capability_coverage", "A capability cannot be both selected and reported missing.", "capability_plan"));
    }
    if (packet.route?.path !== "lightweight" && packet.route?.path !== "flagship") errors.push(packetIssue("executable_packet_route", "Executable packets require a lightweight or flagship route.", "route.path"));
    const reasonCodes = Array.isArray(packet.guardrail?.reasons) ? packet.guardrail.reasons.map((item) => item?.code) : [];
    if (reasonCodes.some((code) => BLOCKING_REASON_CODES.has(code))) {
      errors.push(packetIssue("executable_packet_has_blocking_reason", "Executable packets cannot contain a blocking guardrail reason.", "guardrail.reasons", "Resolve the blocking reason before selecting capabilities."));
    }
  } else {
    if (selected.length > 0) errors.push(packetIssue("non_executable_packet_has_selection", "Non-executable packets cannot select capabilities.", "capability_plan.selected"));
    if (packet.guardrail?.action === "deny" && packet.execution_effect !== "stop") errors.push(packetIssue("deny_packet_not_stopped", "Denied packets must stop execution.", "execution_effect"));
    if (packet.guardrail?.action === "human_review" && packet.execution_effect !== "review") errors.push(packetIssue("review_packet_not_reviewed", "Human-review packets must remain in review.", "execution_effect"));
    if (packet.guardrail?.action === "approve" && ["review", "stop"].includes(packet.execution_effect)) errors.push(packetIssue("approved_packet_is_blocked", "An approved guardrail cannot produce a blocked execution effect.", "execution_effect"));
  }
  if (packet.ok === true && Array.isArray(packet.errors) && packet.errors.length > 0) {
    errors.push(packetIssue("ok_packet_has_errors", "A packet cannot be marked ok while carrying errors.", "errors"));
  }
  if (packet.ok === false && packet.guardrail?.action === "approve") {
    errors.push(packetIssue("failed_packet_approved", "A packet marked not-ok cannot carry an approve guardrail.", "guardrail.action"));
  }

  if (request !== undefined) {
    const requestValidation = validateDecisionRequest(request, evaluationTime);
    if (!requestValidation.ok) {
      errors.push(packetIssue("invalid_originating_request", "The originating request is not valid for packet semantic validation.", "$"));
    } else {
      const normalized = requestValidation.normalized;
      if (packet.task_id !== request.task_id) errors.push(packetIssue("packet_task_mismatch", "Packet task_id does not match the originating request.", "task_id"));
      if (packet.orchestration_state_id !== normalized.orchestration.state_id) errors.push(packetIssue("packet_state_mismatch", "Packet orchestration state does not match the originating request.", "orchestration_state_id"));
      if (packet.capability_catalog_version !== normalized.host.capability_catalog_version) errors.push(packetIssue("packet_catalog_mismatch", "Packet capability catalog version does not match the originating request.", "capability_catalog_version"));
      if (packet.policy_version !== normalized.host.policy.policy_version) errors.push(packetIssue("packet_policy_mismatch", "Packet policy version does not match the originating request.", "policy_version"));
      if (!isRecord(packet.heads)) {
        errors.push(packetIssue("invalid_packet_heads", "Packet heads are missing or malformed.", "heads"));
      } else {
        const expectedNoul = normalized.signals;
        const actualNoul = isRecord(packet.heads.noul) ? packet.heads.noul : {};
        for (const key of ["urgent", "destructive", "policy_sensitive", "human_approval_required", "evidence_required"]) {
          if (actualNoul[key] !== expectedNoul[key]) errors.push(packetIssue("packet_noul_mismatch", `Packet head ${key} does not match the originating request.`, `heads.noul.${key}`));
        }
        const expectedChoice = normalized.choice;
        const actualChoice = isRecord(packet.heads.choice) ? packet.heads.choice : {};
        for (const key of ["pattern", "task_size", "preferred_path", "primary_domain"]) {
          if (actualChoice[key] !== expectedChoice[key]) errors.push(packetIssue("packet_choice_mismatch", `Packet head ${key} does not match the originating request.`, `heads.choice.${key}`));
        }
        const expectedScore = normalized.scores;
        const actualScore = isRecord(packet.heads.score) ? packet.heads.score : {};
        for (const key of ["risk", "complexity", "urgency", "confidence", "context_pressure"]) {
          if (actualScore[key] !== expectedScore[key]) errors.push(packetIssue("packet_score_mismatch", `Packet head ${key} does not match the originating request.`, `heads.score.${key}`));
        }
      }
      if (packet.execution_effect === "execute") {
        const catalog = new Map(normalized.host.capability_catalog.map((descriptor) => [descriptor.id, descriptor]));
        const requested = new Map(normalized.proposal.requested_capabilities.map((item) => [item.id, item]));
        const proposal = normalized.proposal;
        const policy = normalized.host.policy;
        if (proposal.effects.some((effect) => policy.denied_effects.includes(effect))) errors.push(packetIssue("policy_denied_effect", "A packet cannot execute an effect denied by the originating policy.", "capability_plan.selected"));
        if (normalized.signals.destructive || proposal.action.operation === "delete" || proposal.effects.includes("delete")) errors.push(packetIssue("destructive_signal", "Destructive signals and delete effects cannot be executable.", "guardrail.action"));
        if (proposal.action.reversibility === "irreversible" || proposal.action.reversibility === "unknown") errors.push(packetIssue("irreversible_or_unknown", "Irreversible or unknown actions cannot be executable.", "guardrail.action"));
        if (normalized.signals.policy_sensitive) errors.push(packetIssue("policy_sensitive", "Policy-sensitive actions cannot be executable without review.", "guardrail.action"));
        if (normalized.orchestration.environment === "production" && sideEffects(proposal.effects).length > 0) errors.push(packetIssue("production_side_effect", "Production side effects cannot be executable without review.", "guardrail.action"));
        if (normalized.choice.preferred_path === "human_review") errors.push(packetIssue("model_requested_review", "A model-requested human-review path cannot be executable.", "guardrail.action"));
        if (normalized.signals.evidence_required && proposal.evidence_refs.length === 0) errors.push(packetIssue("missing_required_evidence", "Executable actions cannot omit required evidence references.", "guardrail.action"));
        if (normalized.scores.confidence < policy.thresholds.review_confidence) errors.push(packetIssue("low_confidence", "Executable actions require confidence at or above the host review threshold.", "guardrail.action"));
        for (const id of selected) {
          if (typeof id !== "string" || !requested.has(id)) errors.push(packetIssue("selected_capability_not_requested", "Every selected capability must be requested by the originating action.", "capability_plan.selected"));
          const descriptor = catalog.get(id);
          if (!descriptor || !descriptor.available) errors.push(packetIssue("selected_capability_unavailable", "Every selected capability must be available in the originating host facts.", "capability_plan.selected"));
          if (policy.denied_capability_ids.includes(id)) errors.push(packetIssue("selected_capability_denied", "A policy-denied capability cannot appear in an executable selection.", "capability_plan.selected"));
          if (descriptor && policy.review_capability_ids.includes(id)) errors.push(packetIssue("policy_review_capability", "A policy-review capability cannot appear in an executable selection.", "capability_plan.selected"));
          if (descriptor && descriptor.effects.some((effect) => policy.isolation_required_effects.includes(effect)) && descriptor.isolation === "none") errors.push(packetIssue("missing_isolation", "A selected capability lacks the required isolation boundary.", "capability_plan.selected"));
        }
        const approvalEffects = new Set(policy.approval_required_effects);
        for (const id of selected) {
          const descriptor = catalog.get(id);
          if (descriptor && !descriptor.reversible) {
            descriptor.effects.filter((effect) => effect !== "read").forEach((effect) => approvalEffects.add(effect));
          }
        }
        for (const id of selected) {
          const descriptor = catalog.get(id);
          if (!descriptor) continue;
          for (const effect of descriptor.effects.filter((value) => approvalEffects.has(value) && proposal.effects.includes(value))) {
            const status = approvalStatus(normalized.host.approvals, request, id, effect, normalized.evaluationTimeMs, policy);
            if (!status.approved) errors.push(packetIssue(status.code, status.message, "guardrail.reasons"));
          }
        }
        if (normalized.signals.human_approval_required) {
          const effectsToApprove = sideEffects(proposal.effects).length > 0 ? sideEffects(proposal.effects) : [proposal.action.operation];
          const humanApproved = requested.size > 0 && [...requested.values()].every((item) => {
            const descriptor = catalog.get(item.id);
            return descriptor && effectsToApprove.every((effect) => descriptor.effects.includes(effect) && approvalStatus(normalized.host.approvals, request, item.id, effect, normalized.evaluationTimeMs, policy).approved);
          });
          if (!humanApproved) errors.push(packetIssue("human_approval_required", "The action requires human approval that is not present and fresh.", "guardrail.action"));
        }
        for (const item of normalized.proposal.requested_capabilities.filter((candidate) => candidate.required)) {
          if (!selected.includes(item.id)) errors.push(packetIssue("required_capability_not_selected", "Every required requested capability must be selected before execution.", "capability_plan.selected"));
        }
        const selectedSet = new Set(selected);
        const coverage = effectCoverage(normalized.proposal, normalized.proposal.requested_capabilities, catalog, selectedSet);
        if (coverage.uncovered.length > 0) {
          errors.push(packetIssue("effect_coverage_incomplete", `The selected capability set does not cover every proposed effect: ${coverage.uncovered.join(", ")}.`, "capability_plan.selected", "Select descriptors covering every proposed effect."));
        }
        if (missing.length > 0 && selected.length > 0) errors.push(packetIssue("contradictory_capability_coverage", "A packet cannot both report missing capabilities and select executable capabilities.", "capability_plan"));
        for (const item of omitted) {
          if (isRecord(item) && selected.includes(item.id)) errors.push(packetIssue("contradictory_capability_omission", "A selected capability cannot also be omitted.", "capability_plan.omitted"));
        }
      }
    }
  }
  return { ok: errors.length === 0, errors };
}

/** Evaluate a request and return a deterministic, side-effect-free decision packet. */
export function decide(request, evaluationTime = undefined) {
  const validation = validateDecisionRequest(request, evaluationTime);
  if (!validation.ok) return invalidPacket(request, validation);
  const packet = buildPacket(request, validation, evaluationTime);
  const semantic = validateDecisionPacket(packet, request, evaluationTime);
  if (!semantic.ok) return invalidPacket(request, semantic);
  return packet;
}
