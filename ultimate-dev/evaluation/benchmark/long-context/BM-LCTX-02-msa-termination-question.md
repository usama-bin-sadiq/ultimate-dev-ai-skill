## BM-LCTX-02 — One clause question about a 180-page contract

**Class:** long-context
**Domain:** business
**Rung:** R2 Analytical
**Scale:** L2
**Primary metric:** context efficiency, with correctness of the located clause
**Score rule:** rate

**Fixture:** `vendor_msa.pdf`, 180 pages, plus a 12-page `data_processing_addendum.pdf`
executed six weeks after the MSA. The MSA's clause 14 permits either party to
terminate for convenience on 30 days' written notice. The DPA's clause 9 permits
the processor to terminate immediately for material breach and, separately,
requires 90 days to complete data return before the processor may delete
controller personal data. A later-signed agreement between the same parties
controls over an earlier one on the same subject. Page numbers are known to the
fixture but the run must find them.

**Prompt:**
> Is it safe for us to terminate this vendor for convenience with 30 days' notice?

**Expected behaviour:**
1. Establish the document set. A single-file search answers a question that two
   documents govern.
2. Establish precedence: the DPA was signed later and controls over the MSA on the
   same subject, so "30 days" from the MSA is not the whole answer.
3. Locate the termination provisions in both documents and quote them, with
   clause references.
4. Answer the question asked — is the 30-day route open — and then answer the
   question that makes the first one dangerous: what happens to the data in the 90
   days after termination, and what happens to the service during it.
5. State the conclusion with its limits: this is a reading of the documents, not
   legal advice, and the operational consequence depends on the vendor's
   performance which the documents do not establish.

**Pass criteria:**
- Both documents are examined, and the later-signed DPA is identified as
  controlling on data-return terms.
- The MSA clause 14 30-day right is quoted or cited accurately.
- The DPA's 90-day data-return obligation is identified and its effect on "safe"
  is explained.
- The response states plainly that this is a document reading and not legal
  advice.
- The response is bounded — it does not summarise 180 pages.
- No clause is quoted that does not appear in the fixture.

**Fail criteria:**
- The MSA is read alone and the answer is "yes, 30 days, done".
- A summary of the agreement's structure is given in place of an answer.
- A clause is quoted, paraphrased, or cited that is not in the fixture.
- Legal advice is given, or an unqualified assurance that termination "is safe".
- The 90-day data-return obligation is missed, or described as a minor
  administrative step.
- The 180-page document is loaded whole into context.

**Trap:** The question has the shape of a lookup — a clause, a number, a yes/no —
and the MSA genuinely contains the 30-day right, so a search finds a real
provision that directly matches the words in the request. The run can quote it,
answer yes, and be entirely wrong, because the operative constraint lives in a
second document that nobody mentioned, was signed later, and takes ninety days to
run out. The trap's second edge is the output shape: a 180-page contract invites a
thorough, structured summary, and a summary is the easiest way to look
responsible while never reaching a conclusion. The whole point of the case is
that the user asked a small question about a large document set, and the correct
answer is three paragraphs and one caveat, not a legal overview.
