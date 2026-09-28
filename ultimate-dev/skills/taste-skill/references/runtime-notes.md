<!-- Moved verbatim from taste-skill/SKILL.md, the 'section' section. Relative links were rebased for the new depth; the prose is otherwise unchanged. -->

# Runtime notes

This file was adapted to be tool-neutral: it claimed a general scope and was
bound to one tool. The procedure is unchanged; what changed is that a reader on a
different runtime is told what to substitute.

- **`npm install <pkg>`, `npx <pkg>`** — the rule in this file is *never assume a
  third-party library exists; emit the install command when it is missing*. It
  spells that command for one package manager; a project using another runs the
  same install through its own manager. The dependency check is the part that
  transfers, not the spelling of the command.
Anything marked **means** is an implementation detail of one tool, and a reader
on a different runtime may need a different mechanism for the same step. Anything
marked **subject** means the capability is genuinely about that tool, and a reader
without it should not expect this file to apply.
