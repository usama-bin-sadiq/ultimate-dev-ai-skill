## DM-SECURITY-02 — No lockfile integrity, how bad is it really?

**Class:** medium
**Domain:** security
**Kernel specialisation:** none
**Rung:** R2 Analytical
**Scale:** L2
**Primary metric:** task success, with severity grounded in the repo's actual state
**Score rule:** rate

**Fixture:** A Node monorepo. `package.json` declares 214 dependencies; 187 resolve
to a `package-lock.json` with integrity hashes. **27 resolve to no lockfile entry**,
because they are installed from a private registry with no lockfile support. Of
those 27, **3 are actually imported in `src/`** — `internal-metrics`,
`partner-sftp`, and `legacy-report` — and the other 24 are dev-only or unused. The
CI pipeline runs `npm ci` on a cache key that does not include the lockfile hash.
No package is installed with `--ignore-scripts`. A security scanner is enabled and
reports "27 unpinned dependencies" at high severity.

**Prompt:**
> Our scanner says we have 27 unpinned dependencies and it's high severity. How
> risky is this actually?

**Expected behaviour:**
1. Triage to R2. The question is to assess a scanner finding against the actual
   repository, which is a bounded analysis with a determinate answer.
2. Enumerate what the finding is counting, and separate it into what matters:
   27 unpinned, of which 3 are imported in `src/` and reach production paths, and 24
   are dev-only or unused. The severity that matters is attached to the 3, and the
   scanner cannot see that distinction.
3. Identify what actually raises the risk above "a supply-chain vulnerability
   exists": `npm ci` on a cache key that does not include the lockfile hash means
   the same package version can be served from cache after a registry compromise
   without any lockfile change to notice. That is the specific, actionable
   amplifier, and it is not what the scanner reported.
4. Note the private registry as a concentration of risk: 27 packages from one
   registry is a single point of failure that the per-package count hides.
5. Give a proportionate, ranked answer: the 3 production-path packages first, with
   what to do about each; the registry and the CI cache key second, since fixing
   those addresses all 27 at once; the 24 last, and possibly not at all.
6. Do not dismiss the finding. Three real production dependencies without integrity
   pinning is a genuine finding, and the correct answer is "the scanner's count is
   right and its severity is not attached to the right three".

**Pass criteria:**
- The 27 / 3 / 24 split is stated, and the 3 production-path packages are
  identified by name.
- The CI cache key not including the lockfile hash is identified as the amplifier.
- The private registry's role as a single point of failure is noted.
- Recommendations are ranked by the 3 / registry / 24 structure, not by the
  scanner's severity.
- The finding is not dismissed; the discrepancy between the count and the severity
  is explained.
- No claim that any specific package is malicious or vulnerable beyond what the
  repo shows.

**Fail criteria:**
- "27 high-severity dependencies" accepted as the risk.
- The finding dismissed as a false positive.
- The 3 production-path packages not distinguished from the 24.
- The CI cache key issue not identified.
- A blanket recommendation to add integrity pinning to all 27 with no prioritisation
  and no note that the registry does not support lockfiles.
- A specific CVE claimed for a specific package without a source.
- A dependency-audit skill or agent created for a single assessment.

**Trap:** A scanner output is a machine finding, and machine findings arrive with
severity attached, and the default posture towards a high-severity security alert is
to treat the severity as the finding. The whole content of this case is that the
severity is a function of the count, not of the exposure — 27 sounds like 27
production risks and is 3. A run that accepts the scanner's framing produces a
sensible, alarming, wrong report. The second trap is the one that looks like
thoroughness: reading all 27, checking each against advisories, and reporting
individually. That is the most expensive possible use of the analysis, it buries
the three that matter, and it still misses the actual amplifier, which is not a
package at all but a CI cache key that lets a compromised package persist without
a lockfile diff to show for it.
