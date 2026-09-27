# Make the install section of the README clearer

**Objective:** "Make the install section of `README.md` clearer — people are
getting stuck at the platform-specific command."

**Domain:** Writing — technical documentation
**Scale:** L1   **Reasoning rung:** R0

## 0. Triage

- **Complexity** — one section, one file, one class of reader confusion. Nothing
  downstream of this edit affects anything.
- **Uncertainty** — low on method. Improving a section's clarity is not a
  research question. The one thing worth checking is whether the problem still
  exists, which is one `git log`.
- **Consequence** — low. A confusing README costs a few minutes per reader. Nobody
  is harmed, nothing is at risk, and the next person to read it will read it again
  in six months.
- **Reversibility** — free. One file, one commit.

**Rung: R0. Scale: L1.** The next correct action is already determined: read the
section, see whether the described problem is present, fix it if it is, and report.

**Why not R1.** There is no dependency chain and no assumption that could be wrong
in a way that changes the plan. The one genuine uncertainty — *is the problem still
there?* — is resolved by a single command, and a command is not a plan step.

**Why not R2, and this is the trap.** "People are getting stuck" is a
research-shaped statement. It invites a plan: interview five new users, instrument
the docs, establish a clarity baseline, design a rewrite, verify comprehension. That
is a legitimate project and it is emphatically not what was asked, because the
*next action* — read the section — is already determined and its result either
answers the request or tells us it is moot. This is `anti-patterns.md`'s
orchestrating-a-trivial-task, and it is the failure mode this trace exists to
avoid.

**Escalate when:** the section is already clear, in which case the request is based
on a stale observation and the useful response is to report that, not to invent work.
**De-escalate when:** — already at the floor.

## 1. Task model

- **Objective** — the install section of `README.md` is not the reason a new
  contributor gets stuck, or it is and it is fixed in one edit.
- **Requirements** — the platform-specific command is present and unambiguous; any
  factual claim in the section is true.
- **Constraints** — "clearer" is not a specification, so the standard applied is the
  narrower one: is what it says *true*, and is the platform-specific command
  findable without reading the whole section?
- **Unknowns**
  - U1: does the described problem still exist? **Blocking**, and it is the first
    thing to check because it may dissolve the task entirely.
  - U2: is any factual claim in the section wrong? **Not blocking**, but a factual
    error is a clarity error that outranks any prose improvement.
- **Assumptions**
  - A1: "people" means contributors reading the README, not end users installing a
    published package. *If false*: the relevant document is a different one.
    *Confidence: Inferred from the file's context — a root README for a developer
    tool.* *Not verified*, and it is stated in the answer so the user can correct it
    in one line if wrong.
  - A2: the confusion is in the README rather than in the error message a confused
    user sees. *If false*: fixing the README changes nothing.
    *Confidence: Assumed from the request naming the README.*
- **Success criteria** — the section is read, the described problem is either present
  and fixed or absent and reported, and every version claim in the section is
  checked against `package.json` and the host's Node.

**Requirements vs success criteria:** "make it clearer" is the requirement; "the
minimum-version line matches `package.json`'s `engines` field and the running Node,
and the per-platform commands are present and unambiguous" is the criterion, and the
first cannot be checked while the second can.

## 2. Decision records

```text
DECISION
  question      whether to run a comprehension study before editing
  selected      no
  rejected      five user interviews, a clarity baseline metric, and a rewrite
                designed against it — three to five days
  rationale     the request is a change to one section of one file, and the
                determining question is whether the described problem is present,
                which one git log answers in a second. A baseline is only
                meaningful against a measurable objective, "clearer" is not one,
                and five interviews of the people who already installed the tool
                measure a different population from the people who did not
  confidence    high
  cost          three to five days avoided
  evidence      the section's own history is available and dated
  recovery      the section is unchanged since the confusion was reported, in which
                case a comprehension check is warranted because the fix was
                applied somewhere that is not reaching readers
```

