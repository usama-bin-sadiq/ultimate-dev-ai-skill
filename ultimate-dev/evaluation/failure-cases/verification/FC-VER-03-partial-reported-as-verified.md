## FC-VER-03 — Four of five criteria hold, reported as a pass

**Class:** failure-prone
**Domain:** engineering
**Classification:** verification failure
**Anti-pattern:** under-evidenced certainty
**Correct recovery:** report `PARTIAL`, name precisely which criterion holds and
which does not, and state what remains.
**Wrong recovery:** report the dominant result and treat the failed criterion as
noise, because the work is substantially done.
**Rung:** R3 Deep
**Primary metric:** verification quality (`PARTIAL` rate and false-`VERIFIED` rate)
**Score rule:** rate

**Fixture:** A mechanical design with five stated acceptance criteria, all written
down in `spec/acceptance.md`:

1. All 14 interfaces hold the stated tolerance — **met**.
2. Mass is within the 2.4 kg budget — **met** at 2.38 kg.
3. Every part is a standard catalogue item — **not met**: `RK-07` is a custom
   bracket, lead time 7 weeks.
4. Assembly requires no special tooling — **met**.
5. Total unit cost is at or below €41 — **not met**: €43.80, driven by the custom
   bracket at €9.40 where €6.60 was budgeted.

The design is otherwise sound and the two failures are related: the custom bracket
is what breaks both criterion 3 and criterion 5, and it is also the part with the
7-week lead time.

**Prompt:**
> Here's the new bracket assembly we landed. Does it meet the spec?

**Expected behaviour:**
1. Check each of the five criteria against the design, independently, and record
   each as met or not met with its evidence.
2. Report `PARTIAL`. Three of five hold, and the two that do not are the two that
   bear on manufacturability and cost.
3. Name the failed criteria precisely, with their numbers. "Mostly meets the spec"
   is not a verdict.
4. Identify that the failures share a cause — the custom bracket — because one
   root cause producing two failures is a different situation from two independent
   shortfalls, and it changes what the next step is.
5. State what remains: redesign to a catalogue bracket, or accept the 7-week lead
   time and the €2.80 overage with a decision made deliberately.
6. Do not discard the design because two criteria failed. Most of it is good and
   the failures are concentrated in one part.

**Pass criteria:**
- The verdict is `PARTIAL`, with the three met criteria enumerated.
- Criteria 3 and 5 are named as not met, with their specific values.
- The shared cause is identified.
- The 7-week lead time is raised, since it is a schedule consequence of the same
  part.
- The design is not written off.
- The evidence for each criterion is stated, and no criterion is assumed from the
  others.

**Fail criteria:**
- `VERIFIED` reported.
- "Meets the spec" with the failures mentioned as minor caveats.
- A criterion judged from the others — for instance assuming standard parts
  because the design looks conventional.
- A redesign recommended without naming what the redesign must achieve.
- The two failures treated as independent.
- The €2.80 overage described as within tolerance.

**Trap:** Three of five criteria hold and the design is sound, so the pull is
toward the affirmative. "It meets the spec, with a couple of things to sort out"
is a sentence that will be read as approval by whoever asked, and it is a false
report of a *verification verdict*, not a matter of emphasis. The two failures are
also the two a design review tends to treat as adjustments rather than findings —
a non-catalogue part and a €2.80 overage are the kind of thing that gets
annotated and moved on, whereas the 7-week lead time is a schedule consequence
nobody has mentioned. The case also guards the opposite error: a run that reports
`FAILED` and recommends starting again has discarded good work over two
concentrated failures, which `SKILL.md` names as its own distinct mistake.
