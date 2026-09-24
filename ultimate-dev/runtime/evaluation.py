"""Provider-neutral, dependency-free scenario evaluation.

The evaluation runner in this module is intentionally *not* a model benchmark
runner.  It does not discover a provider, select a model, make network calls,
or turn a static golden fixture into evidence about a real model.  A caller
injects the classifier, agent, and verifier callables (or a caller-supplied
backend description) and the runner records what those callables actually did.

The public contract is intentionally small:

``classifier``
    A callable receiving a case/task (and, when accepted, a context object).
    Its structured output can be checked against the case's expected routing
    fields.
``agent``
    A callable receiving the task/case and, when accepted, the classifier
    result.  It may return a value, a mapping with metrics, or a mapping with
    ``trace``/``events``/``steps`` entries.
``verifier``
    An independent callable receiving the agent result and case.  Boolean and
    common structured verdicts are supported.  A missing verifier is reported
    as ``uncertain`` rather than being treated as proof of success.

Statuses deliberately distinguish four outcomes:

* ``pass`` -- the injected verifier (and any expected routing check) passed.
* ``fail`` -- execution or verification explicitly failed.
* ``uncertain`` -- execution happened, but output or verification was
  missing/ambiguous, or an expected route could not be checked.
* ``not_run`` -- no executable backend/component was available, or a required
  stage was never reached.

Repeated trials are available with ``trials=N``.  The result reports both
``pass_at_k`` (at least one success in a sample of k) and ``pass^k`` (all k
successes in a sample of k), so a consistency-oriented pass^k result cannot be
confused with a best-of-k result.  Missing token, cost, or latency values stay
``None`` unless a callable supplies them; wall-clock latency is recorded
separately as ``measured_latency_ms``.  Trace redaction also covers common
credential and private-reasoning fields.

Only the Python standard library is used.  The small YAML reader below supports
the dependency-free subset used by the repository's golden/scripted case
files: mappings, lists, scalars, quoted values, comments, and inline lists or
mappings.  JSON is supported natively.
"""

from __future__ import annotations

import copy
import inspect
import json
import math
import numbers
import re
import time
from collections.abc import Callable, Iterable, Mapping, Sequence
from pathlib import Path
from typing import Any, Optional


__all__ = [
    "EvaluationContext",
    "EvaluationError",
    "EvaluationRunner",
    "CaseList",
    "load_cases",
    "load_golden_cases",
    "load_golden",
    "load_scripted_cases",
    "load_scripted",
    "redact_value",
    "to_json",
    "write_json",
    "run_evaluation",
    "evaluate_cases",
    "run",
    "STATUS_PASS",
    "STATUS_FAIL",
    "STATUS_UNCERTAIN",
    "STATUS_NOT_RUN",
]

STATUS_PASS = "pass"
STATUS_FAIL = "fail"
STATUS_UNCERTAIN = "uncertain"
STATUS_NOT_RUN = "not_run"
_MISSING = object()


class EvaluationError(ValueError):
    """Raised when an evaluation input or callable contract is invalid."""


class CaseList(list):
    """A list of cases with non-mutating source metadata.

    The metadata is used for honest provenance reporting.  Keeping it on the
    container avoids adding private implementation keys to every case returned
    by :func:`load_cases`.
    """

    def __init__(
        self,
        values: Iterable[Mapping[str, Any]] = (),
        *,
        source: str = "provided",
        path: Optional[Path] = None,
        fixture_only: bool = False,
    ) -> None:
        super().__init__(values)
        self.source = source
        self.path = path
        self.fixture_only = fixture_only


# ---------------------------------------------------------------------------
# Minimal standard-library YAML reader
# ---------------------------------------------------------------------------


def _strip_yaml_comment(line: str) -> str:
    """Remove a YAML comment without changing ``#`` inside a quoted scalar."""

    quote: Optional[str] = None
    escaped = False
    for index, char in enumerate(line):
        if quote == '"' and escaped:
            escaped = False
            continue
        if quote == '"' and char == "\\":
            escaped = True
            continue
        if char in ("'", '"'):
            if quote is None:
                quote = char
            elif quote == char:
                quote = None
            continue
        if char == "#" and quote is None:
            if index == 0 or line[index - 1].isspace():
                return line[:index].rstrip()
    return line.rstrip()


def _yaml_lines(text: str) -> list[tuple[int, str, int]]:
    result: list[tuple[int, str, int]] = []
    for line_number, raw in enumerate(text.splitlines(), 1):
        if "\t" in raw[: len(raw) - len(raw.lstrip(" \t"))]:
            raise EvaluationError(
                f"tabs are not supported in the restricted YAML at line {line_number}"
            )
        line = _strip_yaml_comment(raw)
        if not line.strip() or line.strip() in ("---", "..."):
            continue
        indent = len(line) - len(line.lstrip(" "))
        result.append((indent, line.strip(), line_number))
    return result


def _split_top_level(value: str, separator: str = ",") -> list[str]:
    parts: list[str] = []
    start = 0
    quote: Optional[str] = None
    escaped = False
    depth = 0
    for index, char in enumerate(value):
        if quote == '"' and escaped:
            escaped = False
            continue
        if quote == '"' and char == "\\":
            escaped = True
            continue
        if char in ("'", '"'):
            if quote is None:
                quote = char
            elif quote == char:
                quote = None
            continue
        if quote is not None:
            continue
        if char in "[{(":
            depth += 1
        elif char in "]})":
            depth = max(0, depth - 1)
        elif char == separator and depth == 0:
            parts.append(value[start:index].strip())
            start = index + 1
    parts.append(value[start:].strip())
    return [part for part in parts if part]


def _split_yaml_key(value: str) -> Optional[tuple[str, str]]:
    quote: Optional[str] = None
    escaped = False
    depth = 0
    for index, char in enumerate(value):
        if quote == '"' and escaped:
            escaped = False
            continue
        if quote == '"' and char == "\\":
            escaped = True
            continue
        if char in ("'", '"'):
            if quote is None:
                quote = char
            elif quote == char:
                quote = None
            continue
        if quote is not None:
            continue
        if char in "[{(":
            depth += 1
        elif char in "]})":
            depth = max(0, depth - 1)
        elif char == ":" and depth == 0:
            # YAML keys in the supported subset are followed by whitespace or
            # end-of-line.  This avoids treating a colon in a task scalar as a
            # mapping separator when the scalar is not quoted.
            if index + 1 == len(value) or value[index + 1].isspace():
                key = value[:index].strip()
                return key, value[index + 1 :].strip()
    return None


def _parse_yaml_scalar(value: str) -> Any:
    value = value.strip()
    if not value:
        return None
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        if not inner:
            return []
        return [_parse_yaml_scalar(part) for part in _split_top_level(inner)]
    if value.startswith("{") and value.endswith("}"):
        inner = value[1:-1].strip()
        if not inner:
            return {}
        result: dict[str, Any] = {}
        for part in _split_top_level(inner):
            pair = _split_yaml_key(part)
            if pair is None:
                # JSON-style quoted keys do not always have a space after the
                # colon.  Accommodate that harmless variant as well.
                if ":" not in part:
                    raise EvaluationError(f"invalid inline YAML mapping item: {part}")
                key, raw_value = part.split(":", 1)
            else:
                key, raw_value = pair
            key_value = _parse_yaml_scalar(key)
            result[str(key_value)] = _parse_yaml_scalar(raw_value)
        return result
    if len(value) >= 2 and value[0] == value[-1] == '"':
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value[1:-1]
    if len(value) >= 2 and value[0] == value[-1] == "'":
        # YAML single-quoted strings escape a quote by doubling it.
        return value[1:-1].replace("''", "'")
    lowered = value.lower()
    if lowered in {"null", "~"}:
        return None
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    if re.fullmatch(r"[-+]?\d+", value):
        try:
            return int(value)
        except ValueError:
            pass
    if re.fullmatch(r"[-+]?(?:\d+\.\d*|\.\d+|\d+)(?:[eE][-+]?\d+)?", value):
        try:
            return float(value)
        except ValueError:
            pass
    return value


def _parse_yaml_block(
    lines: list[tuple[int, str, int]], index: int, indent: int
) -> tuple[Any, int]:
    if index >= len(lines) or lines[index][0] < indent:
        return None, index
    if lines[index][1].startswith("-"):
        return _parse_yaml_list(lines, index, lines[index][0])
    return _parse_yaml_mapping(lines, index, lines[index][0])


def _parse_yaml_mapping(
    lines: list[tuple[int, str, int]], index: int, indent: int
) -> tuple[dict[str, Any], int]:
    result: dict[str, Any] = {}
    while index < len(lines):
        current_indent, content, line_number = lines[index]
        if current_indent < indent:
            break
        if current_indent > indent:
            raise EvaluationError(
                f"unexpected indentation in restricted YAML at line {line_number}"
            )
        if content.startswith("-"):
            break
        pair = _split_yaml_key(content)
        if pair is None:
            raise EvaluationError(
                f"expected a mapping entry in restricted YAML at line {line_number}"
            )
        raw_key, raw_value = pair
        key = str(_parse_yaml_scalar(raw_key))
        index += 1
        if raw_value:
            result[key] = _parse_yaml_scalar(raw_value)
            continue
        if index < len(lines) and lines[index][0] > indent:
            child_indent = lines[index][0]
            child, index = _parse_yaml_block(lines, index, child_indent)
            result[key] = child
        else:
            result[key] = None
    return result, index


def _parse_yaml_list(
    lines: list[tuple[int, str, int]], index: int, indent: int
) -> tuple[list[Any], int]:
    result: list[Any] = []
    while index < len(lines):
        current_indent, content, line_number = lines[index]
        if current_indent < indent:
            break
        if current_indent != indent or not content.startswith("-"):
            break
        item_text = content[1:].strip()
        index += 1
        if not item_text:
            if index < len(lines) and lines[index][0] > indent:
                child, index = _parse_yaml_block(lines, index, lines[index][0])
                result.append(child)
            else:
                result.append(None)
            continue
        pair = _split_yaml_key(item_text)
        if pair is None:
            result.append(_parse_yaml_scalar(item_text))
            continue

        # A list item can begin a mapping (``- id: value``).  Parse that first
        # pair, then consume the remaining indented mapping entries.
        raw_key, raw_value = pair
        item: dict[str, Any] = {}
        key = str(_parse_yaml_scalar(raw_key))
        if raw_value:
            item[key] = _parse_yaml_scalar(raw_value)
        elif index < len(lines) and lines[index][0] > indent:
            child, index = _parse_yaml_block(lines, index, lines[index][0])
            item[key] = child
        else:
            item[key] = None
        if index < len(lines) and lines[index][0] > indent:
            child_indent = lines[index][0]
            child, index = _parse_yaml_mapping(lines, index, child_indent)
            if isinstance(child, Mapping):
                item.update(child)
        result.append(item)
    return result, index


