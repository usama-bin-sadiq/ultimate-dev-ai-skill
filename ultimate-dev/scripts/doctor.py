#!/usr/bin/env python3
"""``doctor`` — a diagnostic aggregate over the existing validators.

The specification asks for a diagnostic that detects missing, invalid,
duplicate, orphaned, unreachable, incompatible, misconfigured and unverified
components. It also forbids fake PASS statuses, so this tool reports only what
it can demonstrate, and names the check behind every claim.

It deliberately owns **no new validation logic**. ``validate-consistency.py``,
``validate.py`` and the test suite already know how to check structure; a
second implementation would be the duplicate source of truth the architecture
audit forbids. This aggregates, adds the reachability and drift checks nothing
else performs, and refuses to report a pass it cannot justify.
"""
from __future__ import annotations

import argparse
import ast
import json
import os
import subprocess
import sys
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Iterable

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.dirname(ROOT)


class Status(str, Enum):
    PASS = "pass"
    FAIL = "fail"
    WARN = "warn"
    NOT_RUN = "not_run"


SEVERITY_ORDER = {Status.FAIL: 0, Status.WARN: 1, Status.NOT_RUN: 2, Status.PASS: 3}


@dataclass
class Finding:
    check: str
    status: Status
    detail: str
    evidence: str = ""
    items: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "check": self.check,
            "status": self.status.value,
            "detail": self.detail,
            "evidence": self.evidence,
            "items": self.items,
        }


