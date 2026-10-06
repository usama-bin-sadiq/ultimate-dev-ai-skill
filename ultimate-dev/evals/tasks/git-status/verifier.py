#!/usr/bin/env python3
"""Grade one artifact set. Usage: verifier.py <workdir>. Exit 0 = pass."""
import sys, subprocess, pathlib
w = pathlib.Path(sys.argv[1])
out = w / "out" / "git.txt"
if not out.is_file():
    print("FAIL missing out/git.txt"); sys.exit(1)
def g(*a):
    return subprocess.run(["git", *a], cwd=w, capture_output=True, text=True).stdout.strip()
want_branch = g("rev-parse", "--abbrev-ref", "HEAD")
porcelain = [l for l in g("status", "--porcelain").splitlines()
            if l.strip() and not l[3:].startswith("out/")]
want_n = len(porcelain)
got = {}
for line in out.read_text().splitlines():
    if "=" in line:
        k, v = line.split("=", 1); got[k.strip()] = v.strip()
if got.get("branch") != want_branch:
    print(f"FAIL branch want {want_branch!r} got {got.get('branch')!r}"); sys.exit(1)
if got.get("changes") != str(want_n):
    print(f"FAIL changes want {want_n} got {got.get('changes')!r}"); sys.exit(1)
print(f"PASS branch={want_branch} changes={want_n}")
