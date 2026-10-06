#!/usr/bin/env python3
"""Grade one artifact set. Usage: verifier.py <workdir>. Exit 0 = pass."""
import sys, pathlib
w = pathlib.Path(sys.argv[1])
f = w / "out" / "filtered.txt"
c = w / "out" / "counts.txt"
if not f.is_file(): print("FAIL missing out/filtered.txt"); sys.exit(1)
if not c.is_file(): print("FAIL missing out/counts.txt"); sys.exit(1)
src = (w/"logs"/"app.log").read_text().splitlines()
kept = [l for l in src if " ERROR " in l or " WARN " in l]
n_e = sum(1 for l in kept if " ERROR " in l)
n_w = sum(1 for l in kept if " WARN " in l)
import json
thr = json.loads((w/"config.json").read_text())["alert_threshold"]
want_tail = "ALERT" if n_e > thr else "OK"
got = f.read_text().splitlines()
if [g.strip() for g in got[:-1]] != kept:
    print(f"FAIL step 1: expected {len(kept)} lines unchanged; got {len(got)-1}")
    for i,(a,b) in enumerate(zip(kept+[""], got+[""])):
        if a.strip()!=b.strip(): print(f"   line {i+1}: want {a!r} got {b!r}"); break
    sys.exit(1)
if got[-1].strip() != want_tail:
    print(f"FAIL step 3: {n_e} errors vs threshold {thr} -> want {want_tail}, got {got[-1]!r}"); sys.exit(1)
cw = [l.strip() for l in c.read_text().splitlines() if l.strip()]
if cw != [f"ERROR={n_e}", f"WARN={n_w}"]:
    print(f"FAIL step 2: want ['ERROR={n_e}', 'WARN={n_w}'] got {cw}"); sys.exit(1)
print(f"PASS 3 steps: {len(kept)} kept, ERROR={n_e} WARN={n_w}, tail={want_tail}")
