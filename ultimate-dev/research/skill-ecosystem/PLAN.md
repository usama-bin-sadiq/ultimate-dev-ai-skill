# Ecosystem intake — plan

Status: **largely closed.** Written after triage, before implementation, and left
reading as live long after it stopped being one. Sections A and D are done; B and
C are not, and are the only work this plan still describes. Every state below was
re-verified against the tree on 2026-09-30 rather than carried forward.
Owner decision still required at **B6** and **D2**.

The states here were hand-maintained and had drifted to the point of asserting
that finished work was unfixed — a tracked document that lies is worse than no
document. The drift is not repeated: the claims A1–A3 and D3 carry are now
enforced by `tools/validate-skills.py` and by the existence of
`check-gate.py`, so they cannot rot again. This plan's own state column is not
mechanically checked, and a plan's state column is a snapshot rather than a
contract, so it is maintained by hand and dated.

## Objective

Survey the public agent/skill ecosystems, decide per candidate with a recorded
reason, resolve overlaps to a single winner, adapt what survives to the role
contract, and make each adopted role reachable from a decision and covered by an
eval.

## Success criteria

1. Every candidate from every surveyed repo has a verdict and a reason in one file.
2. No two shipped roles share trigger scope (mechanically checked, not asserted).
3. Every shipped role is reachable from `references/delegation.md`.
4. Every shipped role has at least one eval case.
5. `validate-skills.py --strict` passes and would fail if 1–3 regressed.

## Failure criteria — what would make this work worthless

- A catalogue of roles that exist but never fire (the defect the critic found in
  the decision records, repeated one level up).
- Adopting a persona prompt with no procedure in it.
- Recording "Yes" verdicts that are never implemented. This already happened
  once: five verdicts, one shipped.

---

## A — Repair what I broke (blocking; do first)

| # | Task | State |
|---|---|---|
| A1 | 4 roles shipped but absent from `delegation.md`; SKILL.md line 285 claims dispatch *is* tabulated. Fix the table, then make the claim mechanically checked. | **fixed** — all 286 `agents/*.md` appear in the table; verified 2026-09-30 |
| A2 | Installed copy at `~/.agents/skills/ultimate-dev` is stale — loads "Seven roles". Observed again this session, not assumed. | **fixed** — the string is gone and the installed copy matches the repo; verified 2026-09-30 |
| A3 | Add a validator rule: every `agents/*.md` must appear in the dispatch table. Asserts a *named thing*, not a count. | **fixed** — `tools/validate-skills.py` enforces it; verified 2026-09-30 |

A1 is first because it is a false claim already in a commit, and because the
recurring defect class in this project is structure satisfied while contents are
wrong. Shipping 15 roles of which 4 are unroutable is that defect again.

## B — Research and verdicts

| # | Task | State |
|---|---|---|
| B1 | Survey `anthropics/skills`, `vercel-labs/agent-skills` — read every SKILL.md, classify tool-bound vs neutral, name the judgement encoded | **no outcome recorded** — the row said "running" with nothing to show for it. Treated as not done. |
| B2 | Survey `openai/skills`, `ComposioHQ/awesome-claude-skills`, `alirezarezvani/claude-skills` | **done** |
| B3 | Survey role taxonomies — `msitarzewski/agency-agents`, `wshobson/agents`, `github/awesome-copilot`, `VoltAgent/awesome-agent-skills`. Classify SUBSTANTIVE vs PERSONA | **no outcome recorded** — as B1. |
| B4 | Synthesise into `VERDICTS.md`: one row per candidate, with reason | pending |
| B5 | Dedupe: group by trigger scope, pick one winner per group, record what was rejected and why | pending |
| B6 | **Owner decision:** which surviving candidates to actually ship | pending |

### Findings so far (from B2)

- `openai/skills` is **deprecated**; its README advertises a directory that 404s.
- `ComposioHQ/awesome-claude-skills` is **96% vendor wrappers** — 832 of 864 files
  are `*-automation` shims requiring a paid MCP gateway. It is a sales funnel.
