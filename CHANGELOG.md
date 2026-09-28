# Changelog

## [4.0.25] — 2026-09-28

_No summary recorded. Review the comparison for details._

## [4.0.24] — 2026-09-28

_No summary recorded. Review the comparison for details._

## [4.0.23] — 2026-09-27

_No summary recorded. Review the comparison for details._

## [4.0.22] — 2026-09-27

_No summary recorded. Review the comparison for details._

## [4.0.21] — 2026-09-27

_No summary recorded. Review the comparison for details._

## [4.0.20] — 2026-09-27

_No summary recorded. Review the comparison for details._

## [4.0.19] — 2026-09-27

_No summary recorded. Review the comparison for details._

## [4.0.18] — 2026-09-27

_No summary recorded. Review the comparison for details._

## [4.0.17] — 2026-09-27

_No summary recorded. Review the comparison for details._

## [4.0.16] — 2026-09-27

_No summary recorded. Review the comparison for details._

## [4.0.15] — 2026-09-27

_No summary recorded. Review the comparison for details._

## [4.0.14] — 2026-09-27

_No summary recorded. Review the comparison for details._

## [4.0.13] — 2026-09-27

_No summary recorded. Review the comparison for details._

## [4.0.12] — 2026-09-27

_No summary recorded. Review the comparison for details._

## [4.0.11] — 2026-09-27

_No summary recorded. Review the comparison for details._

## [4.0.10] — 2026-09-27

_No summary recorded. Review the comparison for details._

## [4.0.9] — 2026-09-27

_No summary recorded. Review the comparison for details._

## [4.0.8] — 2026-09-27

_No summary recorded. Review the comparison for details._

## [4.0.7] — 2026-09-27

_No summary recorded. Review the comparison for details._

## [4.0.6] — 2026-09-27

_No summary recorded. Review the comparison for details._

## [4.0.5] — 2026-09-27

_No summary recorded. Review the comparison for details._

## [4.0.4] — 2026-09-27

_No summary recorded. Review the comparison for details._

## [4.0.3] — 2026-09-27

_No summary recorded. Review the comparison for details._

## [4.0.2] — 2026-09-27

_No summary recorded. Review the comparison for details._

## [4.0.1] — 2026-09-27

_No summary recorded. Review the comparison for details._
All notable changes to this project are recorded here. The format follows
Keep a Changelog. Versions follow semantic versioning.

## [Unreleased]

_Nothing yet._

## [4.0.0] — 2026-09-27

The decision-kernel rebuild, and the first release in which the evaluation suite
was actually executed. The headline finding is a null result: on a paired run the
kernel did not outperform the unaided baseline. That is recorded in
`ultimate-dev/evaluation/RESULTS.md` rather than smoothed over, because a suite
that cannot report an inconvenient result is not a suite.

### Added

- **`tools/build-fixtures.py` — the evaluation corpus's fixtures now exist and
  are verified.** Sixteen of the 121 cases name a file the run is meant to read
  (`events-2026-04.jsonl`, `src/report.ts`, `access_log_sample.csv`,
  `config/dev.yaml`, and others). None of those files were ever committed, so
  those cases measured whether the agent declines to fabricate rather than the
  behaviour they were written to measure. All are now generated, and three of
  them need a private git repository because their premise is about repository
  state.
- **Every number the corpus asserts about a fixture is re-derived from the
  generated file.** The corpus states 968 top-level refunds against a naive
  substring count of 1,204; one 18,422 ms row with 3,901 ms runner-up; a
  EUR 56,500 merchant drop with EUR 9,800 of March refunds. Those were
  assertions in a Markdown file, which is the category of claim this project
  exists to distrust. The generator now fails the build if any of them does not
  hold. Measured independently: 48,000 lines, `grep -c` 1,204, `jq` 968.
- **`tools/run-pilot.py` — the evaluation suite is executable.** 121 cases across
  seven classes, with environment failures distinguished from case failures,
  undecidable results recorded as `null` rather than guessed, and a refusal to
  publish any rate when too little of the sample produced a usable result.
- **CI now builds the fixtures and checks that every file-referencing case is
  satisfiable.** Two cases are exempt by recorded reason (their file references
  are outputs to create, or incidental mentions inside a prompt).

### Fixed

