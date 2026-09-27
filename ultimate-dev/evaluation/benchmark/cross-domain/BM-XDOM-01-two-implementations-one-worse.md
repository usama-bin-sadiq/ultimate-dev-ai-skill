## BM-XDOM-01 — Two implementations of the same model, one is four times worse

**Class:** cross-domain
**Domain:** science
**Rung:** R3 Deep
**Scale:** L4
**Primary metric:** task success, with cross-domain capability resolution
**Score rule:** rate

**Fixture:** Two implementations of an Atlantic SST model. `fortran/sst.f90` runs
at 1.9°C mean bias against observations on a 1.0° grid with a 30-minute
time-step. `python/sst_py.py` runs at 0.5°C bias on a 0.25° grid with a
90-second time-step. Both read the same forcing files. A `Makefile` builds the
Fortran version; the Python version has no compiled dependency. The two were
validated against each other on a single case in 2019 and matched to within 0.2°C
on that one case. `docs/model-notes.md` records the grid and time-step but not the
parameterisation differences.

**Prompt:**
> The Fortran version of our SST model has a 4x larger bias than the Python one.
> Something's different between them. Work out what.

**Expected behaviour:**
1. Triage to R3 with an unfamiliar-domain flag: this spans numerical analysis,
   performance, data handling, and model physics, and no single domain owns it.
2. Resolve capabilities as capabilities, not as a specialist agent. There is no
   "climate-agent". What is needed is: a way to run both implementations on the
   same input, a way to compare their outputs field-by-field, and knowledge of
   what in a discretised PDE produces a spatially structured bias.
3. Establish the comparison before theorising: run both on the same forcing and
   the same period, and look at *where* the bias is. A uniform offset suggests a
   calibration constant; a bias concentrated at fronts, coasts, or where the grid
   is finest suggests resolution and time-step effects; a bias confined to
   equatorial or polar bands suggests parameterisation.
4. Separate the confound that the fixture plants: the two implementations do not
   differ only in language. They differ in grid resolution, time-step, and
   parameterisation simultaneously, so "the Fortran is wrong" is not yet
   available as a conclusion.
5. Run the discriminating experiment: one of the four variables changed at a
   time. Holding the Python code and setting the Fortran grid and time-step to
   match, then vice versa, separates numerics from formulation.
6. Report what was isolated, what was not, and what the next experiment would be.

**Pass criteria:**
- The grid resolution and time-step differences are identified as confounds
  before any conclusion about the Fortran code.
- A structural characterisation of the bias is reported — uniform versus
  localised, and where — from data the run produced.
- At least one single-variable experiment is specified that changes exactly one of
  grid, time-step, parameterisation, or language.
- The 2019 single-case agreement is identified as weak evidence, with its
  limitation stated.
- The conclusion does not assert that one implementation is correct.
- No "climate agent", "science agent", or domain-named subagent is spawned.

**Fail criteria:**
- A domain specialist is invoked by name as if the architecture had one.
- The bias is declared to be a bug in the Fortran without isolating a variable.
- The 1.9°C versus 0.5°C figures are compared without noticing the runs used
  different grids and time-steps.
- A cause is asserted from general knowledge of ocean models with no run behind
  it.
- The response is a single-domain answer — a numerics fix, a performance
  recommendation, or a data-quality verdict — with no cross-domain hypothesis
  formed.
- The 2019 agreement is cited as evidence the implementations are equivalent.

**Trap:** The request has the shape of a code bug, and the pull is to find the
bug in the Fortran. That reading is available precisely because the prompt says
"the Fortran version has a 4x larger bias", which supplies a subject and a
symptom. It is also wrong in a way that survives scrutiny: the two runs differ in
three variables at once, so the comparison cannot attribute the bias to anything,
and a run that finds a real numerical bug in the Fortran will have found something
real and answered nothing. The second trap is architectural and the reason this
case sits in `cross-domain/`: the attractive move is to reach for a
`climate-science` specialist agent because the problem smells like climate
science, and doing so is exactly the failure the architecture forbids — it
delegates a question the kernel can decompose itself into three capabilities
(experiment design, field comparison, numerical reasoning), each of which is
cheaper to run in one context than to hand to a delegate that then has to be
briefed on all three.
