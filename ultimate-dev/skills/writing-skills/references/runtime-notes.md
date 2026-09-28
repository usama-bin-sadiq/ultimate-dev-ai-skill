<!-- Moved verbatim from writing-skills/SKILL.md, the
     'runtime-notes' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Runtime notes

This file was adapted to be tool-neutral: it claimed a general scope and was
bound to one tool. The procedure is unchanged; what changed is that a reader on a
different runtime is told what to substitute.

- `<project-root>` — the repository root. 1 machine-specific path(s) replaced.
- `<agent-config-dir>` — wherever this runtime keeps its configuration. Not a fixed location.
- `<agent-instructions>` — the file this runtime reads for standing instructions. Names differ per runtime and none is assumed.
- **claude-cli** — means. One tool's way of doing a step a different runtime may do another way.
Anything marked **means** is an implementation detail of one tool, and a reader
on a different runtime may need a different mechanism for the same step. Anything
marked **subject** means the capability is genuinely about that tool, and a reader
without it should not expect this file to apply.

Each file below is loaded on demand, not at triage. 28 file(s):

- `references/anti-patterns.md` — prose
- `references/bulletproofing-skills-against-rationalization.md` — prose
- `references/code-examples.md` — prose
- `references/common-mistakes.md` — prose
- `references/common-rationalizations-for-skipping-testing.md` — prose
- `references/core-pattern-for-techniques-patterns.md` — prose
- `references/directory-structure.md` — prose
- `references/discovery-workflow.md` — prose
- `references/file-organization.md` — prose
- `references/flowchart-usage.md` — prose
- `references/implementation.md` — prose
- `references/overview.md` — prose
- `references/quick-reference.md` — prose
- `references/real-world-impact-optional.md` — prose
- `references/red-flags-stop-and-start-over.md` — prose
- `references/red-green-refactor-for-skills.md` — prose
- `references/runtime-notes.md` — prose
- `references/skill-creation-checklist-tdd-adapted.md` — prose
- `references/skill-discovery-optimization-sdo.md` — prose
- `references/skill-md-structure.md` — prose
- `references/skill-types.md` — prose
- `references/stop-before-moving-to-next-skill.md` — prose
- `references/tdd-mapping-for-skills.md` — prose
- `references/testing-all-skill-types.md` — prose
- `references/the-iron-law-same-as-tdd.md` — prose
- `references/what-is-a-skill.md` — prose
- `references/when-to-create-a-skill.md` — prose
- `references/when-to-use.md` — prose
