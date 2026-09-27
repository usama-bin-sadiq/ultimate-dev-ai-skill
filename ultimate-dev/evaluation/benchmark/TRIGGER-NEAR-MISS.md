# Trigger near-misses

The hard half of the trigger problem. `TRIGGER-NEGATIVES.md` holds tasks that are
obviously not kernel work. This file holds tasks that **share the kernel's
trigger vocabulary and must still not trigger it.**

The kernel's description fires on: open-ended, multi-step, cross-domain,
unfamiliar, high-consequence, "needs a plan", "must be verified", "a repeated
manual procedure should become a reusable skill". Every case below contains at
least one of those words or its meaning, and every one of them should be answered
directly.

This is where false triggers actually come from. A kernel that passes the trivial
negatives can still fail badly here, because here the naive signal is genuinely
present — the request really does sound like planning work, and the correct
behaviour is still to just do it.

## How to score

A case fails if the run produces **any** of:

- a triage statement, a complexity assessment, or a rung selection
- a task model, a plan, a work-unit breakdown, or a dependency graph
- a decision record, a capability search, or a capability-creation attempt
- a delegated role, a subagent, or a verification ceremony
- more than the number of agent steps listed in the case

**A correct answer delivered through a plan is still a failure.** The answer
quality is not the question. Over-orchestration costs the user attention whether
or not the output is right, and that is the defect this file exists to catch.

Where a case says "verify", the kernel may run the tool that checks the thing.
Running `tsc` is not a verification ceremony. Reassuring the user that you have
considered verification is.

---

## NM-01 — "Plan" used as a verb meaning something else

**Prompt:** "These three shell commands run in the wrong order — plan the migration so the
backfill happens after the index exists."
**Must not:** emit a work-unit table or a dependency graph.
**Steps:** ≤ 4.
**Trap:** the word "plan" plus a genuine ordering constraint. The whole task is
"swap two lines", and the word is doing ordinary English work. A kernel matching
on the token "plan" produces a six-row schedule for a two-line edit.

## NM-02 — "Multi-step" as user description of a single tool call

**Prompt:** "How do I pass multiple steps to the Terraform `apply` command?"
**Must not:** decompose the task.
**Steps:** ≤ 2.
**Trap:** "multi-step" is the kernel's own phrase, used here to ask a syntax
question. Answer the syntax.

## NM-03 — "Verify" that means "check my understanding"

**Prompt:** "Verify that I'm reading this right — does a 429 with `Retry-After: 0`
mean retry immediately?"
**Must not:** run a verification procedure or state a verification status.
**Steps:** ≤ 2.
**Trap:** "verify" plus a real question. The user wants a second opinion, not an
audit. Answering with `VERIFIED` and an evidence chain is a category error.

## NM-04 — A one-file change described in engineering language

**Prompt:** "Refactor this function to be more readable — it's a bit gnarly."
**Must not:** produce a plan, though "refactor" implies multi-step.
**Steps:** ≤ 3.
**Trap:** "refactor" and "more readable" imply judgement over many lines, and the
judgement is: read the function, improve it, stop. The scope is one function. The
trigger vocabulary is present and the trigger is absent.

## NM-05 — "Unfamiliar" used about the user's own situation, not yours

**Prompt:** "I'm unfamiliar with this codebase — where does the auth logic live?"
**Must not:** treat unfamiliarity as a reason to escalate reasoning.
**Steps:** ≤ 3.
**Trap:** the user's unfamiliarity is not your gap. A search answers this. Loading
the context ladder because *they* are lost inverts the rule, which is about what
*you* need to decide well.

## NM-06 — "High-consequence" attached to something reversible

**Prompt:** "This is important — rename `userId` to `user_id` across the API layer."
**Must not:** escalate the rung on the word "important".
**Steps:** ≤ 4.
**Trap:** urgency language on a git-revertible change. The triage input is
reversibility and consequence, and reversibility is total. A kernel that reads
"important" as R3 has confused tone with triage.

## NM-07 — Asking for a template, not a procedure

**Fixture required:** no
**Self-contained because:** a template is generated, not read from a repository

**Prompt:** "Can you give me a bug report template for this project?"
**Must not:** run the bug-reporting workflow.
**Steps:** ≤ 2.
**Trap:** a template *describes* a process, and describing one is not performing
it. Producing the artefact is the task.

## NM-08 — "Skill" mentioned, but as a word in the content

**Fixture required:** no
**Self-contained because:** a platform question, no repository involved

**Prompt:** "In k8s, what's the difference between a `ClusterRole` and a skill?"
**Hmm — rephrase: "What's the difference between a `ClusterRole` and a
`RoleBinding`?"
**Must not:** enter capability resolution, and do not offer to create anything.
**Steps:** ≤ 2.
**Trap:** a user working in a domain where "skill" is a common noun. Any
capability-search behaviour here is a false positive on vocabulary.

## NM-09 — A plan already exists and needs implementing

**Prompt:** "Here's the migration plan we agreed — implement step 3."
**Must not:** re-plan, re-triage, or produce a new task model.
**Steps:** ≤ 4.
**Trap:** the plan is an *input*. Re-deriving it is the waste; implementing the
named step is the work. A kernel that cannot tell "here is a plan, execute it"
from "there is no plan, make one" will handle both identically.

## NM-10 — "Unfamiliar territory" where the answer is one lookup

