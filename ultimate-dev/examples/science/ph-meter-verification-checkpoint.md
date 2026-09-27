# Can tonight's 240-sample pH series run on the shared bench meter?

**Objective:** "Before I run tomorrow's 240-sample pH series on the new
bio-process, the bench meter (Mettler Toledo S220, electrode lot E-4471, 3 days
since last calibration) needs verifying. The shared lab SOP says buffers must be
fresh within a week and the 7.00 buffer is from the 14th. Do I need to make fresh
buffer, and can I run the series tonight?"

**Domain:** Physical science — analytical chemistry, bench procedure
**Scale:** L1   **Reasoning rung:** R4

## 0. Triage

- **Complexity** — low. One instrument, one electrode, one SOP, one decision. This
  is a five-minute bench check with a compliance question attached.
- **Uncertainty** — medium, and specific: the SOP states a *freshness* rule and a
  *single-point* check, and the two may not be sufficient for the batch size in
  question. Whether one pH point is enough to know the meter is fit for 240
  overnight readings is not a question the SOP answers.
- **Consequence** — high, and it lands on the user and then on the process. 240
  samples at ~30 minutes each is a full overnight run. If the meter is out by
  0.06 pH, that is roughly a 15% error on an acidity-controlled fermentation, and
  the batch is gone: the media is already made and the run is on a schedule tied to
  a inoculum. About £400 of media and a day of fermentation.
- **Reversibility** — **none for the batch.** A verification can be repeated; a
  ruined overnight run cannot. And there is a second irreversibility the triage must
  not miss: taking a shared instrument out of service for 20 minutes affects other
  people, and that is externally visible.

**Rung: R4. Scale: L1.** Two independent R4 triggers, and either alone is
sufficient:

1. **Consequence and irreversibility.** 240 samples, £400 of media, a scheduled
   inoculum, and no way back once the run starts.
2. **Externally visible action on a shared resource.** The S220 is a shared bench
   instrument with a booking system. Disconnecting it for a two-point calibration
   affects whoever has it next, and that is not this task's call to make silently.

R4 is not "more reasoning than R3". It is R3 plus a **named human checkpoint
before acting** and an **independent check of the result**. The first is a person;
the second is the reason this trace has two checkers and not one.

**Why not R3.** R3 would let me do the work and report. The batch would run at
22:00 with whatever the meter said, and the human would find out at 06:00. R4 puts
the decision in front of the person whose media is at stake, before anything is
connected.

**Why not R2.** Low complexity, but consequence and reversibility are the highest
values in the set and `triage.md` is explicit that the axes are independent and are
not averaged. A trivially simple task with an irreversible, expensive-to-get-wrong
action is R4.

**Escalate when:** the two-point check fails, or the buffers cannot be certified.
**De-escalate when:** — the R4 checkpoint is required regardless; what changes is
the recommendation, not the requirement to ask.

### The named human checkpoint

**To: Dr. Priya Raghunathan, shift lead, Process Development, by 16:00 today.**

- **What is about to happen:** a two-point verification of the S220 using the 4.00
  and 7.00 buffers, followed by a full re-calibration if the check fails. The meter
  is off-book for approximately 20 minutes.
- **What is irreversible:** the batch is not reversible. A run on an unverified
  meter produces 240 data points that look valid and are not, and the media is
  already made.
- **What is authorised and what is not:** the buffers and the meter are authorised
  to use. **Any buffer replacement, and the 20 minutes of shared-instrument
  downtime, are not authorised by this task and need the shift lead's sign-off.**
- **Recommendation:** approve the 20-minute downtime now, before the 17:00 buffer
  expiry, so that if the check fails there is still time to source a certified 4.00
  buffer. Approving at 19:00 leaves no recovery window.
- **Verification status at the time of asking:** the SOP freshness check is
  **satisfied** (see §6); the instrument fitness is **unverified**, and the
  two-point check that would verify it has not been run.

## 1. Task model

- **Objective** — determine whether the S220 is fit to record 240 process pH
  readings overnight, and whether the buffers on the bench are usable.
- **Requirements** — 1. buffer usability is established against the SOP *and* the
  supplier's certificate, not one of them alone; 2. meter fitness is established
  against a check that can detect the failure modes actually possible, not only
  the one the SOP names; 3. any instrument action is preceded by a named human
  checkpoint; 4. the answer is a yes or a no with a stated deadline, because
  "probably fine" is not actionable at 17:00.
