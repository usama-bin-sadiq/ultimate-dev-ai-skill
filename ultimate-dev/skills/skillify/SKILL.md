---
name: skillify
preamble-tier: 2
version: 1.0.0
description: Codify the most recent successful /scrape flow into a permanent browser-skill on disk.
allowed-tools:
  - Bash
  - Read
  - Write
  - AskUserQuestion
triggers:
  - skillify
  - codify this scrape
  - save this scrape
  - make this permanent
neutralised: tool-specific paths and single-runtime invocations replaced
---
<!-- AUTO-GENERATED from SKILL.md.tmpl — do not edit directly -->
<!-- Regenerate: bun run gen:skill-docs -->


## When to invoke this skill

Future /scrape calls with the same intent run
the codified script in ~200ms instead of re-driving the page. Walks
back through the conversation, synthesizes script.ts + script.test.ts
+ fixture, runs the test in a temp dir, and asks before committing.
Use when asked to "skillify", "codify", "save this scrape", or
"make this permanent".

## Preamble (run first)

Detail moved to `references/preamble-run-first.md`.

## Plan Mode Safe Operations

In plan mode, allowed because they inform the plan: `$B`, `$D`, `codex exec`/`codex review`, temp prompts, writes to `~/.gstack/`, writes to the plan file, and `open` for generated artifacts.

## Skill Invocation During Plan Mode

If the user invokes a skill in plan mode, the skill takes precedence over generic plan mode behavior. **Treat the skill file as executable instructions, not reference.** Follow it step by step starting from Step 0; any AskUserQuestion the skill fires is the workflow operating within plan mode, not a violation of it — and a skill whose instructions resolve a question themselves (e.g. a plan-mode auto-select) may legitimately not ask it. AskUserQuestion (any variant — `mcp__*__AskUserQuestion` or native; see "AskUserQuestion Format → Tool resolution") satisfies plan mode's end-of-turn requirement. If AskUserQuestion is unavailable or a call fails, follow the AskUserQuestion Format failure fallback: `headless` → BLOCKED; `interactive` → the prose fallback (also satisfies end-of-turn). At a STOP point, stop immediately. Do not continue the workflow or call ExitPlanMode there. Commands marked "PLAN MODE EXCEPTION — ALWAYS RUN" execute. Call ExitPlanMode only after the skill workflow completes, or if the user tells you to cancel the skill or leave plan mode.

If `PROACTIVE` is `"false"`, do not auto-invoke or proactively suggest skills. If a skill seems useful, ask: "I think /skillname might help here — want me to run it?"

If `SKILL_PREFIX` is `"true"`, suggest/invoke `/gstack-*` names. Disk paths stay `~/<agent-config-dir>/gstack/[skill-name]/SKILL.md`.

## AskUserQuestion Format

Detail moved to `references/askuserquestion-format.md`.

## Artifacts Sync (skill start)

The skill-start output above already ran artifacts sync. Act on its lines:
GBrain hint text (if present) tells you when to prefer `gbrain` over Grep;
`ARTIFACTS_SYNC:` reports sync health (`off`, `mode=... | queue=N`,
`remote-mode`, or a restore hint naming `gstack-brain-restore`).

The one-time privacy stop-gate (artifacts-sync consent) arrives as a
`GSTACK_INSTRUCTION` block from skill-start when consent is actually pending
— fire it via AskUserQuestion exactly as the block instructs.

## Model-Specific Behavioral Patch (claude)

Detail moved to `references/model-specific-behavioral-patch-claude.md`.

## Voice

Detail moved to `references/voice.md`.

## Context Recovery

Detail moved to `references/context-recovery.md`.

## Writing Style (skip entirely if `EXPLAIN_LEVEL: terse` appears in the preamble echo OR the user's current message explicitly requests terse / no-explanations output)

Detail moved to `references/writing-style-skip-entirely-if-explain-level-terse-appears-in-the-preamble-echo-or-the-user-s-current-message-explicitly-requests-terse-no-explanations-output.md`.

## Completeness Principle — Boil the Ocean

AI makes completeness cheap, so the complete thing is the goal. Recommend full coverage (tests, edge cases, error paths) — boil the ocean one lake at a time. The only thing out of scope is genuinely unrelated work (rewrites, multi-quarter migrations); flag that as separate scope, never as an excuse for a shortcut.

When options differ in coverage, include `Completeness: X/10` (10 = all edge cases, 7 = happy path, 3 = shortcut). When options differ in kind, write: `Note: options differ in kind, not coverage — no completeness score.` Do not fabricate scores.

