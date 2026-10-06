#!/usr/bin/env python3
"""Grade one artifact set. Usage: verifier.py <workdir>. Exit 0 = pass."""
import sys, importlib.util, pathlib
w = pathlib.Path(sys.argv[1])
cause = w / "out" / "cause.md"
fixed = w / "out" / "fixed.py"
if not cause.is_file(): print("FAIL missing out/cause.md"); sys.exit(1)
if not fixed.is_file(): print("FAIL missing out/fixed.py"); sys.exit(1)
note = cause.read_text().lower()
if not any(k in note for k in ("- 1","-1","off-by-one","off by one","len(ordered)")):
    print("FAIL cause.md does not identify the corrected expression"); sys.exit(1)
spec = importlib.util.spec_from_file_location("fixed", fixed)
m = importlib.util.module_from_spec(spec)
try:
    spec.loader.exec_module(m)
except Exception as e:
    print(f"FAIL out/fixed.py does not import: {e}"); sys.exit(1)
cases = [
    ("percentile p=1.0", lambda: m.percentile([1,2,3,4], 1.0), 4),
    ("percentile p=0.0", lambda: m.percentile([1,2,3,4], 0.0), 1),
    ("percentile p=0.5", lambda: m.percentile([1,2,3,4], 0.5), 2),
    ("percentile len1",   lambda: m.percentile([7], 1.0), 7),
    ("clamp lo",   lambda: m.clamp(-5, 0, 10), 0),
    ("clamp hi",   lambda: m.clamp(99, 0, 10), 10),
    ("clamp mid",  lambda: m.clamp(5, 0, 10), 5),
]
bad = []
for label, fn, want in cases:
    try:
        got = fn()
    except Exception as e:
        bad.append(f"{label}: raised {type(e).__name__}"); continue
    if got != want: bad.append(f"{label}: want {want} got {got}")
if bad:
    print("FAIL"); [print("   ", b) for b in bad]; sys.exit(1)
print(f"PASS all {len(cases)} behaviour checks")
