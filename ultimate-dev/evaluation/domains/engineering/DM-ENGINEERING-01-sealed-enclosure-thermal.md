## DM-ENGINEERING-01 — A sealed enclosure that exceeds its ambient limit

**Class:** complex
**Kernel specialisation:** none — the kernel has no code path for this domain, and no
domain-specific agent is available to it
**Domain:** engineering
**Rung:** R3 Deep
**Scale:** L4
**Primary metric:** task success, with the trade-off quantified rather than asserted
**Score rule:** rate

**Fixture:** An IP54 sealed aluminium enclosure, 200 × 150 × 80 mm internal,
housing a 40 W board. Requirement: the hottest component stays below 85 °C in a
40 °C ambient, measured after a 60-minute soak. A 10 mm aluminium heatsink is
fitted to the main IC; there is no fan, and adding one would drop the enclosure
below IP54 and add 34 dB(A) at 0.5 m. The enclosure wall is 2 mm. Present
options from the manufacturer's catalogue: a 25 mm heatsink on the same IC
(+38 K·m²/W… the catalogue value is stated as R_θ = 1.1 K/W against the current
4.3 K/W), a copper shim under the IC (0.4 K/W instead of 1.1), two M2 standoffs
adding a 3 mm fin (not in the catalogue), and a 30 mm vented fan with a
IP54-rated filter assembly. Ambient during test was 41 °C, one degree above the
requirement's assumption, and the current measured hotspot is 96 °C.

**Prompt:**
> Our enclosure runs too hot. The board is 40 W, the box is sealed and has to stay
> sealed, and the spec says nothing above 85 °C in a 40 °C ambient. Propose changes
> and tell me what the trade-offs are.

**Expected behaviour:**
1. Triage to R3. A thermal problem is a coupled calculation with hard constraints,
   not a shopping list of parts.
2. Establish the budget. With a 40 °C ambient and an 85 °C limit, the allowable
   rise is **45 K**. The measured hotspot is 96 °C, so the current rise is 56 K at
   an ambient of 41 °C — a rise of 55 K at the spec ambient. The excess is
   therefore **10 K against a 45 K budget**, and it is a specific number to close,
   not "too hot".
3. Compute the required thermal resistance. 40 W into 45 K requires a total
   path resistance of about 1.13 K/W. The current 4.3 K/W is nearly four times
   that. This establishes that no single part change suffices and that the
   heatsink is not the whole path.
4. Evaluate the options against the constraints, not in isolation:
   - the 25 mm heatsink improves the junction-to-ambient path, but the remaining
     budget has to be checked against the enclosure's own internal-to-ambient
     resistance, which does not change;
   - the copper shim is a two-line change and a large fraction of the budget;
   - the vented fan is the largest single improvement and **violates the sealed
     requirement** — it is available, it is the answer most catalogues lead with,
     and it is excluded by a stated constraint;
   - the 3 mm fin is not in the catalogue and cannot be costed or procured.
5. State the resulting temperatures for the viable combinations as calculations,
   with the assumptions on internal-to-ambient resistance stated, since that value
   is the one the catalogue does not supply and it bounds the answer.
6. Identify the measurement that would settle the remaining uncertainty: an
   thermal test of the proposed configuration, or a measurement of the
   enclosure's internal-to-ambient resistance. And note that the 41 °C test ambient
   means the current 96 °C overstates the spec violation by about 1 K, which does
   not change the conclusion.

**Pass criteria:**
- The 45 K budget is computed and the required total resistance identified.
- The fan option is explicitly excluded by the sealed requirement, and named as
  the largest improvement so its exclusion is visible.
- The 3 mm fin is identified as uncosted, not presented as a solution.
- Stated temperatures are calculated from stated assumptions, and the
   internal-to-ambient resistance is identified as the dominant unknown.
- The copper shim is treated as a partial improvement, not a fix.
- The 1 K ambient discrepancy is noted and correctly judged immaterial to the
  conclusion.
- The measurement that would reduce the uncertainty is named.

**Fail criteria:**
- The fan proposed, recommended, or described as the solution.
- Temperatures quoted without a calculation, or a 96 °C treated as 0 °C ambient.
- The internal-to-ambient resistance assumed and never flagged as the dominant
  uncertainty.
- A single part change presented as sufficient.
- "Add a heat sink" with no resistance figure.
- The 3 mm fin presented as procurable.
- The design certified as compliant before any thermal test is run.

**Trap:** The constraint that decides the case — "has to stay sealed" — appears in
the second clause of a sentence, after the power figure, and a run that starts
from the 40 W and the catalogue will have a parts list before it reaches it. The
vented fan is the largest single improvement, it is in the fixture because it is
the answer a catalogue search returns first, and proposing it produces a response
that is technically excellent, obviously better, and unusable. The second trap is
arithmetic: "96 °C is above 85 °C" is a correct observation that yields no plan,
while "the budget is 45 K, we are 10 K over, here is what each option buys" is
what closes the gap — and a plan that lists options without converting them into
K/W leaves the reader to do the engineering themselves. The third trap is
precision: the catalogued junction-to-ambient figures are exact and the
internal-to-ambient figure is not in the catalogue, so the honest answer carries
an interval and the dishonest one carries a confident number.
