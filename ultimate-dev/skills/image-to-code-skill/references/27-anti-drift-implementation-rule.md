<!-- Moved verbatim from image-to-code-skill/SKILL.md, the
     '27-anti-drift-implementation-rule' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## 27. ANTI-DRIFT IMPLEMENTATION RULE

A common failure mode is design drift:
the generated images look strong, but the coded result becomes generic.

Strictly avoid that.

During implementation:
- do not simplify into default templates
- do not replace distinctive sections with generic rows
- do not compress generous spacing into dense layout
- do not replace strong typography with plain hierarchy
- do not remove the page’s visual identity for convenience
- do not merge section logic into repetitive patterns that were not present in the source images
- do not reintroduce nested-box complexity that was intentionally removed during analysis

The final coded result should still feel like the same website as the generated references.

---
