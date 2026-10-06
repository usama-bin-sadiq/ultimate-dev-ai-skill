#!/usr/bin/env python3
"""Grade one artifact set. Usage: verifier.py <workdir>. Exit 0 = pass."""
import sys, csv, io, pathlib
w = pathlib.Path(sys.argv[1])
out = w / "out" / "todos.csv"
if not out.is_file():
    print("FAIL missing out/todos.csv"); sys.exit(1)
want = {1:"BLOCKER",2:"NIT",3:"BLOCKER",4:"NIT",5:"BLOCKER"}
rows = list(csv.reader(io.StringIO(out.read_text())))
rows = [r for r in rows if r and any(c.strip() for c in r)]
if not rows or [c.strip() for c in rows[0]] != ["id","severity"]:
    print(f"FAIL header must be id,severity; got {rows[0] if rows else None}"); sys.exit(1)
got = {}
for r in rows[1:]:
    if len(r) != 2: print(f"FAIL malformed row {r}"); sys.exit(1)
    got[int(r[0])] = r[1].strip().upper()
if got != want:
    diff = {k: (want.get(k), got.get(k)) for k in set(want) | set(got) if want.get(k) != got.get(k)}
    print(f"FAIL mismatches (want, got): {diff}"); sys.exit(1)
print("PASS all 5 classified correctly")
