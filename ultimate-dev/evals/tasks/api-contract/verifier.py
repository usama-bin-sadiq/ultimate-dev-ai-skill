#!/usr/bin/env python3
"""Grade one artifact set. Usage: verifier.py <workdir>. Exit 0 = pass."""
import sys, pathlib
w = pathlib.Path(sys.argv[1])
y = w / "out" / "openapi.fixed.yaml"
c = w / "out" / "changes.txt"
if not y.is_file(): print("FAIL missing out/openapi.fixed.yaml"); sys.exit(1)
if not c.is_file(): print("FAIL missing out/changes.txt"); sys.exit(1)
doc = y.read_text()
notes = c.read_text().lower()
for word in ("pin", "404", "replace"):
    if word not in notes: print(f"FAIL out/changes.txt does not mention {word!r}"); sys.exit(1)
if "latest" in doc: print("FAIL server URL still pins to 'latest'"); sys.exit(1)
if "/v1" not in doc: print("FAIL server URL is not pinned to v1"); sys.exit(1)
if '"404"' not in doc and "'404'" not in doc and "404:" not in doc:
    print("FAIL no explicit 404 response"); sys.exit(1)
if '"400"' not in doc and "400:" not in doc: print("FAIL no explicit 400 response"); sys.exit(1)
if '"500"' not in doc and "500:" not in doc: print("FAIL no explicit 500 response"); sys.exit(1)
if re.search(r"(?m)^\s*default:", doc) if (re:=__import__("re")) else False:
    print("FAIL the catch-all 'default' response is still present"); sys.exit(1)
for keep in ("operationId: getUser", "/users/{id}"):
    if keep not in doc: print(f"FAIL lost {keep!r}"); sys.exit(1)
print("PASS server pinned, 404/400/500 explicit, default removed")
