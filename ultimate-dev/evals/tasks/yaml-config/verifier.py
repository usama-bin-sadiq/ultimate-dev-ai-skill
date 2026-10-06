#!/usr/bin/env python3
"""Grade one artifact set. Usage: verifier.py <workdir>. Exit 0 = pass."""
import sys, pathlib
w = pathlib.Path(sys.argv[1])
out = w / "out" / "config.yaml"
cnt = w / "out" / "count.txt"
if not out.is_file(): print("FAIL missing out/config.yaml"); sys.exit(1)
if not cnt.is_file(): print("FAIL missing out/count.txt"); sys.exit(1)
body = out.read_text()
bad = [t for t in (":-", ":?") if t in body]
if bad: print(f"FAIL {bad} still present"); sys.exit(1)
import re
names = re.findall(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}", body)
want = ["HOST","PORT","TOKEN","HOST","TIMEOUT"]
if names != want: print(f"FAIL interpolations want {want} got {names}"); sys.exit(1)
if cnt.read_text().strip() != str(len(want)):
    print(f"FAIL count want {len(want)} got {cnt.read_text().strip()!r}"); sys.exit(1)
print(f"PASS 5 interpolations normalised, count correct")
