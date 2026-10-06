`calc.py` defines `clamp` and `percentile`. Exactly one of them is
defective. `percentile` raises `IndexError` when called with `p=1.0`.

Do this:

1. Find the single defect. Write a short root-cause note to `out/cause.md` —
   two to four sentences. It must name the specific expression that is wrong and
   the corrected expression.
2. Write the **whole corrected module** to `out/fixed.py`. Keep both functions
   and their names. `clamp` must stay exactly as it is; only fix the defect.

Do not modify `calc.py`.