## Confusion Protocol

For high-stakes ambiguity (architecture, data model, destructive scope, missing context), STOP. Name it in one sentence, present 2-3 options with tradeoffs, and ask. Do not use for routine coding or obvious changes.

## Claimed Limitations Need Evidence

A claimed limitation or requirement ("the API can't do this", "X requires a credential", "that's impossible on this platform") is a material claim. State one only with the verbatim error, the documented statement, or a live probe in hand — pattern-matching a failure to a familiar story is not evidence. When a cheap probe settles the question, run it BEFORE asking the user anything or declaring a step blocked.

## Context Health (soft directive)

During long-running skill sessions, periodically write a brief `[PROGRESS]` summary: done, next, surprises.

If you are looping on the same diagnostic, same file, or failed fix variants, STOP and reassess. Consider escalation or /context-save. Progress summaries must NEVER mutate git state.

## Question Tuning (skip entirely if `QUESTION_TUNING: false`)

Detail moved to `references/question-tuning-skip-entirely-if-question-tuning-false.md`.

## Completion Status Protocol

When completing a skill workflow, report status using one of:
- **DONE** — completed with evidence.
- **DONE_WITH_CONCERNS** — completed, but list concerns.
- **BLOCKED** — cannot proceed; state blocker and what was tried.
- **NEEDS_CONTEXT** — missing info; state exactly what is needed.

Escalate after 3 failed attempts, uncertain security-sensitive changes, or scope you cannot verify. Format: `STATUS`, `REASON`, `ATTEMPTED`, `RECOMMENDATION`.

## Operational Self-Improvement

Detail moved to `references/operational-self-improvement.md`.

## Telemetry (run last)

Detail moved to `references/telemetry-run-last.md`.

## Plan Status Footer

Detail moved to `references/plan-status-footer.md`.

## Iron contract — never write a half-broken skill to disk

Skills are user-trust artifacts. A broken skill in `$B skill list` makes
agents reach for the wrong tool and erodes confidence. This skill writes
to a temp dir, runs the auto-generated test there, and only renames into
the final tier path on (a) test pass + (b) explicit user approval. On
either failure, the temp dir is removed entirely. There is no "almost
shipped" state.

---

## Step 1 — Provenance guard (D1)

Walk back through the conversation, **at most 10 agent turns**, looking
for the most recent `/scrape` invocation that:

- Was bounded (you can identify the user's intent line and the trailing
  JSON the prototype produced)
- Produced a JSON result the user did not subsequently invalidate
  (e.g., did not say "that's wrong", did not ask you to retry)

If you cannot find one, refuse with exactly this message:

> "No recent /scrape result found in this conversation. Run /scrape
> <intent> first, then say /skillify."

Stop. Do not synthesize from chat fragments. Do not synthesize from a
match-path /scrape result (matched skills are already codified — there's
nothing to skillify).

If you find a candidate but the user is currently three turns past it
discussing something unrelated, ask once before proceeding:

> "The last successful /scrape was '<intent line>' a few turns back.
> Skillify that one?"

A "yes" lets you continue. Anything else: refuse with the message above.

## Step 2 — Propose name + triggers

From the prototype intent, extract:

- A short skill name: lowercase letters/digits/dashes, ≤32 chars,
  starts with a letter, no consecutive dashes. E.g.,
  `lobsters-frontpage`, `gh-issue-list`, `pypi-package-stats`.
- 3–5 trigger phrases the agent should match against in future `/scrape`
  calls. Mix the canonical phrase ("scrape lobsters frontpage") with
  paraphrases ("top posts on lobste.rs", "lobsters front page").
- The host (just the hostname, e.g. `lobste.rs`).

Then **AskUserQuestion** to confirm:

```
D<N> — Skill name + tier
Project/branch/task: codifying /scrape "<intent>" as a browser-skill.
ELI10: Pick a short name we'll use to find this skill next time you say
something similar. Pick a tier — global means every project on this
machine sees it, project means just this repo.
Stakes if we pick wrong: bad name buries the skill in $B skill list;
wrong tier means future projects can't find it (or can find it when you
didn't want them to).
Recommendation: A — <proposed-name> at global tier — most scrape skills
generalize across projects.
Note: options differ in kind, not coverage — no completeness score.
A) Keep "<proposed-name>" at global tier — ~/.gstack/browser-skills/<proposed-name>/  (recommended)
B) Keep "<proposed-name>" but at project tier — <project>/.gstack/browser-skills/<proposed-name>/
C) Rename it (free-form — say the new name)
```