def _parse_simple_yaml(text: str) -> Any:
    lines = _yaml_lines(text)
    if not lines:
        return {}
    value, index = _parse_yaml_block(lines, 0, lines[0][0])
    if index != len(lines):
        _, _, line_number = lines[index]
        raise EvaluationError(
            f"could not parse restricted YAML near line {line_number}"
        )
    return value


# ---------------------------------------------------------------------------
# Redaction and JSON-safe conversion
# ---------------------------------------------------------------------------


_SENSITIVE_KEYS = {
    "api_key",
    "apikey",
    "access_key",
    "access_token",
    "auth",
    "authorization",
    "client_secret",
    "cookie",
    "credential",
    "credentials",
    "id_token",
    "password",
    "passwd",
    "private_key",
    "private_reasoning",
    "chain_of_thought",
    "reasoning",
    "thought",
    "thoughts",
    "private_thoughts",
    "refresh_token",
    "secret",
    "session_token",
    "set_cookie",
    "signature",
    "token",
    "accesstoken",
    "refreshtoken",
    "authtoken",
    "clientsecret",
    "privatekey",
    "sessiontoken",
}
_SECRET_ASSIGNMENT_RE = re.compile(
    r"(?i)(\b(?:api[_-]?key|access[_-]?token|refresh[_-]?token|auth(?:orization)?|"
    r"password|passwd|client[_-]?secret|private[_-]?key|token|reasoning)\b\s*[:=]\s*)"
    r"([^\s,;]+)"
)
_BEARER_RE = re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+/=-]+")
_SECRET_VALUE_RE = re.compile(r"(?i)\b(?:sk|pk|api|key|secret)[-_][A-Za-z0-9._~+/=-]{6,}\b")


def _normalise_key(key: Any) -> str:
    return re.sub(r"[^a-z0-9]+", "_", str(key).lower()).strip("_")


def _is_sensitive_key(key: Any, extra_keys: set[str]) -> bool:
    normalized = _normalise_key(key)
    if normalized in extra_keys or normalized in _SENSITIVE_KEYS:
        return True
    # Match compound names such as ``service_api_key`` and ``db.password`` but
    # do not hide ordinary telemetry such as ``token_count`` or ``tokens``.
    return any(normalized.endswith("_" + item) for item in extra_keys if item) or any(
        normalized.endswith("_" + item) for item in _SENSITIVE_KEYS
    )


def _redact_string(value: str, secret_values: Iterable[str]) -> str:
    result = value
    for secret in secret_values:
        if secret:
            result = result.replace(str(secret), "[REDACTED]")
    result = _SECRET_ASSIGNMENT_RE.sub(r"\1[REDACTED]", result)
    result = _BEARER_RE.sub("Bearer [REDACTED]", result)
    result = _SECRET_VALUE_RE.sub("[REDACTED]", result)
    return result


def redact_value(
    value: Any,
    *,
    extra_keys: Iterable[str] = (),
    secret_values: Iterable[str] = (),
) -> Any:
    """Return a JSON-safe copy with common credential material removed.

    Redaction is recursive and applies to mapping keys, strings, sequences,
    and provider-specific trace objects.  It is intentionally conservative:
    unknown objects are represented by a type marker rather than by ``repr``,
    which could accidentally disclose a secret.
    """

    key_values = (extra_keys,) if isinstance(extra_keys, str) else extra_keys
    secret_values = (secret_values,) if isinstance(secret_values, str) else secret_values
    keys = {_normalise_key(item) for item in key_values}
    secrets = tuple(str(item) for item in secret_values if item is not None)
    # Track only the active recursion path.  A global ``seen`` set would
    # incorrectly label the runner's intentionally repeated JSON aliases
    # (``trace``/``events`` and ``backend``/``provenance``) as cycles.
    active: set[int] = set()

    def visit(current: Any) -> Any:
        if current is None or isinstance(current, (bool, int, str)):
            if isinstance(current, str):
                return _redact_string(current, secrets)
            return current
        if isinstance(current, float):
            return current if math.isfinite(current) else None
        identity = id(current)
        if identity in active:
            return "[Circular]"
        active.add(identity)
        try:
            if isinstance(current, Mapping):
                result: dict[str, Any] = {}
                for key, item in current.items():
                    if _is_sensitive_key(key, keys):
                        result[str(key)] = "[REDACTED]"
                    else:
                        result[str(key)] = visit(item)
                return result
            if isinstance(current, (list, tuple, set, frozenset)):
                return [visit(item) for item in current]
            if isinstance(current, Path):
                return _redact_string(str(current), secrets)
            return f"<{type(current).__name__}>"
        finally:
            active.remove(identity)

    return visit(value)


def _json_safe(value: Any) -> Any:
    """Convert values to a deterministic JSON-compatible shape."""

    if value is None or isinstance(value, (bool, int, str)):
        return value
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    if isinstance(value, Mapping):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set, frozenset)):
        return [_json_safe(item) for item in value]
    if isinstance(value, Path):
        return str(value)
    return f"<{type(value).__name__}>"


# ---------------------------------------------------------------------------
# Case loading
# ---------------------------------------------------------------------------


def _case_payload(value: Any, *, source: str) -> tuple[CaseList, str, bool]:
    metadata_source = source
    if isinstance(value, Mapping):
        for key in ("cases", "scripted_cases", "scenarios", "tests"):
            candidate = value.get(key)
            if isinstance(candidate, Iterable) and not isinstance(candidate, (str, bytes, bytearray)):
                raw_cases = list(candidate)
                break
        else:
            raw_cases = [value]
        if isinstance(value.get("source"), str):
            metadata_source = value["source"]
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        raw_cases = list(value)
    else:
        raise EvaluationError("case source must contain an object or an array of objects")

    cases: list[Mapping[str, Any]] = []
    for index, case in enumerate(raw_cases, 1):
        if not isinstance(case, Mapping):
            raise EvaluationError(f"case {index} must be an object")
        cases.append(dict(case))

    lowered = metadata_source.lower()
    fixture_only = any(word in lowered for word in ("golden", "scripted", "fixture"))
    if any("script" in case or "steps" in case for case in cases):
        fixture_only = True
    return CaseList(cases, source=metadata_source, fixture_only=fixture_only), metadata_source, fixture_only


def _read_case_file(path: Path) -> Any:
    try:
        text = path.read_text(encoding="utf-8").lstrip("\ufeff")
    except OSError as exc:
        raise EvaluationError(f"unable to read case file {path}: {exc}") from exc
    if path.suffix.lower() == ".json":
        try:
            return json.loads(text)
        except json.JSONDecodeError as exc:
            raise EvaluationError(f"invalid JSON case file {path}: {exc}") from exc
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        try:
            return _parse_simple_yaml(text)
        except EvaluationError as exc:
            raise EvaluationError(f"invalid case file {path}: {exc}") from exc


def load_cases(source: Any) -> CaseList:
    """Load cases from a path, JSON/YAML text, mapping, or iterable.

    JSON is preferred when content is valid JSON; the restricted YAML reader
    is used for the repository's dependency-free golden/scripted fixtures.
    """

    if source is None:
        return CaseList([], source="none", fixture_only=False)
    if isinstance(source, (bytes, bytearray)):
        try:
            text = bytes(source).decode("utf-8")
        except UnicodeDecodeError as exc:
            raise EvaluationError("byte case source is not valid UTF-8") from exc
        try:
            payload = json.loads(text)
        except json.JSONDecodeError:
            payload = _parse_simple_yaml(text)
        return _case_payload(payload, source="bytes")[0]
    if hasattr(source, "read") and callable(source.read):
        try:
            text = source.read()
        except Exception as exc:
            raise EvaluationError(f"unable to read case stream: {exc}") from exc
        if isinstance(text, bytes):
            text = text.decode("utf-8")
        try:
            payload = json.loads(text)
        except json.JSONDecodeError:
            payload = _parse_simple_yaml(text)
        return _case_payload(payload, source="stream")[0]
    if isinstance(source, CaseList):
        return CaseList(source, source=source.source, path=source.path, fixture_only=source.fixture_only)
    if isinstance(source, Mapping):
        return _case_payload(source, source="provided")[0]
    if isinstance(source, (str, Path)):
        path = Path(source).expanduser()
        try:
            is_file = path.is_file()
        except OSError:
            is_file = False
        if is_file:
            payload = _read_case_file(path)
            loaded, _, _ = _case_payload(payload, source=str(path))
            loaded.path = path
            return loaded
        if isinstance(source, str) and ("\n" in source or source.lstrip().startswith(("{", "["))):
            try:
                payload = json.loads(source)
            except json.JSONDecodeError:
                payload = _parse_simple_yaml(source)
            return _case_payload(payload, source="inline")[0]
        raise EvaluationError(f"case file does not exist: {path}")
    if isinstance(source, Iterable) and not isinstance(source, (bytes, bytearray)):
        return _case_payload(list(source), source="provided")[0]
    raise EvaluationError("unsupported case source")


def load_golden_cases(path: Optional[Any] = None) -> CaseList:
    """Load the repository golden fixture, or a caller-supplied golden file."""

    if path is None:
        path = Path(__file__).resolve().parents[1] / "evals" / "golden-cases.yaml"
    return load_cases(path)


def load_scripted_cases(path: Optional[Any] = None) -> CaseList:
    """Load a scripted fixture using the same neutral case-file contract."""

    if path is None:
        raise EvaluationError("a path is required for scripted cases")
    return load_cases(path)


# Short alias retained for callers that use the conventional loader name.
load_golden = load_golden_cases
load_scripted = load_scripted_cases


# ---------------------------------------------------------------------------
# Case and callable helpers
# ---------------------------------------------------------------------------


