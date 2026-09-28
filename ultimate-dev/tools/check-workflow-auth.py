#!/usr/bin/env python3
"""Every `gh` call that needs a credential must have one in its own step.

Three separate release failures in this repository had the same cause, and each
one survived only because the step before it happened to die first:

  1. an unbound GITHUB_TOKEN under `set -u` in the version step,
  2. a push that failed on a discarded checkout credential,
  3. `gh release create` with no GH_TOKEN in the step's env, exit 4.

A `gh` command does not inherit a token from another step or from the job
environment. It reads its own `GH_TOKEN`, and failing that its own
`GITHUB_TOKEN`. So a step that calls `gh` and declares neither cannot work, and
the only reason the workflow ever got that far is that something upstream broke
first and masked it.

This checks the property rather than the three known cases: for every step in
every workflow, if its script invokes a `gh` subcommand that requires
authentication, that step must declare a token in its own `env:`. A new
workflow written tomorrow gets checked without anyone remembering to.

Subcommands that require auth:

  api, attestation, cache, codespace, extension, gist, issue, label, pr,
  project, release, repo, run, ruleset, secret, ssh-key, teams, variable,
  workflow
      All touch private or write state on behalf of the repository.

Not required, and deliberately not flagged:

  auth, version, help, completion, config
      Local, or the anonymous rate-limited tier. Flagging these would train
      whoever reads the next failure to ignore this one.

Stdlib only, and it reads the YAML with an indentation scanner rather than a
dependency. That is deliberate: a checker that cannot run in the environment it
guards is one that gets skipped, and then the bug it was written for comes back.

Exit 0 clean, exit 1 with one line per undeclared credential.
"""

from __future__ import annotations

import pathlib
import re
import sys

AUTH_SUBCOMMANDS = {
    "api", "attestation", "cache", "codespace", "extension", "gist", "issue",
    "label", "pr", "project", "release", "repo", "run", "ruleset", "secret",
    "ssh-key", "teams", "variable", "workflow",
}

# A token, however it is spelled. `secrets.GITHUB_TOKEN` and `github.token` are
# the same credential written two ways. What is checked is that the *name* is
# bound in the step, because an unbound name is precisely how defect 1 happened.
TOKEN_NAMES = {"GH_TOKEN", "GITHUB_TOKEN"}

GH_CALL = re.compile(r"(?<![\w-])gh\s+([a-z][a-z0-9-]*)")


