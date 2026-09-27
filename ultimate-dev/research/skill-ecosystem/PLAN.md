# Ecosystem intake — plan

Status: in progress. Written after triage, before implementation.
Owner decision required at **D2** and **B6**.

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
| A1 | 4 roles shipped but absent from `delegation.md`; SKILL.md line 285 claims dispatch *is* tabulated. Fix the table, then make the claim mechanically checked. | found, not fixed |
| A2 | Installed copy at `~/.agents/skills/ultimate-dev` is stale — loads "Seven roles". Observed again this session, not assumed. | found, not fixed |
| A3 | Add a validator rule: every `agents/*.md` must appear in the dispatch table. Asserts a *named thing*, not a count. | pending |

A1 is first because it is a false claim already in a commit, and because the
recurring defect class in this project is structure satisfied while contents are
wrong. Shipping 15 roles of which 4 are unroutable is that defect again.

## B — Research and verdicts

| # | Task | State |
|---|---|---|
| B1 | Survey `anthropics/skills`, `vercel-labs/agent-skills` — read every SKILL.md, classify tool-bound vs neutral, name the judgement encoded | running |
| B2 | Survey `openai/skills`, `ComposioHQ/awesome-claude-skills`, `alirezarezvani/claude-skills` | **done** |
| B3 | Survey role taxonomies — `msitarzewski/agency-agents`, `wshobson/agents`, `github/awesome-copilot`, `VoltAgent/awesome-agent-skills`. Classify SUBSTANTIVE vs PERSONA | running |
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
| C3 | **One eval per adopted role.** A role with no case is decoration. This is the step that was skipped for all 11 current roles. | pending |

## D — Self-evolution

| # | Task | State |
|---|---|---|
| D1 | Diagnosis, **done**: our `skills/skill-creator/` has **no `scripts/` directory**. It specifies a `VALIDATING → VALIDATED` gate and ships no mechanism to execute it. The gate is prose. Self-evolution is therefore currently impossible to *demonstrate*, not merely ungated. | done |
| D2 | **Owner decision:** vendor the external `portable-agent-skill-creator` scripts (11 files, verified present at `~/.agents/skills/portable-agent-skill-creator/scripts/`) into our `skill-creator/scripts/`, or write our own minimal gate checker. | **needs decision** |
| D3 | Make the promotion gate executable: a checker that can *fail* a candidate that lacks a held-out case | pending |

Note: the external harness was previously recorded as removed. It is present.
That earlier note was wrong.

## E — Outstanding debt (unchanged, tracked so it is not lost)

| # | Task | State |
|---|---|---|
| E1 | Run the 25 unrun `NM-*`/`TN-*` guard cases in both arms | not started |
| E2 | Author objective assertions for `FC-*` and `SC-*` (zero executed) | not started |
| E3 | 193 record violations across 100 `examples/` records — deliberate, tracked | not started |

---

## Rejected, and why

- **Importing a domain-agent taxonomy** (~100 roles from `agency-agents`).
  Pending B3's SUBSTANTIVE/PERSONA ratio, but the prior is that most are persona.
  A role with no procedure is a paragraph that costs context and changes nothing.
- **Adopting skills requiring a paid API or vendor CLI** (`rube` MCP, LangSmith,
  Figma, Cloudflare). Tool-binding is disqualifying under the user's constraint.
- **Rewriting the historical `examples/` records** to satisfy rules that postdate
  them. Reported as debt instead.