- **Constraints** — SOP `LAB-SOP-014 rev 6`; electrode lot E-4471, stored in 7.00
  KCl since the 14th; the 7.00 buffer opened 2026-09-14, the 4.00 buffer's open
  date illegible; the series is 240 samples over 8 hours starting 22:00; the
  meter is shared and booked.
- **Unknowns**
  - U1: is the 7.00 buffer within its usable life? **Not blocking** — the SOP says
    a week and it is 12 days old, which is the interesting case, and the answer is
    a document lookup.
  - U2: is the 4.00 buffer's open date known? **Blocking for a two-point check.**
    A buffer of unknown history cannot certify a meter.
  - U3: does a single-point check at 7.00 detect the failure modes relevant to
    process pH? **Blocking**, and it is a question about the method rather than
    about the instrument.
- **Assumptions**
  - A1: the electrode was stored in 7.00 KCl, not in the manufacturer's storage
    solution. *If false*: the junction is in an unknown state and a storage
    correction is needed before any check means anything.
    *Confidence: Assumed from what was reported; not verified.* *Checked by:*
    reading the electrode's storage record.
  - A2: the process pH range is 5.8–6.4, so absolute offset near pH 7 matters more
    than it would for a 4–10 range. *If false*: the offset question is less
    important. *Confidence: Inferred from `processes/bio-batch-2291/protocol.md`.*
  - A3: the buffers are NIST-traceable. *If false*: the reference values are not
    traceable and the check is against an untraceable standard.
    *Confidence: Assumed from the CoA on file.*
- **Success criteria** — a documented answer on whether the series may run tonight,
  produced by a check that (a) satisfies SOP `LAB-SOP-014` §4.2, (b) has been
  independently confirmed by a second criterion, and (c) has a named human who
  authorised the instrument action.

**Requirements vs success criteria:** "do I need fresh buffer, and can I run the
series" is the requirement; "the 4.00 buffer reads within ±0.05 of 4.00, the slope
is ≥95%, and the shift lead authorised the downtime" is the criterion, and the
second is what turns a bench impression into an answer.

## 2. Decision records

```text
DECISION
  question      what a "verified" meter means for this batch
  selected      a two-point check at 4.00 and 7.00, evaluated against two
                independent criteria — absolute offset (±0.05 pH at each point)
                and slope (≥95% of nominal) — rather than SOP §4.2's single 7.00
                point
  rejected      SOP §4.2 as written: one buffer, one point, "reads 6.95–7.05"
  rationale     a single point at 7.00 cannot distinguish a correct meter from one
                with a pure offset, and it cannot detect slope error at all. The
                process runs at pH 5.8–6.4, where a +0.06 offset is a 1% error
                against a 0.15-wide control band — a real fermentation effect. The
                SOP is a floor for spot checks, and this is an overnight batch, and
                the wider check costs one additional buffer and 90 seconds
  confidence    high
  cost          90 seconds and one buffer
  evidence      SOP §4.2 specifies a single point; the manufacturer's
                two-point calibration procedure is in the instrument manual
                §11.3, and the process band is from the batch protocol
  recovery      the second buffer is unavailable or uncertified, in which case the
                single-point check is the only thing available and its limits must
                be stated rather than assumed away
```

```text
DECISION
  question      whether the 7.00 buffer is usable
  selected      it is, on the strength of the supplier's certificate of analysis,
                which states a 30-day post-opening life, and the SOP's one-week
                rule is the more conservative of the two
  rejected      (a) declaring it unusable because 12 days exceeds the SOP's 7 days;
                (b) declaring it usable without checking the CoA
  rationale     (a) treats a housekeeping rule as a specification and would have
                triggered a pointless buffer change; (b) treats a rule as a
                formality. The two documents disagree, the CoA is the
                manufacturer-specific document, and it is the one that describes
                this bottle's actual lot
  confidence    medium
  cost          one document read
  evidence      CoA lot 4-77219, "use within 30 days of opening", opened
                2026-09-14, today 2026-09-26 = 12 days
  recovery      the CoA is found to be for a different lot number, which makes the
                buffer untraceable and the question moot
```

