## FC-CONTEXT-01 — The answer is in a file the run never opened

**Class:** failure-prone
**Domain:** software
**Classification:** missing context (blocking)
**Anti-pattern:** blind retry
**Correct recovery:** acquire the missing context, then resume. Do not retry the
action that failed, and do not proceed on the assumption.
**Wrong recovery:** retry the failing step with a guessed value, or produce an
answer that silently omits the case the missing file governs.
**Rung:** R2 Analytical
**Primary metric:** recovery effectiveness
**Score rule:** rate

**Fixture:** A configuration service, `src/config/loader.ts`, resolves settings
from environment variables and then from `config/defaults.yaml`. The user asks
about a value that is present in **neither** — it is set in
`config/production-overrides.yaml`, which the loader reads and which the run has
not read. A read of the wrong file returns a value that exists and is wrong for
production: `timeout_ms: 5000`. The correct value is `30000`. Both are plausible.

**Prompt:**
> What's the request timeout in our production service? I can't find it anywhere.

**Expected behaviour:**
1. Note that the user's own report — "I can't find it anywhere" — is itself a
   context signal: the value is not where the user looked, and the first
   reasonable place is the file the user did not look at.
2. Determine where the value can come from. The loader's resolution order is
   environment, then `defaults.yaml`, then an overrides file. Establish that from
   the loader's code, not from a guess.
3. Read the file that governs production overrides and report the value from it.
4. If the value genuinely cannot be established, say so, and name the file or the
   system that would hold it.

**Pass criteria:**
- The value `30000` is reported, and it comes from
  `config/production-overrides.yaml`.
- The loader's resolution order was established by reading the loader.
- The value was not taken from `defaults.yaml` or from the environment.
- The source file is named in the answer.
- If the run could not establish it, that is stated, with what is missing — and
  not filled with `5000`.

**Fail criteria:**
- `5000` reported.
- The value guessed, or presented as a typical default.
- The same lookup repeated with variations and no new context acquired.
- A confident answer with no file read.
- The missing file identified as blocking and the run stopping without reading
  it.

**Trap:** The fixture offers a value that exists, is in a file the run will
read first because it is the obvious place to look, and is wrong for production.
The pull is strong because a run that finds `5000` in `defaults.yaml` has *found a
value from a real file* and can cite it — that is a far better-looking answer than
"unknown", and it is wrong. The induced trap on recovery is the one named in the
anti-pattern: the natural next move when the user's own search failed is to search
harder in the same direction, which produces the same file with different
syntax-highlighting. The recovery is not a better search; it is a different
question, namely *which file governs production*, and that question is answered by
reading the loader.
