#!/usr/bin/env python3
"""Self-test for the release changelog generator.

The generator had shipped `_No summary recorded._` in every release this
repository has ever made, while `steps.check.outputs.release_notes` sat in the
job outputs read by nothing. The entry was a hardcoded string; the plumbing to
compute a real one was built one step earlier and left disconnected. Nothing
checked the result, so a generator that never tried looked identical to one that
tried and found nothing.

These cases run the generator's own logic against real git history in a
temporary repository, because the interesting inputs are exactly the ones a
mock would get wrong: a range that contains commits, a range that contains only
merge commits, and a range that contains nothing at all.

  C1  a push release with ordinary commits  -> bullets from those subjects
  C2  a manual release with human notes      -> the human's text, verbatim
  C3  human notes of only whitespace          -> falls through to commits
  C4  a range of merge commits only           -> those merges, not the fallback
  C5  an empty range                          -> the honest fallback line
  C6  the entry lands newest-first under the H1
  C7  a second release does not disturb the first entry

The bug this exists to prevent is C2 and C3: preferring the placeholder over
work that was already available.
"""

from __future__ import annotations

import pathlib
import re
import shutil
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
WORKFLOW = HERE.parent.parent / ".github" / "workflows" / "release.yml"

FAILURES: list[str] = []


def check(label: str, condition: bool, detail: str = "") -> None:
    if condition:
        print(f"  pass  {label}")
    else:
        print(f"  FAIL  {label}  {detail}")
        FAILURES.append(label)


def _generator() -> str:
    """The generator's Python, lifted out of the workflow.

    Read from the workflow rather than duplicated here. A copy would be a
    second implementation of the same rule, and the second one would be the one
    that drifts -- which is how this defect existed in the first place: the
    notes were computed in one step and written in another, and only the writer
    survived.
    """
    text = WORKFLOW.read_text(encoding="utf-8")
    start = text.index("          python3 - CHANGELOG.md")
    body = text[start:].split("<<'PY'\n", 1)[1]
    lines = []
    for line in body.split("\n"):
        if line.strip() == "PY":
            break
        lines.append(line[10:] if line.startswith(" " * 10) else line)
    code = "\n".join(lines) + "\n"
    if "RELEASE_NOTES" not in code:
        raise SystemExit(
            "the generator lifted from release.yml does not read RELEASE_NOTES; "
            "the step has changed shape and this test needs updating"
        )
    return code


def _repo(commits: list[tuple[str, str]], tag: str | None) -> pathlib.Path:
    """A throwaway repo. commits is [(subject, kind)] where kind is 'n'|'m'."""
    root = pathlib.Path(tempfile.mkdtemp())
    env = {
        "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@e",
        "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@e",
        "PATH": "/usr/bin:/bin:/usr/local/bin", "HOME": str(root),
    }
    subprocess.run(["git", "init", "-q", "-b", "main", "."],
                   cwd=root, env=env, check=True)
    (root / "VERSION").write_text("0.0.1\n")
    subprocess.run(["git", "add", "-A"], cwd=root, env=env, check=True)
    subprocess.run(["git", "commit", "-qm", "initial"], cwd=root, env=env, check=True)
    if tag:
        subprocess.run(["git", "tag", tag], cwd=root, env=env, check=True)
    for subject, kind in commits:
        (root / "f").write_text(subject)
        subprocess.run(["git", "add", "-A"], cwd=root, env=env, check=True)
        args = ["git", "commit", "-qm", subject]
        if kind == "m":
            args = ["git", "commit", "--allow-empty", "-qm", subject]
        subprocess.run(args, cwd=root, env=env, check=True)
    return root


def _run(root: pathlib.Path, version: str, notes: str) -> str:
    import os
    # Seed once. Reseeding on every call made the second-release case lose the
    # first entry, which reads exactly like a generator that overwrites the
    # history instead of prepending to it.
    seed = root / "CHANGELOG.md"
    if not seed.exists():
        seed.write_text(
            "# Changelog\n\n## [0.0.0] — 2020-01-01\n\nseed\n", encoding="utf-8"
        )
    script = _generator()
    (root / "_gen.py").write_text(script, encoding="utf-8")
    old = os.environ.get("RELEASE_NOTES")
    os.environ["RELEASE_NOTES"] = notes
    try:
        proc = subprocess.run(
            [sys.executable, "_gen.py", "CHANGELOG.md", version, "2026-09-29"],
            cwd=root, capture_output=True, text=True,
        )
    finally:
        if old is None:
            os.environ.pop("RELEASE_NOTES", None)
        else:
            os.environ["RELEASE_NOTES"] = old
    if proc.returncode != 0:
        raise SystemExit(f"generator failed: {proc.stderr.strip()[:300]}")
    return (root / "CHANGELOG.md").read_text(encoding="utf-8")


