# Webinar Plan — <topic>

> Skeleton for `webinar-marketing` Mode 1 (Plan From Scratch). Copy this file,
> fill every section, and delete the guidance in angle brackets before handing
> the plan over. Sections 1–3 are not optional: a plan that skips the funnel
> math is a plan that will be celebrated on registrations and fail on revenue.

**Owner:** <name>  ·  **Event date:** <YYYY-MM-DD>  ·  **Runway:** <N> weeks
**Goal:** <net-new leads | pipeline acceleration | product adoption | retention/expansion | brand/authority>

---

## 1. The Promise

One sentence a stranger would repeat to a colleague. Not the topic — the
**takeaway**.

> <"Leave with a 90-day pipeline plan" — not "learn about pipeline.">

- **Title:** <title>
- **Format:** <see references/webinar-formats.md> — <live | simulated-live | evergreen> · <duration> · <solo | interview | roundtable | panel>
- **Speaker:** <name, role, and the one credential that makes this topic theirs>
- **Why this format fits this goal:** <one line>

## 2. The Audience

| Field | Value |
|---|---|
| Who | <role and company stage> |
| Audience temperature | <customers | warm | owned_cold | paid_cold> |
| Awareness stage | <cold prospects | existing pipeline | current customers> |
| Reachable list size | <N> |
| Promotion channels available | <email | paid | partners | social | sales> |
| Paid budget | <amount or "organic only"> |
| Runway to event | <N> weeks |

## 3. Funnel Math — Sized Backward From the Goal

Work **down** from the business goal. Every rate below is a default; replace
it with the benchmark for this audience temperature from
`references/benchmarks.md`.

```
Business goal (SQOs)            <20>
÷ attendee→SQO rate            ÷ 10%   → <200> engaged attendees needed
÷ register→attend              ÷ 35%   → <570> registrations needed
÷ landing-page CVR             ÷ 40%   → <1,425> qualified visits needed
─────────────────────────────────────────────────────────────
Promotion plan must deliver    <1,425> qualified visits
```

**Per-stage rates used:**

| Stage | Rate used | Benchmark for this temperature | Source |
|---|---|---|---|
| landing-page visit → registration | <%> | <%> | benchmarks.md |
| registration → attended live | <%> | <%> | benchmarks.md |
| attended → engaged | <%> | <%> | benchmarks.md |
| engaged → SQO | <%> | <%> | benchmarks.md |

**Feasibility check — answer all four before proceeding:**

- [ ] Required qualified visits ≤ reachable list × channel reach. If not, the
      goal, format, or budget is wrong — fix it here, not after the event.
- [ ] Required registrations ≤ list size + paid allowance.
- [ ] Paid budget stated covers the visit shortfall, or the shortfall is
      closed by partner/SDR promotion that is actually committed.
- [ ] Runway is long enough to run two reminder cycles (see §5).

> If any box is unchecked, stop and revise the goal or the format. A plan that
> cannot reach its own numbers is the most expensive kind of plan.

## 4. Promotion Plan

Calendar across the runway. See `references/promotion-playbook.md` for channel
mechanics and cadence.

| Week | Channel | Asset | Audience | Sends / volume | Notes |
|---|---|---|---|---|---|
| <W-4> | <email> | <announcement> | <list segment> | <N> | <angle> |
| <W-3> | <paid> | <ad> | <cold lookalike> | <budget> | <creative angle> |
| <W-1> | <email> | <value-focused> | <non-registrants> | <N> | <last chance framing> |
| <W-1> | <partner / SDR> | <1:1 invite> | <accounts> | <N> | <owner> |

- **Announcement angle:** <the promise, in the audience's words>
- **Reminder angle:** <what they lose by skipping>
- **Registration capacity:** <N> · **Waitlist:** <yes/no>

## 5. Registration Page

One job: make the value obvious and registering frictionless.

- **Headline:** <outcome + takeaway>
- **Above the fold:** <what they get, how long, who it's for>
- **Form fields:** <minimum — every extra field costs registrations>
- **Confirmation:** <what happens next, when, and how they add it to a calendar>
- **Calendar file + reminder:** <yes/no>

## 6. Show-Up Sequence

Registration is not attendance. See §"The Five Stages" in `SKILL.md`.

| T− | Touch | Channel | Purpose |
|---|---|---|---|
| T−3 days | Reminder 1 | <email> | Value recap + add-to-calendar |
| T−1 day | Reminder 2 | <email> | Speaker + agenda + social proof |
| T−1 hour | Reminder 3 | <email / SMS> | "Starting in an hour" |
| T+5 min | <nudge> | <in-app / chat> | Late joiners |

- **Replay sent to no-shows:** <timing>
- **Registration → attend target:** <%> · **Show-up target:** <N>

## 7. The Show

| Segment | Minutes | Purpose | Speaker |
|---|---|---|---|
| <cold open> | <N> | <hook / problem> | <name> |
| <core content> | <N> | <the deliverable> | <name> |
| <live-to-close> | <N> | <the offer> | <name> |
| Q&A | <N> | <handle objections> | <name> |

- **The live-to-close moment:** <the single strongest segment — this is what
  Mode 3 will later turn into evergreen>
- **CTA, stated out loud and shown on screen:** <exact wording>

## 8. Follow-Up — Segmented

Do not send one blast. Attendees and no-shows need different asks.

**Attendees (<timing>, immediately)**

| Asset | Purpose |
|---|---|
| Slides + replay link | Deliver on the promise |
| <offer> | The next step — <book a demo / start a trial> |
| <support> | Answer the objections live Q&A surfaced |

**No-shows (<timing>)**

| Asset | Purpose |
|---|---|
| Replay + <highlight clip> | Give the takeaway without the time cost |
| <CTA variant> | Same ask, lower-commitment framing |
| Last-chance | <N> days before the offer closes |

- **Sales handoff:** <who gets which lead, and within what SLA>
- **Attribution:** <how a registration becomes a pipeline entry>

## 9. Measurement

Set these **before** launch; the post-event review is worthless without a baseline.

| Metric | Target | Actual |
|---|---|---|
| Qualified visits | <N> | |
| Registrations | <N> | |
| Attended live | <N> (<%>) | |
| Engaged (watched <threshold>) | <N> | |
| SQOs | <N> | |

- **Scored post-event with:**
  `python3 scripts/webinar_funnel_scorer.py funnel.json`
- **Review owner + date:** <name>, <YYYY-MM-DD>

---

## Open Questions

| Question | Owner | Needed by |
|---|---|---|
| <e.g. is paid budget approved?> | <name> | <date> |

Anything still unanswered at this line is a plan that will slip. Resolve it here.
