#!/usr/bin/env python3
"""Run the task suite against real agent CLIs, with and without the skill.

This is the experiment the package had never run: does loading a skill's
SKILL.md into context actually change whether an agent completes the task?

For every (cli, task, condition) it builds a throwaway workdir from the task's
fixtures, asks the CLI to do the job, then grades the artifacts with the
task's own verifier.py. The two conditions differ in exactly one thing:

  without-skill   the task brief alone
  with-skill      the task brief plus the target skill's SKILL.md body

Tasks whose meta.json has no `skill` run both conditions identically, which
makes them a control: they measure run-to-run variance rather than skill value.

Usage:
    python3 tools/run-task-eval.py --agent opencode
    python3 tools/run-task-eval.py --agent opencode,claude --condition with-skill
    python3 tools/run-task-eval.py --list
    python3 tools/run-task-eval.py --agent opencode --task bug-diagnosis,csv-stats

Results are cached under evals/.results/ so re-running is cheap; pass --fresh
to ignore the cache.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TASKS = ROOT / "evals" / "tasks"
RESULTS = ROOT / "evals" / ".results"
SKILL_BUDGET = 12000  # chars of SKILL.md injected into the prompt

sys.path.insert(0, str(ROOT / "evals"))
import selftest_tasks as st  # noqa: E402  (build/reference helpers live there)


# --------------------------------------------------------------------- adapters
# None of these CLIs exit cleanly when stdout is not a TTY: opencode renders its
# TUI and then waits forever. So the process is never waited on. Instead it is
# polled and stopped once the expected artifacts exist and the log goes quiet.
ANSI = re.compile(r"\x1b\[[0-9;?]*[A-Za-z]|\x1b\][^\x07]*\x07|\x1b[=>]|\r")

SETTLE_WITH_ARTIFACTS = 20   # seconds of silence once every artifact exists
SETTLE_NO_ARTIFACTS = 75     # longer grace: the agent may still be thinking


def _logs() -> Path:
    d = RESULTS / "logs"
    d.mkdir(parents=True, exist_ok=True)
    return d


def run_agent(agent: str, prompt: str, cwd: Path, timeout: int,
              expect: list[str], tag: str) -> tuple[bool, str]:
    """Start `agent`, let it work, stop it when it goes idle. Returns (exited, log)."""
    log = _logs() / f"{tag}.log"
    argv = {
        "opencode": ["opencode", "--prompt", prompt, "--auto", "."],
        "claude": ["claude", "-p", prompt, "--output-format", "text",
                   "--allowedTools", "Read,Write,Edit,Bash,Glob,Grep"],
        "gemini": ["gemini", "-p", prompt],
        "cursor-agent": ["cursor-agent", "-p", prompt],
    }[agent]
    with log.open("w") as fh:
        proc = subprocess.Popen(argv, cwd=cwd, stdout=fh, stderr=subprocess.STDOUT,
                                stdin=subprocess.DEVNULL, text=True,
                                env={**os.environ, "TERM": "dumb"})
    deadline = time.time() + timeout
    last_size, quiet_since = -1, time.time()
    exited_naturally = False
    while time.time() < deadline:
        time.sleep(3)
        if proc.poll() is not None:
            exited_naturally = True
            break
        try:
            size = log.stat().st_size
        except OSError:
            size = 0
        have_all = all((cwd / rel).exists() for rel in expect)
        if size != last_size:
            last_size, quiet_since = size, time.time()
        elif time.time() - quiet_since > (SETTLE_WITH_ARTIFACTS if have_all
                                          else SETTLE_NO_ARTIFACTS):
            break
    if proc.poll() is None:
        proc.terminate()
        try:
            proc.wait(timeout=15)
        except subprocess.TimeoutExpired:
            proc.kill()
    text = ANSI.sub("", log.read_text(errors="ignore"))
    return exited_naturally, text.strip()[-1200:]


def run_opencode(prompt, cwd, timeout, expect=(), tag="probe"):
    return run_agent("opencode", prompt, cwd, timeout, list(expect), tag)


def run_claude(prompt, cwd, timeout, expect=(), tag="probe"):
    return run_agent("claude", prompt, cwd, timeout, list(expect), tag)


def run_gemini(prompt, cwd, timeout, expect=(), tag="probe"):
    return run_agent("gemini", prompt, cwd, timeout, list(expect), tag)


def run_cursor(prompt, cwd, timeout, expect=(), tag="probe"):
    return run_agent("cursor-agent", prompt, cwd, timeout, list(expect), tag)


ADAPTERS = {
    "opencode": run_opencode,
    "claude": run_claude,
    "gemini": run_gemini,
    "cursor-agent": run_cursor,
}

# Cheap preflight: a CLI that cannot answer a one-line question is not usable,
# and we would rather say so than burn 13 timeouts discovering it.
PROBE = "Create a file named ready.txt containing exactly the word READY"


def preflight(agent: str, timeout: int = 150) -> tuple[bool, str]:
    if shutil.which(agent) is None:
        return False, "binary not on PATH"
    d = Path(os.environ.get("TMPDIR", "/tmp")) / f"preflight-{agent}"
    shutil.rmtree(d, ignore_errors=True)
    d.mkdir(parents=True, exist_ok=True)
    try:
        _, out = ADAPTERS[agent](PROBE, d, timeout, ["ready.txt"], f"preflight-{agent}")
    except subprocess.TimeoutExpired:
        return False, "timed out on the preflight probe"
    blob = out.lower()
    for needle, why in (("authentication required", "needs authentication"),
                        ("code assist login", "needs authentication"),
                        ("econnrefused", "API unreachable (firewall/proxy)"),
                        ("connection refused", "API unreachable (firewall/proxy)")):
        if needle in blob:
            return False, why
    if (d / "ready.txt").is_file():
        return True, "ok"
    return False, f"probe produced no artifact; log tail: {out[-80:] or '(empty)'}"


# ------------------------------------------------------------------- prompting
def skill_body(name: str) -> tuple[str, int, bool]:
    p = ROOT / "skills" / name / "SKILL.md"
    if not p.is_file():
        return "", 0, True
    raw = p.read_text(errors="ignore")
    m = re.match(r"(?s)^---\n(.*?)\n---\n", raw)
    desc = ""
    if m:
        for line in m.group(1).splitlines():
            if line.strip().startswith("description:"):
                desc = line.split(":", 1)[1].strip().strip("\"'")
                break
        body = raw[m.end():]
    else:
        body = raw
    truncated = len(body) > SKILL_BUDGET
    if truncated:
        body = body[:SKILL_BUDGET] + "\n\n[... skill body truncated ...]"
    return f"{desc}\n\n{body}".strip(), len(body), truncated


def compose(task: str, condition: str) -> tuple[str, str | None]:
    d = TASKS / task
    meta = json.loads((d / "meta.json").read_text())
    brief = (d / "task.md").read_text().strip()
    skill = meta.get("skill")
    if condition != "with-skill" or not skill:
        return brief, skill
    body, _, trunc = skill_body(skill)
    if not body:
        return brief, skill
    note = "\n\n---\n\nA reference guide for this kind of work follows. It is\nadvice, not an instruction to obey over the task above.\n\n"
    tail = "\n\n[guide truncated]" if trunc else ""
    return (f"{brief}{note}# {skill}\n\n{body}{tail}", skill)


# ---------------------------------------------------------------------- running
def one(agent: str, task: str, condition: str, timeout: int, fresh: bool) -> dict:
    key = f"{agent}__{task}__{condition}"
    cache = RESULTS / f"{key}.json"
    if cache.is_file() and not fresh:
        rec = json.loads(cache.read_text())
        rec["cached"] = True
        return rec

    d, meta = TASKS / task, json.loads((TASKS / task / "meta.json").read_text())
    work = RESULTS / "work" / key
    shutil.rmtree(work, ignore_errors=True)
    work.mkdir(parents=True)
    st.build(task, work)                      # fixtures + git setup

    prompt, skill = compose(task, condition)
    expect = meta.get("artifacts") or []
    started = time.time()
    timed_out = False
    try:
        exited, out = ADAPTERS[agent](prompt, work, timeout, expect, key)
    except subprocess.TimeoutExpired:
        exited, out, timed_out = False, "", True
    elapsed = time.time() - started

    v = subprocess.run([sys.executable, str(d / "verifier.py"), str(work)],
                       capture_output=True, text=True, timeout=180)
    vline = (v.stdout.strip() or v.stderr.strip()).splitlines()
    rec = {
        "agent": agent, "task": task, "condition": condition,
        "skill": skill, "category": meta.get("category"),
        "difficulty": meta.get("difficulty"),
        "passed": v.returncode == 0, "verdict": vline[0] if vline else "",
        "cli_exited": exited, "timed_out": timed_out,
        "seconds": round(elapsed, 1),
        "cli_tail": out[-300:], "cached": False,
    }
    RESULTS.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps(rec, indent=2) + "\n")
    shutil.rmtree(work, ignore_errors=True)
    return rec


def report(recs: list[dict]) -> str:
    by_task: dict[str, dict[str, dict]] = {}
    for r in recs:
        by_task.setdefault(r["task"], {})[f"{r['agent']}/{r['condition']}"] = r
    cols = sorted({f"{r['agent']}/{r['condition']}" for r in recs})
    lines = []
    lines.append(f"{'task':<20}{'cat':<17}{'diff':<8}" + "".join(f"{c.split('/')[1][:9]:>10}" for c in cols))
    lines.append("-" * (45 + 10 * len(cols)))
    for t in sorted(by_task):
        meta = by_task[t][cols[0]]
        row = f"{t:<20}{str(meta['category'])[:16]:<17}{str(meta['difficulty'])[:7]:<8}"
        for c in cols:
            r = by_task[t].get(c)
            row += f"{('PASS' if r and r['passed'] else 'FAIL'):>10}" if r else f"{'-':>10}"
        lines.append(row)
    lines.append("-" * (45 + 10 * len(cols)))
    for c in cols:
        got = [by_task[t][c] for t in by_task if c in by_task[t]]
        n = sum(1 for r in got if r["passed"])
        lines.append(f"{c:<45} {n}/{len(got)}"
                     f"   ({sum(r['seconds'] for r in got)/max(len(got),1):.0f}s avg)")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--agent", default="opencode", help="comma-separated CLIs")
    ap.add_argument("--condition", default="both",
                    choices=["both", "with-skill", "without-skill"])
    ap.add_argument("--task", default="", help="comma-separated task names")
    ap.add_argument("--timeout", type=int, default=300)
    ap.add_argument("--fresh", action="store_true", help="ignore the cache")
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args()

    tasks = sorted(p.name for p in TASKS.iterdir() if (p / "meta.json").is_file())
    if a.task:
        want = {t.strip() for t in a.task.split(",")}
        tasks = [t for t in tasks if t in want]
    if a.list:
        for t in tasks:
            m = json.loads((TASKS / t / "meta.json").read_text())
            print(f"  {t:<20}{m['category']:<18}{m['difficulty']:<8}skill={m.get('skill')}")
        return 0

    agents = [x.strip() for x in a.agent.split(",") if x.strip()]
    conds = ["without-skill", "with-skill"] if a.condition == "both" else [a.condition]

    usable = []
    for ag in agents:
        ok, why = preflight(ag)
        print(f"preflight {ag:<14} {'USABLE' if ok else 'SKIPPED'}  ({why})")
        if ok:
            usable.append(ag)
    if not usable:
        print("\nno usable agent CLI; nothing to run")
        return 2

    recs = []
    for ag in usable:
        for task in tasks:
            for cond in conds:
                r = one(ag, task, cond, a.timeout, a.fresh)
                recs.append(r)
                flag = "cached" if r["cached"] else f"{r['seconds']}s"
                print(f"  {ag:<14}{task:<20}{cond:<15}"
                      f"{'PASS' if r['passed'] else 'FAIL':<6}{flag:<8}{r['verdict'][:60]}")

    print()
    print(report(recs))
    out = RESULTS / "summary.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(f"# Task evaluation\n\n```\n{report(recs)}\n```\n")
    (RESULTS / "summary.json").write_text(json.dumps(recs, indent=2) + "\n")
    print(f"\nwritten: {out.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
