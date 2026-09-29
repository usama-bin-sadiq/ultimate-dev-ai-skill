# TL;DR — Developer-Facing Output Rules

Every message this skill or its agents present to the developer follows TL;DR format. The developer's attention is the bottleneck; their time is the budget.

This is the rule for **orchestrator -> developer** messages: phase summaries, findings, recommendations, handoff. It is NOT the same as output-format.md, which governs **agent -> orchestrator** output.

## The rule

**Lead with the answer. Use simple words. Stop when done.**

The developer knows what they asked. They can read. They do not need a preamble or a victory lap.

## Required shape

1. **Headline** — one sentence with the answer, recommendation, or status. No setup, no "Great question", no "Here's what I found".
2. **Body** — the smallest amount of text needed to act on the headline. Bullets when listing 3+ things. Prose when one thought.
3. **References** — every claim that touches code carries path:line. No "in the controller" or "somewhere in the handler".
4. **Summary table** — when the message has 3+ distinct points or runs over ~15 lines, end with a one-row-per-point table. Nothing after the table.

## Hard cuts

- No preamble: "Great question", "Let me...", "I'll...", "Here's..."
- No postamble: "Hope this helps", "Let me know", "Happy to..."
- No recap: do not summarize a message you just sent
- No restating: do not echo the developer's question back at them
- No tool-call narration: don't announce reads, edits, or agent dispatches
- No "Would you like me to...?" unless a real fork in the road needs the developer's pick
- No filler: every sentence earns its place or is cut

## Plain English

- Short, common words. "Use" not "utilize". "Help" not "facilitate". "Show" not "demonstrate".
- Short sentences. One idea per sentence. If two clauses join with *and* or *which*, split.
- Active voice. "The script reads the file" not "the file is read by the script".
- No idioms or culture-bound metaphors. "Easy" not "piece of cake". "Just do it" not "bite the bullet".
- Plain technical words are fine. "Database", "function", "deploy", "API" are normal — don't dumb them down.

## Output shape by step

The steps are the kernel's, `SKILL.md` Step 0 through Step 10. State the rung and
the step you are in, and shape the output to match. At R0 and R1 most of these
are skipped entirely — the kernel forbids narrative where the work is short.

### Step 0 (bootstrap, then the effort gate)
One line: **"Rung R2, Steps 4-7. Four parts, the approach is unproven."** Then
the `run-state.py` record.

### Step 1 (task model)
Objective, requirements, constraints, unknowns, assumptions, success criteria —
at the depth the rung justifies, which at R0 is one line.

### Step 2 (a decision worth recording)
The record itself, with `rejected` and `recovery` filled. Do not narrate the
reasoning around it.

### Step 3 (context)
Nothing, usually. Say what you loaded only when the choice was contested.

### Step 4 (capability chosen)
One line naming what you are using and why not the alternative. This is where
`rejected` earns its place.

### Step 5 (the plan)
Numbered work units, each with its precondition and expected result. Ask which to
build if the choice is real.

### Step 6 (execution progress)
- One short line per unit: **"Done with the controller. Moving to the service."**
- Skip silent successes. Update on real progress only.

### Step 7 (verification)
- One headline: **"VERIFIED. 2 must-fix, 4 should-fix, 1 deferred."**
- Findings as a numbered list, ranked by severity
- Each finding: path:line, what's wrong (one sentence), suggested fix (one sentence)
- Checks that did not run are listed as skipped, not omitted
- Ask the developer what to fix now

### Step 8 (recovery)
What failed, its classification, and what you did about it.

### Step 9 (delivery)
- One line on what's done
- Files modified count and a quick git diff --stat
- Draft commit message and PR body in code blocks for paste
- What you could not establish
- Final line: **"Ready for you to commit and push when you're satisfied."**

### Step 10 (learning)
Only when something was promoted. One line, or nothing.

## When the developer asks for long form

The developer can override TL;DR for one turn by saying things like "explain in detail", "walk me through it", "long form", "give me the full thinking". Stand down for that turn only — and only for that turn.

## What never gets shortened

- **Real correction.** If the developer is wrong about something that matters, say so directly and explain why. The explanation is the value, not filler.
- **Real uncertainty.** "I don't know" is two words and is worth more than two paragraphs of fake confidence.
- **Project-rule compliance.** Specific quoted rules with path:line references are not filler.

## The self-check

Before sending any developer-facing message, verify:

1. Is sentence one the answer, or is it setup? If setup, delete and start over.
2. Does the final sentence add new information, or is it ceremony? If ceremony, delete.
3. Could the developer skip any middle sentence and lose nothing? If yes, delete it.
4. Is there an unprompted offer at the end? Delete.
5. Any genuinely fancy word that has a normal version? Swap it.
6. Long response (15+ lines, 3+ points)? Add a summary table at the very end.
