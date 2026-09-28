#!/usr/bin/env python3
"""Self-test for check-workflow-auth.py.

The two directions proven against the real release.yml are necessary but not
sufficient. The point of the checker is to catch a workflow nobody has written
yet, so the cases below are synthetic: each is a minimal workflow built in a
temp directory, exercising one property. If the checker only works because it
remembers the shape of the file it was written against, these fail and the
checker is decoration.

  W1  undeclared `gh api` in a workflow it has never seen   -> must FAIL
  W2  `gh release create` with GH_TOKEN declared             -> must PASS
  W3  `gh --version` / `gh auth login`, no token             -> must PASS
  W4  `gh release` mentioned only in a `#` comment          -> must PASS
  W5  the same undeclared call in a *second* job             -> must FAIL
  W6  no .github/workflows anywhere                          -> must FAIL
  W7  the real repository                                    -> must PASS

W6 is the one that matters most. A guard that cannot find its target has
nothing to say, and the first version of this tool walked the file and stopped
at the end of the first job -- so it reported three workflows checked while
examining one job of one of them, and passed. Refusing to report clean when the
target is missing is what stops that from reading as success.
"""

from __future__ import annotations

import importlib.util
import pathlib
import shutil
import sys
import tempfile

TOOL = pathlib.Path(__file__).resolve().parent / "check-workflow-auth.py"

spec = importlib.util.spec_from_file_location("check_workflow_auth", TOOL)
assert spec and spec.loader, f"cannot load {TOOL}"
cwa = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cwa)

FAILURES: list[str] = []


def check(label: str, condition: bool, detail: str = "") -> None:
    if condition:
        print(f"  pass  {label}")
    else:
        print(f"  FAIL  {label}  {detail}")
        FAILURES.append(label)


def run_in(wf_text: str | None, subdir: str = "repo") -> tuple[int, str]:
    """Run the checker against a synthetic workflow tree. Returns (exit, out)."""
    root = pathlib.Path(tempfile.mkdtemp())
    try:
        if wf_text is not None:
            wd = root / subdir / ".github" / "workflows"
            wd.mkdir(parents=True)
            (wd / "synthetic.yml").write_text(wf_text)
        cwd = pathlib.Path.cwd()
        import os
        (root / subdir).mkdir(parents=True, exist_ok=True)
        os.chdir(root / subdir)
        try:
            buf: list[str] = []
            real = sys.stdout

            class _Cap:
                def write(self, s: str) -> None:
                    buf.append(s)

                def flush(self) -> None:
                    pass

            sys.stdout = _Cap()
            try:
                rc = cwa.main()
            finally:
                sys.stdout = real
            return rc, "".join(buf)
        finally:
            os.chdir(cwd)
    finally:
        shutil.rmtree(root, ignore_errors=True)


WRAPPER = """\
name: synthetic
on: push
jobs:
  go:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
{body}
"""

STEP = """\
      - name: {name}
{env}        run: |
          {cmd}
"""


def step(name: str, cmd: str, token: bool = False) -> str:
    """One step. `token` emits a well-formed env block at the right indent.

    The first version of W2 injected `GH_TOKEN:` as a bare mapping key beside
    `run:`, which is not how a workflow declares an env var. The checker was
    right to ignore it and the case failed for a reason that had nothing to do
    with what it was testing -- a test that fails for the wrong reason is worse
    than no test, because it looks like a finding.
    """
    env = ""
    if token:
        env = "        env:\n          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}\n"
    return STEP.format(name=name, cmd=cmd, env=env)


# W1 -- the case that matters. An undeclared credential in a file the checker
# has never seen, in a subcommand it has never seen named here.
rc, out = run_in(WRAPPER.format(
    body=step("Call the API", "gh api repos/$GITHUB_REPOSITORY --jq .full_name")
))
check("W1 undeclared `gh api` fails", rc == 1, f"exit {rc}: {out.strip()[:90]}")
check("W1 names the step", "Call the API" in out, out.strip()[:120])

# W2 -- the fix, generalised. Same subcommand, token present.
rc, out = run_in(WRAPPER.format(
    body=step("Call the API", "gh api repos/x --jq .full_name", token=True)
))
check("W2 declared token passes", rc == 0, f"exit {rc}: {out.strip()[:90]}")

# W3 -- over-flagging is a real failure mode too. A checker that cries wolf on
# `gh --version` gets ignored, and then it protects nothing.
rc, out = run_in(WRAPPER.format(
    body=step("Print version", "gh --version && gh auth login")
))
check("W3 local gh calls are not flagged", rc == 0, f"exit {rc}: {out.strip()[:90]}")

# W4 -- a comment is not a call. release.yml has a comment block that names
# `gh release` while explaining an earlier failure, and flagging it would be a
# false positive on a file that is in fact correct.
rc, out = run_in(WRAPPER.format(
    body="      - name: Explain\n        run: |\n"
         "          # gh release create failed with exit 4 previously\n"
         "          echo done\n"
))
check("W4 commented-out call is not flagged", rc == 0, f"exit {rc}: {out.strip()[:90]}")

# W5 -- the first version of this scanner broke out of the file at the end of
# the first job, so a violation in job two was invisible. W1 alone does not
# catch that, because W1's violation is in job one.
TWO_JOBS = """\
name: synthetic
on: push
jobs:
  first:
    runs-on: ubuntu-latest
    steps:
      - name: Harmless
        run: echo ok
  second:
    runs-on: ubuntu-latest
    steps:
      - name: Sneaky
        run: |
          gh workflow list
"""
rc, out = run_in(TWO_JOBS)
check("W5 violation in a later job still fails", rc == 1, f"exit {rc}: {out.strip()[:90]}")
check("W5 names the later step", "Sneaky" in out, out.strip()[:120])

# W6 -- the target is missing. Reporting clean here is the false clean that
# made the first version worthless, so it must be a failure.
rc, out = run_in(None)
check("W6 missing .github/workflows refuses to pass", rc == 1, f"exit {rc}")
check("W6 says why", "refusing to report clean" in out, out.strip()[:110])

# W7 -- the real thing, and the count matters as much as the verdict. The first
# version of the scanner examined one job of one workflow and printed a
# confident "3 workflow(s) checked", so a plausible-looking count was reporting
# on far less than it claimed. Asserting steps_seen > 20 is what catches that
# shape of lie: a scanner that sees almost nothing still exits 0.
wdir = cwa.workflow_dir()
problems: list[str] = []
steps_seen = 0
files = 0
if wdir is not None:
    for wf in sorted(wdir.glob("*.yml")) + sorted(wdir.glob("*.yaml")):
        files += 1
        steps_seen += len(cwa._steps(wf.read_text().split("\n")))
        problems.extend(cwa.check_workflow(wf))
check("W7 the real repository is clean", not problems,
      "; ".join(problems)[:170])
check("W7 it found the workflows", files >= 3, f"only {files} file(s) found")
check("W7 it examined a plausible number of steps", steps_seen > 20,
      f"only {steps_seen} steps seen across {files} workflow(s)")

if FAILURES:
    print(f"\nFAIL  {len(FAILURES)} of 7 case(s) failed: "
          f"{', '.join(FAILURES)}")
    sys.exit(1)
print("\nall self-tests passed")
sys.exit(0)
