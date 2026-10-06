Do three steps in order. Later steps depend on earlier ones.

**Step 1.** From `logs/app.log`, keep only the lines whose level is `ERROR` or
`WARN`. Write them to `out/filtered.txt`, in file order, unchanged.

**Step 2.** Count the kept lines per level. Write `out/counts.txt` with exactly
two lines, `ERROR` first then `WARN`, formatted as `ERROR=N` and `WARN=N`.

**Step 3.** Read `alert_threshold` from `config.json`. If the `ERROR` count is
**strictly greater** than the threshold, append the single line `ALERT` to
`out/filtered.txt`. Otherwise append the single line `OK`. Append it as the
last line of that file.
