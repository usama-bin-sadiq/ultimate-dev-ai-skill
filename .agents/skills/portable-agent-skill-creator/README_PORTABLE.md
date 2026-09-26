# Portable Skill Creator

A provider-neutral skill for authoring, validating, evaluating, benchmarking,
and improving agent skills.

## Requirements

Python 3.9+ and nothing else. PyYAML is used when present; a built-in
frontmatter parser takes over when it is not. No agent CLI, browser, network,
or display is required to validate, package, or run the test suite.

## Runtime adapters

Adapters are data, not code. The registry lives in `references/adapters.json`;
adding an agent CLI means adding an entry there.

```bash
python3 scripts/agent_runner.py list-runtimes
```

Probes `PATH` and reports which registered CLIs are installed, with a version
and a confidence marker (`documented`, `community`, or absent for a bare
name). Registered out of the box: Claude Code, OpenCode, Codex, Gemini CLI,
Cursor, Qwen Code, GitHub Copilot CLI, `llm`, `mods`, `aichat`, Crush, Amp,
Aider, Goose, Factory Droid, OpenHands, Plandex, and Fabric.

Anything not listed works through the escape hatch — any command that accepts a
prompt from argv or stdin, including MCP hosts and in-house agents:

```bash
python3 scripts/agent_runner.py --agent custom --command 'my-agent run' --prompt "hello"
python3 scripts/agent_runner.py --agent custom --command 'my-agent run' --prompt "hello" --dry-run
```

`--dry-run` prints the exact argv without invoking anything, which is how to
verify an adapter you have not used before. `--agent auto` selects the first
installed CLI in preference order and cannot be combined with `--command`.

## Skill format

The Agent Skills convention: YAML frontmatter with `name` and `description`,
followed by instructions and optional `references/`, `scripts/`, `evals/`,
`agents/`, and `assets/`. Installation and discovery directories differ per
runtime, so this bundle does not hard-code one vendor's path.

## Evaluation

`scripts/grade.py` decides objective assertions deterministically. Assertions
of type `manual` are recorded as undecided and excluded from the pass rate, so
a subjective judgment can neither inflate nor deflate a score.

Trigger detection is kept separate from task performance. A runtime may
discover a skill and not follow it. With no detector configured,
`trigger_observed` is `null` and no precision or recall is reported; an
unmeasured trigger rate is not a zero.

Metrics that were never collected stay `null` with `measured: 0` throughout.
Nothing is estimated or inferred.

## Layout

```text
SKILL.md                    the workflow
evals/evals.json            this bundle's own eval set
references/adapters.json    runtime registry
references/schemas.md       every file this skill reads or writes
scripts/                    the executable workflow
agents/                     optional review roles (grader, comparator, analyzer)
eval-viewer/                static or served results review
assets/eval_review.html     interactive eval-set authoring
tests/test_bundle.py        the suite below
```

## Verifying

```bash
python3 tests/test_bundle.py
```

Runs on a bare Python 3 install with no agent CLI, no PyYAML, no network, and
no display. Every end-to-end path is exercised through a fake agent rather
than a real model call.
