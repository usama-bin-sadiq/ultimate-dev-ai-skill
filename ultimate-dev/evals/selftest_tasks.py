#!/usr/bin/env python3
"""Self-test for the task suite: prove every verifier discriminates.

For each task this materialises a workdir with the fixtures plus a reference
solution, then runs the verifier twice:

  * with the reference artifacts  -> must PASS
  * with deliberately wrong ones  -> must FAIL

A verifier that accepts the wrong answer is a broken grader, not a hard task.
Any task where either half misbehaves is reported and the exit code is 1.
"""

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TASKS = ROOT / "evals" / "tasks"
PY = sys.executable


def w(p: Path, s: str):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(s)


def ref(name: str, w_: Path) -> None:
    """Write the correct artifacts for `name` into workdir w_."""
    o = w_ / "out"
    if name == "grep-artifact":
        src = [l for l in (w_ / "corpus.txt").read_text().splitlines() if "TODO" in l or "FIXME" in l]
        w(o / "matches.txt", "\n".join(src) + "\n")
    elif name == "json-key":
        w(o / "email.txt", "third@corp.org\n")
    elif name == "csv-stats":
        w(o / "summary.txt", "rows_skipped=1\nduplicates=1\nrevenue_total=91.00\n")
    elif name == "rename-files":
        for p in list(w_.iterdir()):
            if p.is_file() and p.suffix != ".txt" and p.name != "count.txt":
                p.rename(p.with_suffix(".txt"))
        w(o / "count.txt", "5\n")
    elif name == "git-status":
        st = subprocess.run(["git", "status", "--porcelain"], cwd=w_, capture_output=True, text=True).stdout
        br = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=w_, capture_output=True, text=True).stdout.strip()
        n = len([l for l in st.splitlines() if l.strip()])
        w(o / "git.txt", f"branch={br}\nchanges={n}\n")
    elif name == "todo-triage":
        rows = ["id,severity"] + [f"{i},{s}" for i, s in
                                  enumerate(["BLOCKER","NIT","BLOCKER","NIT","BLOCKER"], start=1)]
        w(o / "todos.csv", "\n".join(rows) + "\n")
    elif name == "yaml-config":
        w(o / "config.yaml",
          "service:\n  host: ${HOST}\n  port: ${PORT}\n  token: ${TOKEN}\n"
          "telemetry:\n  url: https://${HOST}/collect\n  timeout: ${TIMEOUT}\n")
        w(o / "count.txt", "5\n")
    elif name == "bug-diagnosis":
        w(o / "cause.md",
          "percentile indexes with int(p * len(ordered)), which reaches len(ordered) at p=1.0 "
          "and raises IndexError. The expression should be int(p * (len(ordered) - 1)).\n")
        w(o / "fixed.py",
          (w_ / "calc.py").read_text().replace("int(p * len(ordered))", "int(p * (len(ordered) - 1))"))
    elif name == "test-generation":
        w(o / "test_stats.py",
          "import sys\nfrom stats import mean, median\n\n"
          "fails = 0\n"
          "def check(label, got, want):\n"
          "    global fails\n"
          "    ok = got == want\n"
          "    print(('PASS' if ok else 'FAIL'), label, 'got', got, 'want', want)\n"
          "    if not ok: fails += 1\n\n"
          "check('mean', mean([2,4,6]), 4)\n"
          "check('median even', median([1,2,3,4]), 2.5)\n"
          "check('median odd', median([5,1,3]), 3)\n"
          "sys.exit(1 if fails else 0)\n")
    elif name == "doc-refresh":
        doc = (w_ / "api.md").read_text().splitlines()
        sig = next(l for l in (w_ / "api.py").read_text().splitlines() if l.startswith("def "))
        idx = [i for i, l in enumerate(doc) if l.strip().startswith("def ")][0]
        doc[idx] = sig
        w(o / "api.md", "\n".join(doc) + "\n")
    elif name == "api-contract":
        y = (w_ / "openapi.yaml").read_text()
        y = y.replace("https://api.example.com/latest", "https://api.example.com/v1")
        # replace the whole `default:` block, preserving its real indentation
        lines = y.splitlines()
        start = next(i for i, l in enumerate(lines) if l.strip() == "default:")
        pad = " " * (len(lines[start]) - len(lines[start].lstrip()))
        end = start + 1
        while end < len(lines) and (not lines[end].strip() or
                                    len(lines[end]) - len(lines[end].lstrip()) > len(pad)):
            end += 1
        block = []
        for code, desc in (("404", "not found"), ("400", "bad request"), ("500", "server error")):
            block += [f'{pad}"{code}":', f"{pad}  description: {desc}",
                      f"{pad}  content:", f"{pad}    application/json:",
                      f"{pad}      schema: {{ type: object }}"]
        lines[start:end] = block
        w(o / "openapi.fixed.yaml", "\n".join(lines) + "\n")
        w(o / "changes.txt", "pin the server url to v1\nadd a 404 response\nreplace the default response\n")
    elif name == "slop-removal":
        w(o / "draft.md",
          "# Sync API v2\n\nSync API v2 gives teams batch updates at 500 requests per second, "
          "a 4x improvement over v1. Retries are handled automatically, so you do not need to "
          "manage backoff yourself.\n")
    elif name == "pipeline-series":
        src = (w_ / "logs" / "app.log").read_text().splitlines()
        kept = [l for l in src if " ERROR " in l or " WARN " in l]
        n_e = sum(1 for l in kept if " ERROR " in l)
        n_w = sum(1 for l in kept if " WARN " in l)
        thr = json.loads((w_ / "config.json").read_text())["alert_threshold"]
        w(o / "filtered.txt", "\n".join(kept + ["ALERT" if n_e > thr else "OK"]) + "\n")
        w(o / "counts.txt", f"ERROR={n_e}\nWARN={n_w}\n")
    else:
        raise SystemExit(f"no reference solution for {name}")


