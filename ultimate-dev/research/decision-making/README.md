# Decision-making

What the literature offers for the problem the kernel actually has: choosing how
to spend limited effort on an objective nobody has characterised yet.

## The question this raises for the kernel

JEv decides at seventeen boundaries. There is no fixed order, no known action set,
and no reward signal to learn from. The objective function is "expected outcome
per unit of cost, risk, and uncertainty", which is a stance rather than a
computable quantity. So: how should a decision be made when the option set is
discovered as you go, the values are unknown, and a wrong decision is often only
visible after it has cost real resources?

## Approaches considered

**Sequential decision-making (MDPs and POMDPs).** Formalise states, actions,
transitions, rewards; choose a policy maximising expected cumulative reward. The
partially-observable variant matches the kernel's real position: it never observes
the true state of the problem, only evidence about it. Adopted as a modelling
vocabulary, not a solver — states, actions, and observations map onto task state,
boundaries, and evidence, but rewards do not map, because the kernel has no
scalar reward. It has criteria, some boolean and some not comparable.

**Value of information.** Compute the expected reduction in uncertainty from
acquiring something, and buy it when that exceeds the cost. This is exactly the
context ladder and the research-depth boundary, and it supplies their missing
justification: acquire when the decision could change and the information is
cheap, not when the topic is interesting. Adopted in principle as the criterion
for C5 and C6, not as a formula, because the posterior is a set of text beliefs
rather than a distribution and pretending otherwise would produce a number nobody
can trust.

**Expected value per cost.** Normalise outcomes by cost, take the best ratio.
Rejected as the sole criterion. It prefers cheap certainties over expensive ones
with better outcomes, has no representation for a small probability of
catastrophic outcome, and has no notion of a decision that changes what is
possible later — which is most of what a plan does.

**Metareasoning and metalevel reasoning.** At each point, choose between acting
and thinking about acting, valuing the thinking by the improvement it will
produce. The closest formal treatment of the kernel's central question. Adopted
as the *reason* the architecture has a decision fabric at all: the kernel is a
bet that metareasoning beats both doing everything reflexively and reasoning
about everything. Rejected as an operational rule, because the improvement
estimate needs a value function the kernel does not have.

**Anytime algorithms.** Return a valid answer at any interruption point,
improving with more time. Adopted at the architectural level, and it is the
reason work units are resumable and why PARTIAL is a legitimate terminal verdict.
Rejected as a reason to keep computing: an anytime algorithm improves, and a run
on a trivial task should stop improving immediately.

**Satisficing versus optimising.** Agents satisfice, they do not optimise,
because the world is too complex to compute the optimum. Adopted directly. Stop
at the first rung that is adequate, stop loading context when the decision stops
changing, stop acquiring when the gap closes. Optimising these would be both
unaffordable and wrong: the optimum is usually unreachable, and a good-enough
decision now beats a better one after the deadline.

**Bounded suboptimality and rational metareasoning.** Conditions under which
greedy myopic decisions are within a constant factor of optimal. Not adopted as a
guarantee: it holds under distributional assumptions the kernel cannot satisfy,
and citing it would borrow authority the assumptions do not support.

**Bayesian bandits and Thompson sampling.** Allocate effort between options with
uncertain payoffs. Rejected for now. The kernel's options are qualitatively
different approaches, not parallel draws from one distribution, so one
option's signal does not inform the others. Bandit allocation also optimises the
average case, which is the wrong target when the downside is asymmetric.

**Hierarchical RL and options.** Learn reusable higher-level actions. Rejected as
a mechanism: no reward signal, and learned options are hard to audit. Skill
creation is gated and specification-driven instead, which is slower and
inspectable. See
[0002](../../docs/decisions/0002-skills-are-resources-not-agents.md).

**Decision trees and analytic hierarchy process.** Structure the choice, weigh
criteria, compute. AHP is widely used in engineering for exactly this kind of
effort-versus-risk judgement. Rejected as a decision rule: AHP is sensitive to
criteria weighting in ways not visible in the result, which is fatal here. The
point of the record is that a reviewer can see what was weighed, and a collapsed
score hides it.

## What was adopted

- A **satisficing** posture: stop at the lowest adequate rung, stop loading when
  the decision stops changing, stop acquiring when the gap closes.
- **VOI as the stated criterion** for external evidence and specialist depth, in
  words rather than arithmetic: acquire when the decision could change and the
  cost is small relative to being wrong.
- **Anytime behaviour**: interruptible units, and PARTIAL as a terminal verdict.
- **Explicit rejected alternatives** as a mandatory field — the part of decision
  theory that is cheap to keep and expensive to lose.
- **Local, myopic decisions at the hub**, on the reasoning that
  ∑P(success)·V − C is more defensible than a global optimisation the kernel
  could not actually perform.

## What was rejected and why

- **Full POMDP treatment.** The state space is not enumerable and the reward is
  not scalar; the formalism would produce arithmetic nobody could check, which is
  worse than a stated stance.
- **Ratio-based effort allocation.** Prefers cheap certainties and cannot
  represent catastrophic downside.
- **Automatic weighting of the four triage axes.** Averaging is destructive: a
  simple irreversible action is the highest-consequence case, and a score hides
  it. See [0004](../../docs/decisions/0004-explicit-effort-ladder.md).
- **Learning the decision policy.** No reward signal, and an uninspectable policy
  would replace the audit trail the architecture is built on.
- **Numeric decision scores in the ledger.** They look rigorous and are
  unauditable. Confidence stays high, medium, or low, with the evidence named.

## Open problems

- **Verification cost scaling.** How do you set verification depth when the check
  itself costs as much as the work, and its value is unobservable until after?
  The proportionality rule is a rule of thumb with no theory behind it. This is
  the largest unresolved question in the architecture, and it constrains
  deliverables directly.

- **When to escalate reasoning.** Escalation triggers are observable events, but
  their thresholds are unstated. A task assigned the wrong rung at R2 and
  discovered at R3 has already paid the discovery cost twice. No good rule exists
  for detecting that a task is harder than triage thought, before paying to find
  out.

- **When de-escalation is safe.** Dropping effort can discard reasoning that
  would have caught a problem. The kernel de-escalates when reality is easier,
  which is often right and occasionally catastrophic. There is no principled
  guard, only the blast-radius trigger.

- **Knowing when to stop.** Success criteria are the stop condition, which works
  when they are well written. When they are underspecified there is no principled
  way to know whether more effort would change the verdict, and satisficing means
  the kernel will often stop early. A deliberate trade against an unreachable
  optimum, with unquantified residual risk.

- **Value of information without a posterior.** The criterion is right and
  uncomputable here. Making it numeric requires calibrating belief updating in
  text, which is an open problem in its own right.

- **Optimising across the run rather than within a boundary.** Every decision is
  local, which is probably wrong for long-horizon work. Hierarchical planning
  mitigates it structurally; nobody has measured whether that is enough.

- **Regret as an alternative objective.** Regret handles asymmetric cases better
  and needs a counterfactual the kernel rarely has. Unexplored.
