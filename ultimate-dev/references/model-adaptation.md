# Model Adaptation

The kernel is model-agnostic: it must produce the same rigour whether the work
is done by a very small executor with a short horizon or a large one with a long
horizon. What changes is the **form** of the work, not the standard of proof.
Adapt the form; never lower the bar and call it adaptation.

That first paragraph is the whole of this file, and the rest of it is the
mechanism. The part that follows makes the distinction checkable, because
"adapt the form" is otherwise a licence to do less and describe it as rigour.

## The host is a term in the effort gate

The rung ladder in `triage.md` answers one question: **how hard is this task.**
It has, until now, not answered a second one — **how much procedure can this
model turn into substance** — and that omission is what produces a run that is
thorough on paper and dull in practice. `triage.md` names the gap under "Two
inputs the four questions miss" and then answers it with "re-calibrate", which is
not something a run can execute.

The failure is not that small models are worse. It is that a fixed procedure is a
fixed tax, and the tax lands in opposite directions at the two ends.

**Toward dull on a strong host.** Over-prescription is measurable, not
stylistic. Step-by-step scripts and stacked `MUST`/`NEVER` emphasis measurably
degrade current-generation model output, and the migration advice is to start
from a minimal brief rather than accrete onto an old prompt stack
(`skills/long-horizon-prompting/`, `claim-long-horizon-lean-prompt`).
Current-generation models need less scaffolding and do *worse* with redundant
scaffolding (`skills/senior-prompt-engineer/`). Structured-but-irrelevant
context is a distinct risk class, and in one retrieval setup coherent
well-structured context performed *worse* than shuffled. A long kernel applied
unchanged to a frontier model spends that model's attention on form; it will
comply beautifully and go nowhere.

**Toward dull on a weak host.** Less-capable models do not reliably *trigger*
context loads, so a rule reachable only by looking it up is a rule that does not
fire — the stated remedy is to put critical constraints in **statically**
(`skills/filesystem-context/`). And breadth is the expensive failure: a small
model handed twenty work units produces twenty shallow ones, which reads as
thorough and is not detectable by reading the report, because the report is the
thing that is wrong.

**The direction nobody handles.** Frontier models are systematically
over-optimistic about their own remaining budget, and capability and budget sense
are barely correlated — across the budget-awareness studies surveyed for this
repository, at r ≈ 0.35, which is to say they are different things. Early
stopping on a trajectory that was going to fail saves 28–64% of its tokens. So
the risk on a strong host is not doing too much ceremony. It is **settling early
and calling it done**, and the model least able to notice is the most capable
one. That is why the rule below is a gate rather than a sentence.

> The budget-awareness and retrieval findings come from the external survey under
> `research/` in the source repository, which is deliberately not part of an
> install. The claims are stated here because the gates below stand or fall with
> them, and the survey is the place to re-examine them.

### Three tiers, host-derived

| Tier | What it means | Procedure ceiling |
|---|---|---|
| `small` | Narrow context, weak instruction-following, unreliable self-initiation | **R2** |
| `mid` | The default assumption | **R3** |
| `frontier` | Long horizon, strong self-correction, holds a large brief | **R4** |

```sh
python3 tools/run-state.py init --rung R2 --host mid --objective "..."
python3 tools/run-state.py set-host --host small --why "<what changed>"
```

`--host` is a term, never a model name — the tier is read from what the host
exposes, on the same principle as the section below. A ladder that named models
would be stale the week one ships.

### The ceiling is on procedure, never on the standard of proof

This is the distinction in the opening paragraph, made operational. Getting it
backwards is how you build a kernel that is safe on no host.

**Never scale with the host.** These are correctness, not sophistication, and a
small executor gets all of them, in the same words, with nothing to trigger:
never report a tool result you did not observe · never invent an API, path,
command, or version · never commit, push, or open a pull request · do only what
was asked · ask before anything irreversible, externally visible, or
credential-bearing.

**Scale with the host.** This is form, and form is what a small executor cannot
afford because it has no attention to spare:

| | `small` | `mid` | `frontier` |
|---|---|---|---|
| Decision records | only the ones that change the outcome | material calls | material calls, with `rejected` |
| Process log | the stages, not the narration | same | same |
| Work units | **fewer and larger — never more** | as the plan needs | as the plan needs |
| Context ladder | jump to C2/C3; do not walk C0→C6 | as needed | as needed |
| Delegation | one specialist, not a fleet | parallel where independent | parallel where independent |

On a `small` host, load `SKILL-compact.md` rather than the full `SKILL.md` — it covers the non-negotiable rules and effort gate in 67 lines without paying for ceremony the host cannot sustain.

Read the `small` row as an instruction rather than a permission. **Fewer, larger
units is the whole difference between an executor that does two things properly
and one that does eight things shallowly.**

### Two gates, pointing in opposite directions

`check` enforces both, and the asymmetry is deliberate.

