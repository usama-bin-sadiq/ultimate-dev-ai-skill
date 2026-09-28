<!-- Moved verbatim from review/SKILL.md, the
     'step-4-critical-pass-core-review' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Step 4: Critical pass (core review)

Apply the CRITICAL categories from the checklist against the diff:
SQL & Data Safety, Race Conditions & Concurrency, LLM Output Trust Boundary, Shell Injection, Enum & Value Completeness.

Also apply the remaining INFORMATIONAL categories that are still in the checklist (Async/Sync Mixing, Column/Field Name Safety, LLM Prompt Issues, Type Coercion, View/Frontend, Time Window Safety, Completeness Gaps, Distribution & CI/CD).

**Enum & Value Completeness requires reading code OUTSIDE the diff.** When the diff introduces a new enum value, status, tier, or type constant, use Grep to find all files that reference sibling values, then Read those files to check if the new value is handled. Shared-code analysis also requires reading related callers outside the diff; keep findings anchored to changed code.

**Search-before-recommending:** When recommending a fix pattern (especially for concurrency, caching, auth, or framework-specific behavior), research through Aside (Web research runs in Aside, above):
- Verify the pattern is current best practice for the framework version in use
- Check if a built-in solution exists in newer versions before recommending a workaround
- Verify API signatures against current docs (APIs change between versions)

```bash
_EG="$HOME/<agent-config-dir>/gstack/bin/gstack-egress-lib.sh"; [ -r "$_EG" ] && . "$_EG"; _aside_exec() { if command -v _gstack_egress_run >/dev/null 2>&1; then _gstack_egress_run open aside-agent aside.com aside-exec "user invoked this skill" --no-payload aside exec "$@"; else aside exec "$@"; fi; }
_aside_exec "Search the web for {framework} {version} {pattern} current best practice and whether a built-in replaces it. Read-only: do not sign in, submit, or change anything. Reply with up to 5 bullets, each with its source URL, then stop."
```

Takes seconds, prevents recommending outdated patterns. If the Aside check did not print `READY`, use the WebSearch tool when the host provides it; with neither, note it and proceed with in-distribution knowledge.

Follow the output format specified in the checklist. Respect the suppressions — do NOT flag items listed in the "DO NOT flag" section.

### Shared-code opportunities (core pass)

Run this check on every diff, including fewer than 50 changed lines and hosts without Review Army. Review the changed code and related unchanged callers using the shared rubric below. Do not run the standalone history/PR sweep or impose candidate quotas. At least one verified authored location must be changed in this diff, and at least two actual authored source locations must need the shared behavior; added or uncommitted source qualifies, invented future callers do not. Trace generated copies to their authored templates/resolvers and exclude generated and third-party copies from evidence and savings.

### Shared-code evaluation rubric

- **Prove the callers.** Require at least two verified, first-party authored source
  locations, with functions and lines. Actual added or uncommitted source qualifies.
  Only an engineering-plan review may use proposed callers; label those assumptions
  and distinguish them from existing source. Similar names or formatting alone do
  not establish equivalent behavior. Generated and third-party copies cannot qualify
  as callers or contribute savings. Follow generated copies back to authored
  templates/resolvers. Existing dependencies remain valid reuse targets.
- **Reuse before extracting.** Inspect existing libraries and helpers first. Compare
  behavior, inputs, outputs, error handling, side effects, security requirements,
  dependencies, and deployment/runtime boundaries. Preserve differences callers need;
  do not bridge languages or isolated deployments without a practical shared contract.
- **Keep the helper small.** Name its destination and contract, the callers to migrate,
  and the smallest adoption sequence. Avoid option-heavy helpers and coupling unrelated
  components. Point to existing tests or established use, specify shared-contract and
  caller-integration coverage, and describe the blast radius of a shared failure.
- **Account for the whole change.** Name removed blocks and their replacements. Show
  estimated implementation lines removed, added, and saved separately from total lines
  removed, added, and saved including tests and integration. Savings = removed - added.
  Count moved code on both sides, exclude generated/vendor lines, use ranges when
  uncertain, and do not count overlapping removals twice across opportunities. State
  when tests or integration may make the total change grow.
- **Rank useful changes.** Favor reliability gains and total net savings, then low
  adoption and testing risk. Prefer proven code used by several callers. Use recent
  activity to break ties between comparable benefits, not as evidence by itself.
  Explain choices centered on older code. Reject similarities with incompatible
  contracts and opportunities whose benefits do not justify the abstraction.

The core pass owns optional extraction advice. Present only worthwhile, supported proposals; zero is valid. For each proposal, show the changed anchor and other verified callers, smallest helper/destination, preserved differences, compatibility tests, shared-failure risk, and estimated implementation and total removed/added/saved lines from named blocks. Use `"category":"shared-libs","severity":"INFORMATIONAL","advisory":true`, retain `evidence_paths` (all authored supporting paths) and `helper_target:{"path":"...","symbol":"..."}`. When reusing an existing helper, include its authored path in `evidence_paths` so its contract and raw bytes participate in revalidation; a not-yet-created helper belongs only in `helper_target`. Deduplicate equivalent proposals and overlapping savings. Existing-helper reuse is preferable when compatible.

**Identity before merge or suppression:** Compute the structural fingerprint through the installed `sharedLibsFingerprint` helper, never write model-generated hash text. Feed the finding as literal JSON on stdin (replace the example values; keep the quoted delimiter), not interpolated shell code:

```bash
GSTACK_SHARED_LIB=~/<agent-config-dir>/gstack/lib/review-evidence.ts
bun -e 'const { sharedLibsFingerprint } = await import(process.argv[1]); const value = sharedLibsFingerprint(JSON.parse(await Bun.stdin.text())); if (!value) process.exit(1); console.log(value);' "$GSTACK_SHARED_LIB" <<'GSTACK_SHARED_LIBS_JSON'
{"evidence_paths":["src/caller-a.ts","src/caller-b.ts"],"helper_target":{"path":"src/shared.ts","symbol":"sharedHelper"}}
GSTACK_SHARED_LIBS_JSON
```

Use the returned fingerprint; malformed/missing metadata has no reusable identity and must be revalidated. A real defect in the same code remains a normal defect with its own evidence and Fix-First handling. An optional extraction must never suppress, downgrade, or replace that defect, even if they share a supplied fingerprint or an extraction was previously skipped.