**Tier-shadowing check.** Before showing the question, run `$B skill list`
and check for an existing skill at the same name. If found, add to the
question:

> "Note: a <tier> skill named '<name>' already exists. Picking the same
> name at a higher tier (project > global > bundled) shadows it; picking
> the same tier collides and will be refused at write time. Pick a
> different name to coexist."

## Step 3 — Synthesize `script.ts` (D2)

**Use only the final-attempt `$B` calls** that produced the JSON the
user accepted, plus the user's intent string. Drop:

- Failed selector attempts (the four selectors you tried before the
  working one)
- Unrelated `$B` commands from earlier turns
- All conversation prose, summaries, your own reasoning

The script imports the SDK
and exports a parser function so `script.test.ts` can
exercise it against the bundled fixture without spinning up the daemon.

Mirror the bundled reference at `browser-skills/hackernews-frontpage/script.ts`:

```ts
import { browse } from './_lib/browse-client';

export interface Item { /* one row of the JSON output */ }
export interface Output { items: Item[]; count: number; }

const TARGET_URL = '<the URL the prototype used>';

export function parseFromHtml(html: string): Item[] {
  // Pure function: HTML in, parsed Item[] out. No $B calls.
  // Future fixture-replay tests call this directly.
}

if (import.meta.main) { await main(); }

async function main(): Promise<void> {
  await browse.goto(TARGET_URL);
  const html = await browse.html();
  const items = parseFromHtml(html);
  const output: Output = { items, count: items.length };
  process.stdout.write(JSON.stringify(output) + '\n');
}
```

The parser MUST be a pure function. If your prototype used multiple `$B`
calls (e.g., goto + click "Next" + html), keep all of them in `main()`
but extract the parsing into pure helpers. The fixture-replay tests in
step 5 only exercise the pure parts.

## Step 4 — Capture the fixture

```bash
$B goto "<TARGET_URL>"
$B html > /tmp/skillify-fixture-$$.html
```

The fixture filename inside the staged dir is
`fixtures/<host-with-dashes>-<YYYY-MM-DD>.html`, where the date is today.
E.g. `fixtures/lobste-rs-2026-04-27.html`.

Read the file you wrote, store its contents in a variable, and use it
when staging in step 7.

## Step 5 — Write `script.test.ts`

Mirror `browser-skills/hackernews-frontpage/script.test.ts`. The test
must include at least one ★★ assertion — parsed output has the expected
shape AND non-empty key fields — not a smoke ★ assertion. Smoke tests
that only check `parseFromHtml` doesn't throw are insufficient.

```ts
import { describe, it, expect } from 'bun:test';
import * as fs from 'fs';
import * as path from 'path';
import { parseFromHtml } from './script';

describe('<name> parser', () => {
  const fixturePath = path.join(import.meta.dir, 'fixtures', '<host>-<date>.html');
  const html = fs.readFileSync(fixturePath, 'utf-8');
  const items = parseFromHtml(html);

  it('returns at least one item from the bundled fixture', () => {
    expect(items.length).toBeGreaterThan(0);
  });

  it('every item has the required shape', () => {
    for (const item of items) {
      expect(typeof item.<keyfield>).toBe('<keytype>');
      // ... assert on every required field
    }
  });
});
```

## Step 6 — Resolve the canonical SDK path + read it

The canonical SDK lives at `<gstack-install>/browse/src/browse-client.ts`.
The bundled-skill loader walks the install tree to find it; mirror that.

Resolve the gstack install dir. Two reliable signals (in order):

1. The bundled `hackernews-frontpage` skill — look at its tier path from
   `$B skill list` (the `bundled` row). The skill dir is
   `<gstack-install>/browser-skills/hackernews-frontpage/`, so the install
   dir is two `dirname` calls above its `_lib/browse-client.ts`.
2. The active gstack skills install at `~/<agent-config-dir>/gstack/`. Read
   the symlink target if it's a symlink, otherwise use the path directly.

Example (run as Bun, not bash, to avoid shell-redirect parsing issues):

```ts
import * as fs from 'fs';
import * as os from 'os';
import * as path from 'path';

function resolveSdkPath(): string {
  const candidates = [
    path.join(os.homedir(), '.claude', 'skills', 'gstack', 'browse', 'src', 'browse-client.ts'),
    // Add other install-dir candidates if your environment differs.
  ];
  for (const c of candidates) {
    try {
      const real = fs.realpathSync(c);
      if (fs.existsSync(real)) return real;
    } catch {}
  }
  throw new Error('Could not resolve canonical browse-client.ts');
}

const sdkContents = fs.readFileSync(resolveSdkPath(), 'utf-8');
```

