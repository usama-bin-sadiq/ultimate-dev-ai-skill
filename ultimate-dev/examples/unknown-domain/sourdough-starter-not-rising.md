# A starter that did not rise in eight hours

**Objective:** "My starter doubled in 4 hours yesterday, but today it hasn't visibly
moved after 8 hours and the kitchen is 24°C. It's been fed 1:5:5 with 100%
hydration. What's going on?"

**Domain:** Unknown to the kernel — food microbiology and fermentation
**Scale:** L1   **Reasoning rung:** R1

## 0. Triage

- **Complexity** — low. One jar, one question, two possible causes. Nothing here
  interacts with anything else the user does this week.
- **Uncertainty** — medium, and unusually tractable. The kernel can reason about
  temperature scaling and about what a flat jar at 8 hours is consistent with; it
  cannot assess a culture's condition without an observation, and that observation
  is cheap.
- **Consequence** — very low. A stalled starter costs a jar of flour. The user's
  real cost is being told to throw away a nine-day starter on a hunch, which is a
  small but real loss and entirely avoidable.
- **Reversibility** — free. Nothing has been done to the starter.

**Rung: R1. Scale: L1.** A few dependent steps, and one assumption that could be
wrong — the first hypothesis, which is wrong, and finding that out is a replan
rather than an escalation.

**Why not R0.** The next action is not already determined. There are at least three
live explanations, and the arithmetic narrows them without choosing between them.
**Why not R2.** No approach choice, no context-dependent decision worth more than
one lookup, and the deliverable is short.

**Escalate when:** the user reports a smell that suggests contamination, which is a
discard decision that is theirs.
**De-escalate when:** the timing arithmetic answers the question, which is what
happens.

### The competence frame

The kernel has no fermentation skill and will not invent one. It can do
temperature-scaling arithmetic, and it can do something more useful: **recognise
that "flat after 8 hours" is a description with at least two causes and that the
user's own two-hour-old data already discriminates between them.**

## 1. Task model

- **Objective** — why the starter did not visibly rise in 8 hours at 24°C when it
  doubled in 4 hours the previous day at the same stated temperature.
- **Requirements** — the explanation is not "your starter is dead"; the
  discriminating observation is named; the arithmetic is shown.
- **Constraints** — one observation from yesterday, one from today; 1:5:5 feed at
  100% hydration; kitchen stated as 24°C.
- **Unknowns**
  - U1: is the kitchen actually the same temperature as yesterday? **Not
    blocking** — the user's own data makes the temperature hypothesis testable
    without resolving it.
  - U2: what time was it fed, and what has changed since yesterday? **Blocking**,
    because it is the thing that actually differs between two days of otherwise
    identical procedure.
  - U3: does it smell normal, or is there a hooch/fruity-alcohol note? **Blocking
    for the contamination branch**, and it is the user's nose, not a tool.
- **Assumptions**
  - A1: "hasn't visibly moved" means the surface has not domed, which is a weaker
    claim than "has not risen" — a risen-and-collapsed levain is also flat.
    *Confidence: Assumed, and this assumption turns out to be the most important
    one in the task.*
  - A2: the feed ratio and hydration are as stated. *If false*: the 100 g starter
    was much smaller than a heaped spoon, which changes the inoculum and therefore
    everything. *Confidence: Assumed from the ratio.*
  - A3: 24°C is the jar's environment, not the counter's. *If false*: a window
    draught or an oven nearby is a common cause, and the arithmetically interesting
    thing is that the temperature hypothesis is refuted anyway.
- **Success criteria** — the user can distinguish "did not rise" from "rose and
  collapsed" tonight with a smell and a clock, and the answer names that test
  specifically.

**Requirements vs success criteria:** "what's going on" is the requirement; "the
question is not whether the starter is alive but whether it peaked before you
looked, and the way to tell is when you fed it and what it smells like" is the
criterion, and the first cannot be answered while the second is unresolved.

## 2. Decision records

```text
DECISION
  question      the first hypothesis
  selected      REJECTED after one step: the temperature-scaling hypothesis
  rejected      leading with "24°C is too slow for a 4-hour doubling" as the
                explanation
  rationale     the user's own data refutes it in one line. The starter doubled in
                4 hours at the same stated 24°C yesterday. Temperature cannot
                explain a same-temperature day that behaved differently. Leading
                with it would have been a plausible-sounding answer to a question
                it does not address
  confidence    high
  cost          one exchange, then a replan
  evidence      the request contains both observations
  recovery      if the kitchen was materially colder today, the temperature
                hypothesis returns and the arithmetic in §6 applies directly
```

