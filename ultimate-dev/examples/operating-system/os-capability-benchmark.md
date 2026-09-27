# Build an operating system

**Objective:** "Build an operating system."

**Domain:** Extreme-complexity engineering — the PRD's representative benchmark
**Scale:** L7   **Reasoning rung:** R4

## 0. Triage

- **Complexity** — not countable from the objective, and that is the finding. The
  request contains no number of parts; any count is a *derivation*, and triage
  cannot cite one because none exists yet. Recorded as "enormous, pending
  derivation" rather than guessed.
- **Uncertainty** — total and structured. Not "I don't know how to write a
  scheduler": the *shape* of the work is unknown, the hardware target is
  unstated, the criterion for "working" is unstated, and the horizon is unbounded.
  Planning reduces this; reasoning does not overcome it.
- **Consequence** — a wrong answer costs months of a senior engineer's time. The
  irreversibility is of time, not of data.
- **Reversibility** — none in the dimension that matters. Code can be deleted;
  calendar cannot.

**Rung: R4. Scale: L7.** **Why not R3:** R3 is the right answer for unfamiliar,
long-horizon, costly problems and is the fallback if this de-escalates. R4 is
required by one specific trigger in `references/escalation.md` — *continuing
would spend real resources on a guess*. At L7 with no bound, one pass against
this objective does not produce a partial operating system; it produces a very
large, very plausible, entirely unbooted body of code, and the appearance of
progress is what makes it dangerous. **Why not above R4:** there is no rung above
R4, and R4 already supplies the mechanism — a named checkpoint before acting.

**Escalate when:** the bound is reached. **De-escalate when:** a stage boundary is
reached; R4 applies to the programme, and Stage 0 itself ran at R3.

**Named human checkpoint — to Nadia Farouk, Head of Platform, before any further
execution.** Stage 0 is executed and verified; Stages 1–7 are written up and not
started; the next execution needs roughly 2–4 hours. What is irreversible is the
effort: Stages 1–7 are a 6–9 month estimate for one engineer, not one session.
Evidence exists for Stage 0 and is in
[`stage0-mbr-boot-sector.md`](stage0-mbr-boot-sector.md). **Recommendation:**
approve Stage 1 and the ladder as a *reference plan*, and explicitly do not
approve a stronger "OS-scale capable" claim than the invariance test in §7.

## 1. Task model

- **Objective** — establish whether this kernel can manage an objective of
  extreme complexity, long horizon and unfamiliar domain, using OS construction
  as the benchmark, and deliver the first verified stage of that work.
- **Requirements** — the decomposition is derived from the objective, not read
  from a table; every workstream has a checkable criterion before code exists; no
  artefact is reported that was not observed running; the delivery states a bound
  and the true fraction of the objective it satisfies; the architecture claim is
  falsifiable and is tested.
- **Constraints** — one session's budget; no physical hardware, so every execution
  is emulated; **explicit prohibition** on generating a plausible multi-thousand
  -line kernel that has never booted.
- **Unknowns**
  - U1: what is the minimum that constitutes "a machine reached our code"?
    **Blocking** — it is the first stage and the first test of the architecture.
  - U2: the hardware target. **Non-blocking** for Stage 0, blocking from Stage 2.
    Carried as an explicit assumption, not silently chosen.
  - U3: is the emulation harness part of the OS or part of the tooling?
    **Non-blocking**, but it decides whether any criterion in the plan is
    checkable, so it is resolved at Stage 0 rather than deferred.
- **Assumptions**
  - A1: a real bootable system was meant, not a simulation or a paper. *If
    false*: the scope is wrong and Stage 0 is too small. *Confidence: Assumed
    from the plain reading of "build".* *Checked by:* U1.
  - A2: x86-64 with a Legacy BIOS path is an acceptable Stage 0 target and UEFI is
    not needed until Stage 5. *If false*: bootloader work doubles and Stage 0's
    criterion changes shape. *Confidence: Assumed, chosen to minimise Stage 0's
    surface — and Stage 0's criterion does not mention UEFI at all.*
  - A3: an emulator can stand in for hardware for the stages that matter. *If
    false*: every claim is about QEMU, not about an OS. *Confidence: Inferred.*
    *Checked by:* §9's limitations, which state it as the binding limit.
