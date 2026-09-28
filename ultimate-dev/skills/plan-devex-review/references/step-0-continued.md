<!-- Moved verbatim from plan-devex-review/SKILL.md, the
     'step-0-continued' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Step 0 continued

Before the empathy narrative, read the full design doc if found, <agent-instructions>,
README getting-started, docs/, package.json, CHANGELOG.md, CLI help (`--help`,
`usage:`, `commands:`), errors (`throw new Error`, `console.error`, error
classes), and examples/ or samples/. Use the detected remote base for changed
files; label missing artifacts and unverified behavior unknown.

### 0B. Empathy Narrative as Conversation Starter

Write a first-person narrative using the persona from 0A and verified product
content. Aim for 150-250 words, showing what they see, try and feel. Distinguish
observations from predicted confusion.

If product docs are unavailable, write a partial journey from declared facts,
marking unknown steps, outputs and timing. Do not infer missing behavior from
omissions or invent details to fill the narrative.

Then SHOW it to the user via AskUserQuestion:

> "Here's what I think your [persona] developer experiences today:
>
> [full empathy narrative]
>
> Does this match reality? Where am I wrong?
>
> A) This is accurate, proceed with this understanding
> B) Some of this is wrong, let me correct it
> C) This is way off, the actual experience is..."

**STOP.** Incorporate corrections in working notes only until 0C is answered.
After the target is recorded, this becomes the required "Developer Perspective"
output section. The implementer should read it and feel what the developer feels.

### 0C. Competitive DX Benchmarking

Define the clock before comparing: persona, documented start, first understood
useful result, including reading, setup and first-run state. Label unknowns.
Record observed human onboarding separately from automated execution
time; a warm snippet timer is neither a fresh-start check nor a human benchmark.
Keep estimates labeled until measured. Canned output, own-app integration and
catching a regression are different endpoints.

Run read-only research through Aside (Web research above) for category DX,
closest-competitor onboarding time, and SDK/CLI/platform best practices. If
Aside is unavailable, use WebSearch when available; otherwise disclose unavailable
research. Illustrations are not measurements.

Include peers and YOUR PRODUCT from inspected docs/plan:

| Tool | Start → result | Time + evidence type | DX choice | Source |
|------|----------------|----------------------|-----------|--------|
| [name] | [boundaries/unknown] | [observed/reported/estimated] | [choice] | [URL/source] |

Compare times only across equivalent boundaries; otherwise disclose the limitation
and compare DX choices. Never infer no wait from a peer's silence.
Choosing a target leaves independent remedies pending.

**Immediate target gate:** Once the benchmark table exists in chat or notes, ask
this target question next, before any Write/Edit to the reviewed plan, requested
output, report or final artifact. Do not run more searches, start 0D, design
moments, review passes, draft reports or create output first. 0C is incomplete
until the answer is recorded.

AskUserQuestion:

> "For [persona], [start] to [useful result] takes [X] minutes estimated
> ([Y] steps). [Comparable peer evidence and limitations.]
> Which target fits this journey? Include feasibility and blockers for each:
> A) Champion (< 2 min)
> B) Competitive (2-5 min)
> C) Current trajectory ([X] min)
> D) Tell me what's realistic"

**STOP.** If unanswered, stop here; do not continue to 0D. Carry the approved clock and target into 0D, Pass 1, Pass 8 and the report.
The vehicle must reach that result, not a quicker endpoint.
New targets or journey extensions require their own decisions.

### 0D. Magical Moment Design

Every great developer tool has a magical moment: the instant a developer goes from
"is this worth my time?" to "oh wow, this is real."

Load the "## Pass 1" section from `~/<agent-config-dir>/gstack/plan-devex-review/dx-hall-of-fame.md`
for gold standard examples.

Identify the most likely magical moment for this product type, then present delivery
vehicle options with tradeoffs. Adapt the examples below to the accepted mode and
contracts. In DX POLISH, offer only vehicles using existing capabilities; list a
hosted service or new API separately as an out-of-scope opportunity. A Hall of Fame
example does not authorize an expansion. Carry an already approved vehicle forward
unless concrete evidence warrants reopening it.

AskUserQuestion:

> "For your [product type], the magical moment is: [specific visible success].
>
> How should your [persona from 0A] experience this moment?
>
> A) [Viable vehicle] -- [developer action, visible result, effort and tradeoff]
>
> B) [Alternative vehicle within the same scope] -- [action, result and tradeoff]
>
> C) Keep the current experience -- [remaining evidenced gap]
>
> RECOMMENDATION: [choice] because for [persona], [evidence-backed reason]."

