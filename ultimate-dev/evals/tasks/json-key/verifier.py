#!/usr/bin/env python3
"""Grade one artifact set. Usage: verifier.py <workdir>. Exit 0 = pass."""
import sys, json, pathlib
w = pathlib.Path(sys.argv[1])
out = w / "out" / "email.txt"
if not out.is_file():
    print("FAIL missing out/email.txt"); sys.exit(1)
got = out.read_text().strip()
want = json.loads((w / "payload.json").read_text())["data"]["users"][2]["contact"]["email"]
if got != want:
    print(f"FAIL want {want!r} got {got!r}"); sys.exit(1)
print(f"PASS extracted {got}")