def _indent(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def _mapping_keys_at(lines: list[str], indent: int) -> list[str]:
    """Keys of the `key: value` mapping whose `key:` sits at `indent`."""
    keys = []
    for line in lines:
        if _indent(line) != indent:
            continue
        m = re.match(r"^([A-Za-z_][A-Za-z0-9_.-]*):", line.strip())
        if m:
            keys.append(m.group(1))
    return keys


def _block(lines: list[str], start: int, indent: int) -> list[str]:
    """Lines following `start` that are indented deeper than `indent`."""
    out: list[str] = []
    for line in lines[start:]:
        if not line.strip():
            out.append(line)
            continue
        if _indent(line) <= indent:
            break
        out.append(line)
    return out


def _steps(lines: list[str]) -> list[tuple[str, int, int, list[str]]]:
    """(name, body_start, step_indent, step_lines) for every step, all jobs.

    The step indent is returned rather than assumed. The first version of this
    walked the file and stopped at the end of the first job, so it reported
    three workflows checked while examining one job's worth of steps in one of
    them -- a clean result that meant almost nothing. Job boundaries are found
    by looking for every `steps:` key, not by breaking at the first dedent.
    """
    out: list[tuple[str, int, int, list[str]]] = []
    for i, line in enumerate(lines):
        if not re.match(r"^\s*steps:\s*$", line):
            continue
        steps_indent = _indent(line)
        item_indent = steps_indent + 2
        j = i + 1
        while j < len(lines):
            raw = lines[j]
            if not raw.strip():
                j += 1
                continue
            ind = _indent(raw)
            if ind < steps_indent:
                break                       # left this steps: block
            if ind != item_indent or not re.match(r"^\s*-\s", raw):
                j += 1
                continue
            # `- name: Build the release` labels the step "Build the release".
            # Taking the key instead reported every named step as "name", which
            # is useless in a finding that names the offending step.
            inner = raw.strip().lstrip("-").strip()
            kv = re.match(r"^([A-Za-z_][A-Za-z0-9_.-]*):\s*(.*)$", inner)
            if kv and kv.group(1) in ("name", "id"):
                label = kv.group(2).strip().strip("'\"") or kv.group(1)
            else:
                label = inner.split(":", 1)[0].strip()
            body = _block(lines, j + 1, item_indent)
            out.append((label or f"line {j + 1}", j + 1, item_indent, body))
            j += 1 + len(body)
    return out


def _step_env_keys(body: list[str], step_indent: int) -> set[str]:
    """Env var names declared in this step's own `env:` mapping.

    The mapping sits at step_indent + 2. A hardcoded offset was the first
    version's bug: it never matched, so `in_env` never turned off, and every
    later `key:` in the step -- including `run:` -- was read as an env var.
    """
    keys: set[str] = set()
    for idx, line in enumerate(body):
        if _indent(line) != step_indent + 2:
            continue
        if not re.match(r"^env:\s*$", line.strip()):
            continue
        for name in _mapping_keys_at(body[idx + 1:], step_indent + 4):
            keys.add(name)
    return keys


def _step_script(body: list[str], step_indent: int) -> str:
    """The step's shell script, from a block scalar or an inline `run:`."""
    for idx, line in enumerate(body):
        if _indent(line) != step_indent + 2:
            continue
        m = re.match(r"^run:\s*(.*)$", line.strip())
        if not m:
            continue
        rest = m.group(1)
        if rest in ("|", ">", "|-", ">-", "|+", ">+", ""):
            return "\n".join(body[idx + 1:])
        return rest
    return ""


def check_workflow(path: pathlib.Path) -> list[str]:
    """Findings for one workflow file."""
    lines = path.read_text().split("\n")
    problems: list[str] = []
    for name, lineno, step_indent, body in _steps(lines):
        script = _step_script(body, step_indent)
        if "gh" not in script:
            continue
        # A `#` line inside a run block is a comment, not a call. Counting it
        # is how a step that only *mentions* gh in prose gets flagged. Written
        # as a loop rather than a comprehension because the comment test needs
        # the line, and a comprehension scope does not carry it across.
        calls: set[str] = set()
        for ln in script.split("\n"):
            if ln.strip().startswith("#"):
                continue
            m = GH_CALL.search(ln)
            if m:
                calls.add(m.group(1))
        needs = sorted(calls & AUTH_SUBCOMMANDS)
        if not needs:
            continue
        if _step_env_keys(body, step_indent) & TOKEN_NAMES:
            continue
        problems.append(
            f"{path}:{lineno}: step '{name}' calls gh {needs[0]} but declares "
            f"no GH_TOKEN or GITHUB_TOKEN in its own env:. `gh` does not inherit "
            f"a credential from another step."
        )
    return problems


def workflow_dir() -> pathlib.Path | None:
    """The repo's .github/workflows, found from wherever this is invoked.

    This tool lives in ultimate-dev/tools/ but guards a file two levels up, and
    the pre-commit gate may run it from either the repository root or the skill
    directory. A guard that silently checks nothing because it looked in the
    wrong place is worse than no guard, because it reports clean.
    """
    for base in (pathlib.Path.cwd(), *pathlib.Path.cwd().parents):
        candidate = base / ".github" / "workflows"
        if candidate.is_dir():
            return candidate
    return None


def main() -> int:
    wdir = workflow_dir()
    if wdir is None:
        print("FAIL  no .github/workflows found from "
              f"{pathlib.Path.cwd()}; refusing to report clean")
        return 1
    workflows = sorted(wdir.glob("*.yml")) + sorted(wdir.glob("*.yaml"))
    problems: list[str] = []
    steps_seen = 0
    for wf in workflows:
        steps_seen += len(_steps(wf.read_text().split("\n")))
        problems.extend(check_workflow(wf))
    if problems:
        print(f"FAIL  {len(problems)} undeclared workflow credential(s)")
        for p in problems:
            print(f"      {p}")
        return 1
    print(f"      workflow credentials declared "
          f"({steps_seen} steps across {len(workflows)} workflow(s))")
    return 0


if __name__ == "__main__":
    sys.exit(main())
