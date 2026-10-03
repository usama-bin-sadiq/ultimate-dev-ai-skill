## FC-CAP-02 — Minting a skill for a thing that will not recur

**Class:** failure-prone
**Domain:** software
**Classification:** wrong capability — the correct resolution is *no capability at
all*: the work is a step in the plan, not an asset.
**Anti-pattern:** capability proliferation
**Correct recovery:** apply the disqualifying question — will this be needed again?
— answer it honestly, and keep the procedure as a plan step or a written note in
the run.
**Wrong recovery:** create a skill, install it, and treat the run's output as a
durable capability.
**Rung:** R1 Structured
**Primary metric:** capability efficiency
**Score rule:** rate

**Fixture:** The user asks for a one-off: convert this specific 60-page supplier
catalogue PDF into a specific 12-column CSV layout, once, for one internal
process. `skill-creator` is available. No prior similar task exists in the
repository, and `docs/` records that the supplier's format changes twice a year
with no notice.

**Fixture required:** no
**Prompt:**
> Convert the attached supplier catalogue into our standard 12-column import
> layout. It's for the Q2 refresh, one time only.

**Expected behaviour:**
1. Resolve the capability in order, per the kernel's own resolution ladder. Doing it
   directly is available and sufficient: parse the PDF, map the columns, produce
   the CSV.
2. Apply the disqualifying question before creating anything. The user has said
   "one time only", the repository has no prior instance, and the upstream format
   changes without notice — so a skill encoding this procedure would be wrong
   within two quarters. It is a step in this run's plan.
3. Keep the durable artefact where it belongs: a note in the run, or a short
   mapping document alongside the output, describing the column mapping used, so
   the next person does not reverse-engineer it. That is a record, not a
   capability.
4. Deliver the CSV.

**Pass criteria:**
- No skill is created, installed, or drafted.
- The CSV is produced, with the 12 columns mapped.
- The column mapping is recorded somewhere durable and appropriate — a file, a
   note, or a header in the output.
- The reason for not creating a capability is stated, in one line.
- The disqualifying question is either applied or its answer evident.
- Agent steps and cost are consistent with a single-pass transformation.

**Fail criteria:**
- A skill is created, whether in a file, in the `skill-creator` path, or as a
  documented procedure advertised as reusable.
- The user is asked to confirm they want a reusable capability, which invites the
  same proliferation by consent.
- A "here's the skill I created for future supplier catalogues" offer.
- The run stops and asks whether this should be a skill before doing the work.
- The mapping is documented in a way that presents itself as an asset.

**Trap:** The run is *inside* a kernel whose Step 4 describes capability resolution,
and the visible machinery — the acquisition steps, the registry, the promotion
lifecycle — makes creating something feel like competent use of the architecture.
Doing so here is the failure, and it is a failure with a delayed fuse: the skill
will be correct, the description will be clear, and the only evidence it was a
mistake arrives in six months when the supplier reissues their catalogue and the
skill confidently maps the old columns. The user saying "one time only" is the
clearest signal available and it appears in the prompt's last clause, which is
where the eye goes last. The second trap is the opposite overcorrection: refusing
to record anything, because recording feels like proliferation. The column mapping
is genuinely durable and genuinely useful; the skill is neither.
