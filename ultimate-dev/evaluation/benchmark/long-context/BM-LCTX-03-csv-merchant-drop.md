## BM-LCTX-03 — One question about a 3,600-row CSV

**Class:** long-context
**Domain:** data
**Rung:** R1 Structured
**Scale:** L2
**Primary metric:** task success, with the value traceable to an observed command
**Score rule:** rate

**Fixture:** `transactions_2026-03.csv`, 3,600 rows, columns `txn_id,ts,merchant_id,
amount_eur,kind,status` where `kind` is one of `sale`, `refund`, `chargeback`.
A merchant, `M-2211`, has €118,400 of `sale` volume in February and €61,900 in
March — the largest drop, €56,500. Refunds and chargebacks for M-2211 total
€9,800 in March, so a naive net figure gives a smaller drop. The correct answer
under the stated exclusions is **€56,500**, and the excluded rows are what make
the question interesting.

**Prompt:**
> In `transactions_2026-03.csv`, which merchant saw the largest drop in EUR
> volume between February and March? Exclude refunds and chargebacks — I want
> gross sales, not net.

**Expected behaviour:**
1. Treat this as a query, not a read. The file is 3,600 rows; loading it to reason
   over is unnecessary and is the failure being measured.
2. Compute it with a deterministic tool, filtering `kind = 'sale'` **before**
   aggregating, and grouping by merchant and month.
3. Compute the difference per merchant and take the maximum drop, not the minimum
   revenue.
4. Report the merchant, the two monthly figures, and the drop.
5. Note the exclusions that were applied, so the answer is reproducible.

**Pass criteria:**
- `M-2211` is the reported merchant.
- The reported drop is €56,500, computed on `kind = 'sale'` rows only.
- Refunds and chargebacks are excluded before aggregation, not subtracted
  afterwards — the resulting figure distinguishes the two.
- The computation was executed; the quoted numbers appear in observed output.
- The February and March gross figures for the reported merchant are both shown.
- Agent steps ≤ 5.

**Fail criteria:**
- The CSV is read into the response and reasoned over rather than queried.
- A drop of €46,700 (net of the €9,800) reported, or any figure that includes
  refunds.
- The merchant with the largest absolute March volume reported, confusing size
  with decline.
- A value quoted that no command produced.
- A `pandas` script written and then not run, with its predicted output reported.
- Confidence stated as high when the aggregation order was never verified.

**Trap:** The file is small enough to fit in context, which is exactly the
condition under which an agent reads it instead of querying it, and reading it
gives a *plausible* answer: the numbers are all there, and an agent scanning
3,600 rows will often find the right merchant. The correctness therefore does not
discriminate, which is why the pass criteria are written against the method as
well as the value. The second trap is the filter order. Applying the exclusion
after summing is the natural way to write it and produces €46,700 — a real
number, internally consistent, wrong, and reachable by a run that is otherwise
careful. The third is the direction: "largest drop" is easy to read as "smallest
in March", and under that misreading the answer is whichever merchant happens to
have the thinnest month, which is a different merchant entirely and just as
plausible.
