# Skill discovery

Search before you design. Creation is the last option and by far the most
expensive one, and the search that skips it is the search that produces
proliferation. Record the result — including the negative one — so the next run
does not repeat the work you just did.

You are answering one question: **does anything that already exists cover this
gap?** A gap you have not searched for is a gap you have not proven.

## Search descriptions, not names

Names describe categories and categories lie. The description is the discovery
surface — it is the only text a future run will match against, so it is also the
only honest place to search.

- Search the **user goal**, in the user's vocabulary, not the implementation's.
  Someone asking for the capability will not use your noun for it.
- Search the **trigger condition**, including the vocabulary of the near-miss
  you wrote in `skill-contract.md`. Near-misses are where coverage hides.
- Then search the names, last, to catch the skill whose description is itself
  bad. A vague description is a discovery bug in that skill, not a reason to
  mint a second one — fix the description (`skill-testing.md` covers the
  trigger measurement that tells you which).

## Bound the search

Discovery is a cost like any other. Unbounded searching is as much a failure as
skipping it.

| Where | What to read | Stop when |
|---|---|---|
| Skill directories and their frontmatter | `name` and `description` of every skill | You have candidates or a clean sweep |
| The two or three nearest candidates | Their stated contract: inputs, outputs, failure modes | You can say what each does and does not do |
| Record structure and ledgers | Prior provenance entries for this gap | A prior negative result exists and still holds |
| Adapters, adapters registry, tool listings | Available deterministic operations | A script already does it |

Stop after a fixed budget — a handful of description reads and at most three
contract reads. If nothing is found, the answer is a clean negative, not grounds
for reading everything.

## A stated contract is an assertion, not evidence

A candidate skill's contract is a claim its author made. Before you rely on it,
check that the claim and the body agree: do the declared outputs exist, do the
named failure modes appear in the procedure, does the description match what the
body actually does. A skill whose description promises more than its body
delivers is worse than no skill, because a future run trusts the description.

If the claim cannot be checked cheaply, treat the capability as unvalidated and
either validate it before use or route around it.

## Near-misses: extend, do not rebuild

Most of the time you will find a skill that covers 80% of the gap. That is the
strongest argument against creation, not a reason to start fresh.

| The missing 20% is | The answer |
|---|---|
| A variant of the same procedure, a new edge case | Extend the existing skill — new version, regression check (`skill-versioning.md`) |
| A new step that the existing skill's structure already anticipates | Extend |
| A different procedure with its own decisions | Compose, or create — and say why the existing one could not absorb it |
| The existing skill contradicts what you need | Fix or deprecate the existing skill first; a second skill on the same trigger is the defect |

Two skills that fire on the same request split the trigger signal, and the user
receives two half-processes instead of one. That cost is paid permanently and is
invisible in a single run.

## Record the negative result

Write a discovery entry before you design, and keep it even when you go on to
create. It is what makes the next run cheap.

```text
gap:        <what could not be done with what exists>
searched:   <where, in the user's vocabulary, with the bound you set>
candidates: <each candidate, and precisely what it does not cover>
verdict:    reuse | compose | create | acquire
why not:    <the earlier rung, and the evidence it failed on>
changes_if: <the observation that would reverse this verdict>
```

`changes_if` is the field that keeps the entry alive: it says what new evidence
would make the verdict wrong, instead of leaving a permanent, unchallengeable
claim on file.

## Stop conditions

Stop searching and route to reuse or compose when a candidate covers the need,
when a chain of existing capabilities produces the result, or when the gap turns
out to be one occurrence. Stop searching and continue to design only when the
entry above reads `create` and the four checks in `skill-design.md` all pass.
