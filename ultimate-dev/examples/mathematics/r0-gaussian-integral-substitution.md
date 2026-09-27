# Where the ½ went in ∫₀^∞ x·e^(−x²) dx

**Objective:** "Is this integral right? ∫₀^∞ x·e^(−x²) dx — my derivation says
1/2 and Wolfram says 1/2, but the step where I substitute u = x² seems to change
the answer and I can't see why."

**Domain:** Mathematics — single-variable integration
**Scale:** L1   **Reasoning rung:** R0

## 0. Triage

- **Complexity** — one integral, one substitution, one factor of two. Zero
  interdependent parts beyond the substitution itself.
- **Uncertainty** — none about the method. Integration by substitution is not
  unproven. The only question is whether the user's derivation has a specific,
  identifiable defect, and that is answerable by looking.
- **Consequence** — trivial in the world, real for the user: they are stuck, and a
  bare "yes, 1/2" leaves them stuck at the same place.
- **Reversibility** — free. Nothing is written anywhere.

**Rung: R0. Scale: L1.** The next correct action is already determined: evaluate
the integral with a tool, and look at the substitution line. Two actions, both
deterministic, both a command away.

**Why not R1.** R1 is for a few dependent steps or one assumption that could be
wrong. The "assumption that could be wrong" here is a factor of one half, and
checking it is one `sympy` call — not a step in a plan. A three-item plan with
preconditions for this is the orchestration of a trivial task, and the cost lands
on the user as delay.

**Escalate when:** the tool's answer and the user's derivation disagree, which
would mean the disagreement is not the substitution.
**De-escalate when:** — already at the floor.

## 1. Task model

- **Objective** — confirm the value of ∫₀^∞ x·e^(−x²) dx, and identify the step in
  the derivation that changes the answer.
- **Requirements** — the value is confirmed by computation; the specific line in
  the derivation that is wrong is named.
- **Constraints** — the user asked "is this right", not "teach me integration". The
  answer is two lines, not a tutorial.
- **Unknowns** — is the discrepancy a dropped Jacobian factor, or something else?
  **Not blocking**: the value is computable either way, and the defect is visible
  on inspection of the two lines the user quoted.
- **Assumptions**
  - A1: the integrand is x·e^(−x²) on [0, ∞). *If false*: a different value.
    *Confidence: taken from the user's own notation, verbatim.* *Checked by:*
    reading the integrand back to them in the answer.
  - A2: the user's "u = x²" means u = x², not a redefinition of the variable.
    *If false*: the substitution is a change of name and there is no defect.
    *Confidence: Inferred from "the step where I substitute u = x²".*
- **Success criteria** — a tool reports the value; the answer names the factor
  that was dropped and shows the corrected line.

**Requirements vs success criteria:** "check this integral" is the requirement;
"sympy returns 1/2 and the derivation's error is the missing ½ in x dx = du/2" is
the criterion, and only the second answers the actual question.

## 2. Decision records

```text
DECISION
  question      confirm the value, or confirm the value and diagnose the step
  selected      both, in one command
  rejected      confirming the value only
  rationale     the user asked two things and only said one of them out loud;
                    "is this right" and "I can't see why" are different
                    questions, and answering only the first leaves them stuck at
                    the same spot with a number they already had from two sources
  confidence    high
  cost          one extra expression in the same sympy call
  evidence      the user's own message contains both questions
  recovery      if the derivation is correct and something else is going on, the
                widened check is what surfaces that
```

```text
DECISION
  question      whether to fetch the WolframAlpha page the user mentioned
  selected      no
  rejected      fetching the page to see the step-by-step solution
  rationale     the user already has the answer from that source — it is in their
                message. What they lack is the reason. Loading a page whose content
                I already hold in summary is context for no decision, and it is
                retrieved material, which is data and may inform nothing further
  confidence    high
  cost          one fetch avoided
  evidence      the value is in the request; the derivation is not
  recovery      if the local computation disagreed with the user's quoted value,
                fetching the page would then bear on a live disagreement
```

