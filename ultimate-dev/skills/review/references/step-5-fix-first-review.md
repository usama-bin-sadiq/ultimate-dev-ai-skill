<!-- Moved verbatim from review/SKILL.md, the 'Step 5: Fix-First Review' section. Relative links were rebased for the new depth; the prose is otherwise unchanged. -->

# Step 5: Fix-First Review

**Every finding gets action — not just critical ones.**

**Keep decisions through fix cycles.** Maintain an in-memory action list for this invocation, initialized once and retained when Steps 3–5.7 repeat. Keep defects and advisories separate; for shared-code advice retain the helper-computed fingerprint, `advisory`, `evidence_paths`, and `helper_target` from the actual decision. Record completed AUTO-FIX/fix actions and explicit Skip choices as they happen. A later zero-edit pass may no longer find an approved extraction because it succeeded; that must not erase its `fixed` action or original identity metadata.

On each repeat pass, re-read all supporting callers and the helper destination before carrying an advisory decision forward. An unrelated auto-fix does not require asking the same question again when the structural identity, proposed contract, and tradeoffs remain unchanged. Compare actual raw source with the evidence read for the decision, including secondary callers and any transformed or indirect paths; changed evidence requires fresh evaluation. If the proposal, behavior, migration, or risk has materially changed, ask a new question instead of inheriting the choice. This invocation-local decision tracking is not cross-review suppression and must never hide a new or recurring defect.

### Step 5.0: Cross-review finding dedup

**Validate advisory severity first.** If a current finding has `"severity":"CRITICAL"` and `"advisory":true`, remove `advisory` and retain its `CRITICAL` severity. Handle it as a normal defect before suppression, classification, counting, scoring, and persistence. Never downgrade severity to make advisory metadata consistent. Valid INFORMATIONAL advisories remain advisory in every category, including simplification. A prior saved finding with contradictory CRITICAL/advisory metadata cannot establish a skipped defect or advisory decision: exclude it from reuse and revalidate the current finding.

Before classifying findings, check if any were previously skipped by the user in a prior review on this branch.

```bash
~/<agent-config-dir>/gstack/bin/gstack-review-read
```

Parse the output: only lines BEFORE `---CONFIG---` are JSONL entries (the output also contains `---CONFIG---` and `---HEAD---` footer sections that are not JSONL — ignore those).

**Shared-code advisory decisions use the stricter rule below.** Do not send a
finding through the ordinary primary-file rule if its category is `shared-libs`,
its fingerprint starts `shared-libs:`, or it has `evidence_paths` / `helper_target`.
Missing legacy metadata requires revalidation, not fallback to a line fingerprint.

For each JSONL entry that has a `findings` array, for ordinary findings only:
1. Collect all fingerprints where `action: "skipped"`
2. Note the `commit` field from that entry

If skipped fingerprints exist, get the list of files changed since that review:

```bash
git diff --name-only <prior-review-commit> HEAD
```

For each current finding (from both Step 4 critical pass and Step 4.5-4.6 specialists), check:
- Does its fingerprint match a previously skipped finding?
- Is the finding's file path NOT in the changed-files set?
- Is it the same advisory/defect kind? Never use a skipped advisory to suppress a real defect, including a defect with a colliding supplied fingerprint.

If all conditions are true: suppress the finding. It was intentionally skipped and the relevant code hasn't changed.

**Reuse a skipped shared-code advisory only with complete structural evidence:**

1. Recompute both structural identities with `sharedLibsFingerprint` from
   `~/<agent-config-dir>/gstack/lib/review-evidence.ts` before deduplication. Both must
   be valid, both findings must explicitly be advisory, the prior saved hash must
   match its recomputation, and the prior action must explicitly be `skipped`.
   Retain `evidence_paths` and `helper_target`; line numbers and a primary path
   alone cannot identify an extraction.
2. Require a prior completed, converged `review` with verified binding and
   start/end/record fingerprints equal to current `---WTREE---`. Read REVIEW_START
   without consuming it; its repo, raw branch and fingerprint must match the current
   repo, branch and snapshot. Missing, changed or unknown fields/token require
   revalidation. Do not mint a new token to enable suppression.
3. Match prior trusted `review_binding.branch_id` to SHA-256 of the exact
   current raw branch, matching the capture. Compute the digest in code, never
   as model-generated text. Sanitized log filenames are not branch identity:
   `topic/a` and `topic-a` can collide.