class EvaluationContext(dict):
    """A dict-like context passed to callables that request ``context``."""

    def __getattr__(self, name: str) -> Any:
        try:
            return self[name]
        except KeyError as exc:  # pragma: no cover - normal attribute error path
            raise AttributeError(name) from exc


def _case_id(case: Mapping[str, Any], index: int) -> str:
    value = case.get("id", case.get("case_id", f"case-{index + 1}"))
    return str(value) if value is not None else f"case-{index + 1}"


def _case_task(case: Mapping[str, Any]) -> str:
    for key in ("task", "prompt", "input", "request", "text", "task_description"):
        value = case.get(key)
        if isinstance(value, str):
            return value
        if value is not None:
            return str(value)
    return ""


def _expected_fields(case: Mapping[str, Any]) -> dict[str, Any]:
    expected: dict[str, Any] = {}
    raw = case.get("expected")
    if not isinstance(raw, Mapping):
        raw = case.get("gold")
    if isinstance(raw, Mapping):
        nested = raw.get("classification")
        if isinstance(nested, Mapping):
            expected.update(nested)
        expected.update({key: value for key, value in raw.items() if key != "classification"})
    for source_key in ("expected_classification", "expected_route"):
        value = case.get(source_key)
        if isinstance(value, Mapping):
            expected.update(value)
        elif source_key == "expected_route" and value is not None and "route" not in expected:
            expected["route"] = value
    for key in (
        "expected_size",
        "expected_task_size",
        "expected_domains",
        "expected_domain",
        "expected_risk",
        "expected_pattern",
        "expected_primary_domain",
        "expected_tool",
        "expected_tools",
    ):
        if key in case:
            expected[key[9:]] = case[key]
    if "expected_success" in case and "success" not in expected:
        expected["success"] = case["expected_success"]
    if not expected:
        for key in ("size", "domains", "domain", "risk", "pattern", "route", "primary_domain"):
            if key in case:
                expected[key] = case[key]
    return expected


def _first_value(mapping: Mapping[str, Any], keys: Iterable[str]) -> Any:
    for key in keys:
        if key in mapping:
            return mapping[key]
    return _MISSING


def _as_number(value: Any) -> Optional[float]:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, numbers.Real):
        number = float(value)
    elif isinstance(value, str):
        try:
            number = float(value.strip())
        except (TypeError, ValueError):
            return None
    else:
        return None
    return number if math.isfinite(number) else None


def _as_int(value: Any) -> Optional[int]:
    number = _as_number(value)
    if number is None or number < 0:
        return None
    return int(number)


def _metric_sources(payload: Any) -> list[Mapping[str, Any]]:
    if not isinstance(payload, Mapping):
        return []
    sources: list[Mapping[str, Any]] = [payload]
    for key in ("metrics", "usage", "token_usage", "telemetry", "timing", "stats", "cost_metrics"):
        nested = payload.get(key)
        if isinstance(nested, Mapping):
            sources.append(nested)
    return sources


def _extract_tool_count(payload: Any) -> Optional[int]:
    sources = _metric_sources(payload)
    for source in sources:
        value = _first_value(
            source,
            ("tool_calls", "tool_call_count", "tools_called", "tools_used", "calls", "tool", "tools"),
        )
        if value is not _MISSING:
            if isinstance(value, Mapping):
                nested = _first_value(value, ("count", "total", "calls"))
                if nested is not _MISSING:
                    count = _as_int(nested)
                    if count is not None:
                        return count
                return len(value)
            if isinstance(value, (list, tuple, set, frozenset)):
                return len(value)
            count = _as_int(value)
            if count is not None:
                return count
    for source in sources:
        for key in ("trace", "events", "steps"):
            events = source.get(key)
            if isinstance(events, Sequence) and not isinstance(events, (str, bytes, bytearray)):
                count = sum(1 for event in events if _is_tool_event(event))
                if count:
                    return count
    return None


def _is_tool_event(event: Any) -> bool:
    if not isinstance(event, Mapping):
        return False
    label = str(_first_value(event, ("event", "type", "kind", "name"))).lower()
    return label in {"tool", "tool_call", "tool-call", "function_call", "capability_call"} or label.startswith("tool_")


def _extract_retry_count(payload: Any) -> Optional[int]:
    sources = _metric_sources(payload)
    for source in sources:
        value = _first_value(source, ("retries", "retry_count", "retry_attempts", "retry"))
        if value is not _MISSING:
            if isinstance(value, Mapping):
                nested = _first_value(value, ("count", "total", "calls"))
                if nested is not _MISSING:
                    count = _as_int(nested)
                    if count is not None:
                        return count
                return len(value)
            if isinstance(value, (list, tuple, set, frozenset)):
                return len(value)
            count = _as_int(value)
            if count is not None:
                return count
    for source in sources:
        for key in ("trace", "events", "steps"):
            events = source.get(key)
            if isinstance(events, Sequence) and not isinstance(events, (str, bytes, bytearray)):
                count = sum(
                    1
                    for event in events
                    if isinstance(event, Mapping)
                    and str(_first_value(event, ("event", "type", "kind", "name"))).lower()
                    in {"retry", "retrying"}
                )
                if count:
                    return count
    return 1 if _retryable_result(payload) else None


def _token_value(mapping: Mapping[str, Any]) -> tuple[Optional[float], Optional[float], Optional[float]]:
    input_value = _first_value(
        mapping,
        ("input_tokens", "prompt_tokens", "input", "prompt", "inputTokens", "promptTokens"),
    )
    output_value = _first_value(
        mapping,
        ("output_tokens", "completion_tokens", "output", "completion", "outputTokens", "completionTokens"),
    )
    total_value = _first_value(mapping, ("total_tokens", "total", "tokens", "token", "totalTokens", "token_count"))
    if total_value is _MISSING and (input_value is not _MISSING or output_value is not _MISSING):
        input_number = _as_number(input_value) if input_value is not _MISSING else None
        output_number = _as_number(output_value) if output_value is not _MISSING else None
        if input_number is not None or output_number is not None:
            total_value = (input_number or 0.0) + (output_number or 0.0)
    return (
        _as_number(input_value) if input_value is not _MISSING else None,
        _as_number(output_value) if output_value is not _MISSING else None,
        _as_number(total_value) if total_value is not _MISSING else None,
    )


def _extract_tokens(payload: Any) -> dict[str, Optional[float]]:
    empty = {"input": None, "output": None, "total": None}
    if not isinstance(payload, Mapping):
        return empty
    sources = _metric_sources(payload)
    # Prefer an explicit token container over unrelated top-level telemetry.
    for source in sources:
        tokens = source.get("tokens")
        if isinstance(tokens, Mapping):
            result = _token_value(tokens)
            if any(value is not None for value in result):
                return {"input": result[0], "output": result[1], "total": result[2]}
        if isinstance(tokens, (int, float)) and not isinstance(tokens, bool):
            total = _as_number(tokens)
            if total is not None:
                return {"input": None, "output": None, "total": total}
        result = _token_value(source)
        if any(value is not None for value in result):
            return {"input": result[0], "output": result[1], "total": result[2]}
    return empty


def _extract_cost(payload: Any) -> Optional[float]:
    if not isinstance(payload, Mapping):
        return None
    for source in _metric_sources(payload):
        for key in ("cost_usd", "total_cost", "cost", "usd", "price"):
            value = source.get(key)
            if isinstance(value, Mapping):
                value = _first_value(value, ("usd", "amount", "value", "total"))
            number = _as_number(value)
            if number is not None:
                return number
    return None


def _extract_reported_latency(payload: Any) -> Optional[float]:
    if not isinstance(payload, Mapping):
        return None
    for source in _metric_sources(payload):
        for key in ("latency_ms", "duration_ms", "elapsed_ms"):
            value = source.get(key)
            if isinstance(value, Mapping):
                value = _first_value(value, ("ms", "milliseconds", "value"))
            number = _as_number(value)
            if number is not None:
                return max(0.0, number)
        for key in ("latency", "duration", "elapsed", "latency_seconds"):
            value = source.get(key)
            if isinstance(value, Mapping):
                value = _first_value(value, ("seconds", "s", "value"))
            value = _as_number(value)
            if value is not None:
                # A bare latency/duration is conventionally seconds in many
                # provider APIs; callers can avoid ambiguity with *_ms.
                return max(0.0, value * 1000.0)
    return None


def _declared_failure(payload: Any) -> bool:
    if not isinstance(payload, Mapping):
        return False
    for key in ("success", "passed", "ok", "verified", "valid"):
        if key in payload and (
            payload[key] is False
            or (
                isinstance(payload[key], (int, float))
                and not isinstance(payload[key], bool)
                and payload[key] == 0
            )
        ):
            return True
    status = payload.get("status")
    if isinstance(status, str) and status.lower() in {"fail", "failed", "failure", "error", "errored"}:
        return True
    return bool(payload.get("error"))


def _declared_uncertain(payload: Any) -> bool:
    if not isinstance(payload, Mapping):
        return False
    if payload.get("uncertain") is True or payload.get("indeterminate") is True:
        return True
    status = payload.get("status")
    return isinstance(status, str) and status.lower() in {
        "uncertain",
        "unknown",
        "indeterminate",
        "not_run",
    }


def _retryable_result(payload: Any) -> bool:
    if not isinstance(payload, Mapping):
        return False
    if payload.get("retry") is True or payload.get("retriable") is True or payload.get("retryable") is True:
        return True
    status = payload.get("status")
    return isinstance(status, str) and status.lower() in {"retry", "retrying"}