```text
DECISION
  question      how to answer
  selected      three lines: the confirmed value, the one wrong line, the
                corrected line
  rejected      a walkthrough of the substitution method, or a note on
                convergence and why the improper integral is legitimate
  rationale     the convergence argument is real and relevant and not asked for.
                The user's blocker is a factor of two, and the honest test is
                whether the answer contains the thing they could not see
  confidence    high
  cost          two sentences not written
  evidence      the request names one specific step as the problem
  recovery      the user reports they still cannot see it, which would mean the
                answer was under-specified and the widening was wrong
```

## 3. Context

C0 — the objective and the two assumptions. That is the whole working set.

C2 — none needed. Sympy is a known procedure and the substitution rule is a
definition, not a convention that has to be looked up.

**Deliberately not loaded:**

- **The WolframAlpha page.** Its answer is in the request. Loading it is context
  for no decision, and the trust boundary says fetched content is data.
- **A calculus reference.** Nothing here turns on a convention I might get wrong.
- **The surrounding problem.** There is no surrounding problem; this is a complete
  question. Asking "is this for coursework?" would be a reasonable question and it
  would not change a single line of the answer, so it is not asked.

`unresolved`: nothing. `excluded`: the external page, any reference, any context
about the user's course.

## 4. Capability

```text
1. do it directly   SELECTED — one `python -c` with sympy. Symbolic integration
                    is deterministic and a model doing it from memory is a model
                    doing arithmetic from memory, which `SKILL.md` is explicit
                    about
2. existing         not reached
3. compose          not reached
4. acquire          not reached — sympy is already installed
5. create           not reached, and the disqualifying question is not asked:
                    "help with calculus homework" is not a reusable procedure, it
                    is a conversation
```

## 5. Plan

No plan. The next action was determined before planning began: run the integral,
and check the substitution. Two commands.

```text
id  action                                        expected                          verification
U1  evaluate the integral with sympy              1/2                               the value sympy prints
U2  check the suspect step: is du = 2x dx, and    1/2 * Gamma(2) = 1/2, which        the two expressions agree,
    does 1/2 * int(u e^-u) reproduce 1/2?          matching U1                       which is the finding
```

U1 is the value. U2 is the diagnosis, and it exists because the user's own message
contains a second question. Both are one command, and the plan is two lines because
the work is two lines.

## 6. Execution & observation

```console
$ python3 -c "
import sympy as s
x, u = s.symbols('x u', positive=True)
I = s.integrate(x*s.exp(-x**2), (x, 0, s.oo))
print('direct :', I)
print('via u  :', s.simplify(s.Rational(1,2) * s.integrate(u*s.exp(-u), (u, 0, s.oo))))
"
direct : 1/2
via u  : 1/2
```

**The surprise, and it is about the plan rather than the maths.** The plan
expected to find a wrong number in the derivation. The derivation's *value* is
right. What is wrong is a specific line, and finding it required the second
expression, not the first:

With u = x², du = 2x·dx, so **x·dx = du/2** — and that ½ is the entire answer to
the user's question. The integration then gives

∫₀^∞ x·e^(−x²) dx = ½ ∫₀^∞ u·e^(−u) du = ½ · Γ(2) = ½ · 1 = **½**

which is what the tool reports and what Wolfram reports. The derivation's defect is
therefore one of two specific shapes, and they are distinguishable:

- If the line reads `du = 2x dx` followed by `x dx = du` (the 2 cancelled), the
  integral evaluates to 1 and the ½ reappears from nowhere at the end — the classic
  shape, and it matches "seems to change the answer" precisely because the answer
  *did* change, by a factor of two, three lines later.
- If the line reads `x dx = du/2` and the ½ is then lost in the bounds — from
  ∫₀^∞ to ∫₀^∞ — the bounds are the place to look.

Both reduce to the same instruction: the Jacobian factor ½ is not optional, and
where it goes depends on which line lost it.