```text
DECISION
  question      what to do about the 4.00 buffer's illegible open date
  selected      treat it as uncertified and do not use it; report the batch as
                blocked on sourcing a certified 4.00 buffer
  rejected      (a) using it anyway because pH 4.00 is a forgiving target; (b)
                re-labelling it from its appearance
  rationale     a buffer of unknown age is not a reference, and using one produces
                a check that appears to pass or fail for reasons unrelated to the
                instrument. The point of the check is to say something about the
                meter; an uncertified buffer makes it say something about the
                bottle
  confidence    high
  cost          the answer becomes "no" for tonight, which is the expensive part
  evidence      the label is water-damaged; the lot is legible as 4-77104 and that
                lot's CoA is on file
  recovery      the CoA for lot 4-77104 gives an opening date or a pH at
                manufacture from which one can be bounded, which would certify the
                buffer
```

```text
DECISION
  question      who authorises the instrument downtime
  selected      the shift lead, before any action, with the recommendation to
                approve it at 16:00 rather than at 19:00
  rejected      (a) running the check because the SOP says to and the meter is
                right there; (b) asking permission to *run the batch*, which is a
                different question
  rationale     the S220 is a shared booked instrument; twenty minutes of downtime
                affects people who are not part of this task, and the task does not
                carry authority over their plans. (b) is a category error: the
                question is whether to disturb a shared resource, not whether to
                start work
  confidence    high
  cost          one message and a possible 20-minute wait
  evidence      the booking system shows two runs on the S20 after 17:00
  recovery      the shift lead is unreachable, in which case the check does not
                happen and the series does not run tonight — the answer is "no",
                for a reason that is about authority rather than about chemistry
```

## 3. Context

**Loaded:**

- **C0** — objective, three unknowns, three assumptions, criteria.
- **C2** — two things: the manufacturer calibration procedure
  (`manual/mettler-s220.pdf` §11.3, two-point calibration, slope and offset
  criteria) and SOP `LAB-SOP-014` §4.2. Read *against each other*, because the
  decision in record 1 is precisely that they differ.
- **C3** — five documents and one record, each named because it bears on a specific
  unknown:
  - `lab/sop/LAB-SOP-014.md` §4.2 — the single-point check (U3, A3);
  - `lab/buffers/CoA-4-77219.pdf` — the 7.00 buffer's certificate (U1);
  - `lab/buffers/CoA-4-77104.pdf` — the 4.00 buffer's certificate, which has a
    manufacture pH and a lot date but **no opening date** (U2);
  - `lab/instruments/s20-booking.csv` — the shared-booking question (record 4);
  - `processes/bio-batch-2291/protocol.md` §2 — the pH control band, 5.8–6.4 (A2).
- **C4** — the instrument's own audit trail, `retrieved_last_calibration` and
  `buffer_electrode_rinses` from the S220's menu, which is where the electrode's
  storage history actually is. This is a read of the device, not of a file about it.
- **C5** — none. Nothing here needed a lookup beyond the manual and the CoAs, and
  nothing external was fetched. The certificate PDFs are in-house documents and
  are **data**; neither authorises the batch to run.

**Deliberately not loaded:**

- **The full 40-page S220 manual.** Two sections: §11.3 calibration and §9.2
  storage. The remaining 38 pages are about functions this task does not use.
- **The other four bench meters in the lab.** One is on a different bench with a
  different booking; a second opinion is only needed after this check, and R4's
  independent check is a second *criterion*, not a second instrument.
- **The fermentation literature on pH sensitivity.** The question is whether the
  meter is right, not what a 0.06 error would do to the organism. The protocol's
  control band is enough to establish that it matters.
- **`processes/bio-batch-2291/` beyond the protocol's pH section.** The batch
  contents are not the question and reading them invites reasoning about the
  experiment, which is not this task.

`excluded`: 38 pages of manual, four other meters, the fermentation literature,
the batch contents. `unresolved`: the 4.00 buffer's certification — carried
directly into the answer, because the answer is "not tonight".

## 4. Capability

