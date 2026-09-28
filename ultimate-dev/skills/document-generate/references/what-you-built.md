<!-- Moved verbatim from document-generate/SKILL.md, the 'section' section. Relative links were rebased for the new depth; the prose is otherwise unchanged. -->

# What you built

[Recap: what the reader now has and what it can do. Link to reference docs
for deeper exploration. Suggest next steps.]
```

**Rules for tutorials:**
- **Time to first result < 3 steps.** If the reader hasn't seen something work by step 3,
  the tutorial is too slow.
- Every step must produce a visible change or output. No "now configure X" without showing
  what changes.
- Use the exact commands the reader will type. No "run the appropriate command" abstractions.
- Error paths: if a step commonly fails, show the error and the fix inline.
- End with "What you built" — connect the tutorial back to the real use case.

---

## Step 7: Cross-Document Linking & Discoverability

After writing all documents:

1. **Add cross-links between quadrants.** Every reference doc should link to its how-to.
   Every how-to should link to its reference. Tutorials should link to both.

2. **Update entry-point files.** Add references to new docs in:
   - README.md — add to documentation section or table of contents
   - <agent-instructions> / <agent-instructions> — add to project structure if relevant
   - Any existing docs index or sidebar config

3. **Verify discoverability.** Every new document must be reachable within 2 clicks from
   README.md. If a docs framework is in use, add to the sidebar/nav config.

4. **Check for broken links.** Grep for any `](` references that point to files that don't exist.

---

## Step 8: Quality Self-Review

Before committing, review each document against these criteria:

**Accuracy gate:**
- [ ] Every code example compiles / runs / passes if copy-pasted
- [ ] Every API description matches the actual code signature
- [ ] Every command shown produces the output described
- [ ] No stale references to renamed/removed entities

**Completeness gate:**
- [ ] Reference docs cover 100% of public surface
- [ ] How-tos cover the top 3 tasks a user would attempt
- [ ] Tutorials get to a working result in ≤3 steps
- [ ] Explanation docs name trade-offs, not just choices

**Voice gate:**
- [ ] Written for a smart person who hasn't seen the code
- [ ] No jargon without brief inline gloss on first use
- [ ] Active voice, concrete nouns, short sentences
- [ ] "You can now..." not "The system provides..."

Fix any failures before proceeding.

---

## Step 9: Commit & Output

1. Stage new documentation files by name (never `git add -A` or `git add .`).

**Redaction scan before commit.** Generated docs frequently contain example
credentials; scan the staged doc content and block on a HIGH credential (a
live-format secret in committed docs is a leak). Example configs belong in
` ```example ` fences won't excuse a live-format secret, but the per-span
placeholder filter passes obvious docs examples (e.g. `AKIAIOSFODNN7EXAMPLE`):

```bash
REDACT_VIS=$(~/<agent-config-dir>/gstack/bin/gstack-config get redact_repo_visibility 2>/dev/null)
[ -z "$REDACT_VIS" ] && REDACT_VIS=$(gh repo view --json visibility -q .visibility 2>/dev/null | tr 'A-Z' 'a-z')
git diff --cached --no-color | grep '^+' | sed 's/^+//' | \
  ~/<agent-config-dir>/gstack/bin/gstack-redact --repo-visibility "${REDACT_VIS:-unknown}" --json
# exit 3 (HIGH) → unstage the offending doc, remove the secret, re-stage. Do NOT commit.
```

2. Create a commit:

```bash
git commit -m "$(cat <<'EOF'
docs: generate [scope] documentation (Diataxis)

[One-line summary of what was documented]

Quadrants: [list which quadrants were produced]

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

3. Push to the current branch:

```bash
git push
```

4. **If a PR exists**, update the PR body with a `## Documentation Generated` section listing
   every new file with its Diataxis quadrant and a one-line description:

```
## Documentation Generated

| File | Quadrant | Description |
|------|----------|-------------|
| docs/tutorial-getting-started.md | Tutorial | Walk-through from install to first working example |
| docs/reference-widget-api.md | Reference | Complete widget API with types, defaults, examples |
| docs/explanation-bayesian-scheduler.md | Explanation | Why the scheduler uses Bayesian inference |
| docs/howto-custom-widgets.md | How-to | Creating and registering custom widgets |
```

5. Output a structured summary:

```
Documentation generated:
  Scope: [what was documented]
  Files: [N] new, [M] updated
  Coverage:
    Tutorials:    [count] ([list])
    How-tos:      [count] ([list])
    Reference:    [count] ([list])
    Explanation:  [count] ([list])
  Quality: [pass/fail on each gate]
```

---
