<!-- Moved verbatim from image-to-code-skill/SKILL.md, the
     '4-codex-specific-section-image-rule' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## 4. CODEX-SPECIFIC SECTION IMAGE RULE

Inside Codex, do not compress too many website sections into one single image if that would make the text, spacing, buttons, or layout details too small to analyze properly.

In Codex, prefer separate large images per section.

Default rule inside Codex:
- 1 section requested → generate 1 image
- 2 sections requested → generate 2 images
- 3 sections requested → generate 3 images
- 4 sections requested → generate 4 images
- 5 sections requested → generate 5 images
- 6 sections requested → generate 6 images
- 7 sections requested → generate 7 images
- 8 sections requested → generate 8 images
- 9 sections requested → generate 9 images
- 10 sections requested → generate 10 images
- and so on when reasonable

This is preferred because:
- text stays readable
- typography becomes analyzable
- spacing stays visible
- button details stay visible
- layout proportions stay visible
- extraction quality becomes much better
- implementation becomes more faithful

Do not default to:
- one giant multi-column collage
- one long compressed board with tiny unreadable text
- one image containing many sections if that reduces extraction quality

If necessary, generate more images rather than shrinking everything.

Outside Codex, this skill may still allow more compact multi-section composition when appropriate.
Inside Codex, prioritize section clarity and extraction accuracy.

---