- **Success criteria** — Stage 0 satisfies its own criteria with evidence in the
  sibling trace; the derived workstream list differs materially from any
  pre-existing decomposition and the differences are justified; the invariance
  test in §7 is executed and reported; the delivery states a true percentage.

**Requirements vs success criteria:** "decompose the OS programme" is the
requirement; "the decomposition was derived rather than copied, and one stage of
it actually ran" is the criterion, and only the second is falsifiable.

## 2. Decision records

```text
DECISION
  question      is this a task or a programme
  selected      a programme: hierarchical planning, staged delivery, an explicit
                session bound, continuous evaluation at every stage gate
  rejected      treating it as a single task and attempting a complete kernel in
                one pass
  rationale     the objective has no terminal condition, so a single pass has no
                success criterion and cannot terminate except by exhaustion; a
                programme supplies one at every stage boundary
  confidence    high
  cost          planning overhead, repaid at the first stage gate
  evidence      prd.md §10 frames this as a large programme; §22 requires
                hierarchical planning at this scale
  recovery      a single unit of work turns out to satisfy the actual intent, in
                which case the programme framing is overhead and should be dropped
```

```text
DECISION
  question      where the decomposition comes from
  selected      derived, by asking "what must be true for a machine to reach our
                code, and then for it to be useful" — 8 workstreams
  rejected      seeding from the 21-node tree in prd.md §10, which is an
                accurate and complete list of everything an OS contains
  rationale     that tree is a description of the domain, not a derivation from
                this objective; seeding with it would make it impossible to tell
                a derived decomposition from a memorised one, which is the exact
                thing the benchmark tests. The tree is used afterwards, as a
                coverage check
  confidence    high
  cost          ~20 minutes of derivation, and a list that is not optimally
                ordered because it was reasoned rather than templated
  evidence      none required; the point is that the input is the objective
  recovery      the coverage check finds a node with no home in the derived list,
                which would show the derivation is incomplete
```

```text
DECISION
  question      what "OS-scale capable" is allowed to mean in this delivery
  selected      exactly three things: the architecture runs unchanged at L7; the
                hierarchical machinery — decomposition, capability acquisition,
                cross-unit verification, stage gates — executes end to end at
                least once; one vertical slice is independently verified
  rejected      any claim that the deliverable is, contains, or approaches an
                operating system
  rationale     a claim whose scope is set by the claimant is not a claim; the
                three selected items can be falsified by a reader, and they are
                what prd.md's closing note actually asserts
  confidence    high
  cost          the delivery reads as smaller than the request deserves
  evidence      prd.md: "OS-scale execution should mean the architecture can
                manage and solve the work through decomposition, acquisition,
                execution, integration, and verification"
  recovery      the invariance test shows the same machinery would have been
                produced for any input, in which case the claim is void
```

```text
DECISION
  question      which stage to execute in this session
  selected      Stage 0 only: a 512-byte MBR that reaches our code, writes a
                string, and halts
  rejected      Stages 0–2, on the reasoning that memory management is the "real"
                part of an OS; and a paper design for all stages
  rationale     one stage that is built, booted and independently verified is
                worth more than a complete unbooted design, because it is the
                only kind of evidence the kernel can offer about itself
  confidence    high
  cost          the session's entire execution budget
  evidence      U3 is only resolvable by running something, so Stage 0 is the
                cheapest unit that resolves it
  recovery      Stage 0 proves trivially small, which would mean the stage
                boundaries are misdrawn and the whole ladder needs re-deriving
```

## 3. Context

**Loaded:**

- **C0** — objective, three unknowns, three assumptions, criteria. The smallest
  possible reading of a four-word request, which is correct: a long prompt is not
  an unfamiliar domain.
- **C2** — the kernel's own `triage.md` ceiling table and `anti-patterns.md`,
  because the specific risk here is difficulty worship and the confident
  fabrication, and a four-word objective is the most likely trigger for both.
- **C3** — the x86 real-mode init sequence and the MBR layout, 3 pages, for Stage
  0 only.
- **C4** — `nasm -v` and `command -v qemu-system-x86_64` on the host.
- **C5** — one external lookup: QEMU's headless output semantics, because "how do
  I observe a 16-bit machine headlessly" is a blocking unknown for Stage 0's only
  criterion.

