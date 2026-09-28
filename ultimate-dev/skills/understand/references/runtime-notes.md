<!-- Moved verbatim from understand/SKILL.md, the 'section' section. Relative links were rebased for the new depth; the prose is otherwise unchanged. -->

# Runtime notes

This file was adapted to be tool-neutral: it claimed a general scope and was
bound to one tool. The procedure is unchanged; what changed is that a reader on a
different runtime is told what to substitute.

- **`pnpm install --frozen-lockfile` in a plugin workspace, then
  `pnpm --filter … build`** — the analysis code is a bundled Node workspace that
  has to be built before it runs. That is the toolkit's own build step, not a
  property of the knowledge-graph method: a reader who already has a code-analysis
  tool substitutes it and keeps the graph output contract.
Anything marked **means** is an implementation detail of one tool, and a reader
on a different runtime may need a different mechanism for the same step. Anything
marked **subject** means the capability is genuinely about that tool, and a reader
without it should not expect this file to apply.