- `alirezarezvani/claude-skills` holds the real material, but ~90% of its 388
  skills are one house template applied to a domain. Value is concentrated in
  roughly a dozen.
- One skill (`developer-growth-analysis`) **instructs citation fabrication** — its
  worked example contains invented links. Actively hostile to this kernel; recorded
  as a rejection, not a candidate.

### Highest-value transferable mechanisms (B2)

| Mechanism | Source | Why it fits here |
|---|---|---|
| Source hierarchy + "never invent a number" + gaps over invented precision | `stock-analysis` | The kernel's central claim, stated by a domain expert who needs it more than we do |
| Guardrail as a **code precondition**, not prose | `red-team` | Directly answers "make it self-evolving" — see D |
| Loop prevention: max depth 2, no cycles, carry the chain, forced `Confidence:`/`Caveat:` | `agent-protocol` | Makes delegation recursion a mechanical check |
| Bounded autonomy: escalate at >30% ambiguity, never escalate without options | `spec-driven-workflow` | Sharpens the kernel's escalation trigger into a number |
| KNOWN/INFERRED/UNKNOWN tags; never code against an UNKNOWN; YAGNI ladder with a safety carve-out | `zero-hallucination-coder` | The carve-out list is the part we lack: a reduction rule that must not eat validation |
| "Reject activity goals"; good/weak contrast pairs | `define-goal` | Makes a vague objective a detectable failure rather than a judgement call |
| 🟢/🟡/🔴 confidence tagging | `SKILL-AUTHORING-STANDARD.md` | Alternative to bare `high` — names the grade |
| Never name a skill after a built-in command (CI-enforced) | `SKILL-AUTHORING-STANDARD.md` | A real numbered bug worth not repeating |

## C — Adopt and adapt

| # | Task | State |
|---|---|---|
| C1 | Select survivors from B5 | pending |
| C2 | Adapt each to the role contract: procedure, output contract, prohibitions, tool-neutral wording | pending |
| C3 | **One eval per adopted role.** A role with no case is decoration. This is the step that was skipped for all 11 current roles. | **open, and the number moved** — the corpus grew from 11 roles to 286; none has a role-specific case. The 128 cases are *routing* cases (98 expect a trigger, 17 domains), so roles are exercised but never individually attributed. Read the scope note in E before costing this as 286 cases. |

## D — Self-evolution

| # | Task | State |
|---|---|---|
| D1 | Diagnosis, **done**: our `skills/skill-creator/` has **no `scripts/` directory**. It specifies a `VALIDATING → VALIDATED` gate and ships no mechanism to execute it. The gate is prose. Self-evolution is therefore currently impossible to *demonstrate*, not merely ungated. | done |
| D2 | **Owner decision:** vendor the external `portable-agent-skill-creator` scripts (11 files, verified present at `~/.agents/skills/portable-agent-skill-creator/scripts/`) into our `skill-creator/scripts/`, or write our own minimal gate checker. | **needs decision** |
| D3 | Make the promotion gate executable: a checker that can *fail* a candidate that lacks a held-out case | **fixed** — `skills/skill-creator/scripts/check-gate.py`, with `--require` to exit non-zero; verified 2026-09-30 |

Note: the external harness was previously recorded as removed. It is present.
That earlier note was wrong.

## Scope note on C3 — read before costing it

C3 asks for one eval per role, and the role count went 11 → 286. Taking that
literally is 286 cases, and it is the wrong next move for three reasons:

1. **It measures something else.** The corpus is built to measure *routing* and
   *false-trigger rate*. 98 of its 128 cases already expect a trigger, across 17
   domains. A per-role case would measure whether one role produced a good
   answer, which is a different programme with a different instrument.