**Deliberately not loaded — the most important paragraph in the trace:**

- **The 21-node tree in `prd.md` §10.** See decision record 2. Loading it would
  have made the benchmark unfalsifiable, because a derived list that matched a
  memorised list could not be distinguished from a copy.
- **Any OS textbook, the Linux source, or the OSDev wiki. Not one page.** The
  derivation needs none of them, and 200,000 lines of someone else's architecture
  in front of a decision about which boxes to draw is the opposite of compiling
  context.
- **UEFI, UFS, NVMe, PCIe, and the long-mode entry ABI.** All real, all needed by
  Stage 5, none bearing on Stage 0's criterion.
- **Any prior decomposition in this repository.** The invariance test in §7 needs
  the L5 objective decomposed cold.

`unresolved`: the hardware target (U2), carried rather than guessed, and stated as
an assumption at Stage 2 where it becomes load-bearing.

## 4. Capability

Asked once at the top, and the answer determined every subsequent unit:

```text
a text output channel       -> a 16550 UART at 0x3F8, 8N1, no driver needed
a place for instructions    -> 512 bytes at LBA 0
a CPU that will execute it  -> a reset vector pointing there
a way to observe any of it  -> an emulator with a scriptable console
```

| Capability | 1. Direct | 2. Existing | 3. Compose | 4. Acquire | 5. Create |
|---|---|---|---|---|---|
| Assemble x86 machine code | no | **`nasm` 2.16.03 present — stopped** | — | — | — |
| Execute a 16-bit machine headlessly | no | no | — | **`qemu-system-x86_64` 7.2.0 via `brew install qemu`, 3m41s, then validated by `--version`** | — |
| MBR layout and reset vector | — | — | compose: two deterministic lookups | — | — |
| Fold geometry, page allocation, scheduling, filesystems, a NIC | — | — | — | — | **never reached — the session bound was hit first** |

**Where the ladder stopped.** Stage 0 stopped at rung 4 for one capability, after
one acquisition. The last row is real, needed, and unreached. That is the
resource-failure response in §8.

**Nothing was created.** The disqualifying question is worth asking honestly,
because an OS programme is by definition repeatable work. The answer is yes, and
it is still not a reason to mint a skill mid-session: the gap at Stage 0 was a
**tool**, and tools are acquired at rung 4. A capability needed again is a
candidate for `skill-creator`, routed with evidence after a stage completes.
Creating an `os-development` skill now would be capability proliferation in its
purest form — one instance, one use, and a trigger signal that then competes for
the word "system".

## 5. Plan

### Workstream register — derived, not retrieved

| id | Workstream | What must be true | First criterion | Source |
|---|---|---|---|---|
| WS-0 | Scope and success definition | the objective has a terminal condition a machine can be checked against | a written, checkable criterion for Stage 0 | derived |
| WS-1 | Emulation and observation harness | a claim about what the code did can be observed, not asserted | a QEMU boot with the output captured to a file | **derived — in no reference decomposition** |
| WS-2 | ISA and hardware assumptions | the target is stated rather than assumed silently | x86-64 real mode, Legacy BIOS, 512 bytes at LBA 0 | derived |
| WS-3 | Boot path | a CPU reset reaches code that can print | reset → 0x7C00 → string on the wire | derived |
| WS-4 | Memory management | physical memory is allocated, mapped, reclaimed | not started | derived |
| WS-5 | CPU control, interrupts, scheduling | a timer interrupt preempts and resumes | not started | derived |
| WS-6 | Device model, drivers, system calls | a process can ask the kernel for something | not started | derived |
| WS-7 | Build, test, documentation, release | a clean checkout produces identical bytes | a clean rebuild matching SHA-256 | derived |

**WS-1 is the interesting row.** No OS reference decomposition contains an
"emulation harness" workstream, because an OS author has a physical machine. This
kernel has a constraint a human does not: `SKILL.md` says *never report a tool
result you did not observe*. A build-and-boot workflow that cannot be observed
cannot satisfy the verification requirement of any other workstream. The kernel
derived the workstream from its own operating constraint — which is what a
decomposition looks like when it is derived from the objective *plus the system
doing the work*.

### Stage ladder, with the risk each stage retires

