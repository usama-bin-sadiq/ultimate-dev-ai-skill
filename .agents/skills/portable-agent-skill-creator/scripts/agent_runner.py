#!/usr/bin/env python3
"""Run a prompt through a local agent runtime.

Adapters are data, not code: see ``references/adapters.json``. Adding an agent
CLI means adding a registry entry, not editing this file. ``--agent custom``
plus ``--command`` remains the universal escape hatch for any runtime that can
accept a prompt from argv or stdin.

Usage:
    python scripts/agent_runner.py --agent opencode --prompt "..."
    python scripts/agent_runner.py --agent custom --command 'my-agent run' --prompt "..."
    python scripts/agent_runner.py list-runtimes
    python scripts/agent_runner.py --agent gemini --prompt "..." --dry-run

The runner normalizes only the common denominator across runtimes: prompt,
optional model, working directory, timeout, stdout, stderr, exit code and
wall-clock time. Token accounting is reported only when the runtime actually
exposes it; it is ``null`` otherwise, never estimated.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import time
from pathlib import Path

if __package__ in (None, ""):  # allow `python scripts/agent_runner.py`
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.utils import SKILL_ROOT  # noqa: E402

REGISTRY_PATH = SKILL_ROOT / "references" / "adapters.json"

# Used only if references/adapters.json is missing or unreadable, so that a
# damaged registry degrades to a working subset instead of a hard failure.
FALLBACK_REGISTRY: dict = {
    "adapters": {
        "claude": {
            "executable": "claude",
            "argv": ["-p", "{prompt}"],
            "model_flag": "--model",
            "env_clear": ["CLAUDECODE"],
            "confidence": "documented",
        },
        "opencode": {
            "executable": "opencode",
            "argv": ["run", "{prompt}"],
            "model_flag": "--model",
            "confidence": "documented",
        },
        "codex": {
            "executable": "codex",
            "argv": ["exec", "{prompt}"],
            "model_flag": "--model",
            "confidence": "documented",
        },
    },
    "auto_detect_order": ["claude", "opencode", "codex"],
}

_PROMPT_TOKEN = "{prompt}"


# --------------------------------------------------------------------------
# Registry
# --------------------------------------------------------------------------


def load_registry(path: Path | None = None) -> dict:
    """Load the adapter registry, falling back to a minimal built-in."""
    path = Path(path) if path else REGISTRY_PATH
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(
            f"warning: adapter registry {path} unreadable ({exc}); "
            "using the built-in fallback subset",
            file=sys.stderr,
        )
        return FALLBACK_REGISTRY
    if not isinstance(data, dict) or not isinstance(data.get("adapters"), dict):
        print(
            f"warning: adapter registry {path} has no 'adapters' object; "
            "using the built-in fallback subset",
            file=sys.stderr,
        )
        return FALLBACK_REGISTRY
    return data


def get_adapters(registry: dict | None = None) -> dict:
    return (registry or load_registry())["adapters"]


def adapter_names(registry: dict | None = None) -> list[str]:
    return sorted(get_adapters(registry))


def resolve_adapter(
    agent: str, registry: dict | None = None, command: str | None = None
) -> dict:
    """Resolve an agent name to an adapter.

    ``auto`` picks the first registry entry, in declared preference order, whose
    executable is on PATH. ``custom`` requires ``--command``.
    """
    registry = registry or load_registry()
    adapters = get_adapters(registry)

    if agent == "auto":
        if command:
            # Silently ignoring an explicit command would run a different
            # program than the caller asked for. Refuse instead.
            raise ValueError(
                "--command cannot be combined with --agent auto. "
                "Pass --agent custom --command '<prefix>' to use a specific command."
            )
        for name in registry.get("auto_detect_order", []):
            spec = adapters.get(name)
            if spec and spec.get("executable") and shutil.which(spec["executable"]):
                return {**spec, "name": name, "detected": True}
        raise SystemExit(
            "No supported agent CLI found on PATH. "
            f"Run '{Path(sys.argv[0]).name} list-runtimes' to see what was probed, "
            "then pass --agent explicitly or use --agent custom --command '...'."
        )

    if agent == "custom":
        if not command:
            raise ValueError("--command is required for --agent custom")
        prefix = shlex.split(command)
        if not prefix:
            raise ValueError("--command is empty after shell splitting")
        return {
            "name": "custom",
            "executable": prefix[0],
            # Uniform contract: `argv` holds flags only and never repeats the
            # executable. build_command() prepends it.
            "argv": prefix[1:] + [_PROMPT_TOKEN],
            "confidence": "documented",
            "notes": "user-supplied command prefix",
        }

    spec = adapters.get(agent)
    if spec is None:
        raise ValueError(
            f"Unknown agent '{agent}'. Known adapters: {', '.join(adapter_names(registry))}. "
            "Use --agent custom --command '<prefix>' for any other runtime, or add an "
            f"entry to {REGISTRY_PATH}."
        )
    return {**spec, "name": agent, "detected": False}


# --------------------------------------------------------------------------
# Command construction
# --------------------------------------------------------------------------


def build_command(
    agent: str,
    prompt: str,
    model: str | None = None,
    extra_args: list[str] | None = None,
    command: str | None = None,
    registry: dict | None = None,
) -> list[str]:
    """Build the argv for an agent invocation.

    Kept as a module-level function with this signature because the eval and
    improvement scripts call it directly.
    """
    spec = resolve_adapter(agent, registry=registry, command=command)
    extra_args = list(extra_args or [])

    # Adapter contract: `executable` is the program, `argv` holds flags only and
    # contains the literal {prompt} exactly once. build_command assembles them.
    # Getting this wrong runs the flags as if they were the program.
    template = list(spec.get("argv") or [])
    if not any(_PROMPT_TOKEN == str(t) for t in template):
        # An adapter that does not place the prompt: append it so the prompt is
        # still delivered rather than silently dropped.
        template.append(_PROMPT_TOKEN)

    argv: list[str] = [str(spec["executable"])] if spec.get("executable") else []
    argv += [prompt if token == _PROMPT_TOKEN else str(token) for token in template]

    if model:
        flag = spec.get("model_flag")
        if flag:
            argv += [flag, model]
        else:
            print(
                f"warning: adapter '{spec['name']}' declares no model_flag; "
                f"ignoring --model {model!r}",
                file=sys.stderr,
            )

    argv += extra_args

    # Resolve argv[0] to an absolute path. The eval runner changes the working
    # directory into a per-run sandbox, and a relative executable path would
    # otherwise stop resolving once the process leaves the caller's directory.
    if argv:
        argv[0] = _absolutize(argv[0])
    return argv


def _absolutize(executable: str) -> str:
    """Return an absolute path for a path-like executable, else leave as-is."""
    if os.sep in executable or (os.altsep and os.altsep in executable):
        return str(Path(executable).resolve())
    located = shutil.which(executable)
    return located or executable


def build_env(spec: dict) -> dict:
    """Environment for the child process, minus nested-session guard vars."""
    env = os.environ.copy()
    for key in spec.get("env_clear") or []:
        env.pop(key, None)
    return env


# --------------------------------------------------------------------------
# Execution
# --------------------------------------------------------------------------


_TOKEN_PATTERNS = (
    re.compile(r'"total_tokens"\s*:\s*(\d+)'),
    re.compile(r'"totalTokens"\s*:\s*(\d+)'),
    re.compile(r'"tokens"\s*:\s*(\d+)'),
)


def extract_usage(stdout: str) -> dict:
    """Extract token accounting only when the runtime actually reported it.

    Returns ``{}`` when nothing parseable is present, so callers record a null
    rather than a fabricated number.
    """
    for pattern in _TOKEN_PATTERNS:
        match = pattern.search(stdout or "")
        if match:
            return {"total_tokens": int(match.group(1))}
    return {}


def run_prompt(
    prompt: str,
    agent: str = "auto",
    model: str | None = None,
    command: str | None = None,
    cwd: str = ".",
    timeout: int = 300,
    extra_args: list[str] | None = None,
    registry: dict | None = None,
) -> dict:
    """Execute one prompt and return a normalized run record."""
    registry = registry or load_registry()
    spec = resolve_adapter(agent, registry=registry, command=command)
    argv = build_command(agent, prompt, model, extra_args, command, registry=registry)

    executable = spec.get("executable")
    if executable and not spec.get("detected") and not shutil.which(executable):
        return {
            "agent": spec["name"],
            "exit_code": None,
            "stdout": "",
            "stderr": f"executable not found on PATH: {executable}",
            "duration_ms": None,
            "error": "ExecutableNotFound",
            "total_tokens": None,
        }

    started = time.monotonic()
    try:
        proc = subprocess.run(
            argv,
            cwd=Path(cwd).resolve(),
            capture_output=True,
            text=True,
            timeout=timeout,
            env=build_env(spec),
        )
        duration = round((time.monotonic() - started) * 1000)
        result = {
            "agent": spec["name"],
            "command": redact(argv, prompt),
            "exit_code": proc.returncode,
            "stdout": proc.stdout,
            "stderr": proc.stderr,
            "duration_ms": duration,
        }
    except subprocess.TimeoutExpired as exc:
        result = {
            "agent": spec["name"],
            "command": redact(argv, prompt),
            "exit_code": None,
            "stdout": _as_text(exc.stdout),
            "stderr": _as_text(exc.stderr),
            "duration_ms": round((time.monotonic() - started) * 1000),
            "error": "Timeout",
        }
    except Exception as exc:  # noqa: BLE001 - report, never mask
        result = {
            "agent": spec["name"],
            "command": redact(argv, prompt),
            "exit_code": None,
            "stdout": "",
            "stderr": str(exc),
            "duration_ms": round((time.monotonic() - started) * 1000),
            "error": type(exc).__name__,
        }

    usage = extract_usage(result.get("stdout") or "")
    result["total_tokens"] = usage.get("total_tokens")
    if result["total_tokens"] is None:
        result["metrics_note"] = "runtime did not report token usage"
    return result


def _as_text(value) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return str(value)


def redact(argv: list[str], prompt: str | None = None) -> list[str]:
    """Replace prompt arguments with a marker so run records stay readable.

    ``build_command`` substitutes the real prompt into argv, so the marker is
    matched by value rather than by the template token.
    """
    if prompt is None:
        return [a if a != _PROMPT_TOKEN else "<prompt>" for a in argv]
    return ["<prompt>" if a == prompt else a for a in argv]


# --------------------------------------------------------------------------
# Runtime discovery
# --------------------------------------------------------------------------


def probe_runtimes(registry: dict | None = None) -> list[dict]:
    """Report which registered runtimes are actually invocable on this host."""
    registry = registry or load_registry()
    rows: list[dict] = []
    for name in adapter_names(registry):
        spec = get_adapters(registry)[name]
        executable = spec.get("executable")
        if not executable:
            rows.append(
                {
                    "agent": name,
                    "installed": None,
                    "path": None,
                    "version": None,
                    "confidence": spec.get("confidence", "unknown"),
                    "notes": spec.get("notes", ""),
                }
            )
            continue
        path = shutil.which(executable)
        rows.append(
            {
                "agent": name,
                "installed": path is not None,
                "path": path,
                "version": probe_version(executable),
                "confidence": spec.get("confidence", "unknown"),
                "notes": spec.get("notes", ""),
            }
        )
    return rows


def probe_version(executable: str) -> str | None:
    """Best-effort version string. Returns None rather than guessing."""
    for flag in ("--version", "-v", "version"):
        try:
            proc = subprocess.run(
                [executable, flag],
                capture_output=True,
                text=True,
                timeout=10,
            )
        except Exception:
            return None
        if proc.returncode == 0:
            text = (proc.stdout or proc.stderr or "").strip().splitlines()
            if text:
                return text[0][:120]
    return None


def print_runtime_table(as_json: bool) -> None:
    rows = probe_runtimes()
    if as_json:
        print(json.dumps(rows, indent=2))
        return

    print(f"registry: {REGISTRY_PATH}\n")
    width = max((len(r["agent"]) for r in rows), default=8)
    print(f"{'AGENT'.ljust(width)}  {'INSTALLED':<10} {'VERSION':<24} {'CONFIDENCE':<11} PATH")
    for row in rows:
        installed = {True: "yes", False: "no", None: "n/a"}[row["installed"]]
        print(
            f"{row['agent'].ljust(width)}  {installed:<10} "
            f"{(row['version'] or '-'):<24.24} {row['confidence']:<11} {row['path'] or ''}"
        )
    print(
        "\nconfidence: documented = invocation shape is documented by the tool;\n"
        "            community   = user-reported shape, verify before relying on it;\n"
        "            n/a         = not a standalone CLI (use --agent custom --command)."
    )


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run a prompt through a local agent runtime.",
    )
    sub = parser.add_subparsers(dest="subcommand")

    run = sub.add_parser("run", help="execute a prompt (default)")
    run.add_argument("--agent", default=os.environ.get("AGENT_TOOL", "auto"))
    run.add_argument("--command", help="Command prefix for --agent custom")
    run.add_argument("--prompt", required=True)
    run.add_argument("--model", default=None)
    run.add_argument("--cwd", default=".")
    run.add_argument("--timeout", type=int, default=300)
    run.add_argument("--extra-args", nargs="*", default=[])
    run.add_argument("--output-file", default=None)
    run.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the resolved argv and exit without invoking the runtime",
    )

    listing = sub.add_parser(
        "list-runtimes", help="probe PATH and report installed agent CLIs"
    )
    listing.add_argument("--json", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    parser = build_parser()

    # Backward compatibility: allow flags without the `run` subcommand.
    if not argv or argv[0].startswith("-"):
        argv = ["run", *argv]
    if argv[0] == "list-runtimes":
        args = parser.parse_args(argv)
        print_runtime_table(as_json=args.json)
        return 0

    args = parser.parse_args(argv)
    registry = load_registry()

    if args.dry_run:
        try:
            resolved = build_command(
                args.agent, args.prompt, args.model, args.extra_args, args.command, registry
            )
        except (ValueError, SystemExit) as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
        print(json.dumps({"agent": args.agent, "argv": redact(resolved)}, indent=2))
        return 0

    try:
        result = run_prompt(
            args.prompt,
            agent=args.agent,
            model=args.model,
            command=args.command,
            cwd=args.cwd,
            timeout=args.timeout,
            extra_args=args.extra_args,
            registry=registry,
        )
    except (ValueError, SystemExit) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if args.output_file:
        out = Path(args.output_file)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))
    return 0 if result.get("exit_code") == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
