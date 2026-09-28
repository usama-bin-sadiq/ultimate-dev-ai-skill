<!-- Moved verbatim from plugin-settings/SKILL.md, the
     'creating-settings-files' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Creating Settings Files

### From Commands

Commands can create settings files:

```markdown
# Setup Command

Steps:
1. Ask user for configuration preferences
2. Create `.claude/my-plugin.local.md` with YAML frontmatter
3. Set appropriate values based on user input
4. Inform user that settings are saved
5. Remind user to restart Claude Code for hooks to recognize changes
```

### Template Generation

Provide template in plugin README:

```markdown