```text
DECISION
  question      what to do if the section was already rewritten
  selected      report that in three sentences, fix the one factual error found,
                and change nothing else
  rejected      (a) rewording anyway, to demonstrate effort; (b) expanding the
                section with a troubleshooting table; (c) writing a docs style guide
  rationale     (a) is activity, and it would obscure the finding that the work
                was already done six days ago. (b) is scope the request did not
                authorise and it is written for a problem that has not been shown
                to exist. (c) is a genuine need that this request did not
                express, and a one-file task is not the place to create a
                repository-wide standard
  confidence    high
  cost          nothing, which is the point
  evidence      commit a3f19c2, 2026-09-20, "docs: rewrite install section with
                per-platform tabs", already present in the file
  recovery      a reader reports the same confusion after a3f19c2, which would mean
                the fix is not reaching the people who need it and the diagnosis
                is about distribution rather than wording
```

```text
DECISION
  question      how to improve clarity, given the section is already rewritten
  selected      one factual correction — the minimum Node version — and nothing
                else
  rejected      (a) restructuring the section, (b) adding examples per platform,
                (c) tightening the prose
  rationale     the only verifiable defect found is that the README says
                "Node 20+" while package.json requires ">=20.11", and a reader on
                20.0 or 20.10 will hit an engine error the README did not warn
                them about. That is a correctness issue wearing a documentation
                costume, and it is the highest-value edit available. (a), (b) and
                (c) are all changes with no way to tell whether they helped
  confidence    high
  cost          one line, one commit
  evidence      jq .engines package.json → ">=20.11"; node --version → v20.11.1
  recovery      the engines field is looser than the actual minimum, in which case
                the README should be tightened to the tested version instead
```

## 3. Context

C0 — the objective, two unknowns, two assumptions. That is the working set.

C3 — two things, both minimal: `README.md` §"Install" (the section itself, 31
lines) and `git log --oneline -5 -- README.md` (whether the problem is still
present). The second is the one that decides the task, and it is one command.

**Deliberately not loaded, and the list is the trace:**

- **The other 340 lines of `README.md`.** The request names one section. Reading
  the whole file would be reading to find problems nobody reported.
- **`docs/` in its entirety.** There is a `docs/getting-started.md` and a
  `CONTRIBUTING.md` and a `docs/style-guide.md`. Any of them might be the "right"
  place for a clarity improvement, and none of them is relevant to whether
  `README.md`'s install section is clear.
- **Analytics on the docs site.** Which pages people bounce from would be the
  evidence for a comprehension study, and no study is being run.
- **The issue tracker.** "People are getting stuck" may be issue #412 with a
  description that names a different file. This is the most tempting omission in the
  list and the one with the clearest justification: the user pointed at a file, and
  the named file is what gets read. It is in the answer as a stated scope limit so
  the user can supply the issue number if the file is the wrong one.
- **`package.json` in full.** One field, `jq .engines`, which is the narrowest thing
  that would change the decision.

`excluded`: the rest of the README, all of `docs/`, docs analytics, the issue
tracker, the rest of `package.json`. `unresolved`: whether the confusion is really
in the README — see the scope limit in §9.

## 4. Capability

```text
1. do it directly   SELECTED — git log, sed, jq. The whole task is three commands
2. existing         not reached
3. compose          not reached
4. acquire          not reached
5. create           not reached — and this is where a plausible skill would have
                    been minted, so the disqualifying question deserves an
                    answer: "how to write clear documentation" is not a procedure,
                    it is a judgement, and there is a docs style guide in the
                    repository already. Minting a skill here would duplicate an
                    existing document and split the trigger signal for every future
                    prose edit
```

## 5. Plan

No plan. At R0 the plan is one line: *read the section, check whether the problem
is still there, fix what is verifiable, report.*

```text
id  action                                    expected                          verification
U1  read §Install and its git history         the problem is present, or it is   the commit that rewrote it, dated
                                               not, and it will be named
U2  check every version claim against the     claims match package.json and     jq .engines; node --version
    source of truth                            node --version
```

Two units, both one command, both with a check that can fail. A table with
preconditions and expected results would be a plan paying rent it cannot cover.

## 6. Execution & observation

**U1 — the section, and its history.**

