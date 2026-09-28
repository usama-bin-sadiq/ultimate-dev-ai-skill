<!-- Moved verbatim from hook-development/SKILL.md, the 'section' section. Relative links were rebased for the new depth; the prose is otherwise unchanged. -->

# Additional Resources

### Reference Files

For detailed patterns and advanced techniques, consult:

- **`./patterns.md`** - Common hook patterns (8+ proven patterns)
- **`./migration.md`** - Migrating from basic to advanced hooks
- **`./advanced.md`** - Advanced use cases and techniques

### Example Hook Scripts

Working examples in `examples/`:

- **`validate-write.sh`** - File write validation example
- **`validate-bash.sh`** - Bash command validation example
- **`load-context.sh`** - SessionStart context loading example

### Utility Scripts

Development tools in `scripts/`:

- **`validate-hook-schema.sh`** - Validate hooks.json structure and syntax
- **`test-hook.sh`** - Test hooks with sample input before deployment
- **`hook-linter.sh`** - Check hook scripts for common issues and best practices

### External Resources

- **Official Docs**: https://docs.claude.com/en/docs/claude-code/hooks
- **Examples**: See security-guidance plugin in marketplace
- **Testing**: Use `claude --debug` for detailed logs
- **Validation**: Use `jq` to validate hook JSON output