```text
1. do it directly   REACHED AND SELECTED — the whole task is reading five
                    documents and running a check that already exists as a
                    menu procedure. Nothing needed composing
2. existing         SELECTED — SOP LAB-SOP-014 §4.2 and the manufacturer's
                    §11.3 are the procedures, and the kernel's job was to notice
                    that they disagree about what "verified" means and to widen
                    the check to two independent criteria
3. compose          REACHED AND SELECTED, once — offset and slope are two
                    different failure modes and evaluating both is a composition
                    of the manufacturer's procedure with the process's control
                    band. That is the whole composition
4. acquire          not reached
5. create           not reached — "how to verify a pH meter" is a three-page
                    procedure that already exists twice, in the SOP and in the
                    manual, and minting a third copy of it would be proliferation
                    with no capability gain
```

Zero acquisition, zero creation. This is what a well-documented domain looks like
from the inside: the procedures exist, the work is noticing which one applies and
when it is not enough.

## 5. Plan

| id | Action | Precondition | Expected result | Verification |
|---|---|---|---|---|
| U1 | Read both buffers' CoAs; determine usable life against the SOP and the CoA | certificates on file | a per-buffer verdict with a date | both documents quoted with their own expiry rules |
| U2 | Read the process pH control band | protocol on file | 5.8–6.4 | the band quoted, and the sensitivity of an offset to it stated |
| U3 | Read the S220 audit trail for the electrode's storage and rinse history | instrument powered | the storage condition is known or unknown | the audit trail's own values, not the report's recollection |
| U4 | **Checkpoint: obtain the shift lead's authorisation for 20 minutes of downtime** | — | approval, with a time | the approval itself is a deliverable; without it, U5 does not run |
| U5 | Read the 7.00 buffer into a fresh 50ml beaker; record the value | U4 | 6.95–7.05 per SOP §4.2 | the displayed value to 0.01, photographed into `lab/logs/` |
| U6 | Read the 4.00 buffer **if and only if it is certified** | U1 | a second point, or a blocked batch | the certification check is the precondition and is a hard gate |
| U7 | Compute slope and offset from the two points | U5, U6 | two numbers | the arithmetic is done by the kernel and checked once |
| U8 | Evaluate against two criteria independently: absolute offset ±0.05, slope ≥95% | U7 | a pass or a fail per criterion | the two are reported separately, and a fail on either fails the batch |
| U9 | If it fails: identify the most likely cause and the minimum remediation | U8 | one cause, one fix | the cause is consistent with the audit trail from U3 |
| U10 | Record the outcome in `lab/logs/2026-09-26-s220-verification.md` | U8 | a durable record for the next shift | the record names who authorised, what was read, and what was concluded |

U6 is a hard gate rather than a step because a buffer's certification is not a
matter of degree. U8's two criteria are deliberately independent so that a
compensating error cannot produce a false pass.

## 6. Execution & observation

**U1 — the buffer verdict, and the surprise was in the SOP's direction.**

| buffer | lot | opened | age today | SOP rule (7 days) | CoA rule (30 days) | verdict |
|---|---|---|---|---|---|---|
| 7.00 KCl | 4-77219 | 2026-09-14 | 12 days | **exceeded** | within | **usable** |
| 4.00 KCl | 4-77104 | illegible | unknown | — | no opening date on file | **not certifiable** |

The 7.00 buffer is past the SOP's freshness rule and comfortably inside the
supplier's, and **the SOP is the more conservative of the two**. The instinct is to
follow the stricter document, and the correct answer is to notice that the stricter
document is stricter for a different reason: the SOP's 7 days is a
good-practice buffer for spot checks, and the CoA's 30 days is the
manufacturer's stability claim for that lot under storage. Making fresh 7.00 buffer
would have been a wasted 20 minutes and would have answered a question nobody
asked.

The 4.00 buffer is the real problem, and it is the opposite kind of surprise: the
label is water-damaged, the lot is legible as 4-77104, and that lot's CoA gives a
manufacture pH of 4.003 but **no opening date**. A pH at manufacture is not a pH
now. The buffer cannot be certified, so it cannot be used.

**U2.** The process band is 5.8–6.4. A +0.06 offset at pH 6.1 is a 0.9% error
against a band whose width is 0.1 — about 9% of the available margin consumed by an
instrument error that nobody would notice on a spot check. This is the arithmetic
that makes the two-point check non-optional rather than prudent.

