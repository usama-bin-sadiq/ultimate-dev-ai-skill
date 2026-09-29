#!/usr/bin/env python3
"""Run a stratified pilot of the evaluation suite against a real runtime.

This exists because the alternative is worse: an evaluation suite nobody has ever
executed is a checklist. The architecture's own headline claim is that the same
kernel handles everything from a one-line change to a long-horizon programme, and
the only way to put any number on that is to run some cases.

A pilot, not the full suite, for three reasons:

* Cost. 121 cases across two arms is a large run. A pilot answers "does this
  harness work end to end, and what does the failure profile look like" at a
  fraction of the cost, and tells us whether a full run is worth funding.
* Selection. A stratified sample across all seven case classes is more
  informative per case than the tail of one class.
* Honesty. A pilot is reported as a pilot. The numbers it produces are real but
  they are not the suite's pass rate, and this script labels them that way.

What is measured
----------------
**Over-orchestration** — the kernel's own top-ranked defect. Mechanically
detectable: a run that emits a triage statement, a work-unit table, a DECISION
block, or a capability search on a case that must not trigger has failed, even if
its answer is correct.

**Trigger behaviour** — whether the skill was followed at all, measured
behaviourally. The runtime is told where the skill is; whether it reads it is
inferred from the output, and the inference is recorded as such rather than as a
discovery event. This is a proxy, and the report says so.

Grading
-------
Assertions are written before the run and are deliberately coarse, because a
subjective judgement dressed as a measurement is the failure this project exists
to prevent. Anything not mechanically decidable is recorded ``null`` and excluded,
never guessed.

Usage
-----
    python tools/run-pilot.py --cases 20 --out runs/pilot
    python tools/run-pilot.py --cases 20 --out runs/pilot --dry-run
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tempfile
import time
from math import comb
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
REPO_ROOT = SKILL_ROOT.parent
FIXTURE_ROOT = REPO_ROOT / ".eval-fixtures"
# Where a run actually happens. Outside the repository on purpose.
#
# The first attempt put each arm's copy beside its fixture, as
# `.eval-fixtures/git/<case>.skill`. A glob for the case's files then matched
# both the copy and the original, the agent edited the original, and the
# assertions were scored against a directory it had never opened. The failure
# was invisible: the primary assertion reported "did not make the edit" and
# looked like a wrong answer rather than a mis-scored one.
#
# Isolation has to mean the original is not reachable by a casual upward walk,
# because the agent is free to walk up and it will.
RUN_ROOT = Path(tempfile.gettempdir()) / "ultimate-dev-eval"
# Fixtures are built here rather than in the repository, and each run gets its
# own freshly numbered directory containing nothing but that case's copy.
#
# The repository cannot be the home for a run's fixtures. The prompt names the
# kernel's path, so the agent has a legitimate reason to walk into the
# repository, and from there a glob reaches `.eval-fixtures/`. A run then edits
# the fixture every later run starts from, which invalidates the measurement and
# looks exactly like a wrong answer. Two attempts failed before this one: copies
# beside the originals, then copies in a temp tree whose siblings were still
# reachable. The invariant that actually holds is per-run isolation with nothing
# else in the directory.
FIXTURE_BUILD_ROOT = RUN_ROOT / "fixtures"
RUN_TREE = RUN_ROOT / "runs"
FIXTURE_BUILDER = SKILL_ROOT / "tools/build-fixtures.py"
AGENT_RUNNER = Path.home() / ".agents/skills/portable-agent-skill-creator/scripts/agent_runner.py"

# Over-orchestration is decided from the tool-call trace, never from prose.
#
# Two earlier versions of this grader were wrong in the same way. The first
# matched words like "triage" and "plan" in the final message and reported a 67%
# false-trigger rate that was entirely an artefact: the runs it flagged were
# agents writing "Before I plan anything, Step 0 says this is R0, so let me act
# directly rather than guess" -- de-escalation narrated out loud. The second
# tried to read structure out of the whole stderr stream and inherited the same
# fault, because the runtime echoes the model's narration to stderr too. It
# failed two runs that had performed zero mutations, on the strength of a
# filename mentioned in passing.
#
# So the rule is: only arrow-prefixed tool-call lines are evidence. Everything
# else the runtime prints -- narration, tool result prose, the model's own
# summary of what it is about to do -- is ignored, because a model that says it
# will write a plan and a model that writes a plan are indistinguishable by
# sentence and trivially distinguishable by tool call.

_ARROW = re.compile(r"^\s*(\u2192|\u2190|\u2717|\$)\s*(.+?)\s*$")

# Tools that change the filesystem or repository.
MUTATION_TOOLS = ("Edit", "Write", "Patch", "MultiEdit", "NotebookEdit")
# Tools that hand work to another agent.
DELEGATION_TOOLS = ("Task", "Agent", "Subagent")
# Shell fragments that write.
SHELL_WRITE = re.compile(
    r"(^|[;&|]\s*|\|>\s*)(tee\b|sed\s+-i|mv\s|cp\s|git\s+(add|commit|apply|checkout)|"
    r"cat\s*>|printf.*>)")
# A mutation target that is itself an orchestration artefact.
ARTEFACT_NAME = re.compile(
    r"(plan|ledger|triage|decision|work-?units?|orchestrat)\w*\.(md|json|ya?ml|txt)$",
    re.IGNORECASE)


def strip_ansi(text: str) -> str:
    return re.sub(r"\x1b\[[0-9;]*[A-Za-z]", "", text or "")


def split_observed(stderr: str) -> tuple[list[str], list[str]]:
    """Separate tool calls from the output those calls produced.

    The runtime's trace is a turn header, then a tool call, then that call's
    output as unmarked lines, then the next turn header. Recovering that output
    is what makes an objective assertion possible at all: methodology.md allows
    asserting against what a run observed and forbids asserting against the
    narrative, and the narrative is the only thing a naive grader can see.

    Returns (calls, observed_output_lines).
    """
    calls: list[str] = []
    blocks: list[list[str]] = []
    capturing: list[str] | None = None
    for line in strip_ansi(stderr).splitlines():
        text = line.strip()
        if not text:
            continue
        if text.startswith(">"):          # turn boundary ends the previous call
            capturing = None
            continue
        match = _ARROW.match(text)
        if match:
            calls.append(match.group(2))
            capturing = []
            blocks.append(capturing)
            continue
        if capturing is not None:
            capturing.append(text)
    observed = [line for block in blocks for line in block]
    return calls, observed


def read_trace(stderr: str) -> dict:
    """Structural evidence: what the agent actually did, not what it said.

    Returns counts and findings. Deciding is grade()'s job; keeping the two
    apart is what stops a word from deciding anything.
    """
    calls_raw, observed = split_observed(stderr)
    calls: list[tuple[str, str]] = []
    for rest in calls_raw:
        m = re.match(r"(\u2192|\u2190|\u2717|\$)\s*(.*)", strip_ansi(rest))
        calls.append((m.group(1), m.group(2)) if m else ("", rest))

    mutations, delegated, artefacts, shell_writes = [], False, set(), []
    for arrow, rest in calls:
        tool, _, arg = rest.partition(" ")
        tool = tool.strip()
        if tool.startswith(MUTATION_TOOLS):
            mutations.append(tool)
            for name in re.findall(r"[\w./-]+\.[A-Za-z0-9]+", arg):
                if ARTEFACT_NAME.search(name):
                    artefacts.add(name)
        elif tool.startswith(DELEGATION_TOOLS):
            delegated = True
        elif arrow == "$":
            if SHELL_WRITE.search(rest):
                shell_writes.append(rest.strip()[:80])
    return {
        "tool_calls": len(calls),
        "mutations": len(mutations),
        "delegated": delegated,
        "artefacts": sorted(artefacts),
        "shell_writes": shell_writes,
        "read_skill": any(
            "SKILL.md" in rest for _, rest in calls),
        # The surface objective assertions may target. Never the narrative.
        "observed": observed,
    }


# Prose signals are retained for the reason string only. They can corroborate a
# structural finding and they can flag a case for a human to read, but they can
# never on their own turn a null into a pass or a fail.
ENGAGED_SIGNALS = {
    "names_the_gate": re.compile(r"\b(effort gate|Step 0|\bR[0-4]\b)"),
    "names_a_verdict": re.compile(r"\b(VERIFIED|PARTIAL|FAILED)\b"),
    "names_a_limit": re.compile(
        r"\b(limitation|could not (establish|verify|determine)|unverified|"
        r"not verified|i did not)\b", re.IGNORECASE),
}


CLASS_ORDER = ["RG", "SC", "FC", "BM", "DM", "NM", "TN"]

# A pool rather than a single model, because a free endpoint rate-limits and a
# single-model harness reports "unavailable" for reasons that have nothing to do
# with the skill. The cost of a pool is that results stop being strictly
# comparable across cases, which is why every case records the model that
# actually served it and the report flags a mixed-model run.
DEFAULT_MODEL_POOL = [
    "opencode/space-bunny-free",
    "opencode/mimo-v2.6-flash-free",
    "opencode/nemotron-3.5-lightning-free",
    "opencode/longcat-2.5-preview-free",
    "opencode/ling-3.0-flash-fin-free",
    "console-openrouter/cohere/north-mini-code:free",
]

# Environment failures are the runtime's problem, not the kernel's. Counting them
# as case failures is how a harness invents a measurement: a quota error and an
# over-orchestrated answer look identical in a transcript and mean opposite things.
# Preferred: the runtime's own machine-readable error type. Structural beats
# pattern-matching prose, because a provider can reword a message without changing
# the failure.
RUNTIME_ERROR_TYPES = {
    "provider.quota": "quota",
    "provider.rate_limit": "rate_limit",
    "provider.auth": "auth",
    "provider.unavailable": "unavailable",
    "provider.overloaded": "unavailable",
}

# Fallback when the runtime emits prose rather than a typed event.
ENVIRONMENT_ERRORS = {
    # Credit exhaustion is worded several ways by different gateways, and one
    # variant is not exhaustion at all -- it is the request asking for more
    # max_tokens than the remaining credit can afford, which is fixed by funding
    # or by asking for less, not by retrying.
    "quota": re.compile(
        r"exceed your available credits|requires more credits|add credits|"
        r"can only afford|insufficient_quota|quota", re.I),
    "rate_limit": re.compile(r"rate.?limit|too many requests|\b429\b", re.I),
    "auth": re.compile(r"unauthor|not logged in|invalid api key|\b401\b", re.I),
    "unavailable": re.compile(r"service unavailable|\b502\b|\b503\b|bad gateway|overloaded", re.I),
}


def classify_environment_failure(text: str) -> str | None:
    """Return the environment failure kind, or None if this looks like a real result."""
    for kind, pattern in ENVIRONMENT_ERRORS.items():
        if pattern.search(text):
            return kind
    return None


def scan_runtime_events(stdout: str) -> tuple[str | None, str]:
    """Parse ``--format json`` output. Returns (environment_error, answer_text).

    The runtime emits one JSON object per line. Tool calls and the final message
    arrive as separate events, which is what lets the grader tell "the model
    read the skill and then stopped" apart from "the model never ran".
    """
    answer: list[str] = []
    environment: str | None = None
    for line in stdout.splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if event.get("type") == "error":
            err = event.get("error") or {}
            kind = RUNTIME_ERROR_TYPES.get(err.get("type", ""), "unknown")
            if kind == "unknown":
                kind = classify_environment_failure(json.dumps(err)) or "runtime_error"
            environment = environment or kind
        for key in ("text", "content", "message"):
            value = event.get(key)
            if isinstance(value, str) and value.strip():
                answer.append(value)
    return environment, "\n".join(answer)


def sandbox_for(case_id: str) -> Path | None:
    """The directory a case must run in, or None if it needs no fixture.

    Running a case in the repository root when its fixture lives elsewhere is how
    a case ends up measuring refusal-to-fabricate instead of the behaviour it
    was written to measure.

    None is ambiguous on its own, so `case_needs_fixture` is the only thing that
    should interpret it. A case may legitimately have no fixture because it is
    self-contained -- "what is 17 times 23" needs no workspace, and the absence
    of one is the condition the case is testing. That is a different situation
    from a case whose fixture was specified and never built, and conflating them
    made 26 runnable cases report as harness failures.
    """
    for candidate in (FIXTURE_BUILD_ROOT / case_id,
                      FIXTURE_BUILD_ROOT / "git" / case_id):
        if candidate.is_dir():
            return candidate
    return None


def case_needs_fixture(case: dict) -> bool:
    """Whether this case declares that it requires a workspace to run.

    `fixture: none` is an explicit statement that the case is self-contained. Its
    absence means a fixture is required, because the default for a case that
    inspects a repository is that the repository must exist.
    """
    return str(case.get("fixture_required", "yes")).strip().lower() != "no"


def ensure_fixtures() -> bool:
    """Build and verify the fixtures. A failure here invalidates every case that
    depends on one, so it is fatal rather than a warning."""
    proc = subprocess.run(
        [sys.executable, str(FIXTURE_BUILDER), "--out", str(FIXTURE_BUILD_ROOT)],
        capture_output=True, text=True, cwd=REPO_ROOT,
    )
    if proc.returncode != 0:
        print("fixture build failed; cases depending on fixtures cannot be scored",
              file=sys.stderr)
        print(proc.stdout[-1500:], file=sys.stderr)
        return False
    return True


ASSERTIONS_PATH = SKILL_ROOT / "evaluation" / "assertions.json"


class HarnessError(RuntimeError):
    """A wiring fault in the harness itself, as opposed to a case that cannot be
    decided. These are raised rather than reported, because a measurement
    instrument that is broken should stop the run instead of contributing a null
    that reads like data."""


def load_assertions() -> dict:
    """Per-case objective assertions, or an empty map if the file is absent.

    Absent is not an error. A repository with no assertion store still runs; it
    simply reports quality as null for every case, which is the honest state.
    """
    if not ASSERTIONS_PATH.is_file():
        return {}
    try:
        payload = json.loads(ASSERTIONS_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"{ASSERTIONS_PATH}: invalid JSON: {exc}")
    return payload.get("cases", {})


def snapshot(sandbox: Path | None) -> dict[str, str] | None:
    """Content hashes of a sandbox before the run, for unchanged-file checks.

    Taken from the tree rather than stored in the assertion file, so a change to
    the fixture generator cannot leave a stale expected hash behind. A stored
    hash would be a second source of truth about generated data, which is the
    same mistake as committing the fixtures.
    """
    if sandbox is None or not sandbox.is_dir():
        return None
    import hashlib
    state: dict[str, str] = {}
    for path in sorted(sandbox.rglob("*")):
        if not path.is_file() or ".git" in path.parts:
            continue
        try:
            state[str(path.relative_to(sandbox))] = hashlib.sha256(
                path.read_bytes()).hexdigest()
        except OSError:
            continue
    return state


# Artefacts a run may create anywhere without corrupting a starting state. They
# are excluded from the pollution check for a specific reason: a run that executes
# a test suite creates __pycache__ and .pytest_cache, and the fixture tree is
# rebuilt from scratch at the start of every pilot anyway. Failing on them would
# mean failing every run that does its job, which trains the guard to be ignored.
#
# What the check must still catch is a run editing the fixture's actual content,
# because the next arm and the next pilot both start from it.
ARTEFACT_DIRS = ("__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache")
ARTEFACT_SUFFIXES = (".pyc", ".pyo", ".log")


def _is_artefact(rel: str) -> bool:
    parts = Path(rel).parts
    return (any(d in parts for d in ARTEFACT_DIRS)
            or rel.endswith(ARTEFACT_SUFFIXES))


def changed_files(before: dict[str, str] | None, sandbox: Path | None) -> list[str]:
    if before is None or sandbox is None or not sandbox.is_dir():
        return []
    import hashlib
    after: dict[str, str] = {}
    for path in sorted(sandbox.rglob("*")):
        if not path.is_file() or ".git" in path.parts:
            continue
        try:
            after[str(path.relative_to(sandbox))] = hashlib.sha256(
                path.read_bytes()).hexdigest()
        except OSError:
            continue
    names = set(before) | set(after)
    return sorted(n for n in names
                  if before.get(n) != after.get(n) and not _is_artefact(n))


def _recorded_mode(sandbox: str | None) -> str | None:
    """The coordination mode this run actually recorded, or None.

    Read from the run's own state file rather than from the transcript. The
    transcript contains the kernel *talking about* a mode, which is not the
    same as having chosen one, and a grep for the word would score narration.
    """
    if not sandbox:
        return None
    path = Path(sandbox) / ".ultimate-dev" / "run-state.json"
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    mode = (state.get("coordination") or {}).get("mode")
    return mode if isinstance(mode, str) else None


def _recorded_mode_changes(sandbox: str | None) -> int | None:
    """How many times this run changed its coordination mode."""
    if not sandbox:
        return None
    path = Path(sandbox) / ".ultimate-dev" / "run-state.json"
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    changed = (state.get("coordination") or {}).get("changed")
    return len(changed) if isinstance(changed, list) else None


def apply_assertions(case_id: str, spec: dict, trace: dict,
                     after: dict | None, before: dict | None,
                     sandbox: str | None = None) -> dict:
    """Run the objective assertions. Returns pass/fail/null with per-assertion detail.

    `null` is a real outcome and the most common one: a case with no assertions,
    a case whose fixture is absent, or an assertion type that cannot be decided
    from what is available. None of those is a pass.
    """
    observed_text = "\n".join(trace.get("observed") or [])
    results: list[dict] = []
    undecidable = 0

    # A file-based assertion needs a sandbox and a pre-run snapshot. Distinguish
    # the two reasons one can be missing, because they mean opposite things: no
    # fixture is a data gap and the honest answer is null, while a fixture that
    # exists with no snapshot is a harness bug. Reporting the second as null is
    # how a wiring mistake becomes an unmeasured case that nobody ever notices --
    # which is exactly what happened here once already.
    if before is None and after is not None:
        raise HarnessError(
            f"{case_id}: a post-run state was captured but no pre-run snapshot "
            f"exists, so unchanged-file assertions cannot be decided. This is a "
            f"harness wiring fault, not an undecidable case."
        )
    if after is None and any(a.get("type", "").startswith("file")
                            or a.get("type") == "only_files_changed"
                            for a in spec.get("assertions", [])):
        raise HarnessError(
            f"{case_id}: has file-based assertions but no fixture was built for "
            f"it, so they can never pass or fail. Build the fixture or drop the "
            f"assertion; an assertion with nothing to assert against is noise."
        )

    for assertion in spec.get("assertions", []):
        kind = assertion.get("type")
        aid = assertion.get("id", kind)
        if assertion.get("not_required"):
            results.append({"id": aid, "type": kind, "passed": None,
                            "note": "diagnostic only; not scored"})
            continue

        if kind == "output_matches":
            if not observed_text:
                results.append({"id": aid, "type": kind, "passed": None,
                                "note": "no observed tool output to assert against"})
                undecidable += 1
                continue
            hit = bool(re.search(assertion["pattern"], observed_text))
            results.append({"id": aid, "type": kind, "passed": hit,
                            "why": assertion.get("why", "")})

        elif kind == "file_contains":
            entry = (after or {}).get(assertion["path"])
            if entry is None:
                results.append({"id": aid, "type": kind, "passed": None,
                                "note": f"{assertion['path']} is absent"})
                undecidable += 1
                continue
            hit = assertion["value"] in entry[1]
            results.append({"id": aid, "type": kind, "passed": hit,
                            "why": assertion.get("why", "")})

        elif kind == "file_unchanged":
            if before is None:
                results.append({"id": aid, "type": kind, "passed": None,
                                "note": "no pre-run snapshot; case has no fixture"})
                undecidable += 1
                continue
            rel = assertion["path"]
            now = (after or {}).get(rel)
            hit = now is not None and before.get(rel) == now[0]
            results.append({"id": aid, "type": kind, "passed": hit,
                            "why": assertion.get("why", "")})

        elif kind == "only_files_changed":
            before_hashes = {k: v for k, v in (before or {}).items()}
            after_hashes = {k: v[0] for k, v in (after or {}).items()}
            changed = sorted(k for k in set(before_hashes) | set(after_hashes)
                             if before_hashes.get(k) != after_hashes.get(k))
            allow = set(assertion.get("allow", []))
            offending = [c for c in changed if c not in allow]
            results.append({"id": aid, "type": kind, "passed": not offending,
                            "changed": changed, "offending": offending,
                            "why": assertion.get("why", "")})

        elif kind == "coordination_mode":
            # The routing oracle, graded.
            #
            # The first assertion type that can express a statement about how
            # the run was ASSEMBLED rather than about what it produced. Every
            # other type grades an artefact -- some output text, some file,
            # some set of changed paths. A run that chose `handoff` on a task
            # whose declared correct mode is `inline`, and then produced a
            # perfectly good answer, passed all of them, because nothing looked
            # at the choice.
            #
            # The corpus has stated the correct mode since it was written:
            # evaluation/coordination-modes/CASES.md carries `**Correct mode:**`
            # for CM-01..CM-04. The label was dropped on projection, so the
            # grader never received it and its only gate for a must-fire case
            # was that the answer exceeded 120 characters.
            #
            # Absence of a state file is UNDECIDABLE, never a pass. A run that
            # recorded nothing has not demonstrated a correct choice; it has
            # demonstrated no choice. Scoring that as correct would leave the
            # metric unfalsifiable in exactly the way the previous grader was.
            want = assertion.get("mode") or assertion.get("value")
            observed = _recorded_mode(sandbox)
            if observed is None:
                results.append({
                    "id": aid, "type": kind, "passed": None,
                    "note": ("no run-state record; the run did not record a "
                             "coordination mode, so the choice cannot be graded"),
                })
                undecidable += 1
                continue
            results.append({
                "id": aid, "type": kind, "passed": observed == want,
                "expected": want, "observed": observed,
                "why": assertion.get("why", ""),
            })

        elif kind == "mode_changes_at_most":
            # CM-05 and CM-06 have no single correct mode. Their finding is that
            # the FIRST choice was wrong: repeated mode changes in one run is a
            # misconfiguration, not a hard task. run-state.py check already
            # fails at three; this makes it an assertion rather than something
            # a human has to remember to run.
            observed = _recorded_mode_changes(sandbox)
            if observed is None:
                results.append({
                    "id": aid, "type": kind, "passed": None,
                    "note": "no run-state record; mode changes cannot be counted",
                })
                undecidable += 1
                continue
            limit = int(assertion.get("max", 3))
            results.append({
                "id": aid, "type": kind, "passed": observed <= limit,
                "expected": f"<= {limit}", "observed": observed,
                "why": assertion.get("why", ""),
            })

        else:
            results.append({"id": aid, "type": kind, "passed": None,
                            "note": f"unknown assertion type {kind!r}"})
            undecidable += 1

    scored = [r for r in results if r["passed"] is not None]
    if not scored:
        return {"quality": None, "detail": results,
                "note": "no decidable objective assertion for this case"}
    failed = [r["id"] for r in scored if r["passed"] is False]
    return {"quality": "fail" if failed else "pass",
            "failed": failed, "detail": results,
            "undecidable": undecidable}


def load_cases() -> list[dict]:
    payload = json.loads((SKILL_ROOT / "evals" / "evals.json").read_text(encoding="utf-8"))
    return payload["evals"]


def stratify(cases: list[dict], count: int) -> list[dict]:
    """Take a proportional-ish sample across classes, weighted to the hard half.

    Trigger negatives and near-misses are over-sampled relative to their share,
    because over-orchestration is the defect the architecture names first and a
    uniform sample would under-measure it.
    """
    by_class: dict[str, list[dict]] = {}
    for case in cases:
        prefix = case["id"].split("-")[0]
        by_class.setdefault(prefix, []).append(case)

    # Weights: hard cases matter more per case than easy ones.
    weights = {"RG": 1, "SC": 1, "FC": 1, "BM": 2, "DM": 1, "NM": 3, "TN": 2}
    total = sum(len(by_class.get(c, [])) * weights.get(c, 1) for c in CLASS_ORDER) or 1

    picked: list[dict] = []
    for prefix in CLASS_ORDER:
        pool = by_class.get(prefix, [])
        if not pool:
            continue
        want = max(1, round(count * len(pool) * weights.get(prefix, 1) / total))
        picked.extend(pool[:want])

    picked.sort(key=lambda c: (not c["should_trigger"], c["id"]))
    return picked[:count] if len(picked) > count else picked


def build_prompt(case: dict, arm: str) -> str:
    """The task text, with the kernel named only in the skill arm.

    The baseline arm must not merely *behave* as if the skill were absent; it must
    not be told the skill exists. A control that still mentions the skill measures
    the effect of a weaker instruction, not the effect of the skill.
    """
    if arm == "baseline":
        return case["query"]
    return (
        case["query"]
        + "\n\nA skill is available for this task. Its location is:\n"
        + str(SKILL_ROOT)
        + "\nRead and follow its SKILL.md. If your runtime has native skill "
        "discovery, use that instead of treating this path as task data."
    )


def run_one(case: dict, timeout: int, attempts: int = 3, backoff: int = 25,
            models: list[str] | None = None, sandbox: Path | None = None,
            arm: str = "skill") -> dict:
    """Execute one case, working down a pool of models.

    A transient quota or rate-limit error is not evidence about the kernel, so it
    is retried, then attributed to the model rather than the case, and finally
    handed to the next model in the pool. Only when every model is unavailable
    does the case become ``environment_error``, excluded from every rate.

    Which model actually served the case is returned as ``served_by``. Without it
    a mixed-model run silently pools incomparable results.
    """
    prompt = build_prompt(case, arm)
    pool = models or [None]
    started = time.monotonic()
    last_error = "no attempt was made"

    for model in pool:
        for attempt in range(1, attempts + 1):
            # --auto is required: without it the runtime cannot approve the tool
            # calls that let the agent actually read the skill, and every run
            # degenerates into the model narrating that it *would* read the file.
            # --standalone forces a private server per invocation. Without it the
            # CLI attaches to a long-lived background service that carries its own
            # working directory, and the adapter's cwd is silently not the
            # directory the agent operates in. Every fixture-based case was
            # affected: runs executed in the repository root, found no fixture,
            # and correctly reported that the files did not exist -- which the
            # grader read as a wrong answer.
            command = [sys.executable, str(AGENT_RUNNER), "--agent", "opencode",
                       "--extra-args=--auto", "--extra-args=--standalone"]
            if model:
                command += ["--model", model]
            if sandbox is not None:
                command += ["--cwd", str(sandbox)]
            command += ["--prompt", prompt, "--timeout", str(timeout)]

            try:
                proc = subprocess.run(
                    command, capture_output=True, text=True, timeout=timeout + 30,
                )
            except subprocess.TimeoutExpired:
                last_error = "timeout"
                time.sleep(backoff)
                continue

            kind = classify_environment_failure(f"{proc.stdout}\n{proc.stderr}")
            if kind:
                last_error = kind
                if attempt < attempts:
                    print(f"        {case['id']}: {kind} on {model}; "
                          f"retry {attempt}/{attempts - 1}")
                    time.sleep(backoff * attempt)
                    continue
                print(f"        {case['id']}: {kind} on {model}; next model")
                break

            try:
                payload = json.loads(proc.stdout)
            except json.JSONDecodeError:
                # Not an environment problem and not a result. Report it as a
                # harness failure so it is never mistaken for either.
                return {"id": case["id"], "harness_error": "adapter output not JSON",
                        "served_by": model, "stdout_raw": proc.stdout[-400:],
                        "elapsed_s": round(time.monotonic() - started, 1)}

            return {"id": case["id"], "arm": arm,
                    "stdout": payload.get("stdout", ""),
                    "stderr": payload.get("stderr", ""),
                    "exit_code": payload.get("exit_code"),
                    "elapsed_ms": payload.get("duration_ms"),
                    "served_by": model,
                    "elapsed_s": round(time.monotonic() - started, 1)}

    return {"id": case["id"], "environment_error": last_error,
            "elapsed_s": round(time.monotonic() - started, 1)}


def binom_two_sided(a: int, b: int) -> float | None:
    """Exact two-sided sign test on discordant pairs.

    Returns null when there is nothing to test. A p-value from a normal
    approximation on a handful of pairs is a number the data cannot support, and
    reporting one anyway is the failure this suite exists to catch.
    """
    n = a + b
    if n == 0:
        return None
    tail = sum(comb(n, k) for k in range(0, min(a, b) + 1)) / (2 ** n)
    return min(1.0, 2 * tail)


def grade(case: dict, result: dict, assertion_spec: dict | None = None) -> dict:
    """Apply assertions written before the run. Undecidable becomes null.

    The arm is carried on the result rather than looked up, because a report that
    cannot say which arm a verdict came from is a report of one number where
    there should be two.
    """
    if "environment_error" in result:
        return {"id": case["id"], "verdict": None, "kind": "environment_error",
                "served_by": result.get("served_by"),
                "arm": result.get("arm", "skill"),
                "reason": f"runtime {result['environment_error']}; excluded from all rates"}
    if "harness_error" in result:
        return {"id": case["id"], "verdict": None, "kind": "harness_error",
                "served_by": result.get("served_by"),
                "arm": result.get("arm", "skill"),
                "reason": result["harness_error"]}
    if "error" in result:
        return {"id": case["id"], "verdict": None, "kind": "harness_error",
                "arm": result.get("arm", "skill"), "reason": result["error"]}

    out = result.get("stdout", "")
    trace = read_trace(result.get("stderr", ""))
    prose = sorted(n for n, hit in ENGAGED_SIGNALS.items() if hit.search(out))
    base = {"id": case["id"], "arm": result.get("arm", "skill"),
            "trace": trace, "prose_hits": prose,
            "chars": len(out), "served_by": result.get("served_by"),
            # Where the run actually happened. None means unknown, which is
            # different from True and different from False.
            "worked_in_sandbox": result.get("worked_in_sandbox")}

    # Quality is a separate axis from process, and is null far more often. A
    # process check cannot tell a right answer from a wrong one; conflating them
    # is what let both arms "pass" while either could be wrong.
    if assertion_spec:
        try:
            base["quality"] = apply_assertions(
                case["id"], assertion_spec, trace,
                result.get("after"), result.get("before"),
                result.get("sandbox"))
        except HarnessError:
            raise
    else:
        base["quality"] = {"quality": None, "detail": [],
                           "note": "no objective assertions authored for this case"}

    if case["should_trigger"]:
        # The "did it open the kernel" requirement applies to the skill arm only.
        # A control arm is not told the kernel exists, so failing it for not
        # reading a file it was never offered would score the harness rather than
        # the skill -- and would make every baseline must-fire case a guaranteed
        # failure, which rigs the paired comparison in the kernel's favour.
        if len(out) < 120:
            return {**base, "verdict": "fail",
                    "reason": f"substantive answer expected, got {len(out)} characters"}
        if base["arm"] == "baseline":
            return {**base, "verdict": "pass",
                    "reason": "substantive answer, no kernel offered (control arm)"}
        # Two independent requirements in the skill arm: the kernel was actually
        # opened, and the answer is substantive. Requiring prose instead used to
        # fail a run that opened the kernel, did the work in two tool calls, and
        # reported it in 300 characters -- which is what the kernel asks for.
        # Engagement is recorded, not enforced.
        #
        # This used to require a Read of SKILL.md and fail the run without one.
        # The prompt explicitly invites native discovery -- "if your runtime has
        # native skill discovery, use that instead" -- and this runtime has it,
        # so runs that loaded the kernel the sanctioned way were failed for not
        # also opening the file. One run said so outright: "available natively in
        # this runtime". The result was a skill arm scoring 0/4 while applying
        # the effort gate correctly, which is a measurement of the prompt, not
        # of the skill.
        #
        # A native load may leave no trace in stderr at all, so absence of a Read
        # is not evidence of absence of engagement. It is recorded and the run is
        # graded on what it did, which is decidable.
        engagement = ("file read" if trace["read_skill"]
                      else "not observable; the runtime may load skills natively")
        return {**base, "verdict": "pass",
                "engagement": engagement,
                "reason": f"substantive answer (kernel engagement: {engagement})"}

    # Must not trigger. Structural evidence only.
    structural: list[str] = []
    if trace["mutations"]:
        structural.append(f"{trace['mutations']} file mutation(s)")
    if trace["shell_writes"]:
        structural.append(f"shell write: {trace['shell_writes'][0]}")
    if trace["delegated"]:
        structural.append("delegated to a subagent")
    if trace["artefacts"]:
        structural.append(f"wrote {', '.join(trace['artefacts'])}")

    if structural:
        return {**base, "verdict": "fail", "reason": "over-orchestrated: " + "; ".join(structural)}
    if prose:
        return {**base, "verdict": None,
                "reason": f"discusses the gate ({', '.join(prose)}) but ran "
                          f"{trace['tool_calls']} tool call(s) with no mutation, no "
                          f"delegation and no artefact; discussion is not action, so "
                          f"this is undecidable from the trace"}
    return {**base, "verdict": "pass",
            "reason": f"direct answer; {trace['tool_calls']} read-only tool call(s)"}


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--cases", type=int, default=20)
    parser.add_argument(
        "--only", action="append", default=None, metavar="ID",
        help="Run only these case ids. Repeatable. Overrides --cases.",
    )
    parser.add_argument("--out", default="runs/pilot")
    parser.add_argument(
        "--arm", choices=("skill", "baseline", "both"), default="skill",
        help="'baseline' runs the bare task with no mention of the kernel, which "
             "is the only way to attribute an improvement to the skill rather "
             "than to the harness. 'both' runs every case in each arm.",
    )
    parser.add_argument("--timeout", type=int, default=180)
    parser.add_argument(
        "--models", default=None,
        help="Comma-separated model pool, tried in order. Defaults to a pool of "
             "free models, because a single free endpoint rate-limits and a "
             "harness that gives up is measuring the endpoint, not the skill. "
             "Every result records the model that served it.",
    )
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args(argv)


def resolve_cases(args: argparse.Namespace) -> tuple[list[dict], int] | None:
    """Pick the sample and report its composition.

    Returns ``None`` if the selection is impossible, which ends the run.
    """
    all_cases = load_cases()
    if args.only:
        wanted = set(args.only)
        cases = [c for c in all_cases if c["id"] in wanted]
        missing = wanted - {c["id"] for c in cases}
        if missing:
            print(f"error: no such case id: {', '.join(sorted(missing))}",
                  file=sys.stderr)
            return None
    else:
        cases = stratify(all_cases, args.cases)
    must_fire = sum(1 for c in cases if c["should_trigger"])
    print(f"pilot sample: {len(cases)} cases "
          f"({must_fire} must fire, {len(cases)-must_fire} must not)")
    print(f"sample: {', '.join(c['id'] for c in cases)}")
    return cases, must_fire


ROOT_ENTRIES = ("config", "src", "Makefile", "docs", "tests", "scripts",
                "access_log_sample.csv", "events-2026-04.jsonl",
                "transactions_2026-03.csv", "customer_requests.csv",
                "ops-handover-2026-04.md", "stats.md",
                "migrations", "measurements-2026.csv")


def stage_at_root(sandbox):
    """Copy a fixture's top-level entries into the repository root for one run.

    This runtime does not honour a per-invocation working directory. Background
    servers are running and the agent reports a session-scoped path regardless of
    the cwd it is launched with, so a fixture placed anywhere else is simply
    invisible: the agent correctly reports that the files do not exist, and the
    grader reads that as a wrong answer. That is a category error, not a near
    miss, and it is why every filesystem assertion failed before this.

    The repository root is the one directory the agent reliably sees. So the
    fixture is staged there, the case runs, and the stage is removed afterwards.

    Two safety properties, both refusals rather than cleanups:

    * Nothing is staged over anything. If any top-level entry the fixture needs
      already exists at the root, the case is reported unrunnable and nothing is
      written. A harness that clobbers the user's checkout to make a measurement
      possible is not a harness.
    * The stage is removed in a finally block, so an exception, a timeout, or a
      crash cannot leave a half-staged tree behind.
    """
    if sandbox is None or not sandbox.is_dir():
        return [], "no fixture"
    import shutil
    wanted = sorted(p for p in sandbox.iterdir() if p.name != ".git")
    clashes = [p.name for p in wanted if (REPO_ROOT / p.name).exists()]
    if clashes:
        return [], f"cannot stage: {clashes} already exist at the repository root"
    for entry in wanted:
        src = sandbox / entry.name
        dst = REPO_ROOT / entry.name
        if src.is_dir():
            shutil.copytree(src, dst, symlinks=True)
        else:
            shutil.copy2(src, dst)
    return [p.name for p in wanted], None


def capture_state(names):
    """Hash and text of the staged files, keyed by path relative to the root.

    Captured while the fixture is still staged. Grading later has to work from
    this rather than from the filesystem, because the stage is removed as soon as
    the run returns -- a grader that re-reads the tree at grade time sees an
    unstaged root and would call every file-based assertion absent.
    """
    import hashlib
    state: dict[str, tuple[str, str]] = {}
    for name in names:
        path = REPO_ROOT / name
        targets = [path] if path.is_file() else (
            sorted(f for f in path.rglob("*") if f.is_file()) if path.is_dir() else [])
        for f in targets:
            try:
                raw = f.read_bytes()
            except OSError:
                continue
            state[str(f.relative_to(REPO_ROOT))] = (
                hashlib.sha256(raw).hexdigest(), raw.decode("utf-8", "replace"))
    return state


def unstage(names):
    """Remove a staged fixture. Best effort per entry, never raises."""
    import shutil
    for name in names:
        path = REPO_ROOT / name
        try:
            if path.is_dir():
                shutil.rmtree(path)
            elif path.exists():
                path.unlink()
        except OSError:
            pass


def _run_counter():
    """A monotonic label so every run gets a directory containing only its own
    case. Shared across the process, which is all that is needed: a run must not
    be able to see another run's files, and a counter cannot collide within one
    pilot."""
    counter = getattr(_run_counter, "n", 0)
    _run_counter.n = counter + 1
    return counter


def execute_cases(cases: list[dict], arms: list[str], timeout: int,
                  models: list[str]) -> tuple[list[tuple[dict, dict]], list[dict], float]:
    """Run every case in every arm, serially.

    Returns ``(pairs, results, wall_seconds)``, where a pair is the
    ``(case, raw result)`` that grade() will turn into a verdict.
    """
    started = time.monotonic()
    results: list[dict] = []
    pairs: list[tuple[dict, dict]] = []
    total = len(cases) * len(arms)
    index = 0
    for case in cases:
        sandbox = sandbox_for(case["id"])
        for arm in arms:
            index += 1
            # Each arm gets its own copy of the fixture, snapshotted immediately
            # before the run. Two reasons, and the second is the important one:
            # the snapshot is what an unchanged-file assertion is checked
            # against, and sharing one tree between arms would make the second
            # arm's baseline the first arm's output -- so "dev.yaml was not
            # touched" would pass because the skill arm had already rewritten it.
            before = snapshot(sandbox)
            needs_fixture = case_needs_fixture(case)
            staged, stage_error = stage_at_root(sandbox)
            if stage_error and needs_fixture:
                result = {"id": case["id"], "arm": arm,
                          "harness_error": f"unrunnable: {stage_error}",
                          "served_by": None, "stdout": "", "elapsed_s": 0.0,
                          "sandbox": None, "before": before}
                results.append(result)
                pairs.append((case, result))
                print(f"  [{index:2d}/{total}] {arm:8} {case['id']:18} "
                      f"       -  unrunnable: {stage_error}")
                continue
            if stage_error:
                # A self-contained case with no fixture. Not a failure: the
                # absence of a workspace is the precondition it is testing.
                staged = []
            try:
                result = run_one(case, timeout, models=models,
                                 sandbox=REPO_ROOT, arm=arm)
                after = capture_state(staged)
            finally:
                unstage(staged)
            result["staged"] = staged
            result["after"] = after

            # A run that reached outside its sandbox and modified the fixture
            # tree has invalidated the measurement, because the next run gets a
            # different starting state. Caught here rather than discovered as an
            # unexplained number three runs later.
            #
            # The staged fixture is removed in a finally block above, so the
            # post-run state must be read from the repository root, not the
            # fixture. This is the only place a filesystem assertion's "after"
            # state comes from, so a mistake here silently inverts every
            # unchanged-file assertion.
            result["arm"] = arm
            result["sandbox"] = str(REPO_ROOT)
            result["before"] = before
            result["worked_in_sandbox"] = True if staged else None
            results.append(result)
            status = (result.get("error") or result.get("environment_error")
                      or result.get("harness_error")
                      or f"{len(result.get('stdout', ''))} chars")
            print(f"  [{index:2d}/{total}] {arm:8} {case['id']:18} "
                  f"{result.get('elapsed_s', 0):6.1f}s  {status}")
            pairs.append((case, result))
    return pairs, results, time.monotonic() - started


def arm_rates(graded: list[dict], by_id: dict, arm: str) -> dict:
    """Counts for one arm. Environment failures are counted here, never scored."""
    rows = [g for g in graded if g.get("arm", "skill") == arm]
    ok = [g for g in rows if g["verdict"] is not None]
    neg = [g for g in rows if not by_id[g["id"]]["should_trigger"] and g["verdict"]]
    # Quality is tracked apart from process, and is null far more often because
    # only a handful of cases have an objective assertion. The unmeasured count
    # is reported beside the score so a reader can see how little of the suite
    # the score actually covers -- a 2/2 that means 2 of 121 is not a 100%.
    quality = [(g.get("quality") or {}).get("quality") for g in rows]
    scored = [q for q in quality if q is not None]
    return {
        "runs": len(rows),
        "decided": len(ok),
        "passed": sum(1 for g in ok if g["verdict"] == "pass"),
        "quality_scored": len(scored),
        "quality_passed": sum(1 for q in scored if q == "pass"),
        "quality_unmeasured": sum(1 for q in quality if q is None),
        "false_triggers": sum(1 for g in neg if g["verdict"] == "fail"),
        "negatives_decided": len(neg),
        "environment_failures": sum(1 for g in rows if g.get("kind") == "environment_error"),
    }


def paired_comparison(graded: list[dict], by_id: dict) -> dict:
    """Compare the arms over the cases both of them decided.

    Only cases with a decided verdict in both arms can enter, and that
    restriction is the whole point: an improvement computed over different case
    sets is not an improvement.
    """
    def verdict_map(arm: str) -> dict[str, str]:
        return {g["id"]: g["verdict"] for g in graded
                if g.get("arm", "skill") == arm and g["verdict"] is not None}

    skill_map, base_map = verdict_map("skill"), verdict_map("baseline")
    shared = sorted(set(skill_map) & set(base_map))
    both = [c for c in shared if skill_map[c] == base_map[c]]
    skill_only = [c for c in shared if skill_map[c] == "pass" and base_map[c] == "fail"]
    base_only = [c for c in shared if skill_map[c] == "fail" and base_map[c] == "pass"]
    negatives = [c for c in shared if not by_id[c]["should_trigger"]]
    return {
        "cases_in_both_arms": len(shared),
        "agreed": len(both),
        "skill_only_pass": skill_only,
        "baseline_only_pass": base_only,
        "negative_cases_paired": len(negatives),
        # Exact binomial sign test on the discordant pairs. With few pairs this
        # is the only honest test available; a normal approximation on n<10
        # would report a p-value the data cannot support.
        "sign_test_p": binom_two_sided(len(skill_only), len(base_only)),
        "discordant": len(skill_only) + len(base_only),
    }


def build_report(cases: list[dict], graded: list[dict], by_id: dict,
                 results: list[dict], models: list[str], must_fire: int,
                 wall: float) -> dict:
    """Assemble the machine-readable report.

    The summary and per-arm sections are left to the caller, which fills them
    once the statistics that depend on them exist.
    """
    report = {
        "kind": "pilot",
        "not_a_suite_result": (
            "A stratified pilot, not the full evaluation. These numbers are real "
            "but they are not the suite pass rate and must not be reported as one."
        ),
        "runtime": "opencode",
        # A pool, not a model. Each result also carries the model that served it,
        # because results from different models are not strictly comparable and
        # a report that pools them without saying so is misleading.
        "model_pool": models,
        "mixed_models": None,   # filled in below
        "arm": "with_skill",
        "sample_size": len(cases),
        "must_fire": must_fire,
        "must_not_fire": len(cases) - must_fire,
        "wall_seconds": round(wall, 1),
        "generated": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "results": [],
    }

    for g in graded:
        sandbox = sandbox_for(g["id"])
        report["results"].append({
            "id": g["id"],
            # Fixtures live outside the repository, so this cannot assume the
            # path is under REPO_ROOT. An absolute path in the report is correct;
            # a crash while describing where the run happened is not.
            "fixture": (str(sandbox.relative_to(REPO_ROOT))
                        if sandbox and str(sandbox).startswith(str(REPO_ROOT))
                        else (str(sandbox) if sandbox else None)),
            "arm": g.get("arm", "skill"),
            "class": by_id[g["id"]]["class"],
            "should_trigger": by_id[g["id"]]["should_trigger"],
            "verdict": g["verdict"],
            "reason": g.get("reason"),
            "prose_hits": g.get("prose_hits", []),
            "trace": g.get("trace"),
            "served_by": g.get("served_by"),
            "elapsed_s": next((r.get("elapsed_s") for r in results
                               if r["id"] == g["id"] and r.get("arm") == g.get("arm")), None),
            "chars": g.get("chars"),
            "quality": g.get("quality"),
            "worked_in_sandbox": g.get("worked_in_sandbox"),
        })
    return report


def write_run_logs(out_dir: Path, results: list[dict]) -> None:
    """One stdout transcript per run, so any verdict can be read back by hand."""
    for r in results:
        if "stdout" in r:
            safe = re.sub(r"[^A-Za-z0-9_.-]", "_", r["id"])
            arm = r.get("arm", "skill")
            (out_dir / f"{arm}__{safe}.txt").write_text(r["stdout"], encoding="utf-8")


def print_summary(report: dict, wall: float, out_dir: Path) -> None:
    """Print the human-readable summary.

    The numbers are read back out of the report rather than passed in alongside
    it, so what a reader sees and what the JSON records cannot drift apart. The
    one exception is the wall clock, which is printed unrounded exactly as it was
    measured.
    """
    summary = report["summary"]
    paired = report["paired"]
    served = report["models_that_served"]

    print()
    print(f"completed {summary['runs']} runs in {wall:.0f}s")
    for arm, r in report["arms"].items():
        neg = (f"false triggers {r['false_triggers']}/{r['negatives_decided']}"
               if r["negatives_decided"] else "false triggers not measured")
        print(f"  [{arm:8}] decided {r['decided']:3}/{r['runs']:3}  "
              f"passed {r['passed']:3}  {neg}  "
              f"env-failures {r['environment_failures']}")
    if paired:
        print()
        print(f"  paired: {paired['cases_in_both_arms']} case(s) decided in both arms, "
              f"{paired['agreed']} agreed")
        if paired["discordant"]:
            print(f"    skill only: {paired['skill_only_pass'] or 'none'}")
            print(f"    baseline only: {paired['baseline_only_pass'] or 'none'}")
            pv = paired["sign_test_p"]
            print(f"    exact sign test p = {pv:.3f}" if pv is not None
                  else "    no discordant pairs; nothing to test")
            if pv is not None and pv > 0.05:
                print("    not significant: this run does not show the skill "
                      "changing the outcome on the cases it could decide")
        else:
            print("    no discordant pairs; the arms did not differ on any case "
                  "both of them could decide")
    print(f"  environment failures: {summary['environment_failures']}  "
          f"(excluded from every rate)")
    print(f"  harness failures:     {summary['harness_failures']}")
    print(f"  undecided: {summary['runs'] - summary['decided']}  "
          f"(recorded null, not guessed)")
    if summary["needs_human_review"]:
        print(f"  read these by hand: {', '.join(summary['needs_human_review'])}  "
              f"(discussed orchestration, left no artefact)")
    if served:
        print(f"  served by: {', '.join(served)}")
        if report["mixed_models"]:
            print("  NOTE: more than one model served this run. Results are not "
                  "strictly comparable; per-case attribution is in the report.")
    print()
    if not summary["publishable"]:
        print(f"NO RATE REPORTED. Only {summary['decided']} of "
              f"{report['sample_size']} cases produced a")
        print(f"usable result, below the threshold of "
              f"{summary['min_decided_for_a_rate']}. Publishing a")
        print("false-trigger rate over this sample would be reporting noise as a")
        print("measurement. The per-case results are in the report; the number is not.")
    elif not summary["negatives_decided"]:
        # Every must-not-fire case died of quota. The most important number in
        # the run is the one with no data behind it.
        print("  false-trigger rate: NOT MEASURED — every must-not-fire case "
              "failed in the environment, so there is no sample")
    else:
        hits, total = summary["false_triggers"], summary["negatives_decided"]
        print(f"  false-trigger rate: {hits}/{total} = {hits/total*100:.0f}%")
    print()
    print(f"report: {(out_dir / 'pilot.json').relative_to(SKILL_ROOT.parent)}")


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    if not AGENT_RUNNER.is_file():
        print(f"error: runtime adapter not found at {AGENT_RUNNER}", file=sys.stderr)
        print("The skill-creator bundle provides agent_runner.py. Without it this "
              "script cannot drive a runtime, and an unrun suite is a checklist.",
              file=sys.stderr)
        return 1

    selected = resolve_cases(args)
    if selected is None:
        return 1
    cases, must_fire = selected

    if args.dry_run:
        return 0

    if not ensure_fixtures():
        return 1

    # Runs are serialised. Concurrent invocations collide on the runtime's
    # background service and fail, and a harness that only works one case at a
    # time is still a usable harness -- parallelism here would trade reliability
    # for speed on a measurement that is already expensive.
    models = ([m.strip() for m in args.models.split(",") if m.strip()]
              if args.models else DEFAULT_MODEL_POOL)
    print(f"running against opencode, serial, timeout {args.timeout}s")
    print(f"model pool ({len(models)}): {', '.join(models)}")
    # Arms are interleaved per case, not run as two separate sweeps. A sweep
    # design lets a rate limit or a model change land entirely on one arm, which
    # is indistinguishable from an effect of the skill.
    arms = ["skill", "baseline"] if args.arm == "both" else [args.arm]

    pairs, results, wall = execute_cases(cases, arms, args.timeout, models)
    assertion_specs = load_assertions()
    graded = [grade(c, r, assertion_specs.get(c["id"]))
              for c, r in pairs]
    by_id = {c["id"]: c for c in cases}

    out_dir = SKILL_ROOT.parent / args.out
    out_dir.mkdir(parents=True, exist_ok=True)
    report = build_report(cases, graded, by_id, results, models, must_fire, wall)
    write_run_logs(out_dir, results)

    served = {g.get("served_by") for g in graded if g.get("served_by")}
    report["mixed_models"] = len(served) > 1
    report["models_that_served"] = sorted(served)

    env_failed = [g for g in graded if g.get("kind") == "environment_error"]
    harness_failed = [g for g in graded if g.get("kind") == "harness_error"]
    decided = [g for g in graded if g["verdict"] is not None]
    passed = sum(1 for g in decided if g["verdict"] == "pass")

    arms_present = [a for a in ("skill", "baseline")
                    if any(g.get("arm", "skill") == a for g in graded)]
    paired = (paired_comparison(graded, by_id)
              if len(arms_present) == 2 else None)

    needs_review = sorted({
        f'{g["arm"]}:{g["id"]}' for g in graded
        if g.get("prose_hits") and not by_id[g["id"]]["should_trigger"]
        and not (g.get("trace") or {}).get("mutations")})
    negatives = [g for g in graded
                 if not by_id[g["id"]]["should_trigger"] and g["verdict"]]
    false_triggers = sum(1 for g in negatives if g["verdict"] == "fail")

    min_decided = max(4, int(0.6 * len(pairs)))

    report["arms"] = {a: arm_rates(graded, by_id, a) for a in arms_present}
    report["paired"] = paired
    report["summary"] = {
        "runs": len(graded),
        "decided": len(decided),
        "passed": passed,
        "failed": len(decided) - passed,
        "environment_failures": len(env_failed),
        "harness_failures": len(harness_failed),
        "min_decided_for_a_rate": min_decided,
        "publishable": len(decided) >= min_decided,
        "false_triggers": false_triggers,
        "negatives_decided": len(negatives),
        "needs_human_review": needs_review,
    }
    (out_dir / "pilot.json").write_text(json.dumps(report, indent=2), encoding="utf-8")

    print_summary(report, wall, out_dir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
