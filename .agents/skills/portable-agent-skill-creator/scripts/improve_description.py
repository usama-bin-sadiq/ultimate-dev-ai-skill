#!/usr/bin/env python3
"""Propose an improved skill description, and validate proposals.

Used by ``run_loop.py`` to iterate on a skill's discovery description. The
proposal is validated before it is accepted: a rewrite that exceeds the length
limit, introduces angle brackets, or names a specific vendor when the skill is
provider-neutral is rejected and the previous description is kept. Without that
guard an automated loop can quietly produce a description that is invalid or
worse than what it started with.

Usage:
    python scripts/improve_description.py --eval-results results.json --skill-path ./my-skill
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
from pathlib import Path

if __package__ in (None, ""):  # allow `python scripts/improve_description.py`
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts import agent_runner  # noqa: E402
from scripts.utils import DESCRIPTION_MAX_LENGTH, parse_skill_md  # noqa: E402

_DESCRIPTION_TAG = re.compile(r"<new_description>(.*?)</new_description>", re.DOTALL)

# Naming a vendor in a discovery description is only correct when the skill
# genuinely depends on that vendor. These are treated as a warning so the
# loop's own prompt, not a hardcoded blocklist, remains the primary signal.
_PROVIDER_TERMS = ("claude", "openai", "codex", "chatgpt", "cursor", "copilot", "gemini", "mcp")

_VALIDATOR_PROMPT = """You are improving the discovery description for an Agent Skill named "{skill_name}".

Discovery in agent runtimes is driven almost entirely by the description, so it
must state the user goal, when the skill is useful, and what result it produces.

Current description:
{current_description}

Skill content:
{skill_content}

Evaluation results:
{eval_results}

History of previous attempts (blind to any held-out set):
{history}

Write a concise, provider-neutral description that tells an agent:
1. what user goal the skill handles,
2. when the skill should be considered,
3. what kind of result it enables.

Rules:
- Do not mention a specific vendor, CLI, or filesystem path unless the skill
  genuinely depends on that technology.
- Do not overfit to individual eval prompts; generalize to the skill's purpose.
- Stay under {max_chars} characters and use no angle brackets.
- Return only the new description inside <new_description> tags."""


def validate_description(
    description: str, *, provider_neutral: bool = True
) -> tuple[bool, list[str]]:
    """Check a proposed description against the format rules.

    Returns ``(ok, problems)``. ``provider_neutral`` also reports vendor names
    as a problem, which the loop treats as a rejection.
    """
    problems: list[str] = []
    if not isinstance(description, str) or not description.strip():
        return False, ["description is empty"]
    if len(description) > DESCRIPTION_MAX_LENGTH:
        problems.append(
            f"{len(description)} characters exceeds the {DESCRIPTION_MAX_LENGTH} limit"
        )
    if "<" in description or ">" in description:
        problems.append("description contains angle brackets")
    if provider_neutral:
        lowered = description.lower()
        found = [term for term in _PROVIDER_TERMS if re.search(rf"\b{term}\b", lowered)]
        if found:
            problems.append(f"names provider-specific terms for a neutral skill: {found}")
    return (not problems), problems


def propose_description(
    *,
    skill_name: str,
    skill_content: str,
    current_description: str,
    eval_results: dict,
    history: list[dict],
    agent: str = "auto",
    model: str | None = None,
    timeout: int = 300,
    extra_args: list[str] | None = None,
    command: str | None = None,
) -> str:
    """Ask the runtime for a better description. Raw output, unvalidated."""
    prompt = _VALIDATOR_PROMPT.format(
        skill_name=skill_name,
        current_description=current_description,
        skill_content=skill_content[:12000],
        eval_results=json.dumps(eval_results, indent=2, default=str)[:12000],
        history=json.dumps(history, indent=2, default=str)[:12000],
        max_chars=DESCRIPTION_MAX_LENGTH,
    )
    # Propose from a scratch directory. A description proposal produces no
    # artifacts to inspect, but the runtime is free to write files, and running
    # it in the caller's working directory would drop those into the user's
    # tree or into the skill bundle being evaluated.
    with tempfile.TemporaryDirectory(prefix="skill-creator-proposal-") as scratch:
        result = agent_runner.run_prompt(
            prompt, agent=agent, model=model, timeout=timeout,
            extra_args=extra_args or [], command=command, cwd=scratch,
        )
    if result.get("exit_code") != 0:
        raise RuntimeError(
            f"description proposal failed ({result.get('error') or 'non-zero exit'}): "
            f"{(result.get('stderr') or '')[:400]}"
        )
    stdout = result.get("stdout") or ""
    match = _DESCRIPTION_TAG.search(stdout)
    return (match.group(1) if match else stdout).strip().strip('"').strip()


def improve_description(
    skill_name: str,
    skill_content: str,
    current_description: str,
    eval_results: dict,
    history: list[dict],
    agent: str = "auto",
    model: str | None = None,
    timeout: int = 300,
    extra_args: list[str] | None = None,
    command: str | None = None,
) -> tuple[str, dict]:
    """Return ``(description, report)`` for the next loop iteration.

    The description is the current one when no valid proposal is available, so
    the loop never regresses because of a bad or failed generation.
    """
    report: dict = {
        "accepted": False,
        "problems": [],
        "agent": agent,
        "model": model,
    }
    try:
        proposal = propose_description(
            skill_name=skill_name,
            skill_content=skill_content,
            current_description=current_description,
            eval_results=eval_results,
            history=history,
            agent=agent,
            model=model,
            timeout=timeout,
            extra_args=extra_args,
            command=command,
        )
    except (RuntimeError, ValueError, SystemExit) as exc:
        report["problems"] = [f"proposal unavailable: {exc}"]
        return current_description, report

    if proposal == current_description:
        report["problems"] = ["proposal is identical to the current description"]
        return current_description, report

    ok, problems = validate_description(proposal)
    report["problems"] = problems
    if not ok:
        return current_description, report

    report["accepted"] = True
    report["previous_length"] = len(current_description)
    report["new_length"] = len(proposal)
    return proposal, report


def main() -> int:
    parser = argparse.ArgumentParser(description="Propose a better skill description")
    parser.add_argument("--eval-results", required=True, help="results.json from run_eval")
    parser.add_argument("--skill-path", required=True)
    parser.add_argument("--history", default=None, help="JSON file of prior attempts")
    parser.add_argument("--agent", default=os.environ.get("AGENT_TOOL", "auto"))
    parser.add_argument(
        "--command", default=os.environ.get("AGENT_COMMAND"),
        help="Command prefix for --agent custom. Also settable via AGENT_COMMAND.",
    )
    parser.add_argument("--model", default=None)
    parser.add_argument("--timeout", type=int, default=300)
    parser.add_argument("--extra-args", nargs="*", default=[])
    args = parser.parse_args()

    name, current, content = parse_skill_md(Path(args.skill_path))
    try:
        results = json.loads(Path(args.eval_results).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"error: cannot read {args.eval_results}: {exc}", file=sys.stderr)
        return 1
    history = (
        json.loads(Path(args.history).read_text(encoding="utf-8"))
        if args.history else []
    )

    try:
        new_description, report = improve_description(
            name, content, current, results, history,
            agent=args.agent, model=args.model,
            timeout=args.timeout, extra_args=args.extra_args,
            command=args.command,
        )
    except (ValueError, SystemExit) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print(json.dumps({
        "description": new_description,
        "changed": new_description != current,
        "report": report,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