Read the SDK contents into a variable. The staging step writes it as
`_lib/browse-client.ts` byte-identical to the canonical. Phase 1 decision
#4 — each skill is fully self-contained, no version drift possible.

## Step 7 — Stage the skill (D3 atomic write)

Use the helper at `browse/src/browser-skill-write.ts`. Construct an inline
TypeScript snippet (or shell out to a small Bun one-liner) that calls:

```ts
import { stageSkill } from '<gstack-install>/browse/src/browser-skill-write';

const stagedDir = stageSkill({
  name: '<name>',
  files: new Map([
    ['SKILL.md', skillMd],
    ['script.ts', scriptTs],
    ['script.test.ts', scriptTestTs],
    ['_lib/browse-client.ts', sdkContents],
    ['fixtures/<host>-<date>.html', fixtureHtml],
  ]),
});
console.log(stagedDir);
```

The SKILL.md content for `<name>` follows the Phase 1 frontmatter
contract:

```yaml
---
name: <name>
description: <one-line, what data this returns>
host: <hostname>
trusted: false       # agent-authored skills are untrusted by default
source: agent
version: 1.0.0
args: []             # extend if your script accepts --arg key=value
triggers:
  - <phrase 1>
  - <phrase 2>
  - <phrase 3>
---

# <Name> scraper

<2-3 sentences on what the script does, what URL it hits, and what
shape of JSON it returns. NO conversation context. NO chat fragments.
This is a durable on-disk artifact — keep it tight.>

## Usage

\`\`\`
$ $B skill run <name>
{ "items": [...], "count": N }
\`\`\`
```

Capture `stagedDir` (the path returned by `stageSkill`). You'll pass it
to `$B skill test` next, then to `commitSkill` or `discardStaged`.

## Step 8 — Run `$B skill test` against the staged dir

```bash
$B skill test "<name>" --dir "<stagedDir>"
```

If `$B skill test` does not yet accept `--dir`, fall back to invoking the
test runner directly against the staged path:

```bash
( cd "<stagedDir>" && bun test script.test.ts )
```

If the test fails:

1. Read the test output. If the failure is a fixable parser bug,
   rewrite `script.ts` and `script.test.ts` (still inside the staged
   dir) and retry — at most twice. Show the diff to the user before
   each retry.
2. If still failing after two retries, OR the failure is an
   environmental issue (SDK import, daemon connection):

   ```ts
   import { discardStaged } from '<gstack-install>/browse/src/browser-skill-write';
   discardStaged('<stagedDir>');
   ```

   Report the failure to the user, show them the staged `script.ts` for
   reference, and stop. No on-disk artifact.

## Step 9 — Approval gate

Tests passed. Now ask the user before committing:

```
D<N> — Commit skill "<name>" at <resolved-tier-path>?
Project/branch/task: codified /scrape "<intent>" — tests pass against fixture.
ELI10: The script ran clean against the snapshot we captured. Saying yes
moves the staged folder into ~/.gstack/browser-skills/ where /scrape
will find it next time. Saying no removes the staged folder and nothing
lands on disk.
Stakes if we pick wrong: yes commits an artifact you have to manually rm
later if you regret it ($B skill rm <name> --global). No throws away
~30s of synthesis work.
Recommendation: A — tests passed, the script is self-contained, this is
the productivity payoff for the prototype.
Note: options differ in kind, not coverage — no completeness score.
A) Commit it (recommended)
B) Look at the script first (I'll print SKILL.md + script.ts and re-ask)
C) Discard — don't commit
```

If the user picks B, print the staged `SKILL.md` and `script.ts` (NOT
the fixture or _lib/), then re-ask the same A/B/C question (without B
this time — they already saw it).

## Step 10 — Commit (atomic) or discard

Detail moved to `references/step-10-commit-atomic-or-discard.md`.

## Step 11 — Confirm + verify

Detail moved to `references/step-11-confirm-verify.md`.

## Limits (be honest)

Detail moved to `references/limits-be-honest.md`.

## What this skill does NOT do

- Codify match-path /scrape results (matched skills are already codified)
- Codify mutating flows (those are /automate's job — Phase 2 P0)
- Run skills (that's `$B skill run` — codified skills are run via /scrape's
  match path or directly)
- Edit existing skills ($EDITOR + the skill dir is the surface — `$B skill
  show <name>` finds the path)
- Tombstone or remove ($B skill rm)

## Capture Learnings

Detail moved to `references/capture-learnings.md`.

## Runtime notes

Detail moved to `references/runtime-notes.md`.