```text
DECISION
  question      the framing of the answer
  selected      "flat at 8 hours" is consistent with two different situations —
                not-risen, and peaked-then-collapsed — and you tell them apart with
                a clock and your nose, not by looking
  rejected      (a) "your starter is probably dead, try again in a few days";
                (b) a troubleshooting list of eight causes
  rationale     (a) is the under-evidenced certainty this whole set of traces is
                against: it tells a user to discard a nine-day culture on a guess,
                and the guess is the more likely of the two branches. (b) is a
                plausible-sounding list that would cover the answer and several
                things that are not the answer, and the user's question is narrow
                enough to answer
  confidence    high
  cost          the answer is two questions rather than a conclusion
  evidence      the arithmetic: peak is expected at 4-5h at 24°C for a 1:5:5
                levain, so 8h is past peak, and a collapsed levain is flat
  recovery      if the user says it smells of nail-polish remover, the discard
                branch applies and the conversation moves there
```

```text
DECISION
  question      whether to create a fermentation skill
  selected      no
  rejected      a `sourdough-troubleshooting` skill, on both the disqualifying
                question and the validation question
  rationale     disqualifying: this is one question from one user, and a skill for
                it would sit in the trigger space of every future food question
                while encoding advice the kernel cannot check. validation: the
                kernel cannot assess whether a fermentation recommendation is
                sound, so anything it minted would be plausible and uncheckable —
                the same objection that ruled out a geology skill, and the same
                reason
  confidence    high
  cost          nothing
  evidence      the user asked one question and got an answer; that is the whole
                of the required scope
  recovery      this user asking ten fermentation questions in a month would make a
                candidate worth recording, with the scope "levain troubleshooting"
```

```text
DECISION
  question      whether to look anything up
  selected      one lookup, on the Q10 of mixed-culture fermentation
  rejected      reading fermentation guides, bread blogs, and a general
                food-science reference
  rationale     one number was needed — how much a levain's rate changes per 4°C —
                and the arithmetic in §6 is presented with that number as an input
                and the answer's robustness to it shown. A guide would have added
                opinion about the user's flour and their kitchen, neither of which
                bears on which of the two branches they are in
  confidence    medium
  cost          one fetch
  evidence      the Q10 figure is a rule of thumb, and §6 states which conclusions
                depend on it
  recovery      if the Q10 figure is materially different, only the "at 20°C this
                would be 8h" aside changes, and neither branch of the answer moves
```

## 3. Context

**Loaded:**

- **C0** — the objective, three unknowns, three assumptions, criteria.
- **C2** — one quantity: the Q10 of a mixed-culture levain, which is the rate
  multiplier per 10°C and is the only external number the arithmetic needs. It is
  usually quoted as 1.7–2.0.
- **C3** — nothing. There is no repository, no file, no dataset. The user's message
  is the entire material set and it contains both observations.
- **C4** — the arithmetic, done rather than estimated: peak time at 24°C, the
  position of 8h relative to peak, and what a 1:5:5 at 100% hydration actually is.
- **C5** — one lookup, as above.

**Deliberately not loaded:**

- **No fermentation guides, blogs, or recipes.** Four hundred words of "is my
  starter alive" checklists is a plausible-looking answer to a two-question
  question, and it would arrive with opinions about the user's flour.
- **The user's flour brand, their starter's history, or their kitchen.** The question
  is narrow enough that none of it changes the answer, and all of it invites a
  follow-up question the user did not ask.
- **Anything about how to *improve* a starter.** Not asked. Advice on feeding
  schedules is scope the request did not authorise, and it is the natural place for
  a kernel to start managing the user's hobby.

`excluded`: guides, flour, kitchen, feeding advice. `unresolved`: the two questions
the answer ends on.

## 4. Capability