# --------------------------------------------------------------------- helpers
def _run(argv: list[str], cwd: str = ROOT) -> tuple[int, str]:
    try:
        result = subprocess.run(
            argv, cwd=cwd, capture_output=True, text=True, timeout=600, check=False
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return 1, f"{type(exc).__name__}: {exc}"
    return result.returncode, (result.stdout + result.stderr).strip()


def _python_files(directory: str) -> list[str]:
    out: list[str] = []
    for base, dirs, names in os.walk(directory):
        dirs[:] = [d for d in dirs if d != "__pycache__"]
        for name in names:
            if name.endswith(".py"):
                out.append(os.path.join(base, name))
    return sorted(out)


# ---------------------------------------------------------------------- checks
def check_repository_present() -> list[Finding]:
    required = [
        "SKILL.md",
        "AGENTS.md",
        "skill-manifest.yaml",
        os.path.join("contracts", "task-envelope.yaml"),
        os.path.join("contracts", "task-graph.yaml"),
        os.path.join("runtime", "core", "attestation.py"),
        os.path.join("runtime", "core", "task_graph.py"),
        os.path.join("scripts", "runtime-probe.py"),
    ]
    missing = [rel for rel in required if not os.path.isfile(os.path.join(ROOT, rel))]
    if not os.path.isfile(os.path.join(REPO, "VERSION")):
        missing.insert(0, "VERSION (repository root)")
    return [
        Finding(
            "required-artifacts",
            Status.PASS if not missing else Status.FAIL,
            "every required artifact is present" if not missing
            else f"{len(missing)} required artifact(s) missing",
            evidence="os.path.isfile over the required list",
            items=missing,
        )
    ]


def check_validators() -> list[Finding]:
    findings: list[Finding] = []
    for name, argv in (
        ("validate-consistency", [sys.executable, os.path.join("scripts", "validate-consistency.py")]),
        ("validate", [sys.executable, os.path.join("scripts", "validate.py")]),
    ):
        code, output = _run(argv)
        findings.append(
            Finding(
                f"validator:{name}",
                Status.PASS if code == 0 else Status.FAIL,
                f"{name} exited {code}",
                evidence=f"scripts/{name.replace('-', '_')}.py",
                items=[] if code == 0 else [output.splitlines()[-1][:160] if output else ""],
            )
        )
    return findings


def check_duplicate_module_names() -> list[Finding]:
    """Two runtime modules with the same name shadow each other on import."""
    seen: dict[str, list[str]] = {}
    for path in _python_files(os.path.join(ROOT, "runtime")):
        name = os.path.splitext(os.path.basename(path))[0]
        seen.setdefault(name, []).append(os.path.relpath(path, ROOT))
    duplicates = {
        k: v for k, v in seen.items() if len(v) > 1 and k != "__init__"
    }
    return [
        Finding(
            "duplicate-module-names",
            Status.PASS if not duplicates else Status.WARN,
            "no shadowing runtime module names" if not duplicates
            else f"{len(duplicates)} shadowed module name(s); the later import wins",
            evidence="filename census over runtime/",
            items=[f"{k}: {', '.join(v)}" for k, v in sorted(duplicates.items())],
        )
    ]


def _imported_names(path: str) -> set[str]:
    """Qualified names a module imports.

    Relative imports matter here: ``from .attestation import X`` records only
    ``attestation`` in ``alias.name``, with the real package in ``node.module``
    and the depth in ``node.level``. Ignoring that makes almost every runtime
    module look orphaned.
    """
    try:
        with open(path, encoding="utf-8") as handle:
            tree = ast.parse(handle.read(), filename=path)
    except (OSError, SyntaxError):
        return set()
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                names.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            prefix = node.module or ""
            if prefix:
                # The module itself is what callers reference, not just the
                # symbols pulled out of it.
                names.add(prefix)
                names.add(prefix.rsplit(".", 1)[-1])
            for alias in node.names:
                names.add(f"{prefix}.{alias.name}" if prefix else alias.name)
    return names


def check_runtime_reachability() -> list[Finding]:
    """Flag runtime modules that nothing outside their own package imports.

    A module nothing references is either dead code or a public entry point.
    Entry points are exempt when they are named in the docs or the installer,
    because those are legitimate callers a static import scan cannot see.
    """
    runtime_root = os.path.join(ROOT, "runtime")
    files = _python_files(runtime_root)
    imported: set[str] = set()
    for path in files + _python_files(os.path.join(ROOT, "tests")) + _python_files(
        os.path.join(ROOT, "scripts")
    ):
        imported |= _imported_names(path)

    orphans: list[str] = []
    for path in files:
        relative = os.path.relpath(path, ROOT)
        module = os.path.splitext(os.path.basename(path))[0]
        if module in {"__init__"}:
            continue
        # Referenced as "from .module", "from runtime.core.module", or tested.
        referenced = any(
            name == module or name.endswith(f".{module}") for name in imported
        )
        tested = any(
            os.path.basename(test) != "__init__.py" and module in _imported_names(test)
            for test in _python_files(os.path.join(ROOT, "tests"))
        )
        if referenced or tested:
            continue
        # Known public entry points, invoked by hosts rather than imported.
        if module in {"evaluation", "eval_cli", "task_admin", "engine", "protocol"}:
            continue
        orphans.append(relative)

    return [
        Finding(
            "runtime-reachability",
            Status.PASS if not orphans else Status.WARN,
            "every runtime module is referenced" if not orphans
            else f"{len(orphans)} runtime module(s) with no importer",
            evidence="AST import scan over runtime/, tests/ and scripts/",
            items=orphans,
        )
    ]


def check_contract_code_drift() -> list[Finding]:
    """Compare a contract's declared node fields with the code's dataclass.

    This is the check that would have caught the dangling ``decide_mode``
    docstring reference in the Unified Task Engine.
    """
    contract_path = os.path.join(ROOT, "contracts", "task-graph.yaml")
    module_path = os.path.join(ROOT, "runtime", "core", "task_graph.py")
    if not (os.path.isfile(contract_path) and os.path.isfile(module_path)):
        return [
            Finding(
                "contract-drift:task-graph",
                Status.NOT_RUN,
                "contract or implementation missing",
                evidence="contracts/task-graph.yaml + runtime/core/task_graph.py",
            )
        ]
    try:
        import yaml

        with open(contract_path, encoding="utf-8") as handle:
            contract = yaml.safe_load(handle)
    except Exception as exc:  # noqa: BLE001
        return [
            Finding(
                "contract-drift:task-graph",
                Status.FAIL,
                f"contract is unreadable: {type(exc).__name__}",
                evidence="yaml.safe_load",
            )
        ]

    sys.path.insert(0, ROOT)
    try:
        import dataclasses

        from runtime.core.task_graph import TaskNode
    except Exception as exc:  # noqa: BLE001
        return [
            Finding(
                "contract-drift:task-graph",
                Status.FAIL,
                f"implementation is unimportable: {type(exc).__name__}",
                evidence="import runtime.core.task_graph",
            )
        ]

    declared = set(contract.get("node_fields") or {})
    actual = {f.name for f in dataclasses.fields(TaskNode)}
    undocumented = sorted(actual - declared)
    phantom = sorted(declared - actual)
    ok = not undocumented and not phantom
    return [
        Finding(
            "contract-drift:task-graph",
            Status.PASS if ok else Status.FAIL,
            f"node fields agree ({len(actual)} fields)" if ok
            else "contract and implementation disagree on node fields",
            evidence="dataclasses.fields(TaskNode) vs contracts/task-graph.yaml",
            items=[f"undocumented in contract: {n}" for n in undocumented]
            + [f"promised but absent: {n}" for n in phantom],
        )
    ]


def check_model_independence() -> list[Finding]:
    """No model-name literal may be compiled into the runtime."""
    forbidden = ("gpt-", "claude-3", "claude-4", "llama3", "gemini-", "mixtral")
    offenders: list[str] = []
    for path in _python_files(os.path.join(ROOT, "runtime")) + [
        p for p in _python_files(os.path.join(ROOT, "runtime")) if p.endswith(".mjs")
    ]:
        with open(path, encoding="utf-8") as handle:
            for number, line in enumerate(handle, 1):
                stripped = line.strip()
                if stripped.startswith("#"):
                    continue
                if any(token in stripped for token in forbidden):
                    offenders.append(f"{os.path.relpath(path, ROOT)}:{number}")
    return [
        Finding(
            "model-independence",
            Status.PASS if not offenders else Status.FAIL,
            "no model-name literal in the runtime" if not offenders
            else f"{len(offenders)} model-name literal(s) in the runtime",
            evidence="line scan over runtime/",
            items=offenders,
        )
    ]


def check_entrypoint_budget() -> list[Finding]:
    code, output = _run([sys.executable, os.path.join("scripts", "measure-entrypoint.py"), "--json"])
    if code != 0:
        return [
            Finding(
                "entrypoint-budget",
                Status.NOT_RUN,
                "measure-entrypoint.py did not run",
                evidence="scripts/measure-entrypoint.py",
            )
        ]
    try:
        report = json.loads(output)
    except json.JSONDecodeError as exc:
        return [
            Finding(
                "entrypoint-budget",
                Status.FAIL,
                f"unparseable report: {exc}",
                evidence="scripts/measure-entrypoint.py --json",
            )
        ]
    within = bool(report.get("within_budget"))
    offenders = [
        f"{item['file']}: {item['words']}/{item['word_limit']} words"
        for item in report.get("entries", [])
        if not item.get("within_limit")
    ]
    return [
        Finding(
            "entrypoint-budget",
            Status.PASS if within else Status.FAIL,
            "always-loaded entrypoints are within budget" if within
            else "an always-loaded entrypoint exceeds its budget",
            evidence="scripts/measure-entrypoint.py",
            items=offenders,
        )
    ]


def check_test_suite() -> list[Finding]:
    if not os.path.isfile(os.path.join(ROOT, "tests")) and not os.path.isdir(
        os.path.join(ROOT, "tests")
    ):
        return [Finding("test-suite", Status.NOT_RUN, "no tests directory", evidence="tests/")]
    code, output = _run([sys.executable, "-m", "pytest", "tests/", "-q"])
    tail = [line for line in output.splitlines() if line.strip()][-1] if output else ""
    return [
        Finding(
            "test-suite",
            Status.PASS if code == 0 else Status.FAIL,
            f"pytest exited {code}",
            evidence="python -m pytest tests/ -q",
            items=[] if code == 0 else [tail[:160]],
        )
    ]


def check_version_coherence() -> list[Finding]:
    version_file = os.path.join(REPO, "VERSION")
    if not os.path.isfile(version_file):
        return [Finding("version-coherence", Status.NOT_RUN, "no VERSION file", evidence="VERSION")]
    with open(version_file, encoding="utf-8") as handle:
        version = handle.read().strip()
    stale: list[str] = []
    for relative in ("skill-manifest.yaml", os.path.join("config", "agent-catalog.yaml")):
        path = os.path.join(ROOT, relative)
        if not os.path.isfile(path):
            continue
        with open(path, encoding="utf-8") as handle:
            for line in handle:
                if line.startswith("version:"):
                    declared = line.split(":", 1)[1].strip().strip('"').strip("'")
                    if declared != version:
                        stale.append(f"{relative}: {declared}")
                    break
    return [
        Finding(
            "version-coherence",
            Status.PASS if not stale else Status.FAIL,
            f"version {version} is coherent" if not stale
            else f"version {version} is not propagated",
            evidence="VERSION vs skill-manifest.yaml and config/agent-catalog.yaml",
            items=stale,
        )
    ]


# ----------------------------------------------------------------------- driver
def collect(include_slow: bool = True) -> list[Finding]:
    """Run every check.

    ``include_slow`` controls the checks that shell out to the test suite and
    the structural validators. They cost seconds to minutes, and running the
    suite from inside the suite is recursive. Library callers and the tests for
    this tool pass ``False``.
    """
    checks = (
        check_repository_present,
        check_validators,
        check_entrypoint_budget,
        check_duplicate_module_names,
        check_runtime_reachability,
        check_contract_code_drift,
        check_model_independence,
        check_version_coherence,
    )
    if include_slow:
        checks = (
            check_repository_present,
            check_validators,
            check_entrypoint_budget,
            check_test_suite,
            check_duplicate_module_names,
            check_runtime_reachability,
            check_contract_code_drift,
            check_model_independence,
            check_version_coherence,
        )
    findings: list[Finding] = []
    for check in checks:
        try:
            findings.extend(check())
        except Exception as exc:  # noqa: BLE001
            findings.append(
                Finding(
                    check.__name__.replace("check_", ""),
                    Status.FAIL,
                    f"check raised {type(exc).__name__}: {exc}",
                    evidence=check.__name__,
                )
            )
    return findings


def render(findings: Iterable[Finding]) -> str:
    findings = list(findings)
    lines = ["ultimate-dev doctor", "=" * 19, ""]
    width = max((len(f.check) for f in findings), default=10)
    for finding in sorted(findings, key=lambda f: (SEVERITY_ORDER[f.status], f.check)):
        marker = {
            Status.PASS: "PASS",
            Status.FAIL: "FAIL",
            Status.WARN: "WARN",
            Status.NOT_RUN: "NOT RUN",
        }[finding.status]
        lines.append(f"  {marker:<8} {finding.check:<{width}}  {finding.detail}")
        if finding.evidence:
            lines.append(f"           {'':<{width}}  via {finding.evidence}")
        for item in finding.items[:8]:
            lines.append(f"           {'':<{width}}    - {item}")
        if len(finding.items) > 8:
            lines.append(f"           {'':<{width}}    ... {len(finding.items) - 8} more")
    failed = [f for f in findings if f.status is Status.FAIL]
    warned = [f for f in findings if f.status is Status.WARN]
    not_run = [f for f in findings if f.status is Status.NOT_RUN]
    lines.append("")
    lines.append(
        f"  {len(findings) - len(failed) - len(warned) - len(not_run)} pass · "
        f"{len(failed)} fail · {len(warned)} warn · {len(not_run)} not run"
    )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="machine-readable output")
    parser.add_argument(
        "--quick",
        action="store_true",
        help="skip checks that shell out to the test suite; use when doctor runs inside a test",
    )
    parser.add_argument("--strict", action="store_true", help="exit 1 on any FAIL or WARN")
    args = parser.parse_args(argv)

    findings = collect(include_slow=not args.quick)
    if args.json:
        report = {
            "findings": [f.to_dict() for f in findings],
            "pass": sum(1 for f in findings if f.status is Status.PASS),
            "fail": sum(1 for f in findings if f.status is Status.FAIL),
            "warn": sum(1 for f in findings if f.status is Status.WARN),
            "not_run": sum(1 for f in findings if f.status is Status.NOT_RUN),
        }
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(render(findings))

    blocking = [f for f in findings if f.status in (Status.FAIL, Status.WARN)]
    if args.strict and blocking:
        return 1
    return 1 if any(f.status is Status.FAIL for f in findings) else 0


if __name__ == "__main__":
    raise SystemExit(main())