```console
$ git log --oneline -3 -- README.md
a3f19c2 2026-09-20  docs: rewrite install section with per-platform tabs
41d0e18 2026-08-02  docs: add brew install line for macOS
8b2f19a 2026-07-14  chore: repo housekeeping

$ sed -n '/^## Install/,/^## /p' README.md
## Install

Requires **Node 20+** and a POSIX shell.

    # macOS
    brew install t5-cli && t5 login

    # Linux
    curl -fsSL https://get.example.dev | sh

    # from source
    git clone https://git.example.dev/t5/cli.git && make install
```

**The section was rewritten six days ago, in commit a3f19c2, specifically to fix
this.** It already has per-platform commands, already has a tab-free layout that
works in a terminal, and already has the source path. The request describes a
problem that the file no longer has, and the second-most-recent commit
(41d0e18, 2026-08-02) added the macOS line, so the confusion was real once and was
addressed twice.

**The surprise, and it is the useful part.** Having found nothing to rewrite, the
remaining useful work was to check whether what the section *says* is true — and
it is not:

```console
$ jq -r '.engines.node' package.json
>=20.11

$ node --version
v20.11.1

$ grep -n "Node 20+" README.md
34:Requires **Node 20+** and a POSIX shell.
```

**The README says Node 20+; `package.json` requires ≥20.11.** A contributor on
20.0 or 20.10 reads "you are fine", installs, and hits
`EBADENGINE` from npm or an `Unexpected token` from the build. That is a real
failure, it is caused by this section, and it is the highest-value edit available
— a correctness defect dressed as a documentation nit.

**U2 — the fix, one line.**

```diff
--- a/README.md
+++ b/README.md
@@ -34,7 +34,7 @@ Requires a POSIX shell.
-Requires **Node 20+** and a POSIX shell.
+Requires **Node ≥20.11** and a POSIX shell.
```

The wording stays as it is, the structure stays as it is, and no platform block,
example, or sentence is touched. A second sentence explaining *why* 20.11 was
considered and rejected: the failure mode is `EBADENGINE`, which names the field
and the range, and one clause of explanation is what turns a constraint into
something a reader can act on rather than something to work around.

## 7. Verification

| check | result |
|---|---|
| the section was read before anything was written | yes, and the read is what dissolved the task |
| the described problem still exists | **no** — fixed 2026-09-20 in a3f19c2, six days ago |
| every version claim checked against the source of truth | `>=20.11` from `package.json`, cross-checked against `node --version` v20.11.1 |
| the edit is the minimum that fixes a verified defect | one line, one word |
| nothing outside the stated section was touched | `git diff --stat` → 1 file, 1 insertion, 1 deletion |
| the edit is accurate on this machine as well as in the file | `node --version` satisfies `>=20.11` |

**Verdict: VERIFIED.** The factual claim now matches `package.json`. The clarity
problem named in the request does not exist in the current file, and that is
reported as the primary finding rather than as a footnote to an edit.

**The verdict is narrow and it says so.** It is verified that the version claim is
correct and that the section already addresses the described confusion. It is *not*
verified that no reader is confused — that is a different claim about a different
population, and nothing here could establish it.

## 8. Recovery

Not a stage. There was one surprise and it was not a failure of the work — it was
the plan being wrong about the world, which is the good case. The classification
would be *bad assumption* (that the described problem is still present) and the
response is the mandated one: correct the assumption and re-plan what depended on
it, which here meant abandoning the rewrite and searching for a verifiable defect
instead. Two commands, no ceremony.

The retry that was avoided: rewriting the section anyway, on the theory that a
clearer wording cannot hurt. It can hurt — it would have replaced a version someone
carefully rewrote six days ago with marginally different prose, and it would have
buried the finding that the work was already done.

## 9. Delivery

**Outcome. The section is already clear for the reason you describe, and I made one
fix rather than a rewrite.**

`a3f19c2` rewrote the install section on 2026-09-20, six days ago, with per-platform
commands and the source path; `41d0e18` had added the macOS line a month before
that. Both problems you describe were addressed there. The section as it stands has
all three platform paths, so I have left its structure, wording, and ordering alone
— rewriting it would have undone work someone did deliberately six days ago.