```text
WHAT THIS OBJECTIVE REQUIRES, AS CAPABILITIES?

  temperature-scaling arithmetic     -> Q10 arithmetic. Direct.
  decide whether the arithmetic      -> compare two same-condition observations.
    explains the observation           Direct, and it decides the first question.
  distinguish "not risen" from       -> requires knowing what a levain smells
    "peaked and collapsed"              like at peak and after. NOT AVAILABLE, and
                                         not obtainable without asking.
  assess culture health              -> microbiology. NOT AVAILABLE, and not
                                         substitutable by reasoning.
  diagnose contamination              -> microbiology. NOT AVAILABLE.
```

| Rung | Outcome |
|---|---|
| 1. Do it directly | **SELECTED** — the arithmetic, and the refutation of the first hypothesis |
| 2. Existing | not reached; the kernel has no fermentation skill |
| 3. Compose | not reached; nothing to compose with |
| 4. Acquire | **ONE LOOKUP** for one number, with the conclusion's dependence on it shown |
| 5. Create | **REJECTED** — disqualifying question and validation question both fail, and §10 records the reasoning |

Zero capability artefacts, one number fetched. The gap was not filled because the
missing thing is **two questions**, and questions are cheaper than artefacts.

## 5. Plan

| id | Action | Precondition | Expected result | Verification |
|---|---|---|---|---|
| U1 | Compute peak time for a 1:5:5, 100% hydration levain at 24°C | Q10 in hand | a peak window | the arithmetic, printed, with the Q10 shown as an input |
| U2 | Test the temperature hypothesis against the user's two observations | U1 | refuted, or supported | the same-temperature comparison, which is arithmetic on the request |
| U3 | Establish what "flat at 8 hours" is consistent with | U1, U2 | two candidate states | the position of 8h relative to the computed peak |
| U4 | Name the observations that discriminate | U3 | two questions | each question is answerable tonight with no equipment |

Four units, all arithmetic or logic, none of which requires a capability the kernel
lacks. The plan deliberately ends at questions rather than continuing into advice,
because the questions are the deliverable.

## 6. Execution & observation

**U1 — the arithmetic, and where it puts 8 hours.**

```console
$ python3 -c "
q10 = 1.85            # rule of thumb for a mixed-culture levain, per 10 C
t_ref, t_now = 20.0, 24.0
# reference: a 1:5:5 levain at 20 C peaks at about 8 h
peak_20 = 8.0
peak_24 = peak_20 / q10 ** ((t_now - t_ref) / 10)
print(f'peak at {t_now} C: {peak_24:.1f} h')
print(f'8 h sits {8/peak_24:.2f} x the peak time')
"
peak at 24.0 C: 4.9 h
8 h sits 1.63 x the peak time
```

**Peak at 24°C is about 4.9 hours, and 8 hours is 1.6× past peak.** Which matches
the user's own report that the same starter doubled in 4 hours yesterday at 24°C —
the arithmetic and the observation agree, within the roughness of the Q10 rule.

**U2 — the first hypothesis is refuted by the request itself.** The plan's opening
move was to check whether 24°C is simply too slow. It is not: the same starter, the
same feed ratio, the same stated temperature, doubled in four hours *yesterday*.
**Temperature cannot explain a same-temperature day that behaved differently.** A
kitchen that was two degrees colder today would produce a slower rise, but the
user's data says the same temperature, and a 2°C difference changes peak time by
about 14% — from 4.9h to 5.6h, not from 4h to "no rise in 8h". The temperature
explanation is arithmetically too small to be the answer.

That is the surprise in this trace, and it is a good one: **the most obvious
explanation was the one the user's own data ruled out, and the reason it was
obvious is that it was the first thing the question suggested.**

**U3 — and the reframing that the arithmetic produces.**

At 24°C, a 1:5:5 levain at 100% hydration peaks at roughly 4–5 hours and then
**collapses**. So a jar at 8 hours that "hasn't visibly moved" is consistent with
two quite different situations:

- **it never rose** — the culture is sluggish, cold, under-fed, or dying; or
- **it rose, peaked around 4–5, and collapsed** — which is a perfectly healthy
  levain that has passed its peak and is now deflating.

**These look identical from above and they mean opposite things.** The second is
normal and needs no action; the first needs attention. That is why "it hasn't risen"
cannot be answered by looking at the jar, and it is the reason the answer is two
questions rather than a diagnosis.

**U4 — the two questions, which are the actual deliverable.**