- **The validator was weaker without PyYAML, and said nothing.** The
  dependency-free frontmatter parser accepted a colon-space in an unquoted
  scalar — `description: Solve: it` — which PyYAML rejects outright. On any
  machine without PyYAML, and on every CI runner, the validator reported success
  for a document it had never validated. A check that quietly stops checking is
  worse than no check. The fallback now enforces the same rule, and CI runs the
  malformed-frontmatter mutation twice: once normally, once with PyYAML hidden
  behind a stub module, each with a clean-tree control.
- **The rule rejecting unfilled markers had two implementations and one was
  never running.** The shell check used `git grep -E` with `\b` word boundaries,
  which not every git build's regex engine supports. On this machine it matched
  nothing and reported success; on CI it worked and flagged a CONTRIBUTING.md
  line that forbids those very markers, because its exclusion filter was
  case-sensitive. Two implementations of one rule meant one was quietly broken.
  The shell duplicate is gone — `validate-skills.py` already does this
  case-insensitively and path-aware — and CI now fails if a second
  implementation reappears.
- **A self-test asserted nothing.** The "case needs an unbuilt file" case added a
  Markdown case to the corpus but did not regenerate `evals.json`, which is a
  projection of that Markdown. The validator therefore never saw the new case,
  and the test passed for the wrong reason. It regenerates the projection first.
- **The pilot's grader failed runs for describing what it would not do.** The
  first version matched words like "triage" and "plan" in the final message and
  reported a 67% false-trigger rate that was entirely an artefact: every flagged
  run was an agent writing *"Before I plan anything, Step 0 says this is R0, so let
  me act directly rather than guess."* A second version moved the matching to the
  runtime's stderr and inherited the same fault, because the runtime echoes the
  model's narration there too — it failed two runs that had performed zero
  mutations on the strength of a filename mentioned in passing. The grader now
  reads only arrow-prefixed tool-call lines, so narration cannot decide anything,
  and it is unit-tested in both directions.
- **The bundler's exclusion list was a comment.** `EXCLUDED_TOOL_FILES` named the
  maintenance tools that should not ship, nothing checked that the names were
  honoured, and `collect()` only classifies top-level entries, so the list was
  declared and then ignored. The bundle shipped a fixture generator, an eval
  projector, and a pilot runner that needs a harness an install does not have. It
  now excludes 5 of the 6 tools, checks its own list for stale and unhonoured
  entries, and drops the runtime bundle from 494 KB to 393 KB.
- **`TN-10` asks for something unsatisfiable.** The case specifies that
  `git log -S "TIMEOUT_MS = 3000"` returns commit `a1b2c3d`. A commit hash is
  derived from content, author, timestamp, and parent, so it cannot be chosen. The
  builder produces exactly one matching commit, which is what the case actually
  depends on, and reports the realised hash rather than forcing it. The case text
  should be corrected.
- **The doc-hygiene scan read generated fixtures** and reported three errors in
  files nobody wrote. A generated fixture is not unfinished documentation; it is
  data, and the scan now skips `.eval-fixtures/` for the same reason it skips
  `new-arch.md` and `prd.md`.
- **34 of 121 eval case ids collided.** The header pattern used a reluctant
  identifier group, which stopped at the first hyphen and turned
  `BM-AMBIGUOUS-02` into `BM-AMBIGUOUS`. Every case in an affected file shared
  one id, which silently breaks grading, sampling, and any diff of two runs. The
  group is now greedy and duplicate ids are a build failure.
- **The pilot could not drive a runtime.** Two separate causes: the adapter needs
  `--auto` before the agent can approve the tool calls that let it read the
  skill at all, and `--extra-args` requires the `=` form. Without the first, every
  run degenerated into the model narrating that it *would* read the file.
- **A harness that counted quota exhaustion as case failure.** Environment
  failures are now retried, attributed to the model rather than the case, and
  handed to the next model in a pool; only a fully exhausted pool makes a case
  undecidable. Structural runtime error types are preferred over matching prose,
  because a provider can reword a message without changing the failure.
- **A division by zero on the run's most important number** — the false-trigger
  rate crashed precisely when every must-not-fire case had failed in the
  environment, which is when it matters most. It now reports that the rate was
  not measured.

### Changed

- **A model pool replaces a single model.** A single free endpoint rate-limits,
  and a harness that gives up is measuring the endpoint rather than the skill.
  Every result records the model that served it, and a mixed-model run is flagged
  as not strictly comparable rather than silently pooled.