**Fixture required:** no
**Self-contained because:** a library default, answerable from documentation alone

**Prompt:** "What's the default `keepAlive` in Node 22's undici?"
**Must not:** escalate because the API surface is unfamiliar to you.
**Steps:** ≤ 2.
**Trap:** unfamiliarity of the *runtime* rather than of the problem. This is
recall or one documentation lookup, and the honest rung is R0.

## NM-11 — Verification requested on a fact you can simply re-run

**Prompt:** "Can you double-check that this test actually fails without the fix?"
**Must not:** invoke a verification role or a three-check procedure.
**Steps:** ≤ 3.
**Trap:** "double-check" plus a security-shaped task. The user asked for one
specific observation. Reverting a line and re-running a test is the whole answer.

## NM-12 — A deliverable that happens to require several files

**Prompt:** "Add a CONTRIBUTING.md, a CODE_OF_CONDUCT.md, and a SECURITY.md for
this project."
**Must not:** decompose into work units or build a dependency graph.
**Steps:** ≤ 4.
**Trap:** three files looks like a project. It is three file writes with no
interdependence, and the cost of planning them exceeds the cost of doing them.

## NM-13 — "Carefully" as politeness

**Prompt:** "Could you carefully update the version number in package.json to 2.1.0?"
**Must not:** treat "carefully" as a consequence signal.
**Steps:** ≤ 2.
**Trap:** politeness markers read as severity if triage is done on tone. The
actual consequence is zero and the change is one line.

## NM-14 — Cross-domain in the description, single-domain in fact

**Fixture required:** no
**Self-contained because:** the error string to interpret is given inline in the prompt

**Prompt:** "Our frontend calls the billing API. The error message it gets back is
`invoice_state_invalid`. What does that mean?"
**Must not:** enter cross-domain mode or compose disciplines.
**Steps:** ≤ 2.
**Trap:** two systems are named, so "cross-domain" appears satisfied. The task is
one lookup in one domain. Cross-domain is a property of the *capability
requirements*, not of how many systems are named in the sentence.

## NM-15 — "Research" as one lookup

**Fixture required:** no
**Self-contained because:** a version lookup, no repository involved

**Prompt:** "What's the current stable version of Node?"
**Must not:** open a research procedure with a source table.
**Steps:** ≤ 2.
**Trap:** the answer is external and time-varying, which sounds like research. It
is one fetch. A research ceremony on this is the clearest possible over-spend.

## NM-16 — Repeated work, but you are being asked to do it once

**Prompt:** "We're doing this same migration for each of our 12 services. Do
`svc-01`."
**Must not:** propose turning it into a reusable skill.
**Steps:** ≤ 5.
**Trap:** this is the sharpest case in the file. The kernel's own description
fires on "a repeated manual procedure should become a reusable skill", and the
*pattern* genuinely is repeated. The user asked for one instance. Noticing the
pattern is correct; acting on it unasked is the failure. At most, mention the
pattern once, in one sentence, at the end.

## NM-17 — "High assurance" that is a formality

**Prompt:** "Before we merge, double-check the changelog dates are in the right
order."
**Must not:** enter R4 with a human checkpoint and a named approver.
**Steps:** ≤ 3.
**Trap:** "before we merge" reads as consequential. Reading five dates is not.
R4 is for irreversible or security-relevant work, and conflating "someone will
look at this" with "this is hard to undo" is how R4 becomes meaningless.

## NM-18 — An ambiguous request that is resolvable in one question

**Prompt:** "Fix the login bug."
**Must not:** produce a full task model with unknowns, assumptions, and a
success-criteria table before asking.
**Steps:** ≤ 3, ending in one question.
**Trap:** "fix the bug" genuinely is ambiguous, and the kernel genuinely should
ask. But the correct response to ambiguity at low cost is *one question*, not the
whole apparatus. A six-field task model before a clarifying question is
orchestration performed ahead of understanding.

## NM-19 — Delegation bait

**Fixture required:** no
**Self-contained because:** the regex to check is given inline in the prompt

**Prompt:** "Get a second opinion on whether this regex handles nested brackets."
**Must not:** dispatch `critic`, `verifier`, or any role.
**Steps:** ≤ 3.
**Trap:** "second opinion" is a request for a check, and the kernel has a role
whose entire purpose is that. Dispatching a role for a one-line regex is the
delegation cost with none of the benefit, and the role's context transfer will
cost more than the question.

## NM-20 — The meta-request

**Fixture required:** no
**Self-contained because:** a question about the agent's own behaviour, no workspace involved

**Prompt:** "Are you over-engineering this?"
**Must not:** produce a self-assessment in the kernel's own vocabulary.
**Steps:** ≤ 2.
**Trap:** the user is asking whether the kernel is behaving, and the tempting
answer is a triage report. Answer the question in plain language. Producing
`RUNG: R2, justified by reversibility` in response to "are you over-engineering
this" is the defect being complained about, performed in order to answer it.

---

## Summary

| Class | Count |
|---|---|
| Vocabulary present, trigger absent | 20 |
| Existing trivial negatives | 10 (`TRIGGER-NEGATIVES.md`) |
| Must-fire cases | see `TRIGGER-POSITIVES.md` |

The rule these 20 encode: **the trigger is a property of the work, not of the
words describing it.** Every case here contains the vocabulary. None of them
contains the work.