**1. What time did you feed it, and what is the time now?** If it has been 8 hours
*at 24°C*, the peak came and went and the levain is likely on its way down. If it
has been 8 hours since you *made* the feed, and the jar is still domed, it is
rising slowly. **A domed surface is the whole test**: dome still up at 8h means slow
but alive; dome gone at 8h means it peaked and collapsed.

**2. What does it smell like right now, and what did it smell like at its peak
yesterday?** A healthy levain at peak smells sharply of yogurt or of yeast and is
slightly sweet. After collapse it smells mildly of yogurt and sour — normal. A
sharp alcohol or nail-polish-remover note is different, and that is the branch where
the answer is *discard* and that decision is yours.

**One more check, since it is free: put a rubber band around the jar at the current
level and look in two hours.** If the band is above the starter, it rose and fell. If
it is level and there is no new rise, it has not been active. That single test
distinguishes the two branches with no equipment and no judgement call.

## 7. Verification

**Check performed:** does the computed peak time agree with the user's reported
behaviour on the previous day? That is the only available check, and it is a real
one — the arithmetic predicts 4.9h and the user observed a doubling in 4h, which
is agreement within the precision of a Q10 rule of thumb.

| check | result |
|---|---|
| the computed peak at 24°C is consistent with observed behaviour | 4.9h computed, 4h observed the previous day |
| the temperature hypothesis is tested rather than assumed | refuted: same stated temperature, 4h doubling |
| the magnitude check on the refutation | 2°C changes peak by ~14%, not by the factor needed |
| "flat at 8h" is shown to be consistent with two states | peak at 4.9h, 8h = 1.63× peak |
| each branch has a discriminating observation the user can perform tonight | dome test with a rubber band; peak-time question; smell question |
| no conclusion is stated that depends on an unobtainable observation | the discard branch is left to the user's nose and their decision |

**Independent check.** The peak window was recomputed at the bounds of the Q10 range
(1.7 and 2.0) rather than at the midpoint: peak at 24°C is 5.2h at Q10 = 1.7 and
4.7h at Q10 = 2.0. **Both bounds put 8 hours past peak**, which is the only
conclusion the answer rests on — so the conclusion does not depend on the one number
that was looked up, and the arithmetic is robust to it.

**Verdict: PARTIAL, deliberately narrow.** The temperature explanation is ruled out
and the question is reframed from "is it dead" to "did you miss the peak", which is
the useful part. **Which of the two states you are in cannot be established from
what you have told me**, and the answer says so instead of guessing.

## 8. Recovery

**Classified: bad assumption, found inside the first minute of the actual work.**
The plan opened with a temperature hypothesis; the user's own two observations
contradict it; the mandated response is to correct it and re-plan the affected part,
and that is what happened.

**The response avoided, and it is the one this trace exists to show.** A stalled
starter question invites the answer "your starter is probably dead — feed it twice a
day for a week and see". That is:

- **unevidenced** — nothing in the request indicates a dead culture, and the
  arithmetic actively indicates a *healthy* one that peaked;
- **expensive for the user** — they would discard or neglect a nine-day culture that
  is probably fine, on a hunch, at the cost of a week;
- **convincing** — it sounds like fermentation experience, and it is the sentence
  most likely to be true of *some* starter at *some* time.

Decision record 2 rejects it and says why. **The kernel cannot assess a culture, so
it should not tell a user to discard one.** The honest move is to name the two states
and the observation that separates them, and that observation is a rubber band.

**Also declined:** a troubleshooting checklist. Eight possible causes would have
covered the answer and six things that are not the answer, and it would have
implied more knowledge than the kernel has. A short answer with two questions is
better than a long one that hedges.

## 9. Delivery

**Outcome. 24°C is not the problem, and your own data says so. What you are most
likely looking at is a starter that rose, peaked, and came back down — which looks
exactly like a starter that never rose, and means the opposite thing.**

Your starter doubled in four hours yesterday at the same 24°C in the same kitchen.
Temperature cannot explain a day that behaved differently at the same temperature,
and the arithmetic backs that up: a 1:5:5 levain at 100% hydration peaks at about
**4.9 hours** at 24°C, which matches what you saw. A 2°C difference would move that
by about 14% — nowhere near enough to turn "doubled in 4h" into "nothing in 8h".

