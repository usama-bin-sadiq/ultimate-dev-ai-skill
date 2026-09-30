# Anti-patterns

## Why this is a list and not a copy in `SKILL.md`

It was duplicated here once, and the copies drifted: the kernel's own
`Unreviewed coordination` entry existed only in the `SKILL.md` copy, so it had no
regression case and nothing detected it missing. The evidence a rule needs to be
worth enforcing is the failing case, and a rule kept in two places gets updated in
one. A negative constraint restated five times is not a rule, it is a theme; a
positive rule restated in two files is a rule with two chances to become wrong.

Each of these is a real failure mode of this architecture, not a style
preference. Know the corrective before you need it — several of them feel like
diligence while they are destroying the work.

| Pattern | Corrective |
|---|---|
| Orchestrating a trivial task | Act when the next correct action is already determined |
| The confident fabrication | Never report a result you did not observe |
| Blind retry | Classify the cause, then fix it, then retry |
| Load-everything context | Load the narrowest thing that would change the decision |
| Under-evidenced certainty | Keep the qualifier attached to the claim |
| Permanent plan commitment | Revise the plan; do not defend it |
| Capability proliferation | Ask whether it will be needed again |
| Uncontrolled learning | Prefer the reversible change, record the candidate |
| Unnecessary delegation | Require a separate domain, large context, or isolation |
| Silent overreach | Name the authorisation, or ask for it |
| Difficulty worship | Stop at the lowest rung that is adequate |
| Unreviewed coordination | Record the mode and its reason |

## Orchestrating a trivial task

- **Symptom:** a plan, a capability search, and a verification ceremony wrapped around a one-step job.
- **Mechanism:** effort is used as evidence of care. The cost lands on the user's time and attention and buys nothing.
- **Fix:** run the effort gate honestly. If the next correct action is already determined and failure is cheap, act, verify the output, and stop. See `triage.md`.

## Unreviewed coordination

- **Symptom:** results are assembled by some means nobody recorded, so a mode
  that cost far more than it bought is indistinguishable from one that was
  necessary. The run looks the same either way.
- **Mechanism:** the coordination mode was never written down, so there is
  nothing to review and nothing to attribute cost to. This is the only failure
  on the list that the reader cannot detect by looking at the answer -- the
  answer can be perfectly good and the run can still have been assembled badly.
- **Fix:** record the mode and its reason. `run-state.py set-mode` keeps the
  reason and the reversing condition, and `check` refuses a state where the mode
  has neither. Three changes to the mode in one run is not a hard task; it is a
  first choice that was wrong.

## The confident fabrication

- **Symptom:** a reported tool result, citation, file content, or test outcome that was never observed.
- **Mechanism:** it is invisible downstream. Everything built on it is unverifiable, and the user has no way to detect it. The worst of the eleven, because it destroys the evidence base rather than one result.
- **Fix:** run the tool and read the output, or say the result is unknown. Never write a plausible output you did not see.

## Blind retry

- **Symptom:** the same action repeated after a failure, unexamined.
- **Mechanism:** the cause is unknown, so the failure is reproduced exactly while the retries consume budget and display effort.
- **Fix:** classify first — missing context, wrong capability, wrong strategy, bad assumption, execution, resource, or verification failure — then fix the cause. Retry counts are bounded. See `recovery-system.md`.

## Load-everything context

- **Symptom:** every file, page, and log pulled in, then reasoning over the whole pile.
- **Mechanism:** relevance collapses. The material that would change the decision is diluted among material that would not, and the decision ends up made on noise.
- **Fix:** load the narrowest thing that would change the decision, and no more. Stop when the next level stops changing the answer. See `context-system.md`.

## Under-evidenced certainty

- **Symptom:** a claim whose evidence does not reach it, or an assumption that lost its qualifier somewhere between the plan and the delivery.
- **Mechanism:** the qualifier is where the uncertainty lives. Dropping it converts a guess into a fact in the reader's mind, and the reader cannot recover what was never said.
- **Fix:** keep the qualifier attached wherever the claim appears, and state the confidence with it. See `evidence-system.md`.

## Permanent plan commitment

- **Symptom:** evidence contradicts the plan, and the plan is defended, re-explained, or re-run unchanged.
- **Mechanism:** commitment to the artefact instead of the objective. Every confirming observation is read as confirmation and every contradicting one is explained away.
- **Fix:** observation contradicting the plan is the system working. Return to JEv, record what changed and why, and re-plan the affected part.

## Capability proliferation

- **Symptom:** a skill minted per task; the capability list grows while reuse does not.
- **Mechanism:** a candidate is promoted on a single instance, so nothing generalises, and near-duplicate skills split the trigger signal until none fires reliably.
- **Fix:** apply the disqualifying question — will this be needed again? A one-off is a step in the plan. See `insufficient-capability.md`.

## Uncontrolled learning

- **Symptom:** one failure, or one success, permanently rewriting behaviour.
- **Mechanism:** a single instance is treated as a general pattern, and the change is irreversible, so a bad day becomes a rule.
- **Fix:** prefer the reversible change — adjust this run's approach and record the candidate. Promotion requires evidence that it generalises, plus a stated scope. See `learning-system.md`.

## Unnecessary delegation

- **Symptom:** specialists dispatched for work one context does better, with hand-off and review costing more than the work itself.
- **Mechanism:** delegation looks rigorous, and nobody checks whether the justification test was ever applied.
- **Fix:** require a separate domain, a large context the parent does not need, or an isolation need. If none holds, do it here. See `delegation.md`.

## Silent overreach

- **Symptom:** an action taken because the task implied permission, rather than because permission was granted.
- **Mechanism:** the line between reasonable inference and authorisation was never drawn, so implication is treated as consent. The user finds out after the fact.
- **Fix:** name the authorisation before acting, or ask. Acting beyond a recorded authorisation is overreach whatever the task suggested. See `human-control.md`.

## Difficulty worship

- **Symptom:** effort, ceremony, and reasoning depth scaled to how hard the problem sounds rather than to what triage found.
- **Mechanism:** the ladder is treated as a quota instead of a floor. Carrying R3 reasoning on an R0 task is pure waste, and it is the most common failure of this kernel.
- **Fix:** stop at the lowest rung that is adequate, and de-escalate the moment reality turns out easier. See `triage.md`.

## The unifying failure

Every one of these is the kernel substituting the *appearance* of rigour or
confidence for actual evidence: more ceremony, more retries, more specialists,
more certainty than the evidence supports. That is the single failure this
architecture exists to prevent, and each rule elsewhere in this skill is a guard
against it. When you notice yourself producing more work than you have evidence
for, you are already in one of these.
