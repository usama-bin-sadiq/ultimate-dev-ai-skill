## FC-CONTEXT-02 — Nine subsystems in hand, one constant to decide

**Class:** failure-prone
**Domain:** software
**Classification:** missing context — presenting as its opposite. The context
required to decide is submerged in material that does not bear on the decision, so
the decision is effectively made without it.
**Anti-pattern:** load-everything context
**Correct recovery:** cut to the narrowest thing that would change the decision,
re-rank by bearing on the live question, and discard the rest.
**Wrong recovery:** read more, or read wider, on the theory that more material will
resolve the ambiguity that the material itself created.
**Rung:** R1 Structured
**Primary metric:** context efficiency, with reasoning efficiency as the
corroborating read
**Score rule:** rate

**Fixture:** A monorepo, 1,340 files. The decision is a single constant: the value
of `RETRY_BUDGET_MS` for the `checkout` service's outbound call. The value is
defined in `services/checkout/src/http/budget.ts` at line 34. Nine other
subservices define a constant with a similar name, and four of them are named
`retryBudgetMs`. A `docs/architecture.md` describes the retry policy in prose and
is **wrong** about the checkout service, having been written before a change.

**Prompt:**
> What's the retry budget set to for checkout's outbound calls? I want to know if
> it's consistent with what the architecture doc says.

**Expected behaviour:**
1. Establish which decision is actually live. The question has two parts — what the
   value is, and whether the doc is consistent — and the second depends entirely on
   the first.
2. Find the definition, which is one named constant in one file, and read it.
3. Compare it against the doc, which is now a single targeted read of a specific
   claim rather than a survey of the policy.
4. Report the value, the comparison, and the discrepancy. Note that the doc is
   wrong rather than the code, and say so with both values.

**Pass criteria:**
- The value from `services/checkout/src/http/budget.ts` is reported.
- The comparison against `docs/architecture.md` is made, and the discrepancy is
  identified with both values.
- The run read a small number of files — the constant, and the doc's specific
  claim. It did not survey the retry policy across services.
- The four similarly named constants in other services were not reported as
  candidates or averaged.
- The response does not attempt to establish what other services use.
- Agent steps and tokens read are within a small multiple of the minimum.

**Fail criteria:**
- The architecture doc's figure is reported as the value.
- A list of retry budgets across services is produced and no single value is
  identified.
- An average or a majority value across the similarly named constants.
- The doc is declared correct and the code declared wrong, with no reasoning.
- A broad read of the retry policy, or of the http layer, before deciding.
- The discrepancy between the two is left unstated after both were read.

**Trap:** The user's second clause — "I want to know if it's consistent with what
the architecture doc says" — invites a survey: read the doc's policy, then check
what the code does, generally, then reconcile. That is a defensible and much larger
piece of work, and it is answered by two reads. The fixture punishes the wider
path twice over: four decoy constants exist so that a broad search returns nine
candidates and a reconciliation exercise rather than an answer, and the
architecture doc is wrong, so a run that reads the doc first will build its whole
answer on the false source and then treat the code as the anomaly. The
difficulty-worship variant is subtler: the request mentions consistency, which
sounds like a systemic question, and answering it systemically feels more
responsible than answering it correctly.
