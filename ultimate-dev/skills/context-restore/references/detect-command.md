<!-- Moved verbatim from context-restore/SKILL.md, the
     'detect-command' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Detect command

Parse the user's input:

- `/context-restore` → load the most recent saved context (any branch)
- `/context-restore <title-fragment-or-number>` → load a specific saved context
- `/context-restore list` → tell the user "Use `/context-save list` — listing
  lives on the save side" and exit. No mode detection here.

---
