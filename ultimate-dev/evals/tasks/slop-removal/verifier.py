#!/usr/bin/env python3
"""Grade one artifact set. Usage: verifier.py <workdir>. Exit 0 = pass."""
import sys, re, pathlib
w = pathlib.Path(sys.argv[1])
out = w / "out" / "draft.md"
if not out.is_file(): print("FAIL missing out/draft.md"); sys.exit(1)
doc = out.read_text().lower()
banned = ["delve","dive in","in today's fast-paced","it's important to note",
          "game-changer","seamless","leverage","unlock the power","furthermore",
          "additionally","in conclusion"]
hits = [b for b in banned if b in doc]
if hits: print(f"FAIL banned phrases still present: {hits}"); sys.exit(1)
must = ["sync api v2","500 requests per second","4x","v1","automatic"]
lost = [m for m in must if m not in doc]
if lost: print(f"FAIL lost required facts: {lost}"); sys.exit(1)
if len(out.read_text().split()) > 220:
    print(f"FAIL output is {len(out.read_text().split())} words; should be tighter"); sys.exit(1)
print(f"PASS no banned phrases, all facts kept, {len(out.read_text().split())} words")
