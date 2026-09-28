<!-- Moved verbatim from design-shotgun/SKILL.md, the
     'step-1-context-gathering' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Step 1: Context Gathering

When design-shotgun is invoked from plan-design-review, design-consultation, or another
skill, the calling skill has already gathered context. Check for `$_DESIGN_BRIEF` — if
it's set, skip to Step 2.

When run standalone, gather context to build a proper design brief.

**Required context (5 dimensions):**
1. **Who** — who is the design for? (persona, audience, expertise level)
2. **Job to be done** — what is the user trying to accomplish on this screen/page?
3. **What exists** — what's already in the codebase? (existing components, pages, patterns)
4. **User flow** — how do users arrive at this screen and where do they go next?
5. **Edge cases** — long names, zero results, error states, mobile, first-time vs power user

**Auto-gather first:**

```bash
cat DESIGN.md 2>/dev/null | head -80 || echo "NO_DESIGN_MD"
cat PRODUCT.md 2>/dev/null | head -120 || echo "NO_PRODUCT_MD"
```

A `PRODUCT.md` (impeccable's product-context file) answers the job-to-be-done and audience questions: confirm, do not re-ask. Never open `<agent-config-dir>/impeccable/**`.

```bash
ls src/ app/ pages/ components/ 2>/dev/null | head -30
```

```bash
setopt +o nomatch 2>/dev/null || true
ls ~/.gstack/projects/$SLUG/*office-hours* 2>/dev/null | head -5
```

If DESIGN.md exists, tell the user: "I'll follow your design system in DESIGN.md by
default. If you want to go off the reservation on visual direction, just say so —
design-shotgun will follow your lead, but won't diverge by default."

**Check for a live site to screenshot** (for the "I don't like THIS" use case):

```bash
curl -s -o /dev/null -w "%{http_code}" http://localhost:3000 2>/dev/null || echo "NO_LOCAL_SITE"
```

If the user referenced a URL or said something like "I don't like how this looks,"
screenshot that page with Aside in Step 3c and use `$D evolve` instead of `$D variants`
to generate improvement variants from the existing design. If they didn't name the URL,
ask for it — never guess which page they mean. If the probe above printed `200`, offer
`http://localhost:3000` as the default in the AskUserQuestion below (still ask — never assume).

**AskUserQuestion with pre-filled context:** Pre-fill what you inferred from the codebase,
DESIGN.md, and office-hours output. Then ask for what's missing. Frame as ONE question
covering all gaps:

> "Here's what I know: [pre-filled context]. I'm missing [gaps].
> Tell me: [specific questions about the gaps].
> How many variants? (default 3, up to 8 for important screens)"

Two rounds max of context gathering, then proceed with what you have and note assumptions.
