<!-- Moved verbatim from setup-gbrain/SKILL.md, the 'Important Rules' section. Relative links were rebased for the new depth; the prose is otherwise unchanged. -->

# Important Rules

- **One rule for every secret.** PAT, DB_PASS, pooler URL: env-var only,
  never argv, never logged, never persisted to disk by us. The only file
  that holds the pooler URL long-term is `~/.gbrain/config.json`, written
  by gbrain's own `init` at mode 0600 — that's gbrain's discipline, not
  ours.
- **STOP points are hard.** Gbrain doctor not healthy, D19 PATH shadow, D9
  migrate timeout, smoke test failure — each is a STOP. Do not paper over.
- **Concurrent-run lock.** At skill start, create the parent before acquiring
  the lock atomically. Keep mkdir's error output; missing parents and filesystem
  failures are not evidence of a competing run:

  ```bash
  if ! mkdir -p ~/.gstack; then
    echo "ERROR: Cannot create setup-gbrain lock parent ~/.gstack." >&2
    exit 1
  fi
  if ! mkdir ~/.gstack/.setup-gbrain.lock.d; then
    if [ -d ~/.gstack/.setup-gbrain.lock.d ]; then
      echo "Another /setup-gbrain instance is running. Wait for it, or remove ~/.gstack/.setup-gbrain.lock.d only if you are sure it is stale." >&2
    else
      echo "ERROR: Cannot acquire setup-gbrain lock." >&2
    fi
    exit 1
  fi
  ```

  Release the acquired lock on normal exit AND in the SIGINT trap.
- **CLAUDE.md is the audit trail.** Always update it in Step 8 after a
  successful setup.