## [2.0.0] — 2026-09-26

Restructured the repository and redefined the product as a decision
architecture. This release replaces the previous toolchain with a
specification, an evaluation suite, and the documentation needed to change it
safely.

The kernel changes come from three research sweeps into the public skill
ecosystem, agent reliability engineering, and long-horizon agent scaling. The
research found several claims in the shipped kernel that were either overstated
or measured as counterproductive. Those are corrected here rather than deferred.

### Fixed

- **The prompt-injection claim was false.** `SKILL.md` described treating
  retrieved content as data as "the defence against prompt injection". It is a
  strong prior that measurably reduces susceptibility; it is not a defence.
  Explicit instruction-prohibition has been measured as insufficient on its own,
  and prompt structure does not reliably separate trusted from untrusted material.
  Rewritten to state the limit and to point at structural controls — a second
  factor the attacker does not have — as the only real boundary.
- **"Verification is never skipped" had inverted sign.** Carried-over rigour
  instructions have been measured to cause *over*-verification on current models.
  Step 7 now bounds verification: ask what the check would have to observe, and
  skip it when the answer is something a tool already returned.
- **Self-critique was presented as verification.** Re-reading your own output
  shares every blind spot with the thing it checks, and self-correction without
  external feedback has been measured to reduce accuracy. Step 7 now requires
  `VERIFIED (self-check only)` when independence was unavailable.

### Changed

- **Decision records point, they do not narrate.** `evidence` is now a pointer to
  an observation (`OBS-n`) or the literal `none`, never prose. A prose field
  cannot be checked for existence, which made it the ideal place to hide the
  system's worst failure. Enforced in `knowledge/schemas/decision.md`.
- **`confidence` must name its object.** A bare `high` is read downstream as a
  property of the conclusion rather than of the evidence, which is the documented
  over-trust failure. Now `high in <the thing>`. A bare value is a validation
  error, not a warning.
- **The decision-record count is rung-dependent; the fields are not.** Requiring
  all seventeen on every run was the most expensive possible assertion of
  diligence in a kernel whose most common defect is doing too much. `rejected`
  and `recovery` remain mandatory whenever a record is written.
- **Triage is a lookup, not a self-assessment.** Added observable properties per
  rung, and the rule that when introspection and observation disagree, the
  observation wins. Added model drift and over-verification as explicit inputs.
- **The scale claim is now qualified honestly.** The lifecycle, decision record,
  output contract, evidence requirements, and trust boundaries are identical at
  every level — that part holds. Orchestration topology is *not* scale-invariant:
  delegation shows negative returns past a threshold rather than diminishing
  returns, so it is a regime with a boundary. `references/delegation.md` and
  `references/parallelism.md` now carry upper bounds, not only justification
  tests.
- **`author` requires the reasoning, not just the gap.** A delegated writer handed
  only a conclusion is an uninformed decision-maker and will miss what the
  original analysis ruled out. The hand-over contract now demands the rejected
  alternatives, and asks rather than proceeding when they are missing.
- **Evaluation reports pass^k and clusters its intervals.** Per-trial rate and
  consistency are different questions — 75% per trial over three trials is a
  pass^3 of about 0.42. Cases share a model, harness, and scorer, so they are
  clustered; naive intervals are too narrow. Where the clustered interval crosses
  zero, the result is inconclusive, not positive. `regression/` is now labelled a
  guard rather than a measurement.

- **The evaluation suite is now runnable.** The 121-case Markdown corpus had no
  machine-readable form, so it was documentation rather than a harness.
  `tools/build-evals.py` projects it into `evals/evals.json` in the format
  standard tooling consumes — one-directional, with the Markdown as the source of
  truth. CI fails on drift, so the two cannot diverge.
- **A distribution path that ships only the skill.** The repository is 2.5 MB, of
  which 395 KB is runtime; standard packaging tools do not know which is which and
  bundle all of it. `install.sh --bundle` emits the 75-file runtime subset, rooted
  at the skill name, and refuses to produce a bundle with dangling references, an
  orphaned reference file, or an unclassified top-level tree.

### Fixed

Five defects found by auditing the artifact against `new-arch.md` and `prd.md`
rather than against recollection. All are recorded because two of them were
introduced by earlier fixes in this same release.