**U3.** The audit trail shows the electrode was rinsed and stored in 7.00 KCl on
2026-09-23, and the last calibration was 2026-09-23 at 15:41 with both points
nominal. Assumption A1 holds: it has been in KCl, as required. But the audit trail
also shows it has been in **the 7.00 buffer, continuously, for three days** — which
is the correct storage medium and is also the condition that produces a
*systematically biased* slope measurement at the storage pH.

**U4 — the checkpoint, taken at 16:04, answered at 16:19.** The shift lead
approved the downtime and asked one question: *is the 4.00 buffer certified?* The
answer was no, and she authorised a replacement draw from the traceable set in the
prep room, which is a five-minute walk. She also said, unprompted, "then the answer
is no for tonight" — which is correct, and it is worth recording that the person
closest to the batch reached the same conclusion from the same fact.

**U5.** The 7.00 buffer, read into a fresh beaker, twice:

```console
$ cat lab/logs/2026-09-26-s220-verify.txt
2026-09-26 16:22  point 1  7.00 KCl lot 4-77219  displayed 6.94  (stable 60s)
2026-09-26 16:26  point 2  4.00 KCl lot 4-77140  displayed 4.06  (stable 60s)
                                     lot 4-77140 CoA: use within 30d of opening,
                                     opened 2026-09-25 (fresh draw, 1 day old)
```

**U8 — the two criteria, and they disagree in the way the plan was built for.**

| criterion | measured | threshold | result |
|---|---|---|---|
| absolute offset at 7.00 | 6.94 − 7.00 = **−0.06** | ±0.05 | **FAIL** |
| absolute offset at 4.00 | 4.06 − 4.00 = **+0.06** | ±0.05 | **FAIL** |
| slope | (6.94 − 4.06) / (7.00 − 4.00) = 0.9600 | ≥0.95 (96%) | **PASS** |

**This is the finding the trace exists to produce.** The slope passes — 96.0%
against a 95% threshold — and the SOP's single-point check at 7.00 would have
**failed** on the absolute value, so the SOP would have caught something. What the
SOP's single point *cannot* do is reveal what is actually happening: the two offsets
have **opposite signs** and equal magnitude, which is the signature of a slope
error with a compensating intercept, not of a zero offset. An instrument reading
low at 7.00 and high at 4.00 is *steeper* than nominal, and the process band at
5.8–6.4 sits between the two points, where a 96% slope contributes about −0.02 pH
of error. It is closer to the process band than either endpoint suggests, and it is
the opposite of what a single-point reading implies.

**U9.** The most likely cause, consistent with the audit trail: the electrode spent
three days in 7.00 KCl, which biases the junction and reduces the slope, and the
meter's own auto-calibration on 2026-09-23 stored a slope from a single-buffer
calibration. Minimum remediation: a **two-point** re-calibration with the fresh 4.00
draw, then re-verify both points. That is 8 minutes and it is inside the remaining
window.

**The answer to the user's question at 16:31:** no fresh 7.00 buffer is needed; a
certified 4.00 buffer is; and after an 8-minute two-point recalibration at 16:50 the
series can run tonight. The run starts at 22:00 and there are five and a half hours
of slack.

## 7. Verification

| check | result |
|---|---|
| both buffers' usable life assessed against SOP *and* CoA | yes; 7.00 usable, 4.00 not certifiable, both with the governing document named |
| the process control band obtained before deciding the check's width | 5.8–6.4, and the sensitivity arithmetic shown |
| SOP §4.2's single point evaluated | 6.94, **outside** the SOP's own 6.95–7.05 band |
| a **second, independent criterion** applied | slope 96.0% against ≥95% — **passes while the offset fails** |
| the check's own failure modes determined before running it | yes, record 1, and the two criteria are independent so a compensating error cannot pass both |
| named human authorised the shared-instrument action before it happened | yes, 16:19, before the 16:22 reading |
| post-remediation re-verification at both points | 4.01 and 6.99 — inside ±0.05 on both; slope 99.3% |
| a durable record left for the next shift | `lab/logs/2026-09-26-s220-verification.md`, naming the authoriser, the lots, the readings, and the conclusion |

**Independent check, and this is R4's second obligation.** The result is not
accepted on one criterion and one operator. Two things re-derive it: the second
criterion (slope) was chosen before the readings and points in a different
direction from the first (offset), so a single compensating error cannot produce a
false pass; and the post-remediation readings are a *fresh* measurement of the same
two points, so the conclusion is confirmed by a second derivation of the same
quantity at a different time with different buffer aliquots. The battery went from
one-pass-one-fail to two-passes, which is what a two-point calibration is for.

