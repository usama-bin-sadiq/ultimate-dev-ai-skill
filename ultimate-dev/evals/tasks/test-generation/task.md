`stats.py` exports `mean(values)` and `median(values)`. It has **bugs**:
your tests must catch them. A corrected version is at `fixed.py`.

Write a test file to `out/test_stats.py` with these properties:

- It is runnable directly: `python3 out/test_stats.py`. No test framework.
- It imports `mean` and `median` from a module named `stats` (which will be on
  the path when it runs).
- It asserts real expected values, not just that a return value exists.
- It covers at least: `mean` of `[2,4,6]`, `median` of an even-length list,
  `median` of an odd-length list.
- It prints a line per check and exits non-zero if any check fails.

Run it against `fixed.py` to confirm it passes.
