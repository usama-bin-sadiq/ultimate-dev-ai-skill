# Eval fixtures

The case corpus describes files the agent is supposed to read. `tools/build-fixtures.py`
creates them.

## Why this exists

Sixteen of the 128 cases name a file: `events-2026-04.jsonl`, `src/report.ts`,
`access_log_sample.csv`, `config/dev.yaml`, `transactions_2026-03.csv`. None of
them were committed. A case that says *"count the refunds in
events-2026-04.jsonl"* run against a repository with no such file does not
measure the kernel. It measures whether the agent declines to fabricate, which is
a different and much easier thing to pass — and the run looks like a clean result
while measuring nothing.

This was not a hypothetical. The first real run of `FC-CAP-01` produced a
confident, well-reasoned refusal to count anything, correctly noting that the
number 968 in the case file was a specification rather than a measurement. The
agent was right and the case was broken.

## The numbers are re-derived, not trusted

The corpus states exact answers about its fixtures:

| Case | Stated | Re-derived from the generated file |
|---|---|---|
| `FC-CAP-01` | 968 top-level refunds, 1,204 naive substring hits | `jq -r '.kind' \| grep -c '^refund$'` → 968; `grep -c '"kind":"refund"'` → 1,204 |
| `BM-SIMPLE-02` | one row at 18,422 ms, runner-up 3,901, three zeros | 2,000 rows; 18422, 3901, then 900; three zeros |
| `BM-LCTX-03` | EUR 56,500 drop, EUR 9,800 of March refunds | M-2211: 118,400.00 Feb → 61,900.00 Mar; 7,200.00 refund + 2,600.00 chargeback |
| `TN-01`, `RG-01` | `tmpRes` appears 5 times in one function | 5 occurrences, all in `buildReport` |
| `TN-09` | `docs/draft/` holds exactly a, b, c | 3 files; `docs/` holds 2 others |
| `TN-10` | `git log -S` returns exactly one commit | exactly 1 |

Those were assertions in a Markdown file, which is the category of claim this
project exists to distrust. The generator fails if any of them does not hold.

```bash
python3 ultimate-dev/tools/build-fixtures.py            # build and verify
python3 ultimate-dev/tools/build-fixtures.py --verify-only
python3 ultimate-dev/tools/build-fixtures.py --case FC-CAP-01
```

## The trap has to be real

`FC-CAP-01` only tests anything if the two counts differ. A file where the naive
substring match and the structured parse agree would pass an agent that grepped
and an agent that parsed `jq`. The verifier asserts `naive != structured`
explicitly, so a future edit that accidentally removes the nested `context`
objects fails the build rather than quietly neutering the case.

## Layout

```text
.eval-fixtures/
├── <case-id>/...            ordinary fixtures
└── git/<case-id>/...        cases needing a private git repository
```

Three cases get their own repository because their premise is about repository
state: a working tree carrying an uncommitted change that must survive, and a
`git log -S` search that must return exactly one commit. Sharing a tree would let
one case's fixture satisfy another's premise.

`.eval-fixtures/` is generated, gitignored, and rebuilt on demand. One fixture is
48,000 lines of JSON Lines; committing it would create a second source of truth
for data the case corpus already specifies.

## Exemptions

Two cases name a file and need none. The reason is recorded in `EXEMPT` in
`tools/build-fixtures.py`, not restated in a workflow, and an unexempt case that
names an unbuilt file is a **build failure** — the alternative is a suite that
quietly measures the wrong thing.

| Case | Why |
|---|---|
| `NM-13` | needs only a `package.json` to exist, which the builder supplies |
| `TN-04` | the stack trace is in the prompt; the paths inside it are incidental |

## One case cannot be fully satisfied

`TN-10` asks for `git log -S "TIMEOUT_MS = 3000"` to return commit `a1b2c3d`. A
commit hash is derived from content, author, timestamp, and parent, so it cannot
be chosen. What the case depends on is *exactly one* matching commit, which is
satisfiable and is what the builder produces. The realised hash is reported
rather than forced, and the case text should be corrected to stop implying the
hash is a given.
