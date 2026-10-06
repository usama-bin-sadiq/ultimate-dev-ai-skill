#!/usr/bin/env python3
"""Grade one artifact set. Usage: verifier.py <workdir>. Exit 0 = pass."""
import sys, shutil, subprocess, tempfile, pathlib
w = pathlib.Path(sys.argv[1])
t = w / "out" / "test_stats.py"
if not t.is_file(): print("FAIL missing out/test_stats.py"); sys.exit(1)
src = t.read_text()
if len(src.strip()) < 200:
    print("FAIL test file is too small to contain real checks"); sys.exit(1)
def run(module_text, tag):
    d = pathlib.Path(tempfile.mkdtemp())
    (d/"stats.py").write_text(module_text)
    shutil.copy(t, d/"test_stats.py")
    r = subprocess.run([sys.executable, "test_stats.py"], cwd=d, capture_output=True, text=True, timeout=60)
    shutil.rmtree(d, ignore_errors=True)
    return r
buggy = (w/"stats.py").read_text()
good  = (w/"fixed.py").read_text()
r_bad = run(buggy, "buggy")
if r_bad.returncode == 0:
    print("FAIL tests PASS against the buggy module - they do not catch the bugs")
    print("   stdout:", r_bad.stdout.strip()[:300]); sys.exit(1)
r_good = run(good, "fixed")
if r_good.returncode != 0:
    print("FAIL tests FAIL against the corrected module")
    print("   stdout:", r_good.stdout.strip()[:300])
    print("   stderr:", r_good.stderr.strip()[:300]); sys.exit(1)
print("PASS tests fail on buggy, pass on fixed")
