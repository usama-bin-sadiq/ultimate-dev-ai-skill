## DM-WRITING-01 — A postmortem opening that starts with a timeline

**Class:** medium
**Kernel specialisation:** none — the kernel has no code path for this domain, and no
domain-specific agent is available to it
**Domain:** writing
**Rung:** R1 Structured
**Scale:** L2
**Primary metric:** correctness of the rewrite, with completeness (facts preserved)
**Score rule:** rate

**Fixture:** `incident-2026-05-02.md` opens with a 14-line timeline of timestamped
events. Real facts in the document: the incident began at 09:14 UTC; customer
impact ran 09:14 to 11:02 UTC; 2h48m duration; 41% of checkout requests failed
at peak; the cause was a connection-pool limit reached after a config change at
08:50; the rollback completed at 10:38; the authorising human was the on-call
engineer, no manager was paged. The document is otherwise accurate; the user has
said explicitly that no fact may change.

**Prompt:**
> The opening of our incident report is a timeline and it puts a reader to work
> before they know what happened. Rewrite the opening so someone who is tired and
> needs to act in the next 30 seconds gets what they need first.

**Expected behaviour:**
1. Triage to R1. This is a rewrite of a known piece of text against a stated
   audience and a stated purpose, with an explicit factual constraint. It is not
   an analysis task and the analysis is already done.
2. Read the document rather than the prompt's description of it, because the
   factual material is in the document and the prompt does not contain it.
3. Lead with what a 30-second reader needs: what is broken, what is affected, for
   how long, and what has been done. Duration, impact scope, and current state
   come before sequence.
4. Preserve every fact. No number is altered, rounded, or dropped; nothing is added
   that is not in the document. The on-call engineer detail and the rollback time
   belong in the body, not necessarily in the opening.
5. Produce the rewrite. Not advice about rewriting, not five options, not a
   commentary on the existing draft.

**Pass criteria:**
- A rewritten opening exists as text, not as guidance.
- The first two sentences convey impact and duration — 41% of checkout requests at
  peak and 2h48m — before any sequence of events.
- Every fact in the rewrite is present in the source document, unchanged: 09:14,
  11:02, 41%, 2h48m, 08:50, 10:38.
- No fact appears that is not in the document.
- The timeline is either removed from the opening or demoted, not deleted from the
  document.
- The output is one rewrite, not options or analysis of the draft's flaws.

**Fail criteria:**
- Feedback on the draft with no rewrite produced.
- Multiple alternative openings presented.
- A fact changed: 2h48m written as "nearly 3 hours", 41% as "about 40%", the
  rollback time altered, or the cause restated as "a deployment issue" when the
  document says a config change.
- A fact added, including a severity, a customer count, or a root cause
  elaboration not in the document.
- The advice-to-the-team framing preserved, so the reader still has to work.
- Commentary on the reader's state, or instructions to the reader inside the
  report.

**Trap:** The request is a writing task with a real audience constraint, and the
attractive failure is to diagnose the draft — "consider leading with impact
rather than sequence" — which is correct, useful, and leaves the user with the same
work. The second trap is the opposite: producing a punchy three-line opening from
the prompt's description of the document without reading it, which will be
structurally right and factually wrong, and the numbers are the only thing anyone
will check, and they are the thing that will be wrong. The third is compression
as an end in itself: "41% of checkout requests failed" is the sentence the whole
report exists to deliver, and a run that opens with atmosphere — "a busy morning
turned into a long one" — has optimised for register over the 30-second test it
was given.
