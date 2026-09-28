<!-- Moved verbatim from codex/SKILL.md, the 'section' section. Relative links were rebased for the new depth; the prose is otherwise unchanged. -->

# Important Rules

- **Never modify files.** This skill is read-only. Codex runs in read-only sandbox mode.
- **Present output verbatim.** Do not truncate, summarize, or editorialize Codex's output
  before showing it. Show it in full inside the CODEX SAYS block.
- **Add synthesis after, not instead of.** Any Claude commentary comes after the full output.
- **Bash gate above the wrapper.** Every Bash call to codex sets its `timeout`
  parameter ABOVE the inner `_gstack_codex_timeout_wrapper` budget (Review:
  `timeout: 360000` over the 330s wrapper; Challenge/Consult: `timeout: 660000`
  over the 600s wrappers) so the wrapper fires first with a diagnosable exit 124.
- **No double-reviewing.** If the user already ran `/review`, Codex provides a second
  independent opinion. Do not re-run Claude Code's own review.
- **Detect skill-file rabbit holes.** After receiving Codex output, scan for signs
  that Codex got distracted by skill files: `gstack-config`, `gstack-update-check`,
  `SKILL.md`, or `skills/gstack`. If any of these appear in the output, append a
  warning: "Codex appears to have read gstack skill files instead of reviewing your
  code. Consider retrying."