def _verdict(payload: Any, _seen: Optional[set[int]] = None) -> tuple[Optional[bool], str]:
    """Return ``(success, reason)`` for common verifier return shapes."""

    if _seen is None:
        _seen = set()
    if isinstance(payload, Mapping):
        identity = id(payload)
        if identity in _seen:
            return None, "verifier_cycle"
        _seen.add(identity)
    if isinstance(payload, bool):
        return payload, "boolean_verifier_result"
    if payload is None:
        return None, "verifier_returned_none"
    if isinstance(payload, str):
        normalized = payload.lower()
        if normalized in {"pass", "passed", "success", "succeeded", "ok", "true"}:
            return True, "string_verifier_result"
        if normalized in {"fail", "failed", "failure", "error", "false"}:
            return False, "string_verifier_result"
        if normalized in {"uncertain", "unknown", "indeterminate"}:
            return None, "verifier_uncertain"
        return None, "unrecognised_verifier_result"
    if not isinstance(payload, Mapping):
        return None, "unsupported_verifier_result"
    if payload.get("error"):
        return False, "verifier_error"

    status = payload.get("status")
    if isinstance(status, str) and status.lower() in {
        "pass",
        "passed",
        "success",
        "succeeded",
        "ok",
        "complete",
        "completed",
    }:
        return True, "verifier_status_pass"
    if isinstance(status, str) and status.lower() in {
        "fail",
        "failed",
        "failure",
        "error",
        "errored",
    }:
        return False, "verifier_status_fail"
    if isinstance(status, str) and status.lower() in {
        "uncertain",
        "unknown",
        "indeterminate",
        "not_run",
    }:
        return None, "verifier_status_uncertain"

    for key in ("success", "passed", "ok", "verified", "valid"):
        if key in payload:
            value = payload[key]
            if isinstance(value, bool):
                return value, f"verifier_{key}"
            if isinstance(value, (int, float)) and not isinstance(value, bool) and value in (0, 1):
                return bool(value), f"verifier_{key}"
            if value is not None:
                return None, f"verifier_{key}_not_boolean"
    for key in ("result", "verdict", "outcome", "verification"):
        if key in payload:
            return _verdict(payload[key], _seen)
    nested_metrics = payload.get("metrics")
    if isinstance(nested_metrics, Mapping):
        return _verdict(nested_metrics, _seen)
    return None, "verifier_missing_verdict"


def _events_from_payload(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, Mapping):
        raw_events: list[Any] = []
        for key in ("trace", "events", "steps"):
            value = payload.get(key)
            if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
                raw_events.extend(value)
        if not raw_events and isinstance(payload.get("tool_calls"), Sequence) and not isinstance(
            payload.get("tool_calls"), (str, bytes, bytearray)
        ):
            raw_events.extend({"event": "tool_call", "value": item} for item in payload["tool_calls"])
        if not raw_events and isinstance(payload.get("retries"), Sequence) and not isinstance(
            payload.get("retries"), (str, bytes, bytearray)
        ):
            raw_events.extend({"event": "retry", "value": item} for item in payload["retries"])
        if not raw_events and _as_int(payload.get("tool_calls")) is not None:
            raw_events.append({"event": "tool_call", "count": payload.get("tool_calls")})
        if not raw_events and _as_int(payload.get("retries")) is not None:
            raw_events.append({"event": "retry", "count": payload.get("retries")})
    elif isinstance(payload, Sequence) and not isinstance(payload, (str, bytes, bytearray)):
        raw_events = list(payload)
    else:
        raw_events = []

    result: list[dict[str, Any]] = []
    for event in raw_events:
        if isinstance(event, Mapping):
            item = dict(event)
            item.setdefault("event", item.get("type", item.get("kind", "backend_event")))
            item.setdefault("source", "backend")
        else:
            item = {"event": "backend_event", "source": "backend", "value": event}
        result.append(item)
    return result


def _safe_duration(start: float, end: float) -> float:
    return max(0.0, float(end) - float(start))


def _role_values(
    role: str,
    *,
    case: Mapping[str, Any],
    task: str,
    expected: Mapping[str, Any],
    context: EvaluationContext,
    result: Any,
    classification: Any,
) -> dict[str, Any]:
    values: dict[str, Any] = {
        "case": case,
        "scenario": case,
        "script": case.get("script"),
        "steps": case.get("steps"),
        "metadata": case.get("metadata"),
        "input": task,
        "payload": case if role != "verifier" else result,
        "task": task,
        "prompt": task,
        "text": task,
        "task_description": task,
        "context": context,
        "ctx": context,
        "evaluation_context": context,
        "trial": context.get("trial"),
        "attempt": context.get("attempt"),
        "expected": expected,
        "gold": expected,
        "classification": classification,
        "classified": classification,
        "result": result,
        "actual": result,
        "output": result,
        "response": result,
        "answer": result,
        "verification": context.get("verification"),
        "verifier_result": context.get("verification"),
    }
    return values


def _default_role_value(role: str, position: int, values: Mapping[str, Any], result: Any) -> Any:
    # Named parameters get precise values above.  Unknown positional
    # parameters receive a conventional, useful first argument and a context
    # object as the second argument.
    if role == "verifier":
        if position == 0 and result is not _MISSING:
            return result
        if position == 1:
            return values.get("case")
        return values.get("context") if position > 1 else values.get("case")
    if position == 0:
        if role == "agent" and "task" in values:
            return values["task"]
        return values.get("case")
    if position == 1:
        if role == "agent":
            return values.get("classification")
        return values.get("context")
    return values.get("context")


def _invoke_role(
    fn: Callable[..., Any],
    role: str,
    *,
    case: Mapping[str, Any],
    task: str,
    expected: Mapping[str, Any],
    context: EvaluationContext,
    result: Any,
    classification: Any,
) -> Any:
    """Invoke a role callable while accommodating common Python signatures."""

    values = _role_values(
        role,
        case=case,
        task=task,
        expected=expected,
        context=context,
        result=result,
        classification=classification,
    )
    try:
        signature = inspect.signature(fn)
    except (TypeError, ValueError):
        if role == "verifier" and result is not _MISSING:
            return fn(result)
        return fn(case)

    positional: list[Any] = []
    keywords: dict[str, Any] = {}
    has_varargs = False
    has_varkw = False
    position = 0
    parameters = list(signature.parameters.values())
    parameter_names = {parameter.name for parameter in parameters}
    for parameter in parameters:
        if parameter.kind == inspect.Parameter.VAR_POSITIONAL:
            has_varargs = True
            continue
        if parameter.kind == inspect.Parameter.VAR_KEYWORD:
            has_varkw = True
            continue
        name = parameter.name
        value = values.get(name, _MISSING)
        if value is _MISSING and parameter.default is inspect.Parameter.empty:
            value = _default_role_value(role, position, values, result)
        if value is not _MISSING:
            if parameter.kind == inspect.Parameter.KEYWORD_ONLY:
                keywords[name] = value
            else:
                positional.append(value)
        position += 1

    if has_varargs:
        positional.append(_default_role_value(role, position, values, result))
    if has_varkw:
        for name, value in values.items():
            if name not in keywords and name not in parameter_names:
                keywords[name] = value

    try:
        signature.bind(*positional, **keywords)
    except TypeError:
        # A few extension callables expose an unhelpful signature.  The
        # documented fallback is deliberately small and predictable.
        if role == "verifier" and result is not _MISSING:
            return fn(result)
        return fn(case)
    return fn(*positional, **keywords)


def _normalise_domains(value: Any) -> Optional[list[str]]:
    if value is _MISSING or value is None:
        return None
    if isinstance(value, str):
        return [value]
    if isinstance(value, (set, frozenset)):
        return sorted({str(item) for item in value})
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return sorted({str(item) for item in value})
    return [str(value)]


def _classification_actual(value: Any) -> Any:
    if isinstance(value, Mapping):
        nested = value.get("classification")
        if not isinstance(nested, Mapping):
            nested = value.get("routing")
        if not isinstance(nested, Mapping):
            nested = value.get("decision")
        if isinstance(nested, Mapping):
            merged = dict(nested)
            merged.update({key: item for key, item in value.items() if key != "classification"})
            value = merged
        route = value.get("route")
        if isinstance(route, Mapping):
            merged = dict(value)
            for key, item in route.items():
                merged.setdefault(key, item)
            return merged
    return value


def _expected_success_check(expected: Mapping[str, Any], verifier_success: Optional[bool]) -> dict[str, Any]:
    expected_value = expected.get("success", _MISSING)
    if expected_value is _MISSING:
        return {"status": STATUS_NOT_RUN, "reason": "no_expected_success", "matches": None}
    if not isinstance(expected_value, bool):
        return {"status": STATUS_UNCERTAIN, "reason": "expected_success_not_boolean", "matches": None}
    if verifier_success is None:
        return {
            "status": STATUS_UNCERTAIN,
            "reason": "verifier_not_available_for_expected_success",
            "matches": None,
            "expected": expected_value,
        }
    matches = expected_value is verifier_success
    return {
        "status": STATUS_PASS if matches else STATUS_FAIL,
        "reason": "expected_success_matched" if matches else "expected_success_mismatch",
        "matches": matches,
        "expected": expected_value,
        "actual": verifier_success,
    }


def _routing_check(case: Mapping[str, Any], classification: Any, classifier_ran: bool, classifier_failed: bool) -> dict[str, Any]:
    expected = _expected_fields(case)
    expected = {key: value for key, value in expected.items() if key not in {"success", "passed", "ok"}}
    if not expected:
        return {"status": STATUS_NOT_RUN, "reason": "no_expected_route", "matches": None}
    if classifier_failed:
        return {
            "status": STATUS_FAIL,
            "reason": "classifier_failed",
            "matches": False,
            "expected": expected,
            "actual": None,
        }
    if not classifier_ran or classification is _MISSING:
        return {
            "status": STATUS_UNCERTAIN,
            "reason": "classifier_not_run",
            "matches": None,
            "expected": expected,
            "actual": None,
        }

    actual = _classification_actual(classification)
    if not isinstance(actual, Mapping):
        if isinstance(actual, str) and "route" in expected:
            actual = {"route": actual}
        else:
            return {
                "status": STATUS_UNCERTAIN,
                "reason": "classifier_output_not_structured",
                "matches": None,
                "expected": expected,
                "actual": actual,
            }

    aliases = {
        "size": ("size", "expected_size", "task_size", "complexity"),
        "domains": ("domains", "expected_domains", "domain", "primary_domain", "modules", "selected_modules", "selected_domains"),
        "risk": ("risk", "expected_risk", "risk_level"),
        "pattern": ("pattern", "expected_pattern", "route_pattern"),
        "route": ("route", "path", "selected_route", "primary_domain", "domain"),
        "primary_domain": ("primary_domain", "domain", "route"),
        "tool": ("tool", "selected_tool", "primary_tool"),
        "tools": ("tools", "selected_tools", "tool"),
    }
    mismatches: list[dict[str, Any]] = []
    missing: list[str] = []
    matches: dict[str, bool] = {}
    for expected_key, expected_value in expected.items():
        canonical = expected_key[9:] if expected_key.startswith("expected_") else expected_key
        candidates = aliases.get(canonical, (canonical,))
        actual_value: Any = _MISSING
        for candidate in candidates:
            if candidate in actual:
                actual_value = actual[candidate]
                break
        if actual_value is _MISSING:
            missing.append(str(expected_key))
            continue
        if canonical in {"domains", "tools"}:
            equal = _normalise_domains(expected_value) == _normalise_domains(actual_value)
        else:
            equal = expected_value == actual_value
        matches[str(expected_key)] = bool(equal)
        if not equal:
            mismatches.append(
                {
                    "field": str(expected_key),
                    "expected": expected_value,
                    "actual": actual_value,
                }
            )
    if missing:
        return {
            "status": STATUS_UNCERTAIN,
            "reason": "classifier_output_missing_fields",
            "matches": None,
            "field_matches": matches,
            "missing": missing,
            "mismatches": mismatches,
            "expected": expected,
            "actual": actual,
        }
    return {
        "status": STATUS_PASS if not mismatches else STATUS_FAIL,
        "reason": "expected_route_matched" if not mismatches else "expected_route_mismatch",
        "matches": not mismatches,
        "field_matches": matches,
        "mismatches": mismatches,
        "expected": expected,
        "actual": actual,
    }


