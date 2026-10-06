#!/usr/bin/env python3
"""Grade one artifact set. Usage: verifier.py <workdir>. Exit 0 = pass."""
import sys, re, pathlib
w = pathlib.Path(sys.argv[1])
out = w / "out" / "api.md"
if not out.is_file(): print("FAIL missing out/api.md"); sys.exit(1)
code = (w/"api.py").read_text()
m = re.search(r"^def .*$", code, re.M)
if not m: print("FAIL no def found in api.py"); sys.exit(1)
want = m.group(0).strip()
doc = out.read_text()
lines = [l.strip() for l in doc.splitlines() if l.strip().startswith("def ")]
if not lines: print("FAIL out/api.md has no def line"); sys.exit(1)
if len(lines) > 1: print(f"FAIL expected one def line, found {len(lines)}"); sys.exit(1)
if lines[0] != want:
    print("FAIL signature mismatch"); print(f"  want {want!r}"); print(f"  got  {lines[0]!r}"); sys.exit(1)
orig = (w/"api.md").read_text().splitlines()
new  = doc.splitlines()
if len(orig) != len(new):
    print(f"FAIL line count changed: {len(orig)} -> {len(new)} (only the signature may change)"); sys.exit(1)
sig_idx = [i for i,l in enumerate(orig) if l.strip().startswith("def ")]
if len(sig_idx) != 1:
    print(f"FAIL source api.md should have exactly one def line, found {sig_idx}"); sys.exit(1)
changed = [i for i,(a,b) in enumerate(zip(orig,new)) if a!=b]
if changed != sig_idx:
    print(f"FAIL changed lines {changed}; only the signature line {sig_idx} may change"); sys.exit(1)
print("PASS signature corrected, nothing else touched")