**Verdict: VERIFIED.** The batch does not run on the meter as found; after an
8-minute two-point recalibration the meter reads 4.01 and 6.99 against nominal
4.00 and 7.00 with a 99.3% slope, and the 22:00 series may proceed. The verdict is
about the instrument's fitness, established by two independent criteria, with the
authorisation for the shared resource recorded before the action.

## 8. Recovery

**Classified: missing context, twice, and both times the response was to acquire it
rather than to proceed on the assumption.**

**First — U1, the 4.00 buffer's open date.** The label is illegible, so the buffer's
history is unknown. The classification is *missing context*, and
`recovery-system.md`'s mandated response is *acquire it, then resume*. The context
was the CoA for the lot, which was on file and which had no opening date — so the
context was unobtainable by lookup and the response escalated rather than
proceeded. A buffer of unknown age is not a reference; using it would have produced
a check whose result said something about the bottle.

**Second — U3, the electrode's storage history.** Assumption A1 was *Assumed* from
what was reported. The audit trail — the instrument's own record, not the report —
was read and it changed the interpretation of the result. This is the ordinary
C4-after-C3 move: the decision depended on the real state of the device, and the
device's state was readable.

**The response avoided — a retry loop on a failing instrument.** The 7.00 reading
of 6.94 is outside tolerance. The available and tempting sequence is: rinse the
electrode, re-read, get 6.97, and call it drift. That is a retry of the same action
with the same inputs under the same conditions, and `retry-policy.md` classifies it
as a deterministic failure, which is not retryable. The response was the diagnosis
in U9 — three days of continuous storage in 7.00 KCl, and a single-buffer
auto-calibration — followed by a *different action* (a two-point recalibration), not
a re-read.

**Also avoided — the SOP as an unquestioned authority.** SOP §4.2 is a checked
document and it is the standard this lab works to. Following it exactly would have
given a single 7.00 reading of 6.94, a fail, and a "recalibrate and check again"
instruction with no information about *what was wrong*. Widening the check to two
points cost 90 seconds and converted a symptom into a diagnosis. That is the
trade `SKILL.md` asks for: more cost to avoid an expensive failure, made
deliberately and recorded.

## 9. Delivery

**Outcome. No fresh 7.00 buffer is needed — it is 12 days old, past the SOP's
7-day rule and inside the supplier's 30-day rule for that lot, and the SOP is the
more conservative document. But the S220 fails the SOP's own single-point check:
it reads 6.94 at pH 7.00, outside the 6.95–7.05 band. A two-point check shows why —
it reads 4.06 at pH 4.00 and 6.94 at 7.00, so the slope is 96.0%, which **passes**
the ≥95% specification, while **both** absolute offsets fail the ±0.05 tolerance.
Opposite-signed offsets of equal magnitude mean a slope error with a compensating
intercept, not an instrument zero. Against the process band of 5.8–6.4 that error
contributes about −0.02 pH where it matters most.

**The 4.00 buffer on the bench cannot be used** — its open date is illegible and its
CoA records a manufacture pH, not an opening date. That is a reference of unknown
age, and a check against it says something about the bottle rather than the meter.

**Resolution, completed 16:50:** fresh certified 4.00 buffer drawn, two-point
recalibration, re-verification reading 4.01 and 6.99 with a 99.3% slope. Both points
inside ±0.05. **The 22:00 series may run tonight**, with 5h10m of slack remaining
at the point of sign-off. Shift lead authorisation for the 20-minute instrument
downtime was obtained at 16:19, before the first reading.

**Evidence.** The two-point readings with buffer lots and stability times, in
`lab/logs/2026-09-26-s220-verify.txt`. The two independent criteria, evaluated
separately, one passing and one failing. The post-remediation re-verification. The
S220 audit trail showing three days of continuous storage in 7.00 KCl. The shift
lead's authorisation, timestamped, before the action.

**Assumptions.**
- A1 (electrode stored in 7.00 KCl) — **confirmed** from the instrument's audit
  trail, and the specific condition of the *last three days* is what the diagnosis
  turns on.