def wrong(name: str, w_: Path) -> None:
    """Write artifacts that are plausible but incorrect."""
    o = w_ / "out"
    if name == "grep-artifact":
        w(o / "matches.txt", "fix the parser TODO\n")
    elif name == "json-key":
        w(o / "email.txt", "first@example.com\n")
    elif name == "csv-stats":
        w(o / "summary.txt", "rows_skipped=1\nduplicates=0\nrevenue_total=111.00\n")
    elif name == "rename-files":
        w(o / "count.txt", "0\n")
    elif name == "git-status":
        w(o / "git.txt", "branch=main\nchanges=0\n")
    elif name == "todo-triage":
        w(o / "todos.csv", "id,severity\n1,BLOCKER\n2,BLOCKER\n3,NIT\n4,NIT\n5,NIT\n")
    elif name == "yaml-config":
        w(o / "config.yaml", "service:\n  host: ${HOST:-localhost}\n")
        w(o / "count.txt", "1\n")
    elif name == "bug-diagnosis":
        w(o / "cause.md", "off-by-one in the index\n")
        w(o / "fixed.py", (w_ / "calc.py").read_text())
    elif name == "test-generation":
        w(o / "test_stats.py", "from stats import mean, median\nprint('ok')\n")
    elif name == "doc-refresh":
        doc = (w_ / "api.md").read_text()
        w(o / "api.md", doc.replace("def fetch_user(user_id, include_meta=False) -> User",
                                    "def fetch_user(user_id: str) -> User"))
    elif name == "api-contract":
        w(o / "openapi.fixed.yaml", (w_ / "openapi.yaml").read_text())
        w(o / "changes.txt", "pin\n404\nreplace\n")
    elif name == "slop-removal":
        w(o / "draft.md", "# Sync API v2\n\nIt is a game-changer at 500 requests per second.\n")
    elif name == "pipeline-series":
        src = (w_ / "logs" / "app.log").read_text().splitlines()
        w(o / "filtered.txt", "\n".join(l for l in src if " ERROR " in l) + "\nOK\n")
        w(o / "counts.txt", "ERROR=4\nWARN=3\n")
    else:
        raise SystemExit(f"no wrong answer for {name}")


def build(name: str, dest: Path) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    meta = json.loads((TASKS / name / "meta.json").read_text())
    fx = TASKS / name / "fixtures"
    if fx.is_dir():
        shutil.copytree(fx, dest, dirs_exist_ok=True)
    if meta.get("setup") == "git":
        run = lambda *a: subprocess.run(a, cwd=dest, capture_output=True, text=True)
        run("git", "init", "-q", "-b", "main")
        run("git", "config", "user.email", "t@example.com")
        run("git", "config", "user.name", "T")
        w(dest / "tracked.txt", "one\n")
        run("git", "add", "-A")
        run("git", "commit", "-qm", "init")
        w(dest / "tracked.txt", "one\ntwo\n")          # modified
        w(dest / "brand-new.txt", "untracked\n")        # untracked


def grade(name: str, wdir: Path) -> tuple[bool, str]:
    r = subprocess.run([PY, str(TASKS / name / "verifier.py"), str(wdir)],
                       capture_output=True, text=True, timeout=120)
    line = (r.stdout.strip() or r.stderr.strip()).splitlines()
    return r.returncode == 0, (line[0] if line else f"exit={r.returncode}")


def main() -> int:
    names = sorted(p.name for p in TASKS.iterdir() if (p / "verifier.py").is_file())
    if len(sys.argv) > 1:
        names = [n for n in names if n in sys.argv[1:]]
    ok = True
    print(f"{'task':<20} {'reference':<10} {'wrong-answer':<14} verdict")
    print("-" * 66)
    for n in names:
        good = bad = Path(tempfile.mkdtemp()) / n
        wrongd = Path(tempfile.mkdtemp()) / n
        try:
            build(n, good); build(n, wrongd)
            ref(n, good); wrong(n, wrongd)
            g_ok, g_msg = grade(n, good)
            w_ok, w_msg = grade(n, wrongd)
            verdict = "OK" if (g_ok and not w_ok) else "BROKEN GRADER"
            if verdict != "OK":
                ok = False
            print(f"{n:<20} {('PASS' if g_ok else 'FAIL'):<10} "
                  f"{('rejected' if not w_ok else 'ACCEPTED(!)'):<14} {verdict}")
            if verdict != "OK":
                print(f"    reference: {g_msg}")
                print(f"    wrong    : {w_msg}")
        finally:
            shutil.rmtree(good.parent, ignore_errors=True)
            shutil.rmtree(wrongd.parent, ignore_errors=True)
    print("-" * 66)
    print("all graders discriminate" if ok else "SOME GRADERS ARE BROKEN")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
