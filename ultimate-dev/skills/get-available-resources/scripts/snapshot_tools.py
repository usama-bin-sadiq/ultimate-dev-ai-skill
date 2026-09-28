#!/usr/bin/env python3
"""Validate a resource snapshot, or diff two of them.

Two subcommands:

``validate``
    Check one snapshot against the schema ``1.1`` contract: the required fields,
    the field types, the allowed enum values, and — the part that actually
    catches problems — the distinction between null and zero. A null field means
    unavailable; a zero field means a source explicitly established zero. A
    snapshot that uses zero to mean unknown is wrong in a way that a reader will
    not notice and a planner will act on.

``diff``
    Compare two snapshots structurally, ignoring ``observed_at`` by default. The
    output is bounded, so a snapshot pair that differs in every field produces a
    truncated report rather than an unreadable one.

What a diff is for
------------------
A diff tells you that the effective capacity changed between two observations. It
does not tell you why, and it does not tell you whether the change matters: a
smaller affinity set because the job was requeued is a different situation from a
smaller one because something else is now running. Read the ``changed`` values
and decide.

Usage
-----
    python scripts/snapshot_tools.py validate resource-snapshot.json
    python scripts/snapshot_tools.py diff before.json after.json
    python scripts/snapshot_tools.py diff before.json after.json --include-volatile
    python scripts/snapshot_tools.py validate snap.json --format json --out report.json

Exit codes: 0 valid or diff produced, 1 findings or differences beyond the
tolerated set, 2 bad input.

Provenance
----------
Reconstructed to check the contract in ``references/snapshot_schema.md`` and to
offer the two invocations the SKILL.md documents. The validation rules, the
null-versus-zero checks, and the diff walk are this file's own.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

SCHEMA_VERSION = "1.1"
MAX_INPUT_BYTES = 1024 * 1024
MAX_DIFF_ENTRIES = 512
DIFF_TRUNCATION_NOTE = (
    f"diff truncated at {MAX_DIFF_ENTRIES} entries. Narrow the comparison with jq-style "
    "filtering, or diff specific subtrees, rather than raising the bound."
)

# Required top-level fields and their expected Python types. ``None`` in the
# type tuple means the key may legitimately be null.
TOP_LEVEL_TYPES: dict[str, tuple] = {
    "schema_version": (str,),
    "snapshot_kind": (str,),
    "observed_at": (str,),
    "completeness": (str,),
    "platform": (dict,),
    "privacy": (dict,),
    "cpu": (dict,),
    "memory": (dict,),
    "disk": (dict,),
    "accelerators": (dict,),
    "cgroup_v2": (dict,),
    "container": (dict,),
    "scheduler": (dict,),
    "warnings": (list,),
    "provenance": (list,),
}

COMPLETENESS_VALUES = {"complete", "complete_with_informational_notes", "partial"}
SNAPSHOT_KINDS = {"effective_resource_snapshot"}
SCOPES = {"root", "non_root", "unknown", "not_applicable"}
SEVERITIES = {"info", "warning", "error"}
PROVENANCE_STATUSES = {
    "ok", "unavailable", "absent", "skipped", "not_found", "timeout", "truncated",
    "error", "parse_error",
}
VENDORS = {"nvidia", "amd", "apple"}
BACKENDS = {"cuda", "rocm", "metal"}
MEMORY_MODELS = {"dedicated_or_hbm", "unified", "system_ram", "unknown"}

# Fields where zero is a real, sourced observation and null is "unknown". A zero
# here is meaningful: it says a source established that nothing is available.
ZERO_IS_MEANINGFUL = {
    ("accelerators", "runtime_usable_devices"),
    ("cgroup_v2", "scope_ordinal"),
}

# Keys that must never appear. Their presence is a privacy defect, not a schema
# detail, so it is checked as an error rather than a warning.
FORBIDDEN_KEYS = {
    "nodename", "job_id", "jobid", "slurm_job_id", "submit_host",
    "cgroup_path", "absolute_path", "working_path", "uuid", "device_uuid",
    "pci_address", "pci_bus_id", "environment", "env",
}
# Documented exceptions, by exact dotted path. "host" is a structural key in
# cpu.host and memory.host, and "hostname" is a required platform key whose value
# is null in every conforming snapshot. Blocking them would make every snapshot
# produced by the detector fail its own validator.
ALLOWED_EXACT = {
    "platform.hostname",
    "cpu.host",
    "cpu.host.logical",
    "cpu.host.physical",
    "memory.host",
    "memory.host.total_bytes",
    "memory.host.available_bytes",
    "memory.host.swap_total_bytes",
    "memory.host.swap_free_bytes",
}
# Keys whose *names* are allowed but whose values must be absent or redacted.
REDACTED_VALUES = {"redacted", "path_redacted", None}


def load_json(path: str) -> dict:
    """Read one regular, non-symlink JSON file, bounded in size."""
    if path.startswith(("http://", "https://")):
        raise SystemExit(f"error: {path} is a URL; this tool reads local files only")
    file_path = Path(path)
    if file_path.is_symlink():
        raise SystemExit(f"error: {path} is a symlink; refusing to read through it")
    if not file_path.is_file():
        raise SystemExit(f"error: not a file: {path}")
    if file_path.stat().st_size > MAX_INPUT_BYTES:
        raise SystemExit(
            f"error: {path} is larger than {MAX_INPUT_BYTES} bytes; it is not a snapshot"
        )
    try:
        with file_path.open(encoding="utf-8") as handle:
            data = json.load(handle)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"error: {path} is not valid JSON: {exc}")
    if not isinstance(data, dict):
        raise SystemExit(f"error: {path} must contain a JSON object")
    return data


def _type_name(value) -> str:
    return type(value).__name__


def _get(node, *path, default=None):
    for key in path:
        if not isinstance(node, dict) or key not in node:
            return default
        node = node[key]
    return node


def check_types(snapshot: dict, findings: list[dict]) -> None:
    for field, expected in TOP_LEVEL_TYPES.items():
        if field not in snapshot:
            findings.append({
                "code": "MISSING_FIELD", "field": field,
                "message": f"required top-level field {field!r} is absent",
            })
            continue
        value = snapshot[field]
        if not isinstance(value, expected):
            findings.append({
                "code": "WRONG_TYPE", "field": field,
                "message": f"expected {'/'.join(_type_name(t) for t in expected)}, "
                           f"got {_type_name(value)}",
            })


def check_enums(snapshot: dict, findings: list[dict]) -> None:
    if snapshot.get("schema_version") != SCHEMA_VERSION:
        findings.append({
            "code": "SCHEMA_VERSION", "field": "schema_version",
            "message": f"expected {SCHEMA_VERSION!r}, got {snapshot.get('schema_version')!r}",
        })
    if snapshot.get("snapshot_kind") not in SNAPSHOT_KINDS:
        findings.append({
            "code": "SNAPSHOT_KIND", "field": "snapshot_kind",
            "message": f"expected one of {sorted(SNAPSHOT_KINDS)}, "
                       f"got {snapshot.get('snapshot_kind')!r}",
        })
    if snapshot.get("completeness") not in COMPLETENESS_VALUES:
        findings.append({
            "code": "COMPLETENESS", "field": "completeness",
            "message": f"expected one of {sorted(COMPLETENESS_VALUES)}, "
                       f"got {snapshot.get('completeness')!r}",
        })
    scope = _get(snapshot, "cgroup_v2", "scope")
    if scope is not None and scope not in SCOPES:
        findings.append({
            "code": "CGROUP_SCOPE", "field": "cgroup_v2.scope",
            "message": f"expected one of {sorted(SCOPES)}, got {scope!r}",
        })
    for index, warning in enumerate(snapshot.get("warnings") or []):
        if not isinstance(warning, dict):
            findings.append({
                "code": "WARNING_SHAPE", "field": f"warnings[{index}]",
                "message": "each warning must be an object",
            })
            continue
        if warning.get("severity") not in SEVERITIES:
            findings.append({
                "code": "WARNING_SEVERITY", "field": f"warnings[{index}].severity",
                "message": f"expected one of {sorted(SEVERITIES)}, "
                           f"got {warning.get('severity')!r}",
            })
        for field in ("code", "component", "message"):
            if not isinstance(warning.get(field), str) or not warning.get(field):
                findings.append({
                    "code": "WARNING_FIELD", "field": f"warnings[{index}].{field}",
                    "message": f"{field} must be a non-empty string",
                })
    for index, record in enumerate(snapshot.get("provenance") or []):
        if not isinstance(record, dict):
            findings.append({
                "code": "PROVENANCE_SHAPE", "field": f"provenance[{index}]",
                "message": "each provenance record must be an object",
            })
            continue
        if record.get("status") not in PROVENANCE_STATUSES:
            findings.append({
                "code": "PROVENANCE_STATUS", "field": f"provenance[{index}].status",
                "message": f"expected one of {sorted(PROVENANCE_STATUSES)}, "
                           f"got {record.get('status')!r}",
            })


def check_null_versus_zero(snapshot: dict, findings: list[dict]) -> None:
    """The distinction the whole schema depends on.

    Null means unavailable. Zero means a source established zero. A snapshot that
    writes 0 where it means unknown will be read as a real measurement, and a
    planner that trusts it will size a run to zero.
    """
    capacity = _get(snapshot, "cpu", "effective", "capacity_cores")
    if capacity == 0:
        findings.append({
            "code": "ZERO_AS_UNKNOWN", "field": "cpu.effective.capacity_cores",
            "message": "0 means a source established zero CPU capacity. If the value is "
                       "unknown it must be null, not 0.",
        })
    hard_limit = _get(snapshot, "memory", "effective", "hard_limit_bytes")
    if hard_limit == 0:
        findings.append({
            "code": "ZERO_AS_UNKNOWN", "field": "memory.effective.hard_limit_bytes",
            "message": "0 means a source established a zero memory limit. Unknown must "
                       "be null.",
        })
    usable = _get(snapshot, "accelerators", "runtime_usable_devices")
    if usable == 0:
        findings.append({
            "code": "RUNTIME_USABLE_ZERO", "field": "accelerators.runtime_usable_devices",
            "message": "the detector loads no framework runtime, so this must be null. "
                       "0 would assert that zero devices are usable, which is a claim "
                       "about a runtime that was never loaded.",
        })
    writable = _get(snapshot, "disk", "writable")
    if writable is not None and not isinstance(writable, bool):
        findings.append({
            "code": "WRONG_TYPE", "field": "disk.writable",
            "message": f"expected bool, got {_type_name(writable)}",
        })
    # A negative capacity or limit is not a measurement.
    for field, value in (("cpu.effective.capacity_cores", capacity),
                         ("memory.effective.hard_limit_bytes", hard_limit)):
        if isinstance(value, (int, float)) and value < 0:
            findings.append({
                "code": "NEGATIVE_CAPACITY", "field": field,
                "message": f"{value} is negative; a capacity cannot be negative. If none "
                           "was observed, the value must be null.",
            })


def check_accelerators(snapshot: dict, findings: list[dict]) -> None:
    accelerators = snapshot.get("accelerators")
    if not isinstance(accelerators, dict):
        return
    for index, device in enumerate(accelerators.get("devices") or []):
        if not isinstance(device, dict):
            findings.append({
                "code": "DEVICE_SHAPE", "field": f"accelerators.devices[{index}]",
                "message": "each device must be an object",
            })
            continue
        if device.get("vendor") not in VENDORS:
            findings.append({
                "code": "DEVICE_VENDOR", "field": f"accelerators.devices[{index}].vendor",
                "message": f"expected one of {sorted(VENDORS)}, got {device.get('vendor')!r}",
            })
        if device.get("backend_candidate") not in BACKENDS:
            findings.append({
                "code": "DEVICE_BACKEND",
                "field": f"accelerators.devices[{index}].backend_candidate",
                "message": f"expected one of {sorted(BACKENDS)}, "
                           f"got {device.get('backend_candidate')!r}",
            })
        if device.get("memory_model") not in MEMORY_MODELS:
            findings.append({
                "code": "DEVICE_MEMORY_MODEL",
                "field": f"accelerators.devices[{index}].memory_model",
                "message": f"expected one of {sorted(MEMORY_MODELS)}, "
                           f"got {device.get('memory_model')!r}",
            })
        if device.get("runtime_compatibility") != "not_tested":
            findings.append({
                "code": "RUNTIME_CLAIM",
                "field": f"accelerators.devices[{index}].runtime_compatibility",
                "message": "the detector loads no framework runtime, so this must be "
                           "'not_tested'. Any other value is an unsupported usability claim.",
            })
        for key in ("uuid", "pci_address", "serial", "name"):
            if key in device and device[key] not in REDACTED_VALUES:
                findings.append({
                    "code": "DEVICE_IDENTIFIER", "field": f"accelerators.devices[{index}].{key}",
                    "message": f"{key} must be absent or redacted; device identifiers are "
                               "not emitted",
                })


def check_privacy(snapshot: dict, findings: list[dict]) -> None:
    privacy = snapshot.get("privacy")
    if not isinstance(privacy, dict):
        findings.append({"code": "PRIVACY_BLOCK", "field": "privacy",
                         "message": "the privacy block is missing"})
        return
    for flag in ("hostname_emitted", "absolute_paths_emitted", "cgroup_paths_emitted",
                 "job_ids_emitted", "device_uuids_emitted", "pci_addresses_emitted",
                 "environment_dumped", "stress_test_performed", "write_probe_performed"):
        if privacy.get(flag) is not False:
            findings.append({
                "code": "PRIVACY_FLAG", "field": f"privacy.{flag}",
                "message": f"{flag} must be false; the contract forbids "
                           f"{flag.replace('_emitted', '').replace('_performed', '').replace('_dumped', '')}",
            })


def scan_forbidden_keys(node, path: str, findings: list[dict], depth: int = 0) -> None:
    """Walk the whole snapshot for keys the privacy contract forbids.

    ``host`` and ``hostname`` need the documented-exception list: the schema uses
    them as structural keys, and blocking the bare word would reject every
    snapshot the detector produces. Anything else on the forbidden list is a
    real leak.
    """
    if depth > 12:
        findings.append({"code": "NESTING", "field": path, "message": "nesting is too deep"})
        return
    if isinstance(node, dict):
        for key, value in node.items():
            lowered = str(key).lower()
            child = f"{path}.{key}" if path not in {"$", ""} else str(key)
            if lowered in FORBIDDEN_KEYS and child not in ALLOWED_EXACT:
                findings.append({
                    "code": "PRIVACY_LEAK", "field": child,
                    "message": f"{key!r} is not emitted; it can carry a hostname, a path, "
                               "a job ID, or a device identifier",
                })
            scan_forbidden_keys(value, child, findings, depth + 1)
    elif isinstance(node, list):
        for index, value in enumerate(node[:200]):
            scan_forbidden_keys(value, f"{path}[{index}]", findings, depth + 1)


def validate(snapshot: dict) -> list[dict]:
    findings: list[dict] = []
    check_types(snapshot, findings)
    check_enums(snapshot, findings)
    check_null_versus_zero(snapshot, findings)
    check_accelerators(snapshot, findings)
    check_privacy(snapshot, findings)
    scan_forbidden_keys(snapshot, "$", findings)
    return findings


# -------------------------------------------------------------------- diff --


def flatten(node, prefix: str = "") -> dict:
    """Flatten to dotted paths with leaf values, for a bounded structural diff."""
    flat: dict = {}
    if isinstance(node, dict):
        if not node:
            flat[prefix] = {}
        for key in sorted(node, key=str):
            flat.update(flatten(node[key], f"{prefix}.{key}" if prefix else str(key)))
    elif isinstance(node, list):
        if not node:
            flat[prefix] = []
        for index, value in enumerate(node):
            flat.update(flatten(value, f"{prefix}[{index}]"))
    else:
        flat[prefix] = node
    return flat


VOLATILE_PATHS = ("observed_at",)


def diff(before: dict, after: dict, include_volatile: bool) -> dict:
    """Structural diff, bounded, with the volatile timestamp excluded by default."""
    left = flatten(before)
    right = flatten(after)

    if not include_volatile:
        left = {k: v for k, v in left.items() if k not in VOLATILE_PATHS}
        right = {k: v for k, v in right.items() if k not in VOLATILE_PATHS}

    keys = sorted(set(left) | set(right))
    changes: list[dict] = []
    truncated = False
    for key in keys:
        if key in left and key not in right:
            change = {"path": key, "change": "removed", "before": left[key], "after": None}
        elif key not in left and key in right:
            change = {"path": key, "change": "added", "before": None, "after": right[key]}
        elif left[key] != right[key]:
            change = {"path": key, "change": "changed", "before": left[key], "after": right[key]}
        else:
            continue
        if len(changes) >= MAX_DIFF_ENTRIES:
            truncated = True
            break
        changes.append(change)

    return {
        "changed_count": len(changes),
        "truncated": truncated,
        "truncation_note": DIFF_TRUNCATION_NOTE if truncated else None,
        "volatile_excluded": not include_volatile,
        "changes": changes,
        "interpretation": (
            "A diff says the effective resource state changed between two observations. "
            "It does not say why, and it does not say whether the change matters. A smaller "
            "affinity set because the job was requeued is a different situation from a "
            "smaller one because something else is now running. Read the values and decide."
        ),
    }


# ------------------------------------------------------------------ output --


def render_findings(findings: list[dict], path: str) -> str:
    lines = [f"snapshot: {path}", f"errors: {len(findings)}", ""]
    for finding in findings:
        lines.append(f"error: {finding['field']}: [{finding['code']}] {finding['message']}")
    if not findings:
        lines.append("The snapshot matches the schema 1.1 contract.")
    lines += [
        "",
        "Validating a snapshot checks its shape and its internal honesty. It does not "
        "establish that the resources it describes are actually available, that the "
        "probes ran, or that the numbers are correct.",
    ]
    return "\n".join(lines) + "\n"


def render_diff(result: dict, before_path: str, after_path: str) -> str:
    lines = [
        f"before: {before_path}",
        f"after:  {after_path}",
        f"volatile fields {'included' if not result['volatile_excluded'] else 'excluded'}",
        f"changes: {result['changed_count']}",
        "",
    ]
    if result["truncated"]:
        lines += [f"warning: {result['truncation_note']}", ""]
    for change in result["changes"]:
        lines.append(f"{change['change']:<8} {change['path']}")
        lines.append(f"         before: {_short(change['before'])}")
        lines.append(f"          after: {_short(change['after'])}")
    if not result["changes"]:
        lines.append("No structural differences.")
    lines += ["", result["interpretation"]]
    return "\n".join(lines) + "\n"


def _short(value) -> str:
    text = repr(value)
    return text if len(text) <= 100 else text[:97] + "..."


def write_report(payload: str, filename: str, force: bool) -> None:
    if os.path.sep in filename or (os.altsep and os.altsep in filename) or not filename.endswith(".json"):
        raise SystemExit("error: --out must be a bare .json filename in the current directory")
    target = Path.cwd() / filename
    if target.is_symlink():
        raise SystemExit(f"error: {filename} is a symlink; refusing to write through it")
    if target.exists() and not force:
        raise SystemExit(f"error: {filename} already exists; pass --force to overwrite it")
    descriptor = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
        handle.write(payload + "\n")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate a resource snapshot, or diff two of them.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    sub = parser.add_subparsers(dest="command", required=True)

    validate_parser = sub.add_parser("validate", help="check one snapshot against schema 1.1")
    validate_parser.add_argument("snapshot", help="resource-snapshot.json")
    validate_parser.add_argument("--format", choices=("text", "json"), default="text")
    validate_parser.add_argument("--out", default=None, help="write the report to this .json file")
    validate_parser.add_argument("--force", action="store_true")

    diff_parser = sub.add_parser("diff", help="compare two snapshots structurally")
    diff_parser.add_argument("before", help="the earlier snapshot")
    diff_parser.add_argument("after", help="the later snapshot")
    diff_parser.add_argument("--include-volatile", action="store_true",
                             help="include observed_at, which otherwise changes every run")
    diff_parser.add_argument("--format", choices=("text", "json"), default="text")
    diff_parser.add_argument("--out", default=None, help="write the report to this .json file")
    diff_parser.add_argument("--force", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.command == "validate":
        snapshot = load_json(args.snapshot)
        findings = validate(snapshot)
        if args.format == "json":
            payload = json.dumps(
                {
                    "snapshot": args.snapshot,
                    "schema_version": SCHEMA_VERSION,
                    "errors": len(findings),
                    "findings": findings,
                    "establishes_resource_availability": False,
                },
                indent=2,
            ) + "\n"
        else:
            payload = render_findings(findings, args.snapshot)
        if args.out:
            try:
                write_report(payload, args.out, args.force)
            except SystemExit as exc:
                print(str(exc), file=sys.stderr)
                return 2
            log(f"wrote {args.out}")
        else:
            print(payload, end="")
        return 1 if findings else 0

    before = load_json(args.before)
    after = load_json(args.after)
    result = diff(before, after, args.include_volatile)

    if args.format == "json":
        payload = json.dumps(
            {"before": args.before, "after": args.after, **result}, indent=2
        ) + "\n"
    else:
        payload = render_diff(result, args.before, args.after)
    if args.out:
        try:
            write_report(payload, args.out, args.force)
        except SystemExit as exc:
            print(str(exc), file=sys.stderr)
            return 2
        log(f"wrote {args.out}")
    else:
        print(payload, end="")
    return 0 if not result["truncated"] else 1


if __name__ == "__main__":
    sys.exit(main())