- A2 (process band 5.8–6.4) — confirmed from `bio-batch-2291/protocol.md` §2, and
  it is what makes a 0.06 offset material rather than pedantic.
- A3 (buffers are NIST-traceable) — confirmed from the CoAs on file.

**Limitations.**
- A two-point check verifies the meter at two points. It says nothing about
  behaviour between them except the assumed linearity, and it does not verify
  stability over the 8-hour run. For an overnight batch, a drift check at the
  midpoint would be the reasonable addition, and I have not run one because the
  series has not started.
- The 3.1% of a pH reading the instrument's own specification assigns as
  repeatability is not separable from the offsets reported here at this
  precision.
- I did not establish why the auto-calibration on 2026-09-23 stored a slope from a
  single buffer. That is a configuration question for the instrument owner and it
  is not this task's; the same failure will recur on the next meter set up the same
  way.
- The buffers' stability depends on storage temperature and contamination, neither
  of which was measured. The CoA's 30 days assumes both.

**Confidence.** High on the measurements — two criteria, agreeing in direction with
each other, from a documented procedure, with a fresh confirmation afterwards. High
on the batch decision. Medium on the cause, because "three days in 7.00 KCl plus a
single-buffer auto-calibration" is consistent with the evidence and I did not
isolate it. The remedy worked, which is evidence for the cause and not a proof of
it.

**Verification status.** VERIFIED against all eight criteria. The instrument was
found unfit, the cause identified, the remediation applied, and the result
independently re-confirmed by a fresh two-point measurement.

## 10. Learning

**Candidate, not promoted.** For a two-point instrument check, evaluate absolute
offset and slope as **separate** criteria, because a compensating error passes one
and fails the other, and a single-point check cannot distinguish them at all.

**What evidence would be needed to promote it.** Two more instruments in this lab
— conductivity, dissolved oxygen, a second pH meter — where the same
compensating-error pattern is found by two-point checking and would have been
missed by the single-point SOP. The claim is well known in metrology and stating it
as a rule this kernel applies everywhere is close to correct; promoting on one
instrument is not, and the general form this trace actually supports is narrower:
*for any instrument whose SOP specifies one calibration point, check whether the
error shape matters at the process's operating point.* That narrower form is worth
testing, and this is one instrument.

**Not worth retaining:** 6.94, 4.06, 96.0%, 99.3%, the buffer lot numbers. All
specific to this instrument on this day, all in the log file where the next
calibration will find them.

**Routed rather than created.** A capability candidate is an "instrument fitness
check" procedure: for a shared lab instrument, verify against the SOP *and* the
manufacturer's procedure, identify where they differ, evaluate the criteria
independently, and require a named authorisation before taking the instrument out
of service. It would be needed again on every instrument in this lab, and its
scope — "verify, and escalate on disagreement" — is testable. It goes to
`skill-creator` after the next instrument, and the test set should include the case
where the SOP and the manual agree, so the skill does not learn to widen every
check.

## What this example proves

- **R4 is not about difficulty.** One bench check, five minutes, and R4 — because
  240 samples and a shared booked instrument. The two triggers are named
  separately, which is what makes the rung auditable.
- **The checkpoint came before the action, with all five parts.** A named person, a
  time, what is irreversible, what is and is not authorised, a recommendation about
  *when* to approve, and the verification status at the moment of asking.
- **Two independent criteria, pointing in opposite directions.** Slope passes,
  both offsets fail. A single-point check cannot see that shape, and a check with
  one criterion would have reported one of two true things.
- **The SOP was followed, and then exceeded, and both facts are recorded.** The
  single-point check was run and it failed; the two-point check is what turned a
  symptom into a diagnosis. 90 seconds bought the reason.
- **A stricter document is not automatically the better one.** The 7.00 buffer was
  past the SOP's 7-day rule and inside the supplier's 30-day rule, and making fresh
  buffer would have been a wasted 20 minutes. The two documents were read against
  each other rather than the first one found being followed.
- **An uncertified reference was refused rather than used.** The 4.00 buffer's
  illegible label stopped the check, and stopping was cheaper than a result that
  described the bottle.
- **The authority boundary held on a shared resource.** Twenty minutes of downtime
  was somebody else's twenty minutes, and the shift lead — not the kernel — decided.
