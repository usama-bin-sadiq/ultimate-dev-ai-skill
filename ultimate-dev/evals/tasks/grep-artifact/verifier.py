#!/usr/bin/env python3
"""Grade one artifact set. Usage: verifier.py <workdir>. Exit 0 = pass."""
import sys, pathlib
w = pathlib.Path(sys.argv[1])
src = [l for l in (w / "corpus.txt").read_text().splitlines()
       if "TODO" in l or "FIXME" in l]
out = w / "out" / "matches.txt"
if not out.is_file():
    print("FAIL missing out/matches.txt"); sys.exit(1)
got = out.read_text().splitlines()
if got != src:
    print(f"FAIL expected {len(src)} lines in order; got {len(got)}")
    for i, (a, b) in enumerate(zip(src + [""] * 9, got + [""] * 9)):
        if a != b: print(f"  line {i+1}: want {a!r} got {b!r}")
    sys.exit(1)
print(f"PASS {len(got)} matching lines, order preserved")