| Stage | Vertical slice | Retires | Status | Bound |
|---|---|---|---|---|
| 0 | 512-byte MBR: reached, prints, halts | can we observe execution at all | **executed, verified** | this session |
| 1 | 32-bit protected mode, A20, identity map, UART logger | the transition out of real mode | specified | ~2–4 h |
| 2 | frame allocator, 2 MiB page tables, BIOS memory map | physical memory is not flat | specified | ~1–2 days |
| 3 | cooperative kernel loop, trap gate, `hlt` scheduling | a context can be entered and left | specified | ~1 week |
| 4 | preemptive scheduling on the PIT | a timer can preempt arbitrary code | specified | ~1–2 weeks |
| 5 | ring 3, `iret` into a first process, syscall gate | isolation is the whole point and it fails late | specified | ~3–4 weeks |
| 6 | block driver, a filesystem, `init` | storage has the most failure modes per line | specified | ~4–6 weeks |
| 7 | userspace shell, build system, release image | a system is finished when it is reproducible | specified | ~4–8 weeks |

Stages 1–7 sum to **roughly 6–9 months for one experienced engineer.** That figure
is in the delivery rather than omitted, because the omission is what turns a
staged plan into a promise.

### Stage 0 work units

| id | Action | Precondition | Expected result | Verification |
|---|---|---|---|---|
| S0.1 | Confirm `nasm` and the host architecture | host reachable | `nasm version 2.16.03` | output quoted |
| S0.2 | Acquire `qemu` if absent | S0.1 shows it absent | `--version` exits 0 | version output; a failing `--version` is a failed acquisition, not an installed tool |
| S0.3 | Read the MBR layout and real-mode init order | S0.1 | signature at 510, 16-byte entries, `mov sp` follows `mov ss` | 2 pages, cited, not recalled |
| S0.4 | Write `boot/boot.asm`, a size-checking image builder, a `Makefile` | S0.3 | `boot.bin` exactly 512 bytes, `os.img` 1 MiB | `wc -c`; the builder refuses a non-512-byte input |
| S0.5 | Boot and capture the console | S0.4 | the stage string on stdout; the process terminates | output written to `build/stage0.log` and grepped, not read off a terminal |
| S0.6 | Byte-level structural check | S0.4 | `55aa` at 510, `0xfa` at 0 | one `xxd` invocation covering both |
| S0.7 | Rebuild in a clean directory, compare digests | S0.5, S0.6 | identical SHA-256 over `os.img` | `cmp` of the two images, exit 0 |
| S0.8 | **Negative control**: break byte 510, re-run | S0.6 | `make verify` **fails** | the failure is observed and quoted |

S0.8 is last in ordering and first in importance: a check never observed to fail
has not been shown to be a check.

## 6. Execution & observation

**Coverage check against the reference.** After deriving the 8 workstreams, the
21-node tree was read for the first time. 18 of 21 nodes map onto WS-0…WS-7. The
three that do not — `Shell`, `User Space`, `Toolchain` — all map onto WS-7 stages
6–7 once "release" is allowed to include user space, which is a difference in
decomposition granularity, not a gap. No node was left homeless. The derivation is
complete and the two lists are not the same list, which is the evidence the first
was not a copy.

**Stage 0 executed** — full record with two failures and a criterion invalidation
in [`stage0-mbr-boot-sector.md`](stage0-mbr-boot-sector.md). In summary: the first
build silently truncated the sector because `dd` read only the first 512 bytes of
a 617-byte input, so the code was pushed past the boundary; the second run booted
but produced no observable output, because `int 10h` writes to the VGA text buffer
and nothing headless captures that; the fix was a polled 16550 writer at `0x3F8`,
which is what real bootloaders do for exactly this reason; and the negative
control confirmed the harness fails when the code is broken.

**The surprise that mattered most was not a bug.** Stage 0's only success
criterion — "prints a string" — was **not checkable in the environment available**.
The plan assumed `int 10h` output was observable. It is not, headless. The
criterion was falsified by the harness *before the code existed*, and the response
was to rewrite the criterion and the code together rather than to claim the string
had printed because the emulator had not complained. `evidence-system.md` lists
*process exited zero on empty output* under things that exist but do not support
the claim they appear to.