- **The context ladder contradicted the specification.** `new-arch.md` defines
  seven levels, C0 through C6. The skill shipped six, having merged C0 and C1 and
  renumbered everything above them, so every level from C1 up mismatched the
  specification across 52 files. Restored to seven, with C0 (the task) and C1 (task
  state) separated deliberately: collapsing them loses the ability to say "the
  task is unchanged but the plan has moved".
- **The cross-cutting control plane was missing a system.** The specification
  names eight; seven shipped. **Observability** is now `references/observability.md` —
  the three surfaces that make a run steerable, interruptible, and auditable
  mid-flight, and the three failure modes only catchable with them.
- **Self-Evaluation was a clause, not a layer.** The specification devotes layer
  13 to it with nine questions. The skill compressed it into one sentence inside
  Step 9, dropping three of the nine. Now `references/self-evaluation.md`, with the
  three that catch waste called out as the ones a run skips.
- **The confidence rule was applied in two of four places.** `SKILL.md` and
  `decision-fabric.md` required confidence to name its object; `output-contract.md`
  still specified a bare level, and `evidence-system.md` had no pointer rule. The
  tree contradicted itself on the two rules judged most important. Both now agree.
- **Four of the specification's seventeen decision boundaries were unfindable by
  name.** This kernel says `rung` for reasoning effort, `delegation` for specialist
  delegation, `parallelism` for parallelisation, and resolves workflow selection
  through the capability ladder rather than as its own boundary. Defensible, but
  `decision-fabric.md` now carries an explicit mapping so none of them reads as
  missing.

### Added

- **`references/self-evaluation.md`** and **`references/observability.md`**, plus
  `references/README.md` as the annotated map of all fifty references.
- **`tools/bundle-skill.py`.** Builds a runtime-only bundle and verifies it three
  ways before writing: every backticked path survives bundling, every reference
  file is reachable, and the result passes the skill validator. The
  "survives bundling" check is the one that matters — a naive existence test
  passes a reference into `docs/` because `docs/` still exists in the source, and
  that is exactly the dangling pointer the check exists to catch.
- **`references/runtime-portability.md`.** Twelve optional runtime capabilities,
  how to detect each, and the defined degraded behaviour. Its rule: an absent
  capability is reported, never assumed and never imitated. Also states that R4 is
  unavailable without an independent check, rather than performing an R3 and
  relabelling it.
- **Self-conditioning defence in `references/learning-safety.md`.** Promotion
  gating limits *what* may change; it says nothing about what a retained
  conclusion does to later reasoning. A run that deliberately retains conclusions
  holds its own prior output in front of itself, which is the condition under
  which a wrong conclusion is re-read at every step. Counter-measures and the
  unresolved interaction are stated explicitly.
- **`agents/security-reviewer.md`.** Manufactures an attack rather than checking a
  checklist — structurally unlike the six evaluating roles, which all test a claim
  against evidence. It also closes a real hole: the promotion gate named a role
  that did not exist, so "nothing self-promotes" was enforced by assertion.
- **`evaluation/benchmark/TRIGGER-NEAR-MISS.md`.** Twenty cases that share the
  kernel's trigger vocabulary and must still not trigger it — "plan" as a verb,
  "multi-step" in a syntax question, "unfamiliar" describing the user's situation
  rather than the agent's. The existing negatives are trivially unrelated; these
  are the cases that actually catch false triggers.
- **Three research areas**: `research/skill-ecosystem/`, `research/reliability-engineering/`,
  and `research/long-horizon-scaling/`. Each records what was read, what was not,
  and what it would change.

### Notes

- No new sub-skills were added. Five candidate roles were surveyed against the
  public collections and four were rejected as duplicating existing roles or
  competing with the kernel's trigger. That negative result is recorded in
  `research/skill-ecosystem/`.

### Repository restructure

- **Repository restructured.** The previous single-directory layout was removed
  and replaced with the architecture and PRD structure. The skill now lives in
  `ultimate-dev/`: `SKILL.md` and `references/` at its root, with
  `skills/skill-creator/` as a sub-skill and `agents/` holding the delegated
  roles. `knowledge/`, `evaluation/`, `examples/`, `docs/`, and `research/`
  sit alongside as supporting material. The repository root holds installation
  and release mechanics only. The previous `scripts/` toolchain, its generated
  artefacts, and the manifest and sync machinery that surrounded it are gone.