**STOP.** The chosen delivery vehicle is tracked through the scoring passes.

### 0E. Mode Selection

How deep should this DX review go?

Use the mode the user explicitly requested for this review. If already chosen,
skip the mode question and continue to 0F. Otherwise, ask below.

Present three options:

AskUserQuestion:

> "How deep should this DX review go?
>
> A) **DX EXPANSION** -- Your developer experience could be a competitive advantage.
>    I'll propose ambitious DX improvements beyond what the plan covers. Every expansion
>    is opt-in via individual questions. I'll push hard.
>
> B) **DX POLISH** -- The plan's DX scope is right. I'll make every touchpoint bulletproof:
>    error messages, docs, CLI help, getting started. No scope additions, maximum rigor.
>    (recommended for most reviews)
>
> C) **DX TRIAGE** -- Focus only on the critical DX gaps that would block adoption.
>    Fast, surgical, for plans that need to ship soon.
>
> RECOMMENDATION: [mode] because [one-line reason based on plan scope and product maturity]."

Context-dependent defaults:
* New developer-facing product → default DX EXPANSION
* Enhancement to existing product → default DX POLISH
* Bug fix or urgent ship → default DX TRIAGE

Once selected, commit fully. Do not silently drift toward a different mode.

**STOP.** Do NOT proceed until user responds.

### 0F. Developer Journey Trace with Friction-Point Questions

For each stage (Discover, Install, Hello World, Real Usage, Debug, Upgrade):

1. **Trace the actual path.** Inspect its docs, commands and output; cite files and lines.
2. **Identify evidenced friction.** E.g., the README requires Docker but neither
   checks for it nor explains installation. Label predicted consequences.
3. **Run all four Decision gate steps** before options. Ask only for an admitted
   new or reopened choice, using this menu:

   > "Journey Stage: INSTALL
   >
   > I traced the installation path. Your README says:
   > [actual install instructions]
   >
   > Friction point: [specific issue with evidence]
   >
   > A) Fix in plan -- [specific fix]
   > B) [Alternative approach]
   > C) Document the requirement prominently
   > D) Acceptable friction -- skip"

**DX TRIAGE mode:** Only trace Install and Hello World stages. Skip the rest.
**DX POLISH mode:** Trace all stages.
**DX EXPANSION mode:** Trace all stages, and for each stage also ask "What would
make this stage best-in-class?"

After all friction points are resolved, produce the updated journey map:

```
STAGE           | DEVELOPER DOES              | FRICTION POINTS      | STATUS
----------------|-----------------------------|--------------------- |--------
1. Discover     | [action]                    | [resolved/deferred]  | [fixed/ok/deferred]
2. Install      | [action]                    | [resolved/deferred]  | [fixed/ok/deferred]
3. Hello World  | [action]                    | [resolved/deferred]  | [fixed/ok/deferred]
4. Real Usage   | [action]                    | [resolved/deferred]  | [fixed/ok/deferred]
5. Debug        | [action]                    | [resolved/deferred]  | [fixed/ok/deferred]
6. Upgrade      | [action]                    | [resolved/deferred]  | [fixed/ok/deferred]
```

### 0G. First-Time Developer Roleplay

Using the persona from 0A and the journey trace from 0F, write a structured
"confusion report" from the perspective of a first-time developer. Include
timestamps to simulate real time passing.

```
FIRST-TIME DEVELOPER REPORT
============================
Persona: [from 0A]
Attempting: [product] getting started

CONFUSION LOG:
T+0:00  [What they do first. What they see.]
T+0:30  [Next action. What surprised or confused them.]
T+1:00  [What they tried. What happened.]
T+2:00  [Where they got stuck or succeeded.]
T+3:00  [Final state: gave up / succeeded / asked for help]
```

Ground this in the ACTUAL docs and code from the pre-review audit. Not hypothetical.
Reference specific README headings, error messages, and file paths.

Run the Decision gate on each evidenced confusion point. Report routine work and
prior answers without reconfirming them. Verify imagined confusion rather than
calling it a defect. Never bulk-accept or cut approved decisions.

For each admitted new or reopened choice, offer its remedy, tradeoffs and alternatives.
**STOP.** Wait for its answer before applying that remedy or advancing.

---