2. **The instrument does not exist yet.** A role case needs a decidable
   assertion about that role's output. `evaluation/assertions.json` documents
   why a *generated* assertion is worse than none: one that passes both arms
   measures nothing while appearing to. Hand-authoring 286 of them is a
   multi-week build, not a task.
3. **It is not where the evidence points.** Every paired run in
   `evaluation/RESULTS.md` is a null — Run 2 by hand-read pairs (two baseline
   wins, one skill win, one tie), Run 3 on quality-graded assertions (0
   discordant). The corpus is not yet showing the kernel beating baseline on
   anything. Widening coverage before the existing coverage can detect a
   difference would produce a larger null.

So C3 stays open and is deliberately *not* the next move. E4 is: run the classes
`RESULTS.md` already names as the ones that would make a run informative.

### Gap analysis, in the shape `skills/skill-creator` requires

The skill-creator's Step 0 was run on the "0 of 286 roles have an eval" finding
before any code was written, because four of its six gap categories are closed
without creating a skill and three of those four are mistakes a run makes *while
believing* it is closing a gap.

```text
GAP      No measurement attributes a quality outcome to an individual shipped
         role, so a role that fires correctly and answers badly is invisible.
CAUSE    not-a-capability
EVIDENCE 0 of 286 `agents/*.md` appear as a subject in `evaluation/`. The 128
         cases carry `correct_mode`, `expected_output` and `trap`, and 98 expect
         a trigger, so routing into a role is exercised -- but no case names a
         role as the thing under test. Separately: every paired run in
         `evaluation/RESULTS.md` is null (Run 2 two baseline wins / one skill win
         / one tie; Run 3 quality-graded, 0 discordant), and
         `evaluation/assertions.json` states that an assertion passing both arms
         "measures nothing while appearing to."
FIX      Not to build. Two cheaper actions first: (a) run the `FC-*`/`SC-*`
         classes RESULTS.md names as the difference-detecting set (E4), and
         (b) decide explicitly whether per-role cases are in scope, because
         that is a measurement-programme decision, not a defect.
REUSABLE Step in this plan. The engine's output here is this record, not a skill.
```

The expensive failure this shape exists to prevent is building a 286-case
generator to paper over a question nobody has answered yet: whether per-role
attribution is the measurement this kernel needs at all.

## E — Outstanding debt (tracked so it is not lost)

| # | Task | State |
|---|---|---|
| E1 | Run the 25 unrun `NM-*`/`TN-*` guard cases in both arms | not started. **Blocked on runtime credits.** This is the false-trigger rate — the metric the corpus exists for — and it currently rests on `n = 3` with a 95% upper bound of 63%. `RESULTS.md` asks for `n = 20` per arm. |
| E2 | Author objective assertions for `FC-*` and `SC-*` (zero executed) | **partly done, and partly deliberate.** `evaluation/assertions.json` now carries 9 of 128 (2 BM, 6 CM, 1 FC), up from 3 at Run 3. The remaining nulls are a *policy*, not neglect: "an assertion that passes both arms measures nothing while appearing to." Widening this to all 30 FC/SC cases would produce theatre. |
| E3 | 193 record violations across 100 `examples/` records — deliberate, tracked | not started — by decision, keep |
| E4 | **New.** Run the `FC-*` and `SC-*` cases, which `RESULTS.md` names as the ones that would make a run informative rather than null | not started. **This outranks E1.** Every paired run so far has been a null, and these are the classes written to detect the difference. |

---

## Rejected, and why

- **Importing a domain-agent taxonomy** (~100 roles from `agency-agents`).
  Pending B3's SUBSTANTIVE/PERSONA ratio, but the prior is that most are persona.
  A role with no procedure is a paragraph that costs context and changes nothing.
- **Adopting skills requiring a paid API or vendor CLI** (`rube` MCP, LangSmith,
  Figma, Cloudflare). Tool-binding is disqualifying under the user's constraint.
- **Rewriting the historical `examples/` records** to satisfy rules that postdate
  them. Reported as debt instead.
