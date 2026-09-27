## DM-SOFTWARE-02 — Change a response field's type without breaking anyone

**Class:** multi-step
**Domain:** software
**Kernel specialisation:** none
**Rung:** R2 Analytical
**Scale:** L4
**Primary metric:** task success, with completeness (every consumer identified)
**Score rule:** rate

**Fixture:** `GET /v1/orders` returns `createdAt` as an RFC 3339 string
(`"2026-03-14T09:30:00Z"`). It is consumed by: this repository's mobile app
(TypeScript, 3 call sites), this repository's admin web app (TypeScript, 1 call
site), a partner integration `acme-orders` that polls the endpoint (external,
documented in `docs/api.md`), a data export job in `analytics/` that parses the
field with `dateutil.parser`, and two internal Python scripts found by grep. There
is no API versioning on this endpoint and adding one is out of scope for the
request. A partner changelog process exists and takes 5 business days.

**Prompt:**
> We need `createdAt` on `/v1/orders` to be epoch milliseconds instead of a date
> string. It's breaking our mobile parsing. Find everyone affected, make the
> change safely, and tell me what I need to tell the other teams.

**Expected behaviour:**
1. Triage to R2, and to a real task model. "Change a field's type" is a
   one-line edit and a compatibility problem; the second is the work.
2. Enumerate consumers by evidence, not by intuition. Grep the repository for the
   field, and separately identify consumers that grep cannot find: the partner
   polling the endpoint, the data export, the two scripts. The distinction between
   "found in this repo" and "known to exist" is the case.
3. Establish which consumers break. A `new Date(string)` in TypeScript breaks on
   a number. `dateutil.parser` breaks on an integer. A partner parsing the string
   breaks. Some may tolerate it, and which ones do is determined by reading them,
   not assumed.
4. Decide on the compatibility mechanism, and state the rejected alternative. The
   obvious candidates are a new field alongside the old one, a new versioned
   endpoint, and a flag. A new field is the cheapest and is the one that requires
   no partner coordination; replacing the type in place is the one the user
   literally asked for and the one that breaks three consumers.
5. Make the change, including the consumers in this repository.
6. Produce the external communication: what changes, when, for whom, and what they
   must do. Include the 5-day changelog lead time as a schedule fact, not a
   caveat.

**Pass criteria:**
- All five consumer groups are named, including the partner and the two Python
  scripts that a repository-only search would miss.
- For each consumer, whether it breaks is determined by reading it, and the
  determination is shown.
- A compatibility mechanism is chosen, and the rejected alternative is recorded
  with a reason.
- In-repository consumers are updated consistently, and the change compiles or
  its tests pass — observed.
- The external communication is specific: which fields, which date, what to do,
  and by when.
- The 5-day changelog lead time is reflected in the schedule.

**Fail criteria:**
- A repository-only grep reported as the full consumer list.
- The field's type changed in place with no compatibility mechanism and no
  versioning, breaking the partner without notice.
- A new field added and the old one removed, which is a breaking change wearing a
  compatibility costume.
- The partner not notified, or notified without a date.
- "All internal references updated" claimed without evidence.
- A versioned `v2` endpoint proposed without stating that the partner would have
  to migrate and that no versioning infrastructure currently exists.

**Trap:** The task presents as a type change, and a type change is a
`grep`-and-edit job. The trap is that the repository is the only consumer set a
run can see, so the greedy enumeration looks complete: five call sites found, all
updated, all tests green, and a partner integration broken in production with no
notice. The second trap is the "safe" fix — adding `createdAt_ms` and keeping the
old field. It is genuinely low-risk and it is also a permanent API surface
doubling for a field that will be read by two code paths forever, and a reviewer
who asked "why two fields?" deserves an answer. Deciding between the two requires
knowing how long the old field must live, which is a question for the partner, so
the correct deliverable is the decision plus the communication that forces the
decision — not a silent choice of the comfortable option.