- **Installation is a copy, not a build.** `install.sh` copies the skill into a
  detected skills directory, prunes the documentation trees by default, verifies
  the result, and refuses to overwrite an existing install without confirmation.
  `--all` keeps everything. A pruned install is 71 files and validates clean.
- **The kernel is now a decision architecture, not a Python toolchain.** The
  deliverable is the decision procedure: a task model, a triage gate, the JEv
  decision fabric at seventeen boundaries, a context ladder, a capability
  resolution ladder, a mutable plan of atomic work units, verification against
  observed evidence, structured recovery, and a gated learning lifecycle. There
  is no runtime, no daemon, and no generated payload.
- **CI retargeted.** Validation now checks the structure and internal
  consistency of the specification — skill metadata, reference map completeness,
  link integrity, and the conventions the contributions guide requires — rather
  than running a test suite for a removed toolchain.
- **The universal kernel is now the stated goal.** The product is defined by one
  claim: the same kernel spans a trivial task and a civilisational programme
  without changing architecture. Effort is set by an explicit rung ladder,
  separate from the scale level, and both are recorded.

### Added

- `docs/architecture/` — the fourteen layers, the kernel's execution model, the
  context and capability ladders, and how one kernel operates from L1 to L7.
- `docs/concepts/` — the shared vocabulary, and the verification and evidence
  structures, including the epistemic statuses and the claim-to-evidence chain.
- `docs/decisions/` — the ADR process and the first four decision records: JEv as
  the decision fabric, skills as resources rather than agents, the gated learning
  lifecycle, and the explicit effort ladder.
- `docs/operations/` — how to run, inspect, interrupt, and resume the kernel; the
  kernel's own failure modes with causes and fixes; and budget allocation and
  scope reduction.
- `docs/security/` — the threat model, the concrete controls, and incident
  response, covering injection through retrieved content, malicious tool output,
  capability poisoning, evidence manipulation, unauthorised action, credential
  exposure, and accidental destruction.
- `docs/evaluation/` — how the benchmark classes map to kernel properties, and
  how a failed evaluation becomes an architecture change.
- `research/` — what the architecture borrows from decision-making, context
  optimisation, capability acquisition, skill generation, reasoning,
  verification, recovery, and learning, with the open problems in each area
  stated plainly rather than resolved.
- `evaluation/` — benchmark cases by class, domain cases, failure cases,
  security cases, and regression.
- `examples/` — worked examples, including cases with a trap and a required plan
  deviation.
- `knowledge/` — schemas for the task, decision, context, capability, skill,
  evidence, observation, experience, and learning records, plus the freshness,
  provenance, validation, promotion, and retention policies.
- `LICENSE` — MIT.
- `CONTRIBUTING.md` — the style rules, the reference and evaluation case
  procedures, and the rule that no change may add a domain-specific code path to
  the kernel.

### Removed

- The Python toolchain: task engine, model-adapters layer, attestation gate,
  context utilities, generators, validators, and their tests.
- The generated documentation and prompt payload pipeline, and the CI jobs that
  rebuilt and diffed those artefacts.
- The release workflow that versioned a tool package. Releases now version the
  architecture.

### Migration

- Behaviour written against the toolchain's CLI does not carry over. The
  capability it provided — enforcement, state, and verification — is now
  specified rather than implemented, and enforced by evaluation cases.
- Anything that depended on a generated prompt payload should read
  `SKILL.md` and its references directly.

## [1.0.0]

Historical. This release covered the previous product, which was a Python
toolchain for agent task execution. It is kept for provenance; none of it is
present in the current tree, and nothing below describes current behaviour.

- A runnable task engine with sequential, parallel, and conditional execution, a
  unified state model, checkpointing, and a doctor diagnostic aggregate.
- A model-adapter layer that presented a single execution interface across
  several model providers, with model selection at run time.
- An attestation gate that required side effects to be observed rather than
  asserted, with adversarial coverage added late in the series.
- Configuration expressed as human-authored definitions, migrated from JSON to
  YAML, with generated header files carrying a version marker.
- A generator and sync pipeline producing an installable prompt payload and
  documentation, with CI validating that the generated files matched their
  sources, and a release workflow versioning the tool package.

### Notes on this history

Only two versions are recorded, because only two releases of substance exist:
the toolchain line, and the restructure that replaced it. Intermediate
patch-level releases in the toolchain era were version bumps and defect fixes
against a package that no longer exists in this tree, and are not enumerated
here rather than reconstructed.
