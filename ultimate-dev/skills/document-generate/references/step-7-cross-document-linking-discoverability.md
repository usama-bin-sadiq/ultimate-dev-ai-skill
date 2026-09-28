<!-- Moved verbatim from document-generate/SKILL.md, the
     'step-7-cross-document-linking-discoverability' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Step 7: Cross-Document Linking & Discoverability

After writing all documents:

1. **Add cross-links between quadrants.** Every reference doc should link to its how-to.
   Every how-to should link to its reference. Tutorials should link to both.

2. **Update entry-point files.** Add references to new docs in:
   - README.md — add to documentation section or table of contents
   - <agent-instructions> / <agent-instructions> — add to project structure if relevant
   - Any existing docs index or sidebar config

3. **Verify discoverability.** Every new document must be reachable within 2 clicks from
   README.md. If a docs framework is in use, add to the sidebar/nav config.

4. **Check for broken links.** Grep for any `](` references that point to files that don't exist.

---