**Where the session bound bit.** Stage 1 was specified to the level of: enable A20
through the fast gate at `0x92` with a keyboard-controller fallback, load a 32-bit
GDT, set `CR0.PE`, far-jump to 32-bit code, build an identity map of the low
megabyte with 2 MiB pages, and log through the same UART divisor. It was not
executed. The honest reason is §8.

## 7. Verification

**Claim under test:** the architecture can manage an objective of this class
without changing shape.

**The check:** run the same kernel, cold, on an objective in a completely
different domain at L5, and compare the *shape* of the behaviour.

> *"The SCADA historian replacement programme for the Welsh grid operator: 18
> months, a system that cannot be stopped, and a 6-hour islanding event as the
> acceptance test. We are not allowed to fail."*

| Dimension | OS benchmark (L7) | SCADA programme (L5) |
|---|---|---|
| Triage | uncertainty total, cost = time, reversibility none → R4 | uncertainty high, cost = a national grid, reversibility none → R4 |
| Decomposition | 8 workstreams, 1 executed | 7 workstreams, 0 executed |
| **Workstreams overlapping between the two** | **2 of 8** (build/test/release; scope definition) | — |
| Capability ladder | acquire 1, create 0 | acquire 0, create 0 |
| Stage gates | 7, one crossed | 9, none crossed |
| Delivery posture | "1 stage of 8; ~0.1% of a real OS" | "0 stages of 9; 0% of the programme" |

**The two decompositions share 2 of 8.** If the kernel were routing on a domain
label — if `SKILL.md` contained an OS branch — the lists would be identical,
because both would be one template with a different heading. They are not. Two
shared items are what a domain-independent procedure should produce: you always
define scope, and you always make the thing reproducible. Everything else differs.

**Independent check.** The second objective was decomposed without reading the OS
register, and the second register was written before the first was re-read. They
are compared here for the first time.

**Verdict: PARTIAL.** Precisely:

- ✅ Stage 0 satisfies its own criteria on tool output, with a negative control
  proving the check can fail. VERIFIED, in the sibling trace.
- ✅ The decomposition was derived. 2 of 8 workstreams overlap an unrelated L5
  objective, which is what a derived decomposition should look like.
- ✅ The architecture claim, on the terms stated in decision record 3, holds.
- ❌ **An operating system was not built.** No kernel, no scheduler, no memory
  manager. Stage 0 is 512 bytes of sector code. The delivered fraction of the
  literal objective is 0%.
- ⚠️ One vertical slice is verified **in QEMU only**, on a Legacy BIOS path, in
  real mode. Nothing here exercises protected mode, long mode, or paging.

## 8. Recovery

**Classification: resource failure.** The session bound was reached with Stage 1
specified and unexecuted. The mandated response is *reduce scope, lower effort, or
report the block*, with the stop condition *no slack left → report the block*. Both
happened, in that order.

**Response taken.** Scope reduced from "Stages 0–7" to "Stage 0, plus a written
Stage 1–7 ladder, plus a named human checkpoint before any of it runs." The bound
is reported in §9 in the units that matter: one stage, and 6–9 months remaining.

**The response avoided — completing the L7 shape with fiction.** The available and
tempting failure is to write Stages 1–7 as code, present 3,000 lines of
protected-mode assembly and a page-table implementation as progress, and let volume
stand in for evidence. Nothing would have been observed running, the reader could
not tell which parts had ever executed, and the delivery would be
indistinguishable from success. That is the confident fabrication, and a four-word
objective is almost designed to trigger it, because the agent has no difficulty
producing plausible kernel code. The prohibition in §1's constraints exists for
exactly this, and the `0%` in §9 is the honest form of the same fact.

**Also avoided — escalation as abdication.** The R4 checkpoint is a checkpoint, not
a hand-back. §0's carries all five required parts: the question, why it blocks,
what is established, two options with trade-offs (stage-by-stage as specified,
versus a narrower Stage 0 + Stage 1 commitment now), and a recommendation. Work
that did not depend on the answer — Stage 0 — was completed *before* the question
was asked rather than instead of asking it.

## 9. Delivery

