#!/usr/bin/env python3
"""Grade one artifact set. Usage: verifier.py <workdir>. Exit 0 = pass."""
import sys, pathlib
w = pathlib.Path(sys.argv[1])
out = w / "out" / "summary.txt"
if not out.is_file():
    print("FAIL missing out/summary.txt"); sys.exit(1)
got = out.read_text().strip().splitlines()
want = ["rows_skipped=1", "duplicates=1", "revenue_total=91.00"]
if [g.strip() for g in got] != want:
    print("FAIL"); print(f"  want {want}"); print(f"  got  {[g.strip() for g in got]}"); sys.exit(1)
print("PASS rows_skipped=1 duplicates=1 revenue_total=91.00")
