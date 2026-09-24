"""Small dependency-free contracts shared by the durable runtime.

The JSON Schemas under ``runtime/schemas`` remain canonical.  This module
provides a strict boundary check for the legacy Python compatibility surface
without introducing a package-manager or provider dependency.
"""
from __future__ import annotations

import copy
import hashlib
import json
import math
import re
from pathlib import Path
from typing import Any, Mapping


class ContractError(ValueError):
    """Raised when a runtime boundary receives an invalid contract."""


_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
_CAPABILITY_RE = re.compile(r"^[a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_]*)+$")
_FINGERPRINT_RE = re.compile(r"^[a-f0-9]{64}$")

EXECUTION_EFFECTS = frozenset({"execute", "review", "clarify", "stop"})
GUARDRAIL_ACTIONS = frozenset({"approve", "human_review", "deny"})
ROUTE_PATHS = frozenset({"lightweight", "flagship", "human_review", "none"})
ROUTE_PATTERNS = frozenset({"inline", "subagent", "handoff", "router", "compose"})

# Effects used by the Python compatibility boundary.  JEV has a deliberately
# smaller execution-effect vocabulary; these are capability side-effect labels
# and must not be confused with ``execution_effect`` in a decision packet.
CAPABILITY_EFFECTS = frozenset({
    "read",
    "write",
    "execute",
    "delete",
    "network",
    "communicate",
    "destroy",
    "force_push",
    "production",
    "rotate_credentials",
    "irreversible",
})
MAX_CODE_BYTES = 1_048_576
MAX_LANGUAGE_LENGTH = 64

_REQUIRED_PACKET_KEYS = frozenset({
    "schema_version",
    "task_id",
    "orchestration_state_id",
    "capability_catalog_version",
    "policy_version",
    "ok",
    "execution_effect",
    "errors",
    "heads",
    "aggregate",
    "guardrail",
    "route",
    "capability_plan",
    "context_plan",
    "trace",
})


def validate_identifier(value: Any, label: str = "identifier") -> str:
    """Return a safe path component or fail closed."""
    if not isinstance(value, str) or not _IDENTIFIER_RE.fullmatch(value):
        raise ContractError(f"{label} must match {_IDENTIFIER_RE.pattern}")
    if value in {".", ".."}:
        raise ContractError(f"{label} is not a valid path component")
    return value


def validate_capability_id(value: Any) -> str:
    if not isinstance(value, str) or not _CAPABILITY_RE.fullmatch(value):
        raise ContractError(f"invalid capability id: {value!r}")
    return value


def validate_fingerprint(value: Any) -> str:
    if not isinstance(value, str) or not _FINGERPRINT_RE.fullmatch(value):
        raise ContractError("action_fingerprint must be a lowercase SHA-256 hex digest")
    return value


def safe_child_path(base: Path, relative: str | Path) -> Path:
    """Resolve a relative path and prove it remains below ``base``."""
    if not isinstance(relative, (str, Path)):
        raise ContractError("path must be a string or Path")
    candidate = Path(relative)
    if "\\" in str(relative) or candidate.is_absolute() or any(part == ".." for part in candidate.parts):
        raise ContractError(f"path escapes allowed root: {relative}")
    root = base.resolve()
    resolved = (root / candidate).resolve()
    if resolved != root and root not in resolved.parents:
        raise ContractError(f"path escapes allowed root: {relative}")
    return resolved


def canonical_json(value: Any) -> str:
    try:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise ContractError(f"value is not canonical JSON: {exc}") from exc


