#!/usr/bin/env python3
"""Grade eval assertions against a run's output and artifacts.

This is the executable half of the expectations contract. SKILL.md defines what
an expectation is; this module decides whether it held. Objective assertions
are checked here deterministically, so a run's pass rate does not depend on a
judge being available or on a judge's mood.

Supported assertion types:

======================  ===============================================
``file_exists``         path exists and is a file
``file_absent``         path does not exist
``file_contains``       file contains a literal string
``json_valid``          file is valid JSON, optionally with required keys
``frontmatter_valid``   a skill directory passes quick_validate
``command_succeeds``    a command exits 0 in the run directory
``output_contains``     the run output contains a literal string
``output_matches``      the run output matches a regular expression
``no_placeholder``      none of the given markers remain in output or files
``manual``              cannot be decided mechanically; deferred to review
======================  ===============================================

``manual`` assertions are reported with ``passed: null``. They are never
counted as a pass, and the summary reports them separately, so a subjective
check can never quietly inflate a score.

Assertion shape:

    {"type": "file_contains", "path": "report.md", "value": "## Summary"}

Usage:
    python scripts/grade.py --assertions assertions.json --output-dir runs/1
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

if __package__ in (None, ""):  # allow `python scripts/grade.py`
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.quick_validate import validate_skill  # noqa: E402
from scripts.utils import VALID_ASSERTION_TYPES, read_json  # noqa: E402

# Files that are never sensible to treat as run output.
_TEXT_SUFFIXES = {
    ".md", ".txt", ".json", ".jsonl", ".yaml", ".yml", ".py", ".js", ".ts",
    ".tsx", ".jsx", ".html", ".css", ".sh", ".toml", ".cfg", ".ini", ".csv",
    ".xml", ".sql", ".rs", ".go", ".rb", ".java", ".kt", ".c", ".h", ".cpp",
    ".env", ".gitignore",
}
_SCAN_FILE_LIMIT = 200


def _text_files(base: Path) -> list[Path]:
    """Text files under ``base`` that assertions may search."""
    found: list[Path] = []
    for path in sorted(base.rglob("*")):
        if len(found) >= _SCAN_FILE_LIMIT:
            break
        if not path.is_file():
            continue
        if "__pycache__" in path.parts or ".git" in path.parts:
            continue
        if path.suffix.lower() in _TEXT_SUFFIXES or path.name.startswith("."):
            found.append(path)
    return found


def _combined_output(stdout: str, stderr: str, base: Path) -> str:
    """Everything an output assertion may legitimately search."""
    parts = [stdout or "", stderr or ""]
    for path in _text_files(base):
        try:
            parts.append(path.read_text(encoding="utf-8", errors="replace"))
        except OSError:
            continue
    return "\n".join(parts)


def _expectation(
    assertion: dict, passed: bool | None, evidence: str, text: str | None = None
) -> dict:
    return {
        "text": text or assertion.get("value") or assertion.get("text")
        or f"{assertion.get('type')} {assertion.get('path', '')}".strip(),
        "type": assertion.get("type"),
        "passed": passed,
        "evidence": evidence,
        "manual": assertion.get("type") == "manual",
    }


def grade_assertion(
    assertion: dict,
    *,
    base: Path,
    stdout: str = "",
    stderr: str = "",
    exit_code: int | None = None,
    combined: str | None = None,
) -> dict:
    """Evaluate one assertion. Returns an expectation record."""
    kind = assertion.get("type")
    if kind not in VALID_ASSERTION_TYPES:
        return _expectation(
            assertion,
            False,
            f"unknown assertion type {kind!r}; expected one of "
            f"{', '.join(sorted(VALID_ASSERTION_TYPES))}",
            text=assertion.get("text") or f"assertion type {kind!r} is valid",
        )

    def target(key: str = "path") -> Path:
        raw = assertion.get(key, ".")
        path = Path(str(raw))
        return path if path.is_absolute() else base / path

    if kind == "manual":
        return _expectation(
            assertion,
            None,
            "requires human or agent review; not decided mechanically",
        )

    if kind == "file_exists":
        path = target()
        ok = path.is_file()
        return _expectation(
            assertion, ok,
            f"{'found' if ok else 'missing'}: {path}",
            text=f"file exists: {assertion.get('path')}",
        )

    if kind == "file_absent":
        path = target()
        ok = not path.exists()
        return _expectation(
            assertion, ok,
            f"{'unexpectedly present' if not ok else 'absent as expected'}: {path}",
            text=f"file absent: {assertion.get('path')}",
        )

    if kind == "file_contains":
        path = target()
        value = str(assertion.get("value", ""))
        ignore_case = bool(assertion.get("ignore_case", True))
        if not path.is_file():
            return _expectation(
                assertion, False, f"file missing: {path}",
                text=f"{path.name} contains {value!r}",
            )
        body = path.read_text(encoding="utf-8", errors="replace")
        ok = value.lower() in body.lower() if ignore_case else value in body
        return _expectation(
            assertion, ok,
            f"{'contains' if ok else 'does not contain'} {value!r} in {path}",
            text=f"{assertion.get('path')} contains {value!r}",
        )

    if kind == "json_valid":
        path = target()
        required = assertion.get("required_keys") or []
        if not path.is_file():
            return _expectation(
                assertion, False, f"file missing: {path}",
                text=f"{path.name} is valid JSON",
            )
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            return _expectation(
                assertion, False, f"invalid JSON in {path}: {exc}",
                text=f"{path.name} is valid JSON",
            )
        missing = [k for k in required if k not in data] if isinstance(data, dict) else []
        ok = not missing
        return _expectation(
            assertion, ok,
            "valid JSON" if ok else f"valid JSON, but missing keys: {missing}",
            text=f"{path.name} is valid JSON"
            + (f" with keys {', '.join(required)}" if required else ""),
        )

    if kind == "frontmatter_valid":
        path = target()
        result = validate_skill(path)
        return _expectation(
            assertion,
            result.ok,
            result.message(),
            text=f"{path.name} has valid skill frontmatter",
        )

    if kind == "command_succeeds":
        command = str(assertion.get("command", "")).strip()
        if not command:
            return _expectation(
                assertion, False, "no 'command' supplied",
                text="command exits 0",
            )
        try:
            proc = subprocess.run(
                command, shell=True, cwd=base, capture_output=True,
                text=True, timeout=int(assertion.get("timeout", 300)),
            )
        except subprocess.TimeoutExpired:
            return _expectation(
                assertion, False, f"command timed out: {command}",
                text=f"`{command}` exits 0",
            )
        except Exception as exc:  # noqa: BLE001
            return _expectation(
                assertion, False, f"command failed to run: {exc}",
                text=f"`{command}` exits 0",
            )
        ok = proc.returncode == 0
        detail = (proc.stderr or proc.stdout or "").strip().splitlines()
        return _expectation(
            assertion, ok,
            f"exit {proc.returncode}" + (f": {detail[-1][:200]}" if detail and not ok else ""),
            text=f"`{command}` exits 0",
        )

    haystack = combined if combined is not None else _combined_output(stdout, stderr, base)

    if kind == "output_contains":
        value = str(assertion.get("value", ""))
        ignore_case = bool(assertion.get("ignore_case", True))
        ok = value.lower() in haystack.lower() if ignore_case else value in haystack
        return _expectation(
            assertion, ok,
            f"{'found' if ok else 'not found'} in run output: {value!r}",
            text=f"output contains {value!r}",
        )

    if kind == "output_matches":
        pattern = str(assertion.get("pattern") or assertion.get("value", ""))
        try:
            ok = re.search(pattern, haystack, re.MULTILINE) is not None
        except re.error as exc:
            return _expectation(
                assertion, False, f"invalid regular expression {pattern!r}: {exc}",
                text=f"output matches {pattern!r}",
            )
        return _expectation(
            assertion, ok,
            f"{'matched' if ok else 'did not match'}: {pattern!r}",
            text=f"output matches {pattern!r}",
        )

    if kind == "no_placeholder":
        markers = assertion.get("values") or []
        if isinstance(markers, str):
            markers = [markers]
        found = [m for m in markers if m and str(m) in haystack]
        return _expectation(
            assertion, not found,
            "no placeholder markers remain" if not found
            else f"placeholder markers still present: {found}",
            text=f"output contains none of: {', '.join(map(str, markers))}",
        )

    return _expectation(assertion, False, f"unhandled assertion type {kind!r}")


def grade_run(
    assertions: list[dict],
    *,
    base: Path,
    stdout: str = "",
    stderr: str = "",
    exit_code: int | None = None,
) -> dict:
    """Grade every assertion for one run and summarize the outcome."""
    base = Path(base)
    combined = _combined_output(stdout, stderr, base) if assertions else ""
    expectations = [
        grade_assertion(
            a, base=base, stdout=stdout, stderr=stderr,
            exit_code=exit_code, combined=combined,
        )
        for a in assertions
    ]

    decided = [e for e in expectations if e["passed"] is not None]
    manual = [e for e in expectations if e["passed"] is None]
    passed = sum(1 for e in decided if e["passed"])
    total = len(decided)
    pass_rate = (passed / total) if total else None

    return {
        "expectations": expectations,
        "summary": {
            "passed": passed,
            "failed": total - passed,
            "total": total,
            "manual": len(manual),
            # None when no assertion was decided mechanically, so a score is
            # never reported as 0.0 for "nothing was checked".
            "pass_rate": pass_rate,
        },
    }


def grade_many(runs: list[dict], assertions: list[dict], base: Path) -> dict:
    """Grade a list of run records and aggregate them."""
    graded = [
        grade_run(
            assertions,
            base=Path(r.get("output_dir") or base),
            stdout=r.get("stdout", ""),
            stderr=r.get("stderr", ""),
            exit_code=r.get("exit_code"),
        )
        for r in runs
    ]
    totals = {
        "runs": len(graded),
        "passed": sum(g["summary"]["passed"] for g in graded),
        "failed": sum(g["summary"]["failed"] for g in graded),
        "total": sum(g["summary"]["total"] for g in graded),
        "manual": sum(g["summary"]["manual"] for g in graded),
    }
    rates = [g["summary"]["pass_rate"] for g in graded if g["summary"]["pass_rate"] is not None]
    totals["pass_rate"] = (sum(rates) / len(rates)) if rates else None
    return {"runs": graded, "summary": totals}


def main() -> int:
    parser = argparse.ArgumentParser(description="Grade eval assertions against a run")
    parser.add_argument(
        "--assertions",
        help="JSON file holding a list of assertions, or an evals.json object",
    )
    parser.add_argument("--eval-id", help="Use assertions from this eval id in evals.json")
    parser.add_argument("--output-dir", default=".", help="Run directory holding artifacts")
    parser.add_argument("--stdout-file", help="File containing the run's stdout")
    parser.add_argument("--stderr-file", help="File containing the run's stderr")
    parser.add_argument("--exit-code", type=int, help="Run exit code")
    args = parser.parse_args()

    assertions: list[dict] = []
    if args.assertions:
        data = read_json(args.assertions, default=None)
        if data is None:
            print(f"error: cannot read {args.assertions}", file=sys.stderr)
            return 1
        if isinstance(data, dict) and "evals" in data:
            wanted = str(args.eval_id) if args.eval_id is not None else None
            match = next(
                (e for e in data["evals"] if str(e.get("id")) == wanted), None
            ) if wanted else (data["evals"][0] if data["evals"] else None)
            assertions = (match or {}).get("assertions") or []
        elif isinstance(data, dict) and "assertions" in data:
            assertions = data["assertions"]
        elif isinstance(data, list):
            assertions = data

    stdout = (
        Path(args.stdout_file).read_text(encoding="utf-8", errors="replace")
        if args.stdout_file else ""
    )
    stderr = (
        Path(args.stderr_file).read_text(encoding="utf-8", errors="replace")
        if args.stderr_file else ""
    )

    result = grade_run(
        assertions,
        base=Path(args.output_dir),
        stdout=stdout,
        stderr=stderr,
        exit_code=args.exit_code,
    )
    print(json.dumps(result, indent=2))
    return 0 if result["summary"]["failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