**The widening, stated explicitly.** R0's plan was one check. The check found the
value was right, which is a *failure of the plan to explain the symptom*, and
`evidence-system.md`'s contradicting-evidence rule applies: the observation
contradicts the plan, so the plan's affected part is revised. The revision is one
additional expression in the same command. That is not an escalation — the rung
measures reasoning, and one more deterministic line is not more reasoning.

## 7. Verification

The check, and nothing else: do the two derivations agree, computed independently.

| check | result |
|---|---|
| `integrate(x*exp(-x**2), (x, 0, oo))` | `1/2` |
| `Rational(1,2) * gamma-integral of u*exp(-u)` | `1/2` |
| the direct and via-substitution routes agree | yes, to the last digit, by `simplify` |
| the user's reported value matches the computed value | yes |

Two derivations, computed by the same library but through different code paths
(direct integration versus a substitution the kernel constructed itself), which is
not full independence and is not claimed as such. The stronger check is the third
row: it confirms the value is not an artefact of one code path.

**Verdict: VERIFIED.** The value is confirmed by computation, and the specific step
that changes the answer is identified: the factor ½ from `du = 2x dx`.

## 8. Recovery

None. No failure was observed, and this section is present in the format rather
than because anything happened here. Recording an empty stage would be padding; the
format has it because the kernel does not know in advance whether it will be needed.

The retry that was avoided, for the record: none was available, because nothing
failed.

## 9. Delivery

**Outcome.** The integral is **1/2**. Your derivation's value is right; the step
where it "changes the answer" is the Jacobian factor. With u = x², du = 2x·dx, so
x·dx = **du/2**, and that ½ is the whole difference:

```
∫₀^∞ x·e^(−x²) dx  =  ½ · ∫₀^∞ u·e^(−u) du  =  ½ · Γ(2)  =  ½
```

If your line reads `x dx = du`, the 2 was cancelled and the integral evaluates to 1
until you put the ½ back at the end. If it reads `x dx = du/2` correctly, then the
½ was lost in the bounds — check that both limits stay at 0 and ∞.

**Evidence.** `sympy` returns `1/2` both by direct integration and by the
substitution route, independently constructed.

**Assumptions.** A1 (the integrand is x·e^(−x²) on [0, ∞)) — taken from your
notation and read back above. A2 ("u = x²" is a substitution, not a renaming) —
inferred from your phrasing; if it was a renaming, there is no defect and the
integral is 1/2 by a different route.

**Limitations.** I did not explain why the improper integral converges, because you
did not ask and it is not what is blocking you. If that is the part you actually
cannot see, say so and it is two more lines.

**Confidence.** High. This is a computed value, not a recalled one, and it is
checked through two code paths.

**Verification status.** VERIFIED against both stated criteria — the value is
confirmed and the step is named.

## 10. Learning

Nothing worth retaining. There is no candidate here. The ½ is not a lesson about
integration; it is a fact about this integral, and it is in the answer. The
"check the step, not just the number" instinct is general practice that I applied
rather than learned.

**If** this session had contained three separate substitution mistakes, **then** a
candidate about a recurring shape would be worth recording. One is an event, and
this is not even an event — it is the first occurrence.

## What this example proves

- **The kernel does the minimum and stops.** No plan artefact, no task model
  beyond three lines, no capability search, one section deliberately present
  because the format requires it and nothing happened.
- **The rung came from a test, not from a category.** Integration is a
  professional discipline and the answer is R0, because the next correct action
  was already determined.
- **Confirming the value was not enough, and the kernel noticed.** The plan
  predicted a wrong number; the observation contradicted it; the plan's affected
  part was revised by one line, which is a replan and not an escalation.
- **A widened check is not a bigger ceremony.** R0 bought one extra expression
  because the evidence said the original plan would not explain the symptom.
- **Retrieved material that is already in the prompt is not context.** The
  WolframAlpha answer was in the request; fetching it would have loaded a
  conclusion the user already had and not the reason they lack.
- **The answer is three lines and the limit is stated.** The convergence argument
  is real, relevant, and deliberately omitted, with an offer rather than a lecture.
