# Worked example: a complete handoff

A filled-in instance of the five-section template, for the invocation
`/cs:handoff "finish wiring the redaction linter and open a draft PR"`. Copy the
shape, not the content. Everything under **Artifacts** is a path or a URL; if a
line here has more than a path in it, it is in the wrong section.

Every path below belongs to the reader's own repository, not to this skill, so
none of them resolve here. That is the point of the example.

The four anti-patterns this document is shaped to avoid: no pasted diff, no
retyped PRD, no summarised commit message, no list of twenty skills.

---

# Handoff: finish the redaction linter and open a draft PR

## Goal of next session

Finish wiring `redaction_linter.py` into the save path and open a draft PR for
the handoff skill's first end-to-end pass. The linter scans a drafted handoff
for secrets and PII before the file is written, blocks the save on findings in
strict mode, and flags inline in warn mode. Finishing it means the save path
calls it, the SessionEnd reminder treats a lint failure as "no recent handoff",
and the CI job goes green.

Not in scope: the library search, the feed, and anything that publishes.

## State of play

**Done**

- Config loader reads project config, then global config, then defaults. Landed
  in `src/handoff/config_loader.py`; unit tests in
  `src/handoff/tests/test_config_loader.py` pass on `main`.
- SessionStart hook resolves the configured save location and surfaces the most
  recent handoff. Verified manually on a two-session run; no automated test yet.
- `handoff_self_check.py` flags an empty Goal, State bullets with no artifact
  reference, a missing Decisions section against a dirty tree, and an out-of-range
  skill count. It runs before the linter and writes nothing.

**In flight**

- `src/handoff/redaction_linter.py` detects API keys, OAuth and JWT tokens,
  `-----BEGIN ... PRIVATE KEY-----` blocks, `.env`-style `KEY=value` lines,
  connection strings, and email addresses. It runs; it is not yet called from
  `save_handoff()`, which is the whole of the remaining wiring. Branch
  `feature/redaction-lint-wiring` has the skeleton; do not start from `main`.

**Blocked**

- The warn-mode output format is agreed with nobody. The choice is open
  question 2 below.
- `docs/redaction-patterns.md` lists two patterns the user asked for and the
  implementation does not cover: internal URLs carrying a session id, and names
  of unrelated third parties. The list is in that file; the PR cannot claim
  coverage it does not have until this is settled.

**Verification status**

`pytest src/handoff/tests -q` green as of the last push. No end-to-end test yet:
nothing asserts that a save with a finding in it is actually refused.

## Open decisions

1. **Where does the lint run relative to writing the file?**
   Recommendation: lint the rendered Markdown in memory, then write once. A
   temp-file-then-rename dance is more code and buys nothing at these sizes.

2. **What does warn mode print?**
   Recommendation: one line per finding, `path:line: rule`, then the save
   proceeds. The alternative, writing findings into the file as comments, was
   rejected earlier because the file is read by the next agent and comments
   there are indistinguishable from content.

3. **Does a lint finding suppress the SessionEnd reminder?**
   Recommendation: yes. A handoff that was never written is not a recent
   handoff, and the reminder's purpose is to fire before context is lost.

4. **How far does the third-party-name rule go?**
   Needs a user decision. It has false positives on common nouns and no good
   general test; a name list in the config is the only version that works, and
   that is maintenance nobody has agreed to own.

## Skills to use

- **test-driven-development** — the save path needs a failing test first: a save
  that must be refused. RED before the wiring exists.
- **systematic-debugging** — the config loader's precedence is subtle, and
  question 1 above is a design question the tests will answer badly if written
  after the fact.
- **writing-skills** — the PR also updates the skill's SKILL.md prose for the new
  lint behaviour, and that text is itself a skill artifact.
- **verification-before-completion** — the PR is not done until CI is green on a
  run that actually exercised the refusal path, not just the unit tests.

## Artifacts

- Source: `src/handoff/`
- Branch: `feature/redaction-lint-wiring`
- Draft PR: not yet opened. Create it against `main` with the title
  `handoff: refuse save on redaction findings in strict mode`.
- Pattern list owed by the user: `docs/redaction-patterns.md`
- Test command: `pytest src/handoff/tests -q`
- Prior discussion this references rather than repeats: the config-loader
  decision is recorded as `ADR-0007-config-precedence`; the save-location
  question is `ISSUE-42`.

## Notes for whoever picks this up

Secrets were in the transcript while debugging the connection-string pattern.
The draft above carries no credential, and no value from the debug session
should be copied into a commit message, a test fixture, or a new handoff.