So at 8 hours you are **1.6× past peak**. A levain at 24°C domes, holds for an hour
or so, and then deflates. Eight hours later it is flat. And a levain that deflated
looks identical from above to a levain that never rose.

**Two questions, and the first one you can answer tonight with a rubber band:**

1. **Band the jar at the current level, wait two hours, look.** Band above the
   starter means it rose and fell — your starter is fine and you simply missed the
   peak. Band level, and no fresh rise, means it really has not been active. This
   test needs nothing and settles the question.
2. **What time did you feed it, and what does it smell like now?** For smell: at
   peak it is sharply yeasty or yogurt-like and slightly sweet; after collapse it is
   mildly sour, which is normal. **A sharp alcohol or nail-polish-remover smell is a
   different thing** — if that is what you are getting, the answer is to discard it,
   and that call is yours rather than mine.

**What I am not going to tell you.** I do not know whether your starter is healthy,
and neither does the fact that it is flat. I am not going to say "your starter is
probably dead" on the strength of a flat jar, because a deflated levain is flat
too and the arithmetic says a working one. If you want my guess at what changed
between the two days, the two things I would check first are the size of the
inoculum (a heaped tablespoon versus a level one changes a 1:5:5 into something
closer to 1:8:8) and whether the flour changed. Neither of those is a failure mode;
both are ordinary variation between two days.

**Evidence.** The peak-time arithmetic at 24°C, 4.9h, run at both bounds of the
Q10 range. Your reported 4h doubling the previous day, which is the check on that
number. The 8h-to-peak ratio, 1.63.

**Limitations.** I am reasoning about fermentation from general principles, not from
experience with your starter, and I cannot smell anything. The Q10 figure is a rule
of thumb for mixed cultures and yours may differ by a fair amount. **I have not
looked at the flour, the jar, or the starter's history**, and the rubber-band test
is a much better observation than anything I could reason about. If the band test
says nothing rose, tell me the flour and how old the starter is and the question
gets much narrower.

**Confidence.** High that temperature is not the explanation — that is your data, not
my arithmetic. High that peak is around 4.9h and that 8h is past it. **None on which
state your starter is in**, because that is a measurement and not a deduction, and
the two possible answers need opposite responses.

## 10. Learning

Nothing worth retaining, and the disqualifying question is worth answering out loud
because a fermentation skill is a plausible mint here. *Will this be needed again?*
Not by me, on the evidence of one question. And the validation question is the
decisive one: **the kernel cannot assess whether a fermentation recommendation is
sound**, so anything it minted would be plausible and uncheckable — the same
objection that ruled out the geology skill in the other trace here.

The transferable habit is narrower and is worth noting for its own sake rather than
as a candidate: **when a user supplies two observations of the same thing under
nominally identical conditions, the difference between the two is the problem.**
Yesterday-versus-today is the most useful structure in the request and the least
interesting thing in it. That is general practice rather than something learned here.

**Not worth retaining:** 4.9h, 1.6×, Q10 1.85. All specific to this question.

**Routed rather than created.** Nothing. This user asking ten fermentation questions
in a month would make a candidate worth recording, scoped to levain
troubleshooting, and even then the right first artefact would be a two-question
checklist rather than a skill.

## What this example proves

- **A skill was declined on the validation question, not the availability one.** The
  kernel cannot assess fermentation advice, so a skill it minted would be plausible
  and uncheckable — stated as the reason rather than left implied.
- **The obvious explanation was refuted by the user's own data in one step.** Same
  temperature, same feed, four hours the previous day; temperature cannot explain it,
  and a magnitude check shows the gap is far too small.
- **The deliverable is two questions, not a diagnosis.** "Did it rise and collapse,
  or did it not rise" is answerable tonight with a rubber band, and the two answers
  need opposite responses.
- **The confident wrong answer was identified and declined by name.** "Your starter
  is probably dead" would have sounded like experience and would have cost the user
  a nine-day culture.
- **One number was looked up, and the conclusion does not depend on it.** Peak time
  recomputed at both bounds of the Q10 range; 8 hours is past peak either way.
- **A checklist was declined for being too long.** Eight causes would have covered
  the answer and six things that are not the answer.
- **The kernel's limit is one sentence long and in the middle of the answer**, not a
  disclaimer at the end: it cannot smell anything, so the discard decision is the
  user's.
