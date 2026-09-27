## DM-EDUCATION-02 — Teach 24-hour time to international students who will work in 12-hour markets

**Class:** complex
**Domain:** education
**Kernel specialisation:** none
**Rung:** R2 Analytical
**Scale:** L3
**Primary metric:** completeness, with the failure criteria made observable
**Score rule:** rate

**Fixture:** A 2-week module, 6 sessions of 90 minutes, cohort of 24, mixed
nationalities, all relocating for jobs that use 12-hour notation in any written
or spoken context. Existing assessment is weekly quizzes worth 40% of the module
grade and a final practical worth 60%. A constraint in `pedagogy/constraints.md`:
assessment must be a "can-do" statement, so a learner must demonstrate the
capability under the conditions they will actually use it — and the cohort's stated
worst case is reading a spoken 12-hour time from a colleague across a noisy room
while writing it down.

**Prompt:**
> Design a two-week module that teaches our international hires both 24-hour and
> 12-hour time, because some of our local teams use 12-hour and the students will
> be talking to them.

**Expected behaviour:**
1. Triage to R2. The constraints are stated and the design space is bounded; this
   is a plan with a rubric, not an open pedagogical question.
2. Read `pedagogy/constraints.md` before designing. The "can-do" requirement is
   what makes the assessment design non-optional, and it means the module's
   assessment must be rebuilt, not merely extended.
3. Sequence the teaching. The 24-hour system is unambiguous and maps to
   international convention; 12-hour is ambiguous without a reference point. Teach
   24-hour first as the anchor, then introduce 12-hour as a transformation that
   requires knowing the half of the day, then make the two-way conversion the
   assessed skill rather than either system alone.
4. Address the specific stated failure mode, which is not knowing the notation —
   it is disambiguating a *spoken* 12-hour time. A module that teaches conversion
   accurately and never rehearses "is that ten or twenty-two" has not met the
   constraint.
5. Build assessment that is observable: a can-do task, a rubric, and a pass
   condition, replacing the weekly quiz format where the quiz cannot demonstrate
   the capability. State how the existing 40/60 weighting is handled.
6. State what the module deliberately does not do, so the design's boundary is
   visible — for example, it does not attempt fluency in spoken 12-hour
   production, and says so.

**Pass criteria:**
- A 6-session structure is specified, with per-session content.
- The 12-hour ambiguity and the spoken disambiguation are explicitly taught, and
  the spoken case appears in assessment, not only in explanation.
- Assessment is a can-do task with a stated pass condition and rubric.
- The 40/60 weighting change is addressed.
- The scope boundary is stated, including what is not attempted.
- The constraint file's requirement is cited as the reason the assessment was
  rebuilt.

**Fail criteria:**
- A module that teaches the two systems and reuses the existing weekly quiz.
- The spoken-disambiguation case absent, or present only as an explanation.
- A generic lesson plan with objectives and activities and no pass condition.
- "Can-do" used as a slogan with no observable task attached.
- No mention of the constraint file, and a design that would fail it silently.
- Sessions filled with content rather than rehearsal against the stated worst
  case.
- A claim about learning outcomes stated as a result rather than as a design
  intention.

**Trap:** The request is a design task with all its constraints supplied, and the
attractive output is a well-organised module outline with learning objectives,
activities, and a resources list — the shape of every teaching document ever
produced, and the shape that is worth least here. The constraint in the fixture
is the one that changes the work: a can-do requirement means the assessment must
be rebuilt, which is invasive, which affects the grade weighting, and which is
more work than designing six sessions. A run that delivers six excellent sessions
and a quiz has done the visible half. The second trap is that the conversion
between the two systems is genuinely easy to teach and the disambiguation of a
spoken time is not, so a run that teaches the conversion will feel like it has
covered the material while leaving the cohort's actual stated weakness untouched.