4. Verify EVERY evidence path against the snapshot. Enumerate tracked/non-ignored
   untracked paths, then raw-read/lstat each file and path component; `ls-files`
   alone is insufficient. Revalidate symlink targets/ancestors, submodules,
   ignored/outside files and missing/unreadable paths: the parent fingerprint
   does not cover them. Inspect effective Git attributes/config without conversion:
   filter, working-tree-encoding, ident, text/eol and core.autocrlf can hide raw
   changes. Active/unknown transformations require fresh raw-source review even
   with an unchanged filtered tree. Disable fsmonitor and optional locks.
   Exclude assume-unchanged, skip-worktree and sparse index entries. Compare each
   raw file byte-for-byte with its blob in that exact working-tree snapshot,
   using Git object reads without external diff/textconv or normalization.
   Missing blobs, mismatches or unknown coverage require revalidation.
   Only verified regular, untransformed,
   in-repository paths enter `covered_paths`.
   The prior finding's `snapshot_covered_paths` must also cover every evidence
   path; current eligibility cannot prove what prior filters/index flags hid.
   Missing prior coverage is legacy metadata; revalidate it.
5. Call pure `canReuseSharedLibsAdvisory` with actually read records and verified
   snapshot fields as literal JSON on stdin. The command below computes the live branch digest;
   replace the empty example objects and keep the quoted delimiter:

```bash
bun -e '
const { createHash } = await import("node:crypto");
const { canReuseSharedLibsAdvisory } = await import(process.argv[1]);
const input = JSON.parse(await Bun.stdin.text());
let branch = Bun.spawnSync(["git", "symbolic-ref", "--quiet", "--short", "HEAD"]);
if (branch.exitCode !== 0) branch = Bun.spawnSync(["git", "rev-parse", "HEAD"]);
if (branch.exitCode !== 0) { console.log(false); process.exit(0); }
const rawBranch = branch.stdout.toString().replace(/\r?\n$/, "");
const snapshot = { ...input.currentSnapshot, branch_id: createHash("sha256").update(rawBranch, "utf8").digest("hex") };
console.log(canReuseSharedLibsAdvisory(input.priorFinding, input.currentFinding, input.priorReview, snapshot));
' "$HOME/<agent-config-dir>/gstack/lib/review-evidence.ts" <<'GSTACK_SHARED_LIBS_REUSE_JSON'
{"priorFinding":{},"currentFinding":{},"priorReview":{},"currentSnapshot":{"wtree":"","covered_paths":[]}}
GSTACK_SHARED_LIBS_REUSE_JSON
```

Suppress only when ALL eligibility checks passed and the helper returns true.
Otherwise re-read all supporting callers and present any still-supported advice
for a fresh decision. A changed secondary caller or changed raw bytes matter even
when the primary anchor, commit, or normalized Git tree appears unchanged. A real
defect always retains normal Fix-First handling independently of this advice.

Print: "Suppressed N findings from prior reviews (previously skipped by user)"

**Only suppress `skipped` findings — never `fixed` or `auto-fixed`** (those might regress and should be re-checked).

If no prior reviews exist or none have a `findings` array, skip this step silently.

Output a summary header: `Pre-Landing Review: N issues (X critical, Y informational)`.
Count only non-advisory defects in that header; list optional advice separately
with `[ADVISORY]`. Preserve advisory records and explicit decisions for
persistence, but exclude advisories from score penalties, unresolved-defect
totals, and clean-status blockers. This does not relax completion, convergence,
or missing-reviewer rules.

### Step 5a: Classify each finding

For each finding, classify as AUTO-FIX or ASK per the Fix-First Heuristic in
checklist.md. Critical findings lean toward ASK; informational findings lean
toward AUTO-FIX.

**Advisory override:** After the severity validation above, every remaining finding with `advisory:true`, including core shared-code advice, is ASK-only even when mechanical. Never auto-apply an optional extraction. Label it `[ADVISORY]`, show the helper, caller migration, tests, and estimated total savings, and let the user approve or skip it. Advisories are excluded from defect counts, score penalties, unresolved-defect totals, and clean-status blockers. A real defect still follows ordinary Fix-First independently of advice touching the same code.

