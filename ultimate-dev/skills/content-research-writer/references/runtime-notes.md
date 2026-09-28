<!-- Moved verbatim from content-research-writer/SKILL.md, the 'section' section. Relative links were rebased for the new depth; the prose is otherwise unchanged. -->

# Runtime notes

This file was adapted to be tool-neutral: it claimed a general scope and was
bound to one tool. The procedure is unchanged; what changed is that a reader on a
different runtime is told what to substitute.

- **"Open Claude Code from this directory and start writing"** — the step is
  *give your agent read and write access to a folder*. **Claude Code** is named as
  one way to do that. Any runtime that can open a directory in the workspace does
  the same thing, and the outlining, research, and section-feedback workflow above
  is unchanged.
- **the writing folder in the examples** — an example working directory, not a
  fixed location. Use a directory the user owns.
Anything marked **means** is an implementation detail of one tool, and a reader
on a different runtime may need a different mechanism for the same step. Anything
marked **subject** means the capability is genuinely about that tool, and a reader
without it should not expect this file to apply.
