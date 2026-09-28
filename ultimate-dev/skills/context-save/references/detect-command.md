<!-- Moved verbatim from context-save/SKILL.md, the
     'detect-command' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Detect command

Parse the user's input to determine the mode:

- `/context-save` or `/context-save <title>` → **Save**
- `/context-save list` → **List**

If the user provides a title after the command (e.g., `/context-save auth refactor`),
use it as the title. Otherwise, infer a title from the current work.

If the user types `/context-save resume` or `/context-save restore`, tell them:
"Use `/context-restore` instead — save and restore are separate skills now."

---