def fingerprint(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def _require_mapping(value: Any, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ContractError(f"{label} must be an object")
    return value


def _require_list(value: Any, label: str) -> list[Any]:
    if not isinstance(value, list):
        raise ContractError(f"{label} must be an array")
    return value


def _validate_object_keys(value: Mapping[str, Any], required: set[str], optional: set[str], label: str) -> None:
    keys = set(value)
    missing = sorted(required - keys)
    unknown = sorted(keys - required - optional)
    if missing:
        raise ContractError(f"{label} is missing fields: {', '.join(missing)}")
    if unknown:
        raise ContractError(f"{label} has unknown fields: {', '.join(unknown)}")


def _validate_score(value: Any, label: str, *, include_load: bool = False) -> None:
    score = _require_mapping(value, label)
    required = {"risk", "complexity", "urgency", "confidence", "context_pressure"}
    optional = {"load"} if include_load else set()
    _validate_object_keys(score, required, optional, label)
    for key in required | optional:
        number = score[key]
        if (
            isinstance(number, bool)
            or not isinstance(number, (int, float))
            or not math.isfinite(float(number))
            or not 0.0 <= number <= 1.0
        ):
            raise ContractError(f"{label}.{key} must be a finite number between 0 and 1")


def _validate_reasons(value: Any, label: str) -> None:
    for index, reason in enumerate(_require_list(value, label)):
        item = _require_mapping(reason, f"{label}[{index}]")
        _validate_object_keys(item, {"code", "message", "capability_ids"}, {"path", "remedy"}, f"{label}[{index}]")
        if not isinstance(item.get("code"), str) or not item["code"]:
            raise ContractError(f"{label}[{index}].code is required")
        if not isinstance(item.get("message"), str) or not item["message"]:
            raise ContractError(f"{label}[{index}].message is required")
        ids = _require_list(item.get("capability_ids"), f"{label}[{index}].capability_ids")
        try:
            unique = len(ids) == len(set(ids))
        except TypeError as exc:
            raise ContractError(f"{label}[{index}].capability_ids must be strings") from exc
        if not unique:
            raise ContractError(f"{label}[{index}].capability_ids must be unique")
        for capability_id in ids:
            validate_capability_id(capability_id)
        for optional in ("path", "remedy"):
            if optional in item and not isinstance(item[optional], str):
                raise ContractError(f"{label}[{index}].{optional} must be a string")


def validate_jev_packet(packet: Any, task_id: str, *, strict: bool = True) -> dict[str, Any]:
    """Validate the runtime-relevant JEV packet boundary.

    The full JSON Schema is the normative contract.  This focused validator
    intentionally checks the fields the Python Runtime relies on and rejects
    malformed/ambiguous packets before persistence or execution.
    """
    value = _require_mapping(packet, "JEV packet")
    if strict:
        missing = sorted(_REQUIRED_PACKET_KEYS - set(value))
        if missing:
            raise ContractError(f"JEV packet is missing required fields: {', '.join(missing)}")
    else:
        for key in ("schema_version", "task_id", "ok", "execution_effect", "guardrail", "route", "capability_plan"):
            if key not in value:
                raise ContractError(f"JEV packet is missing required field: {key}")

    if value.get("schema_version") != "1.0":
        raise ContractError("unsupported JEV schema version")
    if value.get("task_id") != task_id:
        raise ContractError("JEV packet task_id does not match runtime task")
    if not isinstance(value.get("ok"), bool):
        raise ContractError("JEV packet ok must be boolean")
    if strict:
        _validate_object_keys(value, set(_REQUIRED_PACKET_KEYS), set(), "JEV packet")
        for key in ("orchestration_state_id", "capability_catalog_version", "policy_version"):
            if value[key] is not None and (not isinstance(value[key], str) or not value[key].strip()):
                raise ContractError(f"JEV {key} must be a non-empty string or null")
        _validate_reasons(value.get("errors"), "JEV errors")

    effect = value.get("execution_effect")
    if not isinstance(effect, str) or effect not in EXECUTION_EFFECTS:
        raise ContractError(f"invalid JEV execution_effect: {effect!r}")
    guardrail = _require_mapping(value.get("guardrail"), "JEV guardrail")
    _validate_object_keys(guardrail, {"action", "reasons"}, set(), "JEV guardrail")
    if not isinstance(guardrail.get("action"), str) or guardrail.get("action") not in GUARDRAIL_ACTIONS:
        raise ContractError("invalid JEV guardrail action")
    _validate_reasons(guardrail.get("reasons"), "JEV guardrail.reasons")
    if effect == "execute" and guardrail.get("action") != "approve":
        raise ContractError("executable JEV packets require an approve guardrail")
    if value.get("ok") is False and guardrail.get("action") == "approve":
        raise ContractError("a non-ok JEV packet cannot have an approve guardrail")

    route = _require_mapping(value.get("route"), "JEV route")
    _validate_object_keys(route, {"pattern", "path", "task_size", "primary_domain", "reasons", "authority"}, set(), "JEV route")
    if not isinstance(route.get("path"), str) or route.get("path") not in ROUTE_PATHS:
        raise ContractError("invalid JEV route path")
    if not isinstance(route.get("pattern"), str) or route.get("pattern") not in ROUTE_PATTERNS:
        raise ContractError("invalid JEV route pattern")
    if route.get("authority") != "recommendation":
        raise ContractError("JEV route authority must be recommendation")
    if not isinstance(route.get("task_size"), str) or route.get("task_size") not in {"atomic", "moderate", "complex"}:
        raise ContractError("invalid JEV route task_size")
    if not isinstance(route.get("primary_domain"), str) or not route["primary_domain"]:
        raise ContractError("JEV route primary_domain is required")
    route_reasons = _require_list(route.get("reasons"), "JEV route.reasons")
    if any(not isinstance(reason, str) for reason in route_reasons):
        raise ContractError("JEV route reasons must be strings")

    plan = _require_mapping(value.get("capability_plan"), "JEV capability_plan")
    _validate_object_keys(plan, {"selected", "omitted", "missing_capabilities"}, set(), "JEV capability_plan")
    selected = _require_list(plan.get("selected"), "JEV capability_plan.selected")
    omitted = _require_list(plan.get("omitted"), "JEV capability_plan.omitted")
    missing = _require_list(plan.get("missing_capabilities"), "JEV capability_plan.missing_capabilities")
    try:
        if len(selected) != len(set(selected)) or len(missing) != len(set(missing)):
            raise ContractError("JEV capability IDs must be unique")
    except TypeError as exc:
        raise ContractError("JEV capability IDs must be strings") from exc
    for capability_id in selected:
        validate_capability_id(capability_id)
    for capability_id in missing:
        validate_capability_id(capability_id)
    for item in omitted:
        omitted_item = _require_mapping(item, "JEV capability_plan.omitted item")
        _validate_object_keys(omitted_item, {"id", "code", "message"}, set(), "JEV capability_plan.omitted item")
        if not isinstance(omitted_item.get("id"), str):
            raise ContractError("omitted capability id is required")
        if not isinstance(omitted_item.get("code"), str) or not omitted_item["code"]:
            raise ContractError("omitted capability code is required")
        if not isinstance(omitted_item.get("message"), str) or not omitted_item["message"]:
            raise ContractError("omitted capability message is required")
        validate_capability_id(omitted_item["id"])
    if effect != "execute" and selected:
        raise ContractError("non-executable JEV packets cannot select capabilities")
    if effect == "execute" and (not selected or missing):
        raise ContractError("executable JEV packets require selected capabilities and no missing capabilities")
    if value.get("ok") is True and value.get("errors"):
        raise ContractError("an ok JEV packet cannot contain errors")
    if value.get("ok") is False and selected:
        raise ContractError("a non-ok JEV packet cannot select capabilities")
    if effect == "execute" and route.get("path") in {"human_review", "none"}:
        raise ContractError("executable JEV packets require an executable route")

    if strict:
        _validate_reasons(value.get("errors"), "JEV errors")
        heads = _require_mapping(value.get("heads"), "JEV heads")
        _validate_object_keys(heads, {"noul", "choice", "score"}, set(), "JEV heads")
        noul = _require_mapping(heads.get("noul"), "JEV heads.noul")
        _validate_object_keys(noul, {"urgent", "destructive", "policy_sensitive", "human_approval_required", "evidence_required"}, set(), "JEV heads.noul")
        if any(not isinstance(noul[key], bool) for key in noul):
            raise ContractError("JEV heads.noul fields must be boolean")
        if effect == "execute" and any(
            noul[key]
            for key in ("destructive", "policy_sensitive", "human_approval_required")
        ):
            raise ContractError("destructive or approval-sensitive JEV packets cannot be executable")
        choice = _require_mapping(heads.get("choice"), "JEV heads.choice")
        _validate_object_keys(choice, {"pattern", "task_size", "preferred_path", "primary_domain"}, set(), "JEV heads.choice")
        if not isinstance(choice.get("pattern"), str) or choice.get("pattern") not in ROUTE_PATTERNS or not isinstance(choice.get("preferred_path"), str) or choice.get("preferred_path") not in ROUTE_PATHS:
            raise ContractError("invalid JEV heads.choice routing")
        if effect == "execute" and choice["preferred_path"] != route["path"]:
            raise ContractError("JEV choice and route paths disagree")
        if effect == "execute" and choice["pattern"] != route["pattern"]:
            raise ContractError("JEV choice and route patterns disagree")
        if not isinstance(choice.get("task_size"), str) or choice.get("task_size") not in {"atomic", "moderate", "complex"} or not isinstance(choice.get("primary_domain"), str):
            raise ContractError("invalid JEV heads.choice classification")
        _validate_score(heads.get("score"), "JEV heads.score")
        aggregate = _require_mapping(value.get("aggregate"), "JEV aggregate")
        if "load" not in aggregate:
            raise ContractError("JEV aggregate.load is required")
        _validate_score(aggregate, "JEV aggregate", include_load=True)
        context = _require_mapping(value.get("context_plan"), "JEV context_plan")
        _validate_object_keys(context, {"profile", "reasons", "authority"}, set(), "JEV context_plan")
        if not isinstance(context.get("profile"), str) or context.get("profile") not in {"minimal", "standard", "deep"}:
            raise ContractError("invalid JEV context profile")
        if any(not isinstance(reason, str) for reason in _require_list(context.get("reasons"), "JEV context_plan.reasons")):
            raise ContractError("JEV context reasons must be strings")
        if context.get("authority") != "recommendation":
            raise ContractError("JEV context authority must be recommendation")
        trace = _require_mapping(value.get("trace"), "JEV trace")
        _validate_object_keys(trace, {"rules_applied", "deterministic"}, set(), "JEV trace")
        rules = _require_list(trace.get("rules_applied"), "JEV trace.rules_applied")
        if any(not isinstance(rule, str) for rule in rules):
            raise ContractError("JEV trace rules must be strings")
        if trace.get("deterministic") is not True:
            raise ContractError("JEV trace must be deterministic")

    return copy.deepcopy(dict(value))


def normalize_effects(effects: Any, *, add_execute: bool = False) -> frozenset[str]:
    """Validate and normalize capability side-effect labels.

    Effect declarations are security policy, not free-form text.  Callers may
    add effects, but may not omit the operation's mandatory ``execute`` label.
    """
    if isinstance(effects, str):
        values = {effects}
    else:
        try:
            values = set(effects or ())
        except TypeError as exc:
            raise ContractError("effects must be a string or iterable of strings") from exc
    if any(not isinstance(value, str) or not value for value in values):
        raise ContractError("effects must contain non-empty strings")
    unknown = values - CAPABILITY_EFFECTS
    if unknown:
        raise ContractError(f"effects contains unknown labels: {', '.join(sorted(unknown))}")
    if add_execute:
        values.add("execute")
    return frozenset(values)


def classify_code_effects(code: Any, language: Any = "python") -> frozenset[str]:
    """Conservatively classify side effects before code reaches a host.

    This is intentionally a *fail-closed* classifier rather than a Python
    sandbox.  It recognizes common filesystem, process, network, and
    communication primitives and broadens unknown executable code to the
    irreversible/network set.  A host may provide a stricter classifier via a
    capability declaration, but callers cannot narrow this result.
    """
    if not isinstance(code, str) or not code.strip() or "\x00" in code:
        raise ContractError("code must be a non-empty string without NUL")
    try:
        encoded = code.encode("utf-8")
    except UnicodeEncodeError as exc:
        raise ContractError("code must be UTF-8 text") from exc
    if len(encoded) > MAX_CODE_BYTES:
        raise ContractError(f"code exceeds the {MAX_CODE_BYTES}-byte limit")
    if not isinstance(language, str) or not language.strip() or "\x00" in language or len(language) > MAX_LANGUAGE_LENGTH:
        raise ContractError("language must be a bounded non-empty string without NUL")
    normalized_language = language.strip().casefold()
    effects: set[str] = {"execute"}
    text = code.casefold()

    # File-system reads are not themselves destructive, but retaining the
    # label lets policy/JEV reason about the complete requested scope.
    if re.search(r"\b(?:open|read_text|read_bytes|readlink|glob|iterdir|scandir|listdir)\b", text):
        effects.add("read")
    if re.search(
        r"(?:\b(?:write_text|write_bytes|mkdir|makedirs|touch|rename|replace|chmod|chown)\s*\("
        r"|\.\s*write\s*\(|open\s*\([^\n]{0,160}['\"][wax+])",
        text,
    ):
        effects.add("write")
    if re.search(
        r"(?:\b(?:unlink|remove|rmdir|removedirs|rmtree|truncate)\s*\("
        r"|\b(?:drop|delete|erase|destroy)\b"
        r"|\brm(?:\s+(?:-[^\s]+\s+)*[^\s]+)?$)",
        text,
    ):
        effects.update({"write", "delete", "irreversible"})
    if re.search(
        r"(?:\b(?:requests|httpx|aiohttp|urllib|urlopen|socket|websocket)\b"
        r"|https?://|\b(?:curl|wget|nc|netcat)\b)",
        text,
    ):
        effects.add("network")
    if re.search(
        r"(?:\b(?:send|sendall|post|put|publish|email|smtplib|webhook|communicate)\b"
        r"|\.(?:send|post|put|publish)\s*\()",
        text,
        re.IGNORECASE,
    ):
        effects.add("communicate")
    if re.search(r"(?:\bgit\s+push\s+(?:--force|-f)\b|\bforce[_ -]?push\b)", text):
        effects.update({"force_push", "irreversible"})
    if re.search(r"(?:\b(?:deploy|production|terraform\s+apply|kubectl\s+apply)\b)", text):
        effects.add("production")
    if re.search(r"(?:\b(?:rotate|rotation)\b.{0,48}\b(?:credential|secret|token|key)\b)", text):
        effects.update({"rotate_credentials", "irreversible"})

    # Calls not recognized as a known side-effect-free primitive are treated
    # broadly.  This prevents a caller from hiding a helper call behind a
    # narrow ``effects={'execute'}`` declaration.
    calls = set(re.findall(r"\b([A-Za-z_][A-Za-z0-9_]*)\s*\(", text))
    known_names = {
        "print", "len", "str", "int", "float", "bool", "repr", "enumerate", "range", "sorted", "sum", "min", "max",
        "open", "write", "read_text", "read_bytes", "readlink", "glob", "iterdir", "scandir", "listdir",
        "write_text", "write_bytes", "mkdir", "makedirs", "touch", "rename", "replace", "chmod", "chown",
        "unlink", "remove", "rmdir", "removedirs", "rmtree", "truncate", "requests", "httpx", "aiohttp",
        "urllib", "urlopen", "socket", "websocket", "send", "sendall", "post", "put", "delete", "publish",
        "email", "smtplib", "webhook", "communicate", "curl", "wget", "nc", "netcat", "get",
    }
    attribute_calls = set(re.findall(r"\.\s*([A-Za-z_][A-Za-z0-9_]*)\s*\(", text))
    safe_attribute_names = {
        "write", "read", "read_text", "read_bytes", "unlink", "remove", "rmdir", "rename", "replace",
        "mkdir", "makedirs", "touch", "chmod", "chown", "send", "sendall", "post", "put", "delete", "publish",
    }
    if calls - known_names or attribute_calls - safe_attribute_names:
        effects.update({"write", "delete", "network", "communicate", "irreversible"})
    elif re.search(r"\b(?:import|from)\s+", text):
        effects.update({"write", "network", "communicate", "irreversible"})

    if normalized_language not in {
        "python", "py", "javascript", "js", "typescript", "ts", "bash", "sh",
        "shell", "zsh", "fish", "ruby", "rb", "go", "rust", "java", "kotlin",
        "powershell", "ps1",
    }:
        effects.update({"write", "delete", "network", "communicate", "irreversible"})
    return frozenset(effects)


def action_fingerprint(action: Mapping[str, Any]) -> str:
    _require_mapping(action, "action")
    if not isinstance(action.get("operation"), str) or not action["operation"]:
        raise ContractError("action.operation is required")
    return fingerprint(dict(action))


def selected_capability(packet: Mapping[str, Any], capability_id: str) -> bool:
    validate_capability_id(capability_id)
    if not isinstance(packet, Mapping) or not isinstance(packet.get("capability_plan"), Mapping):
        return False
    selected = packet["capability_plan"].get("selected", [])
    return isinstance(selected, list) and capability_id in selected