# C1 -- the ordinary push case. Two commits since the tag become two bullets.
root = _repo([("fix: the first thing", "n"), ("fix: the second thing", "n")], "v1.0.0")
try:
    out = _run(root, "1.0.1", "")
    check("C1 commit subjects become bullets",
          "- fix: the first thing" in out and "- fix: the second thing" in out,
          out[:180])
    check("C1 the placeholder is gone", "No summary recorded" not in out)
    check("C1 the entry is versioned", "## [1.0.1] — 2026-09-29" in out)
finally:
    shutil.rmtree(root, ignore_errors=True)

# C2 -- a human typed the notes. They are the most accurate description
# available and must win over anything derived from commits.
root = _repo([("fix: mechanical", "n")], "v1.0.0")
try:
    out = _run(root, "1.0.1", "Rolled back the bad tag and re-cut it by hand.")
    check("C2 human notes win", "Rolled back the bad tag" in out, out[:180])
    check("C2 derived commits do not also appear", "fix: mechanical" not in out)
finally:
    shutil.rmtree(root, ignore_errors=True)

# C3 -- notes that are present but blank. Treating these as content would ship
# an entry with a blank line where the summary should be, which is the shape of
# the original defect wearing a different hat.
root = _repo([("fix: real work", "n")], "v1.0.0")
try:
    out = _run(root, "1.0.1", "   \n\t  \n")
    check("C3 whitespace-only notes fall through to commits",
          "- fix: real work" in out, out[:180])
finally:
    shutil.rmtree(root, ignore_errors=True)

# C4 -- a range of only merge commits. --no-merges filters them all out, so a
# naive implementation would fall to the fallback and say nothing had changed,
# when in fact the whole release was merge commits.
root = _repo([("Merge pull request #1", "m"), ("Merge pull request #2", "m")],
             "v1.0.0")
try:
    out = _run(root, "1.0.1", "")
    check("C4 merge-only range is still described",
          "Merge pull request #1" in out, out[:200])
    check("C4 merge-only range is not the fallback",
          "No commits or notes" not in out)
finally:
    shutil.rmtree(root, ignore_errors=True)

# C5 -- nothing at all in range. The fallback is the only honest output, and
# it now says that, rather than pretending a generator ran and found nothing.
root = _repo([], "v1.0.0")
try:
    out = _run(root, "1.0.1", "")
    check("C5 empty range falls back honestly",
          "No commits or notes to summarise" in out, out[:180])
    check("C5 and the old placeholder never appears",
          "No summary recorded" not in out)
finally:
    shutil.rmtree(root, ignore_errors=True)

# C6/C7 -- ordering and idempotence across consecutive releases.
root = _repo([("fix: one", "n")], "v1.0.0")
try:
    first = _run(root, "1.0.1", "")
    heads = [l for l in first.split("\n") if l.startswith("# ")]
    secs = [l for l in first.split("\n") if l.startswith("## ")]
    check("C6 newest entry is the first section after the H1",
          heads == ["# Changelog"] and secs[0] == "## [1.0.1] — 2026-09-29",
          f"h1={heads} first-section={secs[:1]}")
    (root / "CHANGELOG.md").write_text(first, encoding="utf-8")
    (root / "f").write_text("two")
    env = {"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@e",
           "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@e",
           "PATH": "/usr/bin:/bin:/usr/local/bin", "HOME": str(root)}
    subprocess.run(["git", "add", "-A"], cwd=root, env=env, check=True)
    subprocess.run(["git", "commit", "-qm", "fix: two"], cwd=root, env=env, check=True)
    second = _run(root, "1.0.2", "")
    check("C7 the earlier entry survives a second release",
          "## [1.0.1] — 2026-09-29" in second, second[:200])
    check("C7 the newer entry is on top",
          second.index("1.0.2") < second.index("1.0.1"), "out of order")
    check("C7 newest-first across the whole file",
          re.findall(r"^## \[(\d+\.\d+\.\d+)\]", second, re.MULTILINE)
          == ["1.0.2", "1.0.1", "0.0.0"],
          str(re.findall(r"^## \[(\d+\.\d+\.\d+)\]", second, re.MULTILINE)))
finally:
    shutil.rmtree(root, ignore_errors=True)

if FAILURES:
    print(f"\nFAIL  {len(FAILURES)} case(s) failed: {', '.join(FAILURES)}")
    sys.exit(1)
print("\nall self-tests passed")
sys.exit(0)
