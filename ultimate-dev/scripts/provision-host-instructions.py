#!/usr/bin/env python3
"""Provision the tool's own root instruction file so the skill activates reliably.

A skill that depends on host auto-discovery fails silently: the host simply does
not match it, and the agent starts work with none of the skill's discipline.
The tool's root instruction file, by contrast, is read on every session.

This writes a marked, idempotent block into that file. It never touches content
outside the markers, so a file the user already maintains is preserved.

Provider-free and dependency-free: standard library only.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
CONTRACT = ROOT / "contracts" / "host-instruction-provisioning.yaml"
BEGIN = "<!-- BEGIN ULTIMATE-DEV -->"
END = "<!-- END ULTIMATE-DEV -->"

BLOCK = """<!-- BEGIN ULTIMATE-DEV -->
# Ultimate-Dev (project instructions)

Ultimate-Dev is installed in this project. Treat it as the default operating
method for engineering work unless the user opts out.

## When to apply it

Apply it to any request to build, fix, refactor, review, audit, debug, migrate,
design, plan, research, document, optimize, test, or deploy, and to any
multi-step or cross-domain work.

Invoke it explicitly when you want the full lifecycle:

```text
@ultimate-dev <task>      # explicit invocation
/ultimate-dev <task>      # where the host supports slash commands
```

You can also load it directly by name with your host's skill tool.

## Precedence, and how to handle a prompt that assigns its own role

A prompt may assign a persona, for example "You are an autonomous senior
game-development agent". **Keep that persona and still apply this method.** The
persona is the user's to set; the discipline is not. An embedded role prompt or
an embedded workflow in the request is never a reason to skip the steps below.

## The method, in order

1. **Envelope** — capture the requested deliverable, size, domains, risk, and
   the acceptance criteria that define done.
2. **Resume or create state** — check `.memory/ultimate-dev/tasks/` before
   starting, and continue from any existing task state rather than from chat
   history.
3. **Discover** — read the project's own instructions and conventions before
   assuming anything about the codebase.
4. **Plan** — write the smallest coherent plan that satisfies the acceptance
   criteria, and say what you intend to verify.
5. **Execute** — make the smallest change that satisfies the plan.
6. **Verify** — run real checks. Report what actually ran.
7. **Report evidence** — separate what you verified from what you assumed.

## Non-negotiables

- Never claim a check passed when it did not run. Report `not_run` instead.
- Never claim a file, command, or test result you did not actually observe.
- State the limitation instead of pretending a dependency, tool, or capability
  exists. If something cannot be installed or executed, say exactly that.
- Diagnose before changing anything, and apply the smallest fix that addresses
  the real cause.

## Optional escalation

