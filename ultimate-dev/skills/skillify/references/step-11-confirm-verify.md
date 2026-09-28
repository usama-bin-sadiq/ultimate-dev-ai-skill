<!-- Moved verbatim from skillify/SKILL.md, the 'Step 11 — Confirm + verify' section. Relative links were rebased for the new depth; the prose is otherwise unchanged. -->

# Step 11 — Confirm + verify

After a successful commit, run one verification:

```bash
$B skill list | grep <name>
$B skill run <name>    # should match the JSON the prototype produced
```

If the post-commit run does not match the prototype output, something
in synthesis drifted. Surface this to the user — they may want to
`$B skill rm <name>` and retry. Do NOT silently roll back; the user
deserves to see the discrepancy.

End the skill with one line: "Skill '<name>' committed at <tier>. Future
/scrape calls matching '<canonical-trigger>' will run in ~200ms."

---