# ---------------------------------------------------------------------------
# Metrics and result aggregation
# ---------------------------------------------------------------------------


def _combine_tokens(values: list[dict[str, Optional[float]]]) -> dict[str, Optional[float]]:
    result: dict[str, Optional[float]] = {}
    for key in ("input", "output", "total"):
        supplied = [item[key] for item in values if item.get(key) is not None]
        result[key] = sum(supplied) if supplied else None
    if result["total"] is None and (result["input"] is not None or result["output"] is not None):
        result["total"] = (result["input"] or 0.0) + (result["output"] or 0.0)
    return result


def _percentile(values: list[float], percentile: float) -> Optional[float]:
    if not values:
        return None
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    position = (len(ordered) - 1) * percentile
    lower = int(math.floor(position))
    upper = int(math.ceil(position))
    if lower == upper:
        return ordered[lower]
    fraction = position - lower
    return ordered[lower] + (ordered[upper] - ordered[lower]) * fraction


def _pass_probabilities(successes: Sequence[Optional[bool]], k: Optional[int]) -> dict[str, Any]:
    total = len(successes)
    success_count = sum(value is True for value in successes)
    if total == 0:
        return {
            "success_rate": None,
            "pass_at_k": None,
            "pass_power_k": None,
            "pass_at_1": None,
            "pass_at_k_formula": "1 - C(n-c, k) / C(n, k)",
            "pass_power_k_formula": "C(c, k) / C(n, k)",
        }
    success_rate = success_count / total
    effective_k = 1 if k is None else k
    if effective_k < 1 or effective_k > total:
        at_k = None
        power_k = None
    else:
        failures = total - success_count
        at_k = 1.0 if failures < effective_k else 1.0 - math.comb(failures, effective_k) / math.comb(total, effective_k)
        power_k = math.comb(success_count, effective_k) / math.comb(total, effective_k)
    return {
        "success_rate": success_rate,
        "pass_at_k": at_k,
        "pass_power_k": power_k,
        "pass_at_1": success_rate,
        "pass_at_k_formula": "1 - C(n-c, k) / C(n, k)",
        "pass_power_k_formula": "C(c, k) / C(n, k)",
    }


def _aggregate_metrics(
    payloads: list[Any],
    *,
    actual_retries: int,
    measured_latency_ms: float,
    reported_latencies: list[float],
) -> dict[str, Any]:
    tool_counts = [_extract_tool_count(payload) for payload in payloads]
    reported_retries = [_extract_retry_count(payload) for payload in payloads]
    tool_calls = sum(count for count in tool_counts if count is not None)
    reported_retry_total = sum(count for count in reported_retries if count is not None and count > 0)
    retries = max(actual_retries, reported_retry_total)
    tokens = _combine_tokens([_extract_tokens(payload) for payload in payloads])
    costs = [_extract_cost(payload) for payload in payloads]
    supplied_costs = [cost for cost in costs if cost is not None]
    cost = sum(supplied_costs) if supplied_costs else None
    if reported_latencies:
        latency = sum(reported_latencies)
        latency_source = "reported"
    else:
        latency = measured_latency_ms
        latency_source = "measured"
    return {
        "tool_calls": tool_calls,
        "retries": retries,
        "latency_ms": round(max(0.0, float(latency)), 6),
        "latency": round(max(0.0, float(latency)), 6),
        "measured_latency_ms": round(max(0.0, float(measured_latency_ms)), 6),
        "latency_source": latency_source,
        "tokens": tokens,
        "input_tokens": tokens["input"],
        "output_tokens": tokens["output"],
        "total_tokens": tokens["total"],
        "cost": cost,
        "cost_usd": cost,
        "reported_tokens": any(item.get("total") is not None for item in (_extract_tokens(payload) for payload in payloads)),
        "reported_cost": bool(supplied_costs),
        "reported_latency": bool(reported_latencies),
    }


def _status_counts(records: Iterable[Mapping[str, Any]]) -> dict[str, int]:
    counts = {status: 0 for status in (STATUS_PASS, STATUS_FAIL, STATUS_UNCERTAIN, STATUS_NOT_RUN)}
    for record in records:
        status = record.get("status")
        if status in counts:
            counts[status] += 1
    return counts


