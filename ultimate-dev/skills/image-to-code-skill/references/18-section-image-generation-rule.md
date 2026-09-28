<!-- Moved verbatim from image-to-code-skill/SKILL.md, the
     '18-section-image-generation-rule' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## 18. SECTION IMAGE GENERATION RULE

Inside Codex, treat each section as its own analyzable unit.

If the user asks for:
- a hero only → generate 1 hero image
- 4 sections → generate 4 section images
- 8 sections → generate 8 section images
- 12 sections → generate 12 section images when reasonable

General preference:
- one section = one primary image
- one complex section = one primary image + one or more optional detail images
- one unclear section = regenerate it again as a fresh clean standalone image

This section-first generation rule exists to prevent:
- tiny unreadable text
- tiny buttons
- unclear spacing
- weak extraction quality
- lossy design-to-code translation

---
