# Evaluation

How this repository knows whether the kernel does what it claims, and how a
failed evaluation becomes an architecture change rather than a patch.

Evaluation exists because the kernel's output is prose. "It worked" is not a
finding. A finding is: a specific case, a specific decision record, a specific
verdict, against a property the architecture claims to have.

## The claim under test

The architecture makes one claim that everything else follows from:

> Can this kernel scale from a trivial task to the hardest class of problems
> without requiring a different architecture?

Everything in the suite is a way of pressing on that claim from a different
angle. A suite of easy tasks would pass for a well-written workflow. The suite is
built to separate the two.

## Benchmark classes and the properties they test

| Class | Kernel property under test | Typical failure it catches |
|---|---|---|
| **simple** | the kernel does not over-orchestrate; it recognises when the next action is determined | planning ceremony on a one-line change |
| **medium** | decomposition, per-unit verification, honest reporting | unverified units presented as a result |
| **complex** | capability resolution under partial coverage; recovery mid-run | improvised capability used unvalidated; blind retry |
| **ambiguous** | task modelling, asking rather than guessing, stating assumptions | a wrong objective solved confidently |
| **long-context** | context discipline: loading the narrowest thing that changes the decision | load-everything, or load-too-little with a confident answer |
| **multi-step** | plan mutability; replanning when evidence contradicts | permanent plan commitment |
| **cross-domain** | domain independence; no routing table | domain-specific reasoning leaking into the kernel |
| **high-assurance** | rung discipline, human checkpoint, independent verification | an irreversible action taken at R0 |
| **failure-prone** | classification, bounded retry, honest stop | retry storms; scope reduced without saying so |
| **unknown-domain** | capability acquisition, `skill-creator` use, scoped promotion | skill proliferation; an unscoped promotion |
| **security** | every control in `../security/controls.md` | injection, poisoning, fabricated evidence |

## How a case is written

A case that does not discriminate teaches nothing. Each case carries four things.

**An objective**, in the user's terms, with enough context to be ambiguous
where ambiguity is the point.

**A trap.** The case must contain something the kernel can get wrong if it is
guarding against the obvious failure only. A retrieved document with an
instruction in it. A tool that returns a plausible error. A requirement that
looks satisfiable and is not. A second criterion that quietly conflicts with the
first. Without a trap, the case measures capability, not architecture.

**A plan deviation.** The expected path must include at least one deviation from
the plan the kernel would form initially: an assumption that fails, an unknown
dependency discovered mid-run, evidence that contradicts a decision. A case
where the plan survives intact tests almost nothing, because the interesting
behaviour is the revision.

**Success criteria and a required verdict.** What must be true, and whether
PARTIAL is an acceptable answer. Cases that require VERIFIED will produce
pressure to launder a PARTIAL, so state explicitly which cases permit it.

**A required decision record.** Which boundaries the run should cross, and which
it should not. A run that reaches the right answer through a plan nobody would
choose has not passed.

## What is measured

Correctness alone is not enough, because the kernel's distinguishing claims are
about cost and honesty.

| Metric | What it means | Why it is here |
|---|---|---|
| Task success | the criteria hold | the obvious one |
| Verification quality | the right check kind, at the right depth, and reported | the output contract is a claim about checking |
| Honest reporting | every claim carries its epistemic status; PARTIAL is not upgraded | the most damaging defect is invisible otherwise |
| Recovery effectiveness | failures classified, causes identified, retries bounded | distinguishes recovery from persistence |
| Context efficiency | loaded material bears on a live decision | detects load-everything and load-too-little |
| Reasoning efficiency | rung matches triage; escalation and de-escalation both occur | detects difficulty worship and rung inertia |
| Capability efficiency | resolution walked the ladder; creation is rare | detects proliferation and unvalidated improvisation |
| Cost | spend against value delivered | the property the ladder exists to protect |
| Security robustness | controls held under adversarial input | see `../security/` |
| Learning soundness | promotion required evidence and scope | detects uncontrolled learning |

### The comparison that matters

Every meaningful run is evaluated twice: the same model without the kernel, and
the same model with it. A kernel that produces the same result more slowly is not
an improvement, and a kernel that improves the result while destroying the cost
advantage is trading one defect for another.

The comparison is also the only way to detect over-orchestration honestly. A run
that looks reasonable in isolation can be shown to be wasteful by comparison
with the same task answered directly.

## From a failed evaluation to an architecture change

Most failures should not become code changes. This is the order of responses,
and moving up it is a defect in the review process.

1. **The case is wrong.** The expected path was not actually correct, or the
   trap is not a trap. Fix the case. This happens more often than anyone
   expects, and it is not a failure of the kernel.
2. **The case is ambiguous.** Two readings of the objective, and the kernel took
   a defensible one. Sharpen the case, and add it to the ambiguous class.
3. **The case exposes a missing reference.** The kernel lacked a procedure it
   should have had. Add the reference file. Most failures end here, and that is
   the healthy outcome.
4. **The case exposes a boundary that does not exist.** A decision the kernel
   had to make with no boundary to record it. Add the boundary to the fabric and
   write an ADR, because this changes
   [0001](../decisions/0001-jev-as-decision-fabric.md).
5. **The case exposes a wrong rung mapping.** The ladder sends this kind of task
   to the wrong rung. Change the mapping table and write an ADR, because this
   changes [0004](../decisions/0004-explicit-effort-ladder.md).
6. **The case exposes a missing control.** Something the kernel did that the
   security model forbids. Change `../security/controls.md` and add a security
   case in the same change.
7. **The case exposes a wrong architecture claim.** The design is wrong, not the
   implementation. Write an ADR, supersede the record that made the claim, and
   say plainly in the research notes what is now known that was not known.

Rules for this process:

- **Every step above four requires an ADR.** Below four, a reference file or a
  case change is enough, and an ADR for a missing reference file is noise.
- **A fix that adds a domain-specific branch is not a fix.** If the case is only
  fixed by teaching the kernel about a domain, the kernel has acquired a domain
  and lost the property being tested. See the contributions guide at
  `CONTRIBUTING.md` in the repository root.
- **Every security case is a permanent regression case.** A security control
  that has failed once must fail loudly forever after, or the control will be
  removed by someone who has not seen the incident.
- **Record the metrics, not just the verdict.** A fix that improves the verdict
  while degrading cost or context efficiency has moved the defect, not removed
  it.

## What "done" means for the suite

The suite is adequate when:

- Every class above has cases that fail without the kernel and pass with it.
- Every security control in `../security/controls.md` has at least one case.
- Every anti-pattern listed in the kernel has a case that detects it.
- Every promoted capability in the skill library has a case that fails if its
  trigger or its scope is wrong.
- Every ADR's "revisit when" conditions have at least one metric tracked that
  would notice them.

The last one matters more than it looks. An ADR without a tracked condition is a
decision nobody will ever revisit, which is a decision that will eventually be
reversed by accident.

## Honest limits of the evaluation

- Most cases run against one model family, so the results characterise that
  family. Cross-model reproducibility is a goal, not a current property.
- Judging a prose deliverable requires human review for the honesty and
  proportionality properties. That is the most expensive part of the suite and
  the least automatable.
- Long-horizon properties, such as whether the system degrades over months of
  accumulated promoted rules, cannot be established by a suite that runs in
  minutes. Degradation is inferred from deprecation counts and promotion-scope
  audits, which is weaker than measuring it.
- The suite is built from real failures, which means it covers the defects we
  have seen. A defect nobody has seen is, by definition, not in the suite. This
  is the strongest argument for treating reported failures as cases rather than
  as issues to close.