**Above the ceiling, say why.** A rung above what the host can carry is refused
unless `init --exceeds-ceiling "<why>"` records a reason. The ceiling is a
default, not a law — one focused hard call is precisely what a small executor is
good at. What is forbidden is arriving there by default, because the result is
breadth instead of depth and nothing in the report reveals it.

**Below the floor, on a frontier host, say why.** De-escalating is free and often
correct — `triage.md` calls never de-escalating the most common failure of this
architecture. But on a frontier host, dropping from R3 or above without a
recorded reason is the under-investment failure, and it arrives silently.

Note what the second gate is not. It does not tell a frontier host to apply more
procedure; that is the over-prescription failure wearing a friendly hat. It makes
an early stop a **recorded** choice rather than an invisible one.

### What is not claimed

- No run here has executed across more than one model, so there is no paired
  before/after for host adaptation. `maturity.md` holds the executed counts.
- The ceilings are defensible but not derived. They sit where the shape of the
  failure changes — past R2 a small host's marginal decision is worth less than
  its first — not where a curve was fitted.
- `mid` is a default, not a measurement.

A tier that turns out wrong for a given host should be corrected in one flag, per
run. That is cheaper than being right in advance.

## Degrade gracefully, do not branch on identity

The kernel must not assume any particular endpoint, vendor, interface, or
capability is present. Detect what the executor can actually do, then shape the
work to that. Where a capability is missing, the response is one of:

- **Substitute** — a different means of reaching the same expected result.
- **Degrade** — do less at lower rigour, and say so in the output.
- **Acquire** — resolve the capability, validate it, then proceed.
- **Report** — the objective needs what is absent; say what is missing and stop.

Do not simulate a missing capability. Do not branch behaviour on the identity of
the executor; branch on its **observed** limits. The same kernel code must run
in an environment that reports nothing about itself and in one that reports
everything.

## Observable dimensions you may adapt on

| Dimension | Options | Shift toward the other when |
|---|---|---|
| **Deterministic vs generative** | Tool for arithmetic, parsing, hashing, counting, formatting; reasoning for judgement, framing, ambiguity | The work has a right answer you can check with a tool — always take the tool. See `deterministic-vs-agentic.md` |
| **Single vs split context** | One context for the whole task; split units, subagents, or workstreams | The material exceeds what can be held coherently, or independent work does not need shared state. Splitting costs a re-briefing; do not pay it for tidiness. See `delegation.md` |
| **Depth vs breadth** | One part examined exhaustively, or every part examined once | Uncertainty is concentrated in one part — go deep there. Breadth first, then depth where the evidence is worst |
| **One attempt vs verified retries** | Attempt once and report; or iterate until a check passes | A cheap check exists and a failure is recoverable. Then retry; without a check, retrying is gambling, not rigour |
| **Context volume** | Narrow and compiled; broad and raw | Load the narrowest thing that would change the decision, then no more. See `context-system.md` |
| **Granularity of output** | A conclusion, or the conclusion plus its evidence | The consumer is deciding something consequential. More evidence, less conclusion padding |

## The rule for capabilities you cannot fully verify

If you cannot verify the output of a capability, you do not get **more
attempts** — you get **stronger verification**. Repeating an unverifiable action
produces the same unverifiable result with a larger bill, and multiple agreeing
unverified outputs are not corroboration: they are the same assumption counted
more than once.

So, in order: find a check that would fail if the output were wrong; if none
exists, get one (an independent derivation, a comparison against a known case, a
human read) before using the output; and if no check can exist, mark the result
as unverified in the output contract rather than implying it is sound.

## Unmeasured means unmeasured

Report a metric you could not measure as **unmeasured**. Never substitute a
plausible number, an estimate wearing the costume of a measurement, or a figure
carried over from a different context. A confident invented figure is worse than
a gap, because it removes the reader's reason to check anything else you said.

If the environment reports no usage, cost, or duration figures for this run, say
exactly that — "the environment reported no usage or cost figures" — rather than
estimating them. The absence of a number is a fact about the run and may be
stated as one.

The same discipline applies to every claim about your own work: difficulty,
coverage, completeness, and confidence are all claims, and each is VERIFIED,
PARTIAL, or FAILED per `verification-system.md`. "Probably all of them" is
PARTIAL until you check.

## Prohibitions

- **No confidence inflation on transfer.** Assuming the executor handles a
  familiar shape as well as it handled a different one is an untested
  assumption. Check it or mark it.
- **No silent narrowing of the objective.** Degrading is allowed; quietly
  delivering less than was asked is not. Name what was dropped.
- **No tuning behaviour to a specific endpoint's interface.** A shape that only
  works where one capability exists is a capability dependency, not a strategy.
- **No estimate in a measurement slot**, in this file's terms and in the output
  contract. See `output-contract.md`.

See `reasoning-system.md` for the rung that governs how much adaptation is
warranted, `deterministic-vs-agentic.md` for the split that matters most, and
`evidence-system.md` for what counts as support for a claim.
