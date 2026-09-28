<!-- Moved verbatim from devex-review/SKILL.md, the
     'step-4-documentation-audit' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Step 4: Documentation Audit

Navigate the docs structure in Aside (search is `pg.fill(<search selector>, <query>)`,
then `pg.locator(<search selector>).press("Enter")` — or `pg.getByRole("searchbox").press("Enter")`,
or a click — then `snapshot`):
- Check search functionality (try 3 common queries)
- Verify code examples are copy-paste-complete
- Check language switcher behavior
- Check information architecture (can you find what you need in <2 min?)

Screenshot key findings. Score 0-10. Load "## Pass 4" from dx-hall-of-fame.md.
