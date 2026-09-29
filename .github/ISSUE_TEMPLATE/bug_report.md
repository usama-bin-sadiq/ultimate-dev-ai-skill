---
name: Bug report
about: A defect in the kernel, an agent, a skill, or the evaluation harness
title: "<area>: <specific failure or symptom>"
labels: bug
assignees: ''
---

<!--
Title convention: <area>: <specific symptom>
  areas: skill (SKILL.md), agents/<name>, skills/<name>, evaluation, docs, arch
  The project lives under `ultimate-dev/` in this repository, so every path
  below is written `ultimate-dev/...`. Copy them as-is.
  e.g. triage: assigns R3 to a single-constant change
       verification: reports PARTIAL as VERIFIED
       eval: BM-SIMPLE-01 does not detect the over-orchestration it exists to catch
If you cannot name an area yet, say so in the summary. Do not file as a general
"the kernel is worse" report — a run that fails somewhere is not yet a defect.
-->

## Summary

<!-- One or two sentences: what the kernel did, and what it should have done
     instead. Name the deviation, not the topic. -->

## Defect class

The kernel makes a two-sided claim — it must be rigorous when the work is hard
*and* stay out of the way when the next action is already determined. Both
sides are bugs. Which one is this?

- [ ] **Over-orchestration** — ceremony on work that did not need it (R3
      reasoning on an R0 task, a plan for a one-line change, a capability
      search that found nothing). See `ultimate-dev/evaluation/benchmark/simple/`.
- [ ] **Under-orchestration** — a confident direct answer on work that needed
      more: no plan, no capability check, no verification.
- [ ] **Wrong effort assignment** — the rung or scale was defensible at
      Step 0 but never escalated or de-escalated when reality diverged.
- [ ] **Verification defect** — `VERIFIED` without evidence, `PARTIAL`
      reported as `VERIFIED`, or a check that cannot fail.
- [ ] **Recovery defect** — blind retry, budget spent without replanning, or
      escalation that was not warranted.
- [ ] **Context defect** — loaded too much and drowned, or too little and
      decided on unexamined assumptions.
- [ ] **Capability defect** — wrong tool chosen, or a skill minted for a one-off.
- [ ] **Security / trust defect** — injection, poisoned capability, unsafe
      action, or evidence accepted that should not have been. Please see
      `ultimate-dev/evaluation/security-cases/` and prefer a private report if
      the disclosure itself is sensitive.
- [ ] **Documentation defect** — the docs are wrong, contradictory, or
      disagree with `ultimate-dev/SKILL.md`. Docs are part of the deliverable here.
- [ ] **Harness defect** — an eval, fixture, or metric that mismeasures.

## Where in the loop

<!-- Which stage produced the defect. The kernel can be re-entered at any
     boundary, so name the boundary, not just the phase.
     RECEIVE · UNDERSTAND · TRIAGE · DECIDE · ACQUIRE · PLAN · EXECUTE ·
     OBSERVE · VERIFY · RECOVER · SYNTHESIZE · SELF-EVALUATE · LEARN -->

Stage: <!-- e.g. TRIAGE -->

## Artefact

<!-- Which file's behaviour is wrong. Be specific: the defect is usually in one
     instruction, not in the design as a whole. -->

- [ ] `ultimate-dev/SKILL.md`
- [ ] `ultimate-dev/agents/<name>.md`
- [ ] `ultimate-dev/skills/<name>/`
- [ ] `ultimate-dev/evaluation/`
- [ ] `ultimate-dev/docs/` or `ultimate-dev/ARCHITECTURE.md`
- [ ] Other: <!-- path -->

## Environment

Diagnostics are collected so the run can be reproduced. If a value cannot be
obtained, write `Unavailable: <reason>` — do not guess, and do not let a
missing value block the report.

- Commit / ref: <!-- `git rev-parse --short HEAD` -->
- opencode version: <!-- `opencode --version` -->
- Model: <!-- held constant per ultimate-dev/evaluation/methodology.md; state which -->
- Active skill: <!-- e.g. ultimate-dev @ R2 / L3 — the rung and scale the run chose -->
- Agent used: <!-- e.g. verifier, critic; or "none" -->
- OS: <!-- `uname -a` -->
- Shell: <!-- `$SHELL` -->
- Other runtime config: <!-- plugins, custom instructions, AGENTS.md -->

## Reproduction

<!-- The objective, in the user's terms, plus the minimum steps that show the
     deviation. Keep it minimal: an issue that needs three files of setup is
     usually a design disagreement, not a bug. -->

Objective: <!-- the request as a user would phrase it -->

1. <!-- step -->
2. <!-- step -->
3. <!-- step -->

Linked eval case: <!-- e.g. BM-SIMPLE-01, FC-VER-03, FC-CAP-02 — or "none" -->

## Expected Behavior

<!-- The behaviour the docs require. Quote the instruction you are holding the
     run to, and cite the file. "It should be smarter" is not a specification. -->

## Actual Behavior

<!-- What happened, in the run's own words where possible. Include the actual
     rung/scale chosen, and the exact point where it departed. -->

Chosen rung/scale: <!-- e.g. R3 / L3 -->

Evidence of departure: <!-- the artefact, transcript, or metric that shows it -->

## Additional Context

<!-- Any of: transcript excerpt, score/metric, frequency, workarounds tried,
     whether it reproduces every time, related issues, screenshots.

     Redact tokens, API keys, private URLs, usernames, and confidential data
     before pasting. If you are unsure whether something is sensitive, leave it
     out and describe it. -->

Reproducibility: <!-- every time / intermittent / once -->

Related workarounds: <!-- what you did instead, and whether it helped -->

Anything else: <!-- -->
