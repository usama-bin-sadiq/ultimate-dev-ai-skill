<!-- Moved verbatim from command-development/SKILL.md, the 'section' section. Relative links were rebased for the new depth; the prose is otherwise unchanged. -->

# Troubleshooting

**Command not appearing:**

- Check file is in correct directory
- Verify `.md` extension present
- Ensure valid Markdown format
- Restart Claude Code

**Arguments not working:**

- Verify `$1`, `$2` syntax correct
- Check `argument-hint` matches usage
- Ensure no extra spaces

**Bash execution failing:**

- Check `allowed-tools` includes Bash
- Verify command syntax in backticks
- Test command in terminal first
- Check for required permissions

**File references not working:**

- Verify `@` syntax correct
- Check file path is valid
- Ensure Read tool allowed
- Use absolute or project-relative paths