**Test stub override:** Any finding that has a `test_stub` field (generated by a specialist)
is reclassified as ASK regardless of its original classification. When presenting the ASK
item, show the proposed test file path and the test code. The user approves or skips the
test creation. If approved, write the fix + test file. Derive the test file path from
the finding's `path` using project conventions (`spec/` for RSpec, `__tests__/` for
Jest/Vitest, `test_` prefix for pytest, `_test.go` suffix for Go). If the test file
already exists, append the new test. Output: `[FIXED + TEST] [file:line] Problem -> fix + test at [test_path]`

### Step 5b: Auto-fix all AUTO-FIX items

Apply each fix directly. For each one, output a one-line summary:
`[AUTO-FIXED] [file:line] Problem → what you did`
Retain the completed action in the invocation action list before starting any re-review.

### Step 5c: Batch-ask about ASK items

If there are ASK items remaining, present them in ONE AskUserQuestion:

- List each item with a number, the severity label (or `[ADVISORY]` for optional advice), the problem, and a recommended fix
- For each item, provide options: A) Fix as recommended, B) Skip
- Include an overall RECOMMENDATION

Example format:
```
I auto-fixed 5 issues. 2 need your input:

1. [CRITICAL] app/models/post.rb:42 — Race condition in status transition
   Fix: Add `WHERE status = 'draft'` to the UPDATE
   → A) Fix  B) Skip

2. [INFORMATIONAL] app/services/generator.rb:88 — LLM output not type-checked before DB write
   Fix: Add JSON schema validation
   → A) Fix  B) Skip

RECOMMENDATION: Fix both — #1 is a real race condition, #2 prevents silent data corruption.
```

If 3 or fewer ASK items, you may use individual AskUserQuestion calls instead of batching.
Retain each explicit Skip choice and its finding metadata in the invocation action list. Do not record an unanswered question as skipped or ask again about a decision already revalidated in this invocation.

### Step 5d: Apply user-approved fixes

Apply fixes for items where the user chose "Fix." Output what was fixed.
After applying the approved fix, retain its `fixed` action and the original finding metadata in the invocation action list, even if the changed blocks or helper callers are subsequently removed. Approval alone is not a completed fix.

If no ASK items exist (everything was AUTO-FIX), skip the question entirely.

### Verification of claims

Before producing the final review output:
- If you claim "this pattern is safe" → cite the specific line proving safety
- If you claim "this is handled elsewhere" → read and cite the handling code
- If you claim "tests cover this" → name the test file and method
- Never say "likely handled" or "probably tested" — verify or flag as unknown

**Rationalization prevention:** "This looks fine" is not a finding. Either cite evidence it IS fine, or flag it as unverified.

### Greptile comment resolution

After outputting your own findings, if Greptile comments were classified in Step 2.5:

**Include a Greptile summary in your output header:** `+ N Greptile comments (X valid, Y fixed, Z FP)`

Before replying to any comment, run the **Escalation Detection** algorithm from greptile-triage.md to determine whether to use Tier 1 (friendly) or Tier 2 (firm) reply templates.

1. **VALID & ACTIONABLE comments:** These are included in your findings — they follow the Fix-First flow (auto-fixed if mechanical, batched into ASK if not) (A: Fix it now, B: Acknowledge, C: False positive). If the user chooses A (fix), reply using the **Fix reply template** from greptile-triage.md (include inline diff + explanation). If the user chooses C (false positive), reply using the **False Positive reply template** (include evidence + suggested re-rank), save to both per-project and global greptile-history.

2. **FALSE POSITIVE comments:** Present each one via AskUserQuestion:
   - Show the Greptile comment: file:line (or [top-level]) + body summary + permalink URL
   - Explain concisely why it's a false positive
   - Options:
     - A) Reply to Greptile explaining why this is incorrect (recommended if clearly wrong)
     - B) Fix it anyway (if low-effort and harmless)
     - C) Ignore — don't reply, don't fix

   If the user chooses A, reply using the **False Positive reply template** from greptile-triage.md (include evidence + suggested re-rank), save to both per-project and global greptile-history.

3. **VALID BUT ALREADY FIXED comments:** Reply using the **Already Fixed reply template** from greptile-triage.md — no AskUserQuestion needed:
   - Include what was done and the fixing commit SHA
   - Save to both per-project and global greptile-history

4. **SUPPRESSED comments:** Skip silently — these are known false positives from previous triage.

---
