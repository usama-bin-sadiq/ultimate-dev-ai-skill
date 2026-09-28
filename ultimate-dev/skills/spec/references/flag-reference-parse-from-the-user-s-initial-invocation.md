<!-- Moved verbatim from spec/SKILL.md, the 'section' section. Relative links were rebased for the new depth; the prose is otherwise unchanged. -->

# Flag Reference (parse from the user's initial invocation)

When the user invokes `/spec`, scan their message for these flags. Flags are space-
separated tokens starting with `--`. Last flag wins on conflict.

| Flag | Default | Effect |
|------|---------|--------|
| `--dedupe` | ON | Phase 1: check `gh issue list --search` for near-duplicates before drafting. |
| `--no-dedupe` | — | Skip the dedupe check. |
| `--no-gate` | OFF (gate is ON) | Skip the codex quality-score gate between Phase 4 and Phase 5. **Redaction (Phase 4.5a semantic + 4.5b regex) still runs — there is no flag that disables it.** |
| `--audit` | OFF | Route Phase 5 to the Audit/Cleanup template (instead of Standard). |
| `--execute` | conditional default (see Phase 5) | Spawn `claude -p` in a fresh worktree after filing the issue. |
| `--no-execute` | — | File issue only; do NOT spawn agent (alias: `--file-only`). |
| `--file-only` | — | Same as `--no-execute`. |
| `--plan-file <path>` | inferred from harness | Load the spec into the specified plan file instead of inferring. |
| `--sync-archive` | OFF | Include the spec archive in artifacts-sync (default: local only). |

Echo the parsed flag set back to the user at the start of Phase 1 so they can
confirm: "Flags: dedupe=ON, gate=ON, audit=OFF, execute=auto (plan mode = ...)."

---
