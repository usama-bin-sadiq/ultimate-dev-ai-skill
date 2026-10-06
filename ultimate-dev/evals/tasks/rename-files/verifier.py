#!/usr/bin/env python3
"""Grade one artifact set. Usage: verifier.py <workdir>. Exit 0 = pass."""
import sys, pathlib
w = pathlib.Path(sys.argv[1])
out = w / "out" / "count.txt"
if not out.is_file():
    print("FAIL missing out/count.txt"); sys.exit(1)
# every top-level fixture file must now end in exactly .txt
bad = [p.name for p in w.iterdir()
       if p.is_file() and p.suffix != ".txt" and p.name != "count.txt"]
if bad:
    print(f"FAIL not renamed to lowercase .txt: {bad}"); sys.exit(1)
n = 5
got = out.read_text().strip()
if got != str(n):
    print(f"FAIL out/count.txt want {n} got {got!r}"); sys.exit(1)
print("PASS 5 files renamed, count correct")