def _aggregate_trial_metrics(trials: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    metrics = [trial.get("metrics", {}) for trial in trials]
    tool_calls = sum(int(item.get("tool_calls", 0)) for item in metrics if isinstance(item, Mapping))
    retries = sum(int(item.get("retries", 0)) for item in metrics if isinstance(item, Mapping))
    latencies = [
        float(item.get("latency_ms", 0.0))
        for item in metrics
        if isinstance(item, Mapping)
    ]
    tokens = _combine_tokens(
        [
            item.get("tokens", {})
            for item in metrics
            if isinstance(item, Mapping) and isinstance(item.get("tokens", {}), Mapping)
        ]
    )
    costs = [
        item.get("cost")
        for item in metrics
        if isinstance(item, Mapping) and item.get("cost") is not None
    ]
    cost = sum(costs) if costs else None
    return {
        "tool_calls": tool_calls,
        "retries": retries,
        "latency_ms": {
            "total": round(sum(latencies), 6),
            "mean": round(sum(latencies) / len(latencies), 6) if latencies else None,
            "p50": _percentile(latencies, 0.50),
            "p95": _percentile(latencies, 0.95),
        },
        "tokens": tokens,
        "cost": cost,
        "cost_usd": cost,
    }


def _case_status(trials: Sequence[Mapping[str, Any]]) -> str:
    statuses = [trial.get("status") for trial in trials]
    if not statuses:
        return STATUS_NOT_RUN
    if STATUS_FAIL in statuses:
        return STATUS_FAIL
    if STATUS_UNCERTAIN in statuses:
        return STATUS_UNCERTAIN
    if STATUS_NOT_RUN in statuses:
        return STATUS_UNCERTAIN if STATUS_PASS in statuses else STATUS_NOT_RUN
    return STATUS_PASS


def _backend_provenance(
    classifier: Optional[Callable[..., Any]],
    agent: Optional[Callable[..., Any]],
    verifier: Optional[Callable[..., Any]],
    backend: Any,
    case_source: str,
    fixture_only: bool,
) -> dict[str, Any]:
    supplied_backend: Any
    if isinstance(backend, Mapping):
        supplied_backend = dict(backend)
    elif isinstance(backend, str):
        supplied_backend = {"name": backend}
    elif backend is not None:
        supplied_backend = {
            key: getattr(backend, key)
            for key in ("name", "kind", "provider", "model", "real_model")
            if hasattr(backend, key)
        }
    else:
        supplied_backend = {}
    available = any(callable(item) for item in (classifier, agent, verifier))
    if available:
        kind = str(supplied_backend.get("kind") or "injected_callables")
        source = "injected_callables"
    else:
        kind = "none"
        source = "none"
    limitations = [
        "This runner executes injected callables; it does not discover, select, or authenticate a model provider.",
        "It uses only the Python standard library and introduces no runtime provider or network dependency.",
        "Results from static golden/scripted cases are fixture executions, not a real model benchmark.",
        "Missing token, cost, or supplied latency values remain null; measured wall-clock latency is reported separately.",
        "Reported stage latencies are summed; callers should provide per-call rather than cumulative durations.",
        "Pass@k/pass^k aggregates count only true successes; use status_counts and scored_trials to interpret uncertain or not_run trials.",
    ]
    if not available:
        limitations.append("No provider/backend was supplied, so every component is explicitly not_run rather than scored.")
    backend_fixture = any(word in kind.lower() for word in ("script", "fixture", "golden"))
    if fixture_only or backend_fixture:
        limitations.append("The case source or backend is marked fixture-only; do not generalize its score to model quality.")
    real_model = available and bool(supplied_backend.get("real_model", False))
    return {
        "mode": "injected_callables" if available else "no_provider",
        "provider_mode": available,
        "backend_mode": "provider" if available else "none",
        "execution_mode": "injected_callables" if available else "no_provider",
        "source": source,
        "kind": kind,
        "backend_name": kind,
        "type": kind,
        "provenance": source,
        "provider": supplied_backend.get("provider") if available else None,
        "model": supplied_backend.get("model") if available else None,
        "real_model": real_model,
        "verified_real_model": False,
        "is_model_benchmark": False,
        "is_real_model": real_model,
        "provider_neutral": True,
        "benchmark_claim": "not_claimed",
        "case_source": case_source,
        "fixture_only": fixture_only or backend_fixture,
        "is_fixture": fixture_only or backend_fixture,
        "is_static_fixture": fixture_only or backend_fixture,
        "case_fixture_only": fixture_only,
        "backend_fixture_only": backend_fixture,
        "provider_available": available,
        "available_callables": {
            "classifier": callable(classifier),
            "agent": callable(agent),
            "verifier": callable(verifier),
        },
        "supplied_backend": supplied_backend,
        "limitations": limitations,
    }


class EvaluationRunner:
    """Execute cases against injected, provider-neutral callables.

    Parameters
    ----------
    cases:
        A case list, case mapping, path, or ``None``.  It may be supplied here
        or to :meth:`run`.
    classifier, agent, verifier:
        Optional callables.  See the module docstring for the flexible
        invocation contract.  No callable is discovered implicitly.
    trials:
        Default number of independent trials per case.
    pass_k:
        Sample size used for both ``pass_at_k`` and ``pass^k`` metrics.
    max_retries:
        Optional bounded retry count for exceptions or explicitly retryable
        results.  Retries are opt-in because a callable may perform side
        effects.
    backend:
        Optional descriptive metadata only.  It is never used to import or
        contact a provider.
    """

    def __init__(
        self,
        cases: Any = None,
        classifier: Optional[Callable[..., Any]] = None,
        agent: Optional[Callable[..., Any]] = None,
        verifier: Optional[Callable[..., Any]] = None,
        *,
        trials: int = 1,
        num_trials: Optional[int] = None,
        n_trials: Optional[int] = None,
        repeat: Optional[int] = None,
        repetitions: Optional[int] = None,
        n: Optional[int] = None,
        pass_k: Optional[int] = None,
        pass_power_k: Optional[int] = None,
        k: Optional[int] = None,
        max_retries: int = 0,
        retry_on: Iterable[str] = ("exception",),
        backend: Any = None,
        clock: Optional[Callable[[], float]] = None,
        redact_keys: Iterable[str] = (),
        secret_values: Iterable[str] = (),
    ) -> None:
        # Also accept the natural ``EvaluationRunner(classifier, agent,
        # verifier, cases)`` positional form without weakening the documented
        # ``cases, classifier, agent, verifier`` form.
        if (
            callable(cases)
            and callable(classifier)
            and callable(agent)
            and not callable(verifier)
            and isinstance(verifier, (list, tuple, CaseList, Mapping, Iterable))
        ):
            cases, classifier, agent, verifier = verifier, cases, classifier, agent
        if isinstance(cases, Mapping) and not isinstance(cases, CaseList):
            # A single case mapping is a valid case source, but a mapping with
            # a cases key is handled by load_cases.
            cases = load_cases(cases)
        elif cases is not None and not isinstance(cases, CaseList):
            cases = load_cases(cases)
        self.cases: CaseList = cases if isinstance(cases, CaseList) else (cases or CaseList([], source="none"))
        self.classifier = classifier
        self.agent = agent
        self.verifier = verifier
        if num_trials is not None:
            trials = num_trials
        if n_trials is not None:
            trials = n_trials
        if repeat is not None:
            trials = repeat
        if repetitions is not None:
            trials = repetitions
        if n is not None:
            trials = n
        self.trials = self._validate_trials(trials)
        self.pass_k = self._validate_pass_k(
            pass_k
            if pass_k is not None
            else pass_power_k
            if pass_power_k is not None
            else k
        )
        self.max_retries = self._validate_nonnegative(max_retries, name="max_retries")
        self.retry_on = (
            set()
            if retry_on is None
            else {str(retry_on).lower()}
            if isinstance(retry_on, str)
            else {str(item).lower() for item in retry_on}
        )
        self.backend = backend
        self.clock = clock or time.perf_counter
        self.redact_keys = (
            ()
            if redact_keys is None
            else (str(redact_keys),)
            if isinstance(redact_keys, str)
            else tuple(redact_keys)
        )
        self.secret_values = (
            ()
            if secret_values is None
            else (str(secret_values),)
            if isinstance(secret_values, str)
            else tuple(str(item) for item in secret_values)
        )

    @staticmethod
    def _validate_trials(value: Any, *, name: str = "trials") -> int:
        if isinstance(value, bool) or not isinstance(value, numbers.Integral) or int(value) < 1:
            raise EvaluationError(f"{name} must be a positive integer")
        return int(value)

    @staticmethod
    def _validate_nonnegative(value: Any, *, name: str) -> int:
        if isinstance(value, bool) or not isinstance(value, numbers.Integral) or int(value) < 0:
            raise EvaluationError(f"{name} must be a non-negative integer")
        return int(value)

    @staticmethod
    def _validate_pass_k(value: Any) -> Optional[int]:
        if value is None:
            return None
        if isinstance(value, bool) or not isinstance(value, numbers.Integral) or int(value) < 1:
            raise EvaluationError("pass_k must be a positive integer or None")
        return int(value)

    def _redact(self, value: Any) -> Any:
        return _json_safe(
            redact_value(
                value,
                extra_keys=self.redact_keys,
                secret_values=self.secret_values,
            )
        )

    def _add_event(self, trace: list[dict[str, Any]], event: str, **values: Any) -> None:
        row: dict[str, Any] = {"event": event, "phase": event, "source": "runner"}
        row.update(values)
        trace.append(row)

    def _execute_phase(
        self,
        role: str,
        fn: Optional[Callable[..., Any]],
        *,
        case: Mapping[str, Any],
        task: str,
        expected: Mapping[str, Any],
        context: EvaluationContext,
        trace: list[dict[str, Any]],
        result: Any = _MISSING,
        classification: Any = _MISSING,
    ) -> tuple[Any, dict[str, Any]]:
        if not callable(fn):
            self._add_event(
                trace,
                role,
                status=STATUS_NOT_RUN,
                reason="no_callable",
            )
            return _MISSING, {"ran": False, "failed": False, "retries": 0, "duration_ms": 0.0}

        retries = 0
        for attempt in range(self.max_retries + 1):
            context["attempt"] = attempt
            started = self.clock()
            try:
                value = _invoke_role(
                    fn,
                    role,
                    case=case,
                    task=task,
                    expected=expected,
                    context=context,
                    result=result,
                    classification=classification,
                )
            except Exception as exc:  # user callables are an injected boundary
                if "exception" in self.retry_on and attempt < self.max_retries:
                    retries += 1
                    self._add_event(
                        trace,
                        "retry",
                        status=STATUS_FAIL,
                        phase_name=role,
                        attempt=attempt,
                        next_attempt=attempt + 1,
                        error={"type": type(exc).__name__, "message": str(exc)},
                    )
                    continue
                self._add_event(
                    trace,
                    role,
                    status=STATUS_FAIL,
                    error={"type": type(exc).__name__, "message": str(exc)},
                    duration_ms=round(_safe_duration(started, self.clock()), 6),
                )
                return _MISSING, {
                    "ran": True,
                    "failed": True,
                    "retries": retries,
                    "duration_ms": _safe_duration(started, self.clock()),
                    "error": {"type": type(exc).__name__, "message": str(exc)},
                }

            retry_verifier_failure = (
                role == "verifier"
                and "verifier_failure" in self.retry_on
                and _verdict(value)[0] is False
            )
            if (
                (_retryable_result(value) and "retryable" in self.retry_on)
                or retry_verifier_failure
            ) and attempt < self.max_retries:
                retries += 1
                self._add_event(
                    trace,
                    "retry",
                    status=STATUS_UNCERTAIN,
                    reason="retryable_result",
                    phase_name=role,
                    attempt=attempt,
                    next_attempt=attempt + 1,
                    output=value,
                )
                continue

            duration = _safe_duration(started, self.clock())
            declared_failed = role in {"classifier", "agent"} and (
                value is False or _declared_failure(value)
            )
            declared_uncertain = role in {"classifier", "agent"} and (
                _declared_uncertain(value) or _retryable_result(value)
            )
            self._add_event(
                trace,
                role,
                status=STATUS_FAIL
                if declared_failed
                else STATUS_UNCERTAIN
                if declared_uncertain
                else STATUS_PASS,
                output=value,
                duration_ms=round(duration, 6),
                **(
                    {"reason": "callable_declared_failure"}
                    if declared_failed
                    else {"reason": "callable_uncertain"}
                    if declared_uncertain
                    else {}
                ),
            )
            for event in _events_from_payload(value):
                event.setdefault("phase", role)
                event["source"] = event.get("source", "backend")
                trace.append(event)
            return value, {
                "ran": True,
                "failed": declared_failed,
                "uncertain": declared_uncertain,
                "retries": retries,
                "duration_ms": duration,
            }

        # The loop always returns; this is a defensive guard for subclasses.
        return _MISSING, {"ran": True, "failed": True, "retries": retries, "duration_ms": 0.0}

    def _run_trial(
        self,
        case: Mapping[str, Any],
        *,
        case_id: str,
        trial_index: int,
    ) -> dict[str, Any]:
        # Backends are injected and may retain/mutate their input.  Evaluate a
        # private copy so one trial cannot silently rewrite the case contract
        # seen by a later trial.
        case = (
            copy.deepcopy(dict(case))
            if any(callable(item) for item in (self.classifier, self.agent, self.verifier))
            else dict(case)
        )
        task = _case_task(case)
        expected = _expected_fields(case)
        context = EvaluationContext(
            {
                "case": case,
                "task": task,
                "expected": expected,
                "trial": trial_index,
                "attempt": 0,
                "classification": None,
                "result": None,
                "verification": None,
                "trace": [],
            }
        )
        trace: list[dict[str, Any]] = []
        context["trace"] = trace
        instrumented_tool_calls: list[Any] = []
        instrumented_retries: list[Any] = []

        def record_tool_call(value: Any = None, **details: Any) -> None:
            if isinstance(value, Mapping):
                event = dict(value)
            else:
                event = {"tool": value} if value is not None else {}
            event.update(details)
            event.setdefault("event", "tool_call")
            instrumented_tool_calls.append(event)
            trace_event = dict(event)
            event_name = trace_event.pop("event", "tool_call")
            trace_event.pop("source", None)
            self._add_event(trace, event_name, source="instrumented", **trace_event)

        def record_retry(value: Any = None, **details: Any) -> None:
            if isinstance(value, Mapping):
                event = dict(value)
            else:
                event = {"reason": value} if value is not None else {}
            event.update(details)
            event.setdefault("event", "retry")
            instrumented_retries.append(event)
            trace_event = dict(event)
            event_name = trace_event.pop("event", "retry")
            trace_event.pop("source", None)
            self._add_event(trace, event_name, source="instrumented", **trace_event)

        context["tool_calls"] = instrumented_tool_calls
        context["retries"] = instrumented_retries
        context["record_tool_call"] = record_tool_call
        context["record_retry"] = record_retry
        self._add_event(trace, "trial_start", case_id=case_id, trial=trial_index)
        if case.get("script") is not None or case.get("steps") is not None:
            self._add_event(
                trace,
                "script",
                script=case.get("script", case.get("steps")),
                source="fixture",
            )
        started = self.clock()

        classification = _MISSING
        classification_meta = {"ran": False, "failed": False, "retries": 0, "duration_ms": 0.0}
        agent_result = _MISSING
        agent_meta = {"ran": False, "failed": False, "retries": 0, "duration_ms": 0.0}
        verification = _MISSING
        verifier_meta = {"ran": False, "failed": False, "retries": 0, "duration_ms": 0.0}

        if callable(self.classifier):
            classification, classification_meta = self._execute_phase(
                "classifier",
                self.classifier,
                case=case,
                task=task,
                expected=expected,
                context=context,
                trace=trace,
            )
            context["classification"] = None if classification is _MISSING else classification
        else:
            self._add_event(trace, "classifier", status=STATUS_NOT_RUN, reason="no_callable")
            classification_meta = {"ran": False, "failed": False, "retries": 0, "duration_ms": 0.0}

        # A classifier exception invalidates the route, so do not execute an
        # agent with an untrusted/missing classification.  A missing optional
        # classifier is different: an agent may still be independently useful.
        if (
            not classification_meta["failed"]
            and not classification_meta.get("uncertain")
            and callable(self.agent)
        ):
            agent_result, agent_meta = self._execute_phase(
                "agent",
                self.agent,
                case=case,
                task=task,
                expected=expected,
                context=context,
                trace=trace,
                classification=classification,
            )
            context["result"] = None if agent_result is _MISSING else agent_result
        elif not callable(self.agent):
            self._add_event(trace, "agent", status=STATUS_NOT_RUN, reason="no_callable")
        else:
            reason = "classifier_failed" if classification_meta["failed"] else "classifier_uncertain"
            self._add_event(trace, "agent", status=STATUS_NOT_RUN, reason=reason)

        if (
            callable(self.verifier)
            and agent_meta["ran"]
            and not agent_meta["failed"]
        ):
            verification, verifier_meta = self._execute_phase(
                "verifier",
                self.verifier,
                case=case,
                task=task,
                expected=expected,
                context=context,
                trace=trace,
                result=agent_result,
                classification=classification,
            )
            context["verification"] = None if verification is _MISSING else verification
        elif not callable(self.verifier):
            self._add_event(trace, "verifier", status=STATUS_NOT_RUN, reason="no_callable")
        elif not agent_meta["ran"]:
            self._add_event(trace, "verifier", status=STATUS_NOT_RUN, reason="agent_not_run")
        else:
            self._add_event(trace, "verifier", status=STATUS_NOT_RUN, reason="agent_failed")

        routing = _routing_check(
            case,
            classification,
            classifier_ran=classification_meta["ran"],
            classifier_failed=classification_meta["failed"],
        )
        verifier_success: Optional[bool]
        verifier_reason: str
        if not callable(self.verifier):
            verifier_success, verifier_reason = None, "verifier_not_run"
        elif verifier_meta["failed"]:
            verifier_success, verifier_reason = False, "verifier_failed"
        else:
            verifier_success, verifier_reason = _verdict(verification)
        expectation = _expected_success_check(expected, verifier_success)

        status_reasons: list[str] = []
        if classification_meta["failed"]:
            status = STATUS_FAIL
            status_reasons.append("classifier_failed")
        elif routing["status"] == STATUS_FAIL:
            status = STATUS_FAIL
            status_reasons.append(routing["reason"])
        elif classification_meta.get("uncertain") or _retryable_result(classification):
            status = STATUS_UNCERTAIN
            status_reasons.append("classifier_uncertain")
        elif expectation["status"] == STATUS_FAIL:
            status = STATUS_FAIL
            status_reasons.append(expectation["reason"])
        elif not agent_meta["ran"]:
            status = STATUS_NOT_RUN
            status_reasons.append("agent_not_run")
        elif agent_meta["failed"]:
            status = STATUS_FAIL
            status_reasons.append("agent_failed")
        elif agent_result is False or _declared_failure(agent_result):
            status = STATUS_FAIL
            status_reasons.append("agent_declared_failure")
        elif not callable(self.verifier):
            status = STATUS_UNCERTAIN
            status_reasons.append(verifier_reason)
        elif verifier_meta["failed"]:
            status = STATUS_FAIL
            status_reasons.append(verifier_reason)
        elif verifier_success is False:
            status = STATUS_FAIL
            status_reasons.append(verifier_reason)
        elif (
            classification_meta.get("uncertain")
            or _retryable_result(classification)
            or agent_meta.get("uncertain")
            or _declared_uncertain(agent_result)
            or _retryable_result(agent_result)
        ):
            status = STATUS_UNCERTAIN
            status_reasons.append("callable_uncertain")
        elif verifier_success is None:
            status = STATUS_UNCERTAIN
            status_reasons.append(verifier_reason)
        elif expectation["status"] == STATUS_UNCERTAIN:
            status = STATUS_UNCERTAIN
            status_reasons.append(expectation["reason"])
        elif routing["status"] == STATUS_UNCERTAIN:
            status = STATUS_UNCERTAIN
            status_reasons.append(routing["reason"])
        else:
            status = STATUS_PASS
            status_reasons.append("independent_verifier_passed")

        measured_latency = _safe_duration(started, self.clock())
        payloads = [
            item
            for item in (classification, agent_result, verification)
            if item is not _MISSING
        ]
        payloads.append({"tool_calls": instrumented_tool_calls, "retries": instrumented_retries})
        actual_retries = sum(
            int(meta.get("retries", 0))
            for meta in (classification_meta, agent_meta, verifier_meta)
        )
        reported_latencies = [
            latency
            for payload in payloads
            for latency in [_extract_reported_latency(payload)]
            if latency is not None
        ]
        metrics = _aggregate_metrics(
            payloads,
            actual_retries=actual_retries,
            measured_latency_ms=measured_latency,
            reported_latencies=reported_latencies,
        )
        trial_success = True if status == STATUS_PASS else False if status == STATUS_FAIL else None
        metrics["success"] = trial_success
        metrics["status"] = status
        self._add_event(
            trace,
            "trial_end",
            case_id=case_id,
            trial=trial_index,
            status=status,
            metrics=metrics,
        )

        safe_case = {
            key: value
            for key, value in case.items()
            if not str(key).startswith("_")
        }
        component_status = {
            "classifier": STATUS_FAIL
            if classification_meta["failed"]
            else STATUS_UNCERTAIN
            if classification_meta.get("uncertain")
            else STATUS_PASS
            if classification_meta["ran"]
            else STATUS_NOT_RUN,
            "agent": STATUS_FAIL
            if agent_meta["failed"]
            else STATUS_UNCERTAIN
            if agent_meta.get("uncertain")
            else STATUS_PASS
            if agent_meta["ran"]
            else STATUS_NOT_RUN,
            "verifier": STATUS_FAIL
            if verifier_meta["failed"]
            else STATUS_PASS
            if verifier_meta["ran"]
            else STATUS_NOT_RUN,
        }
        errors: list[dict[str, Any]] = []
        for phase_name, phase_meta in (
            ("classifier", classification_meta),
            ("agent", agent_meta),
            ("verifier", verifier_meta),
        ):
            if phase_meta.get("error"):
                errors.append({"phase": phase_name, **dict(phase_meta["error"])})
        result: dict[str, Any] = {
            "case_id": case_id,
            "trial": trial_index,
            "trial_index": trial_index,
            "trial_number": trial_index + 1,
            "status": status,
            "outcome": status,
            "executed": status != STATUS_NOT_RUN,
            "success": trial_success,
            "passed": trial_success,
            "task": task,
            "case": safe_case,
            "expected": expected,
            "classification": None if classification is _MISSING else classification,
            "agent_result": None if agent_result is _MISSING else agent_result,
            "verification": None if verification is _MISSING else verification,
            "routing": routing,
            "expectation": expectation,
            "metrics": metrics,
            "tool_calls": metrics["tool_calls"],
            "retries": metrics["retries"],
            "latency_ms": metrics["latency_ms"],
            "latency": metrics["latency_ms"],
            "tokens": metrics["tokens"],
            "cost": metrics["cost"],
            "trace": trace,
            "events": trace,
            "errors": errors,
            "error": errors[0] if errors else None,
            "status_reasons": status_reasons,
            "component_status": component_status,
            "stages": component_status,
        }
        return self._redact(result)

    def run(
        self,
        cases: Any = None,
        trials: Optional[int] = None,
        *,
        num_trials: Optional[int] = None,
        n_trials: Optional[int] = None,
        repeat: Optional[int] = None,
        repetitions: Optional[int] = None,
        n: Optional[int] = None,
        pass_k: Optional[int] = None,
        pass_power_k: Optional[int] = None,
        k: Optional[int] = None,
    ) -> dict[str, Any]:
        """Run cases and return a machine-readable result dictionary."""

        selected = self.cases if cases is None else load_cases(cases)
        trial_count = trials if trials is not None else num_trials
        if n_trials is not None:
            trial_count = n_trials
        if repeat is not None:
            trial_count = repeat
        if repetitions is not None:
            trial_count = repetitions
        if n is not None:
            trial_count = n
        if trial_count is None:
            trial_count = self.trials
        trial_count = self._validate_trials(trial_count)
        requested_k = (
            pass_k
            if pass_k is not None
            else pass_power_k
            if pass_power_k is not None
            else k
            if k is not None
            else self.pass_k
        )
        requested_k = self._validate_pass_k(requested_k)
        if (
            requested_k is not None
            and requested_k > trial_count
            and num_trials is None
            and trials is None
            and n is None
            and repetitions is None
            and repeat is None
        ):
            trial_count = requested_k
        source = getattr(selected, "source", "provided")
        fixture_only = bool(getattr(selected, "fixture_only", False))
        provenance = _backend_provenance(
            self.classifier,
            self.agent,
            self.verifier,
            self.backend,
            source,
            fixture_only,
        )
        case_results: list[dict[str, Any]] = []
        for case_index, case in enumerate(selected):
            case_id = _case_id(case, case_index)
            trial_results = [
                self._run_trial(case, case_id=case_id, trial_index=trial_index)
                for trial_index in range(trial_count)
            ]
            successes = [trial.get("success") for trial in trial_results]
            pass_values = _pass_probabilities(successes, requested_k)
            case_status = _case_status(trial_results)
            case_success: Optional[bool]
            if not trial_results or any(value is False for value in successes):
                case_success = False if any(value is False for value in successes) else None
            elif any(value is None for value in successes):
                case_success = None
            else:
                case_success = True
            case_result = {
                "id": case_id,
                "case_id": case_id,
                "source": source,
                "status": case_status,
                "outcome": case_status,
                "executed": any(trial.get("executed") for trial in trial_results),
                "success": case_success,
                "passed": case_success,
                "trials": trial_results,
                "runs": trial_results,
                "metrics": _aggregate_trial_metrics(trial_results),
                "summary": {
                    "status": case_status,
                    "successes": sum(value is True for value in successes),
                    "failures": sum(value is False for value in successes),
                    "uncertain": sum(
                        trial.get("success") is None
                        and trial.get("status") == STATUS_UNCERTAIN
                        for trial in trial_results
                    ),
                    "not_run": sum(trial.get("status") == STATUS_NOT_RUN for trial in trial_results),
                    "trials": len(trial_results),
                    "scored": any(trial.get("success") is not None for trial in trial_results),
                    "score": (
                        _pass_probabilities(successes, requested_k)["success_rate"]
                        if any(value is not None for value in successes)
                        else None
                    ),
                    "consistent": bool(trial_results) and all(trial.get("success") is True for trial in trial_results),
                    **pass_values,
                    "pass^k": pass_values["pass_power_k"],
                },
                "pass_at_k": pass_values["pass_at_k"],
                "pass@k": pass_values["pass_at_k"],
                "pass_k": pass_values["pass_power_k"],
                "pass_power_k": pass_values["pass_power_k"],
                "pass^k": pass_values["pass_power_k"],
            }
            case_results.append(self._redact(case_result))

        all_trials = [trial for case in case_results for trial in case["trials"]]
        all_successes = [trial.get("success") for trial in all_trials]
        aggregate_pass = _pass_probabilities(all_successes, requested_k)
        case_status_counts = {status: 0 for status in (STATUS_PASS, STATUS_FAIL, STATUS_UNCERTAIN, STATUS_NOT_RUN)}
        for case in case_results:
            if case.get("status") in case_status_counts:
                case_status_counts[case["status"]] += 1
        summary = {
            "cases": len(case_results),
            "trials": len(all_trials),
            "executed_trials": sum(trial.get("status") != STATUS_NOT_RUN for trial in all_trials),
            "scored_trials": sum(trial.get("success") is not None for trial in all_trials),
            "scored": any(trial.get("success") is not None for trial in all_trials),
            "score": aggregate_pass["success_rate"] if any(value is not None for value in all_successes) else None,
            "status_counts": _status_counts(all_trials),
            "case_status_counts": case_status_counts,
            "not_run": sum(trial.get("status") == STATUS_NOT_RUN for trial in all_trials),
            "uncertain": sum(trial.get("status") == STATUS_UNCERTAIN for trial in all_trials),
            "failed": sum(trial.get("status") == STATUS_FAIL for trial in all_trials),
            "passed": sum(trial.get("status") == STATUS_PASS for trial in all_trials),
            "pass": sum(trial.get("status") == STATUS_PASS for trial in all_trials),
            "fail": sum(trial.get("status") == STATUS_FAIL for trial in all_trials),
            "successes": sum(value is True for value in all_successes),
            "failures": sum(value is False for value in all_successes),
            "success_rate": aggregate_pass["success_rate"],
            "pass_at_k": aggregate_pass["pass_at_k"],
            "pass@k": aggregate_pass["pass_at_k"],
            "pass_k": aggregate_pass["pass_power_k"],
            "pass_power_k": aggregate_pass["pass_power_k"],
            "pass_at_1": aggregate_pass["pass_at_1"],
            "pass^k": aggregate_pass["pass_power_k"],
            "pass_rate": aggregate_pass["success_rate"],
            "consistent": bool(all_trials) and all(trial.get("success") is True for trial in all_trials),
            "tool_calls": sum(int(trial.get("metrics", {}).get("tool_calls", 0)) for trial in all_trials),
            "retries": sum(int(trial.get("metrics", {}).get("retries", 0)) for trial in all_trials),
        }
        latencies = [
            float(trial.get("metrics", {}).get("latency_ms", 0.0))
            for trial in all_trials
        ]
        measured_latencies = [
            float(trial.get("metrics", {}).get("measured_latency_ms", 0.0))
            for trial in all_trials
        ]
        token_values = [
            trial.get("metrics", {}).get("tokens", {}) for trial in all_trials
        ]
        costs = [
            trial.get("metrics", {}).get("cost")
            for trial in all_trials
            if trial.get("metrics", {}).get("cost") is not None
        ]
        summary["latency_ms"] = {
            "total": round(sum(latencies), 6),
            "mean": round(sum(latencies) / len(latencies), 6) if latencies else None,
            "p50": _percentile(latencies, 0.50),
            "p95": _percentile(latencies, 0.95),
        }
        summary["latency"] = summary["latency_ms"]
        summary["measured_latency_ms"] = {
            "total": round(sum(measured_latencies), 6),
            "mean": round(sum(measured_latencies) / len(measured_latencies), 6)
            if measured_latencies
            else None,
            "p50": _percentile(measured_latencies, 0.50),
            "p95": _percentile(measured_latencies, 0.95),
        }
        summary["tokens"] = _combine_tokens(
            [item for item in token_values if isinstance(item, Mapping)]
        )
        summary["cost"] = sum(costs) if costs else None
        summary["cost_usd"] = summary["cost"]
        summary["metrics"] = {
            "success_rate": summary["success_rate"],
            "pass_at_k": summary["pass_at_k"],
            "pass^k": summary["pass^k"],
            "tool_calls": summary["tool_calls"],
            "retries": summary["retries"],
            "latency_ms": summary["latency_ms"],
            "measured_latency_ms": summary["measured_latency_ms"],
            "tokens": summary["tokens"],
            "input_tokens": summary["tokens"]["input"],
            "output_tokens": summary["tokens"]["output"],
            "total_tokens": summary["tokens"]["total"],
            "cost": summary["cost"],
            "cost_usd": summary["cost"],
        }
        result = {
            "schema_version": "1.0",
            "kind": "provider_neutral_evaluation",
            "provenance": provenance,
            "backend": provenance,
            "backend_provenance": provenance,
            "mode": provenance["mode"],
            "limitations": provenance["limitations"],
            "status": _case_status(all_trials),
            "config": {
                "trials": trial_count,
                "pass_k": requested_k,
                "k_effective": requested_k or 1,
                "max_retries": self.max_retries,
                "retry_on": sorted(self.retry_on),
                "redaction": {"enabled": True, "placeholder": "[REDACTED]"},
            },
            "summary": summary,
            "metrics": summary["metrics"],
            "cases": case_results,
            "case_results": case_results,
            "trial_results": all_trials,
            # ``results`` is a deliberately boring compatibility alias for
            # callers that use result-oriented terminology.
            "results": case_results,
        }
        return self._redact(result)

    def to_json(self, result: Optional[Mapping[str, Any]] = None, *, indent: int = 2, sort_keys: bool = True) -> str:
        """Serialize a result dictionary as redacted JSON."""

        value = self.run() if result is None else self._redact(result)
        return json.dumps(value, indent=indent, sort_keys=sort_keys, ensure_ascii=False)

    def write_json(
        self,
        result: Any,
        path: Any,
        *,
        indent: int = 2,
        sort_keys: bool = True,
    ) -> Path:
        """Write a redacted result to *path* and return the path."""

        if isinstance(result, (str, Path)) and isinstance(path, Mapping):
            result, path = path, result
        destination = Path(path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(self.to_json(result, indent=indent, sort_keys=sort_keys) + "\n", encoding="utf-8")
        return destination

    def evaluate(self, cases: Any = None, **kwargs: Any) -> dict[str, Any]:
        """Alias for :meth:`run`."""

        return self.run(cases, **kwargs)

    def evaluate_case(
        self,
        case: Mapping[str, Any],
        *,
        trial: int = 0,
        trial_index: Optional[int] = None,
    ) -> dict[str, Any]:
        """Alias for :meth:`run_case`."""

        return self.run_case(case, trial=trial, trial_index=trial_index)

    def run_case(
        self,
        case: Mapping[str, Any],
        *,
        trial: int = 0,
        trial_index: Optional[int] = None,
    ) -> dict[str, Any]:
        """Execute one trial directly, useful for focused diagnostics."""

        if not isinstance(case, Mapping):
            raise EvaluationError("case must be a mapping")
        selected_trial = trial if trial_index is None else trial_index
        return self._run_trial(case, case_id=_case_id(case, 0), trial_index=selected_trial)


# ---------------------------------------------------------------------------
# Functional entry points
# ---------------------------------------------------------------------------


def run_evaluation(
    cases: Any = None,
    classifier: Optional[Callable[..., Any]] = None,
    agent: Optional[Callable[..., Any]] = None,
    verifier: Optional[Callable[..., Any]] = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """Construct and run an :class:`EvaluationRunner` in one call."""

    return EvaluationRunner(
        cases=cases,
        classifier=classifier,
        agent=agent,
        verifier=verifier,
        **kwargs,
    ).run()


def evaluate_cases(
    cases: Any = None,
    classifier: Optional[Callable[..., Any]] = None,
    agent: Optional[Callable[..., Any]] = None,
    verifier: Optional[Callable[..., Any]] = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """Alias for :func:`run_evaluation`."""

    return run_evaluation(cases, classifier, agent, verifier, **kwargs)


# A short alias is convenient for callers that treat the runner as a
# function-oriented API.
run = run_evaluation


def to_json(result: Mapping[str, Any], *, indent: int = 2, sort_keys: bool = True) -> str:
    """Serialize an evaluation result as JSON without exposing credentials."""

    safe = redact_value(result)
    return json.dumps(_json_safe(safe), indent=indent, sort_keys=sort_keys, ensure_ascii=False)


def write_json(
    result: Any,
    path: Any,
    *,
    indent: int = 2,
    sort_keys: bool = True,
) -> Path:
    """Write a redacted evaluation result to a JSON file."""

    if isinstance(result, (str, Path)) and isinstance(path, Mapping):
        result, path = path, result
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(to_json(result, indent=indent, sort_keys=sort_keys) + "\n", encoding="utf-8")
    return destination