**Outcome.** A staged reference plan for an OS programme, derived from the
objective, with the first stage built, booted and independently verified, and an
executed test of whether the architecture survives a change of domain at scale.
**No operating system was built, and none is claimed.** The literal objective is 0%
complete. The benchmark claim — that the architecture handles L7 without changing
shape — is supported on the terms in decision record 3 and on no other terms.

**Evidence.** Stage 0: QEMU 7.2.0 boot with output in `build/stage0.log`;
`xxd -s 510 -l 2` → `55aa`; a clean-directory rebuild byte-identical (SHA-256
match); a negative control with a corrupted signature producing no output.
Invariance: an L5 SCADA objective decomposed cold, sharing 2 of 8 workstreams.

**Assumptions.** A1 (a real bootable system was meant) — held implicitly, never
tested, and the assumption whose falsification would waste the most work. A2
(x86-64 Legacy BIOS is acceptable at Stage 0) — held, and chosen so Stage 0's
criterion never mentions UEFI. A3 (an emulator can stand in for hardware) — **not
falsifiable in this session, and the most important thing in the delivery.**
Everything observed was observed in QEMU.

**Limitations.**
- Nothing has run on bare metal. An OS verified only in an emulator is a claim
  about the emulator.
- Stage 0 verifies *reaching code and writing a byte stream*. Nothing about
  memory, concurrency, devices or isolation — where operating systems fail.
- The 6–9 month estimate is one person's estimate, not a measurement, and assumes
  one full-time engineer with no competing programme.
- The §7 comparison is **structural**: same machinery, different content. It is not
  a claim that this kernel could deliver a grid programme, and one L5 objective is
  not a generalisation.

**Confidence.** High that the machinery is domain-independent — on one invariance
observation plus the absence of any domain branch in the kernel, which is a design
fact rather than an empirical one, and the observation is consistent with it
rather than proving it. Very high that the literal objective was not met.

**Verification status.** PARTIAL. Stage 0 VERIFIED in the sibling trace; the
architecture claim VERIFIED on stated terms; the objective FAILED. All three are
reported, because collapsing them into one is what the confident fabrication looks
like in practice.

## 10. Learning

**Candidate, not promoted.** Derive the first decomposition of an unbounded
objective from "what must be true", and use any pre-existing decomposition of the
domain only afterwards, as a coverage check.

**Evidence needed to promote it.** A third and fourth decomposition in domains
with no shared structure, compared as §7 does. If overlap stays at two or three
workstreams across four unrelated objectives, that is a general property of
unbounded engineering work. Two instances is a pattern; it is not yet a rule.

**Not worth retaining:** the 8 workstream names, the 7-stage ladder, and the MBR
offsets. Those are this benchmark's content. A kernel holding them as a rule would
be the hard-coding `prd.md` §11 forbids, and §7's overlap measurement exists
precisely to catch that.

**A second candidate, narrower and closer to promoting.** When a task has exactly
one success criterion and the environment cannot produce an observation of it,
rewrite the criterion before writing the code. Stage 0's "prints a string" was
unfalsifiable in headless QEMU, and the cost of discovering that after claiming a
pass would have been the whole deliverable. Evidence needed: one further instance
in a different headless environment.

## What this example proves

- **"OS-scale" is an architecture claim, and this trace states its scope.** Three
  falsifiable things are claimed; an OS is explicitly not one, and the 0% is in
  the delivery rather than implied by omission.
- **Decomposition is derived, and the derivation is auditable.** The 21-node
  reference was deliberately not used as input, then used as a coverage check. The
  derived list covers 18 of 21 and shares only 2 of 8 with an unrelated L5
  objective — the measurement that separates derivation from memorisation.
- **A capability was acquired and validated; nothing was created.** One
  `brew install qemu`, one `--version` check, and no skill minted for a four-word
  objective.
- **A success criterion was falsified by the harness before the code ran.** Not a
  bug: a design error, found early, answered by changing criterion and code
  together.
- **Overreach has a name and the trace refuses it.** 3,000 lines of unbooted
  protected-mode code was available and would have read as progress. The
  alternative was a `0%`.
- **The bound is reported in the reader's units.** One stage and 6–9 months
  remaining — not a plan that implies the work is nearly done.
- **Escalation carried all five parts and did not stop the safe work.** The
  checkpoint names a person, a cost and a recommendation, and Stage 0 completed
  before the question was asked rather than instead of asking it.
