# Trigger Mechanism

How Ultimate-Dev actually gets activated, why auto-discovery is not enough, and
what to do when it does not fire.

## The problem this solves

A skill that depends on the host matching its description against a request
fails **silently**. Nothing errors. The agent simply starts working, and the
skill's discipline never appears in the output. From the outside it looks like
the model ignored instructions, when in fact the skill was never loaded.

This is most likely on a very large prompt, for three reasons:

1. A 3,000-word specification is a weak match target compared with the short
   requests a description is tuned for.
2. Such a prompt usually opens by assigning its own role, for example
   *"You are an autonomous senior game-development agent."* That is a direct
   collision with the skill's own identity claim, and the prompt's role is more
   proximate, so it wins.
3. A large prompt often already contains the workflow the skill would impose.
   Loading the skill then changes nothing observable, so nobody notices it
   failed to load.

Point 3 matters: when this happens the model is behaving correctly. The prompt
authorized exactly the behavior the skill would have added ceremony around.

## The four channels, strongest first

| Channel | Reliability | How to use it |
|---|---|---|
| 1. Tool root instruction file | **Highest** — the tool reads it every session | `provision-host-instructions.py`, run once per project |
| 2. Explicit invocation | Deterministic | `@ultimate-dev <task>` or `/ultimate-dev <task>` |
| 3. Skill tool / manual load | Deterministic | Load the skill by name in the host UI or skill tool |
| 4. Auto-discovery by description | Best effort | Say `@ultimate-dev` when you need certainty |

Use channel 1 as the default. It is the only one that needs nothing from the
user and nothing from the host's matcher.

## Channel 1: provision the tool's own instruction file

Each supported tool reads one instruction file from the project root, and that
file is loaded every session. Writing the skill's operating method there makes
activation reliable.

```bash
# See which tools this project looks like, and whether the file exists
python ultimate-dev/scripts/provision-host-instructions.py --project . --detect

# Write it
python ultimate-dev/scripts/provision-host-instructions.py --project .

# Target a specific tool when detection is ambiguous
python ultimate-dev/scripts/provision-host-instructions.py --project . --tool claude-code

# Verify, without writing (exit 1 when absent)
python ultimate-dev/scripts/provision-host-instructions.py --project . --check
```

Detection order is deliberate: a **live environment variable** outranks a
**marker file**. A marker file only means the tool was used at some point, so a
project carrying both `CLAUDE.md` and `AGENTS.md` still resolves to the host you
are actually running under.

| Tool | File written |
|---|---|
| claude-code | `CLAUDE.md` |
| codex | `AGENTS.md` |
| opencode | `AGENTS.md` |
| cursor | `.cursorrules` |
| windsurf | `.windsurfrules` |
| cline | `.clinerules` |
| copilot | `.github/copilot-instructions.md` |
| gemini | `GEMINI.md` |
| generic | `AGENTS.md` |

### Safety properties

The provisioner is deliberately conservative, because it writes into files a
user may already maintain:

- Content **outside** the markers is never read for rewriting and never changed.
- The block is delimited by `<!-- BEGIN ULTIMATE-DEV -->` and
  `<!-- END ULTIMATE-DEV -->`.
- Re-running replaces only what is between the markers, so your own edits
  elsewhere in the file always survive.
- A missing file is created; an existing one is appended to.
- An unknown `--tool` is reported as an error rather than guessed.

Verified by `tests/test_host_instruction_provisioning.py`, including the case
that a user edit made before provisioning survives a later re-provision.

## Precedence: persona versus method

When a prompt assigns a role, **keep the persona and apply the method.**

The persona is the user's to set. The discipline is the skill's contribution,
and it is what makes the output trustworthy: a stated envelope, a real plan,
actual verification, and honest reporting of what could not be run.

An embedded role prompt or an embedded workflow in the request is never a reason
to skip the envelope, the plan, or the evidence.

## When the skill was never loaded

If channel 4 failed, say so in one line and offer the explicit invocation:

```text
Ultimate-Dev is not active in this session. Say `@ultimate-dev <task>` to run
this under the full lifecycle, or run
`python ultimate-dev/scripts/provision-host-instructions.py --project .` to make
it automatic from now on.
```

Failing loudly is better than failing quietly. The alternative — noticing that
the skill did not load and silently continuing anyway — is the behavior this
document exists to prevent.

## Diagnosing a trigger failure

1. **Is the skill installed and current?** A stale install keeps old behavior
   regardless of what the repository contains.

   ```bash
   cat ~/.agents/skills/ultimate-dev/VERSION   # installed
   cat VERSION                                  # repository
   ```

2. **Is the root instruction file provisioned?**

   ```bash
   python ultimate-dev/scripts/provision-host-instructions.py --project . --check
   ```

3. **Did the host pick the right file?** Run `--detect` and compare the
   selection with the tool you are actually using.

4. **Did the session cache the skills?** Reinstalling rewrites the skill
   directory; restart the host so its cache is rebuilt.

5. **Did the request assign its own role?** If so, expect the method to be
   softened unless the skill is active, and use an explicit invocation.

## Relationship to the rest of the package

The provisioning contract is `contracts/host-instruction-provisioning.yaml`. It
is a description of behavior, not a runtime requirement: nothing here needs
Python at request time, and the provisioned text is plain Markdown any host can
read. If you would rather manage the file by hand, write the same content
yourself; the provisioner is a convenience, not a dependency.