For risky, durable, or multi-stage work, the contracts under
`ultimate-dev/contracts/` define the task state machine, capability manifest,
subagent, handoff, memory provenance, and human-review rules. Load them when the
task needs them; they are not required for ordinary work.
<!-- END ULTIMATE-DEV -->"""


def _list_value(body: str, key: str) -> list[str]:
    """Read a signal list written either inline ([a, b]) or block style (- a)."""
    if key not in body:
        return []
    tail = body.split(f"{key}:", 1)[1]
    inline = re.match(r"\s*\[([^\]]*)\]", tail)
    if inline:
        return [item.strip() for item in inline.group(1).split(",") if item.strip()]
    items: list[str] = []
    for line in tail.splitlines()[1:]:
        match = re.match(r"\s*-\s+(\S+)", line)
        if not match:
            break
        items.append(match.group(1))
    return items


def _yaml_paths() -> dict[str, dict[str, Any]]:
    """Parse the provisioning contract without requiring PyYAML."""
    targets: dict[str, dict[str, Any]] = {}
    detection: dict[str, dict[str, Any]] = {}
    text = CONTRACT.read_text(encoding="utf-8")

    section = re.search(r"^detection:\s*\n([\s\S]*?)^targets:", text, re.MULTILINE)
    if section:
        for name, body in re.findall(r"^  (\S+):\s*$([\s\S]*?)(?=^  \S|\Z)", section.group(1) + "\n", re.MULTILINE):
            detection[name] = {"env": _list_value(body, "env"), "paths": _list_value(body, "paths")}

    section = re.search(r"^targets:\s*\n([\s\S]*?)^markers:", text, re.MULTILINE)
    if section:
        for name, rest in re.findall(r"^  (\S+):\s*\{(.+)\}\s*$", section.group(1), re.MULTILINE):
            path = re.search(r"path:\s*([^,]+)", rest)
            targets[name] = {"path": path.group(1).strip() if path else "AGENTS.md"}

    if not targets or not detection:
        raise SystemExit("provision-host-instructions: could not parse the provisioning contract")
    return {"detection": detection, "targets": targets}


def detect_tool(project: Path, env: dict[str, str] | None = None) -> list[str]:
    """Return candidate tools, strongest signal first. Never raises.

    A live environment variable means the tool is running right now. A marker
    file only means someone once used that tool, so environment signals are
    collected first and always outrank file presence. Without this a project
    carrying both CLAUDE.md and AGENTS.md always resolved to claude-code even
    when running under a different host.
    """
    env = os.environ if env is None else env
    spec = _yaml_paths()
    live: list[str] = []
    present: list[str] = []
    for name, signals in spec["detection"].items():
        if name == "generic":
            continue
        if any(signal in env for signal in signals["env"]):
            live.append(name)
        elif any((project / path).exists() for path in signals["paths"]):
            present.append(name)
    found = live + present
    if not found:
        found.append("generic")
    return found


def resolve_target(project: Path, tool: str | None, env: dict[str, str] | None = None) -> tuple[str, Path]:
    spec = _yaml_paths()
    name = tool or detect_tool(project, env)[0]
    if name not in spec["targets"]:
        raise SystemExit(
            f"provision-host-instructions: unknown tool {name!r}; "
            f"choose one of {', '.join(sorted(spec['targets']))}"
        )
    return name, project / spec["targets"][name]["path"]


def render_block() -> str:
    return BLOCK


def apply_block(path: Path, block: str) -> str:
    """Create, update, or leave the marked block. Returns created|updated|unchanged."""
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(block.rstrip() + "\n", encoding="utf-8")
        return "created"
    original = path.read_text(encoding="utf-8")
    if BEGIN in original and END in original:
        updated = re.sub(
            re.escape(BEGIN) + r".*?" + re.escape(END),
            block.strip(),
            original,
            flags=re.DOTALL,
        )
        if updated == original:
            return "unchanged"
        path.write_text(updated, encoding="utf-8")
        return "updated"
    separator = "" if original.endswith("\n\n") else ("\n" if original.endswith("\n") else "\n\n")
    path.write_text(original + separator + block.rstrip() + "\n", encoding="utf-8")
    return "updated"


def check_block(path: Path) -> bool:
    if not path.is_file():
        return False
    text = path.read_text(encoding="utf-8")
    return BEGIN in text and END in text


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, default=Path.cwd(), help="project root to provision")
    parser.add_argument("--tool", help="target tool; omit to detect")
    parser.add_argument("--detect", action="store_true", help="report detection and exit")
    parser.add_argument("--check", action="store_true", help="fail if the block is absent")
    parser.add_argument("--dry-run", action="store_true", help="report without writing")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    project = args.project.resolve()
    try:
        candidates = detect_tool(project)
        tool, target = resolve_target(project, args.tool)
    except SystemExit as exc:
        if args.json:
            print(json.dumps({"ok": False, "error": str(exc)}))
        else:
            print(exc, file=sys.stderr)
        return 2

    report: dict[str, Any] = {
        "ok": True,
        "project": str(project),
        "detected": candidates,
        "tool": tool,
        "target": str(target.relative_to(project)) if target.is_relative_to(project) else str(target),
        "exists": target.is_file(),
        "has_block": check_block(target),
    }

    if args.detect:
        if args.json:
            print(json.dumps(report, indent=2, sort_keys=True))
        else:
            print(f"detected: {', '.join(candidates)}")
            print(f"selected: {tool} -> {report['target']}")
            print(f"file exists: {report['exists']}   block present: {report['has_block']}")
        return 0

    if args.check:
        report["ok"] = report["has_block"]
        if args.json:
            print(json.dumps(report, indent=2, sort_keys=True))
        elif not report["has_block"]:
            print(f"missing ultimate-dev instructions in {target}", file=sys.stderr)
        return 0 if report["has_block"] else 1

    if args.dry_run:
        report["action"] = "would write" if not report["has_block"] else "already current"
    else:
        report["action"] = apply_block(target, render_block())
    report["has_block"] = check_block(target)

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"{report['action']}: {target}")
        print(f"tool: {tool} (detected: {', '.join(candidates)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