**The one real defect I found, and fixed:** the section says **Node 20+**;
`package.json` says `engines.node: ">=20.11"`. Someone on 20.0 or 20.10 installs
successfully and then hits `EBADENGINE`. One line changed:

```diff
-Requires **Node 20+** and a POSIX shell.
+Requires **Node ≥20.11** and a POSIX shell.
```

**Scope limit, because it matters more than the edit.** I read the install section
of the root `README.md`, which is the file you named. I did not look at the issue
tracker, so I cannot see *which* confusion people are hitting. If there is an issue
or a doc-site bounce for this, the file in question may be
`docs/getting-started.md` or the install output rather than the README — and that
would be a different fix in a different place. Give me the issue number and I will
look at the right document.

**Evidence.** `a3f19c2` dated 2026-09-20 with its message; `41d0e18` dated
2026-08-02. `jq -r '.engines.node' package.json` → `>=20.11`. `node --version` →
v20.11.1. `git diff --stat` → 1 file, 1 insertion, 1 deletion.

**Assumptions.**
- A1 ("people" means contributors reading the root README) — assumed from context.
  If they are end users installing a published package, `docs/getting-started.md` is
  the right file and I have edited the wrong one, though nothing is broken by it.
- A2 (the confusion is in the README rather than in the install output) — assumed
  from your description, and the unverified part, and the reason for the scope limit
  above.

**Limitations.** I did not run a comprehension check and cannot tell you whether any
reader is now unconfused. I did not read the issue tracker, so I cannot corroborate
that this was ever a problem. I did not verify that 20.11 is the *tested* minimum as
opposed to the *declared* one — CI runs 20.x and 22.x and the 20.x image is pinned at
20.11.1, which is consistent with 20.11 being the real floor, but I read that from
the workflow file and did not test 20.10.

**Confidence.** High that the version line was wrong and is now right — two
independent sources and a local check. High that the section already addresses the
described confusion, since I read it. **Low on whether the reported confusion is
even in this file**, which is the scope limit above and the reason the edit is one
line rather than a rewrite.

**Verification status.** VERIFIED for the version claim, as a factual correction.
The clarity request is answered by reporting that it was already addressed, and that
is the whole of the answer.

## 10. Learning

Nothing worth retaining. This run produced no candidate. "Check whether the
described problem still exists before planning to fix it" is general practice that I
applied rather than learned, and one instance of a `git log` is not a rule this
kernel should install.

**If** documentation requests in this repository repeatedly name problems that
recent commits already fixed, **then** a candidate is worth recording: *check the
file's history before planning an edit to it, and report the finding rather than
manufacturing work.* That would be a fact about this team's workflow rather than
about documentation, and it needs more than one observation.

**Not worth retaining:** the commit hashes, the `>=20.11` string, the EBADENGINE
error name. All in the repository where the next reader will find them.

**Routed rather than created.** Nothing here should be routed. The one thing worth
naming is the negative: a "documentation clarity" skill was a plausible creation in
this trace and was rejected, because `docs/style-guide.md` already exists and
duplicating it would split the trigger signal for every future prose edit.

## What this example proves

- **The gate ran before the plan, and the gate dissolved the task.** Three
  sentences of triage and one `git log` replaced a rewrite that would have undone
  work done deliberately six days ago.
- **R0 produced one unit, one check, and no plan artefact.** The `§5` heading
  exists because the format requires it; what is under it is two commands.
- **With nothing to improve, improve something verifiable.** The Node version
  mismatch is a correctness defect in the same paragraph, and it was found by
  checking claims rather than by re-reading prose.
- **The scope limit is the honest part of the answer.** The issue tracker was not
  read, so whether this confusion is in this file at all is unknown, and the user is
  told in one line what to supply.
- **A plausible skill was declined on the disqualifying question.** A
  documentation-clarity skill would duplicate an existing style guide and split a
  trigger signal.
- **Nothing was retained.** No candidate, no promotion, no rule — and the trace says
  why rather than manufacturing a lesson from a one-line edit.
