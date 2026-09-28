<!-- Moved verbatim from hatch-pet/SKILL.md, the
     'lightweight-visual-workers' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Lightweight Visual Workers

Use lightweight subagents for image-heavy work by default. This bounds each `$imagegen` rollout to one selected image, keeps contact-sheet vision payloads out of the parent thread, and reduces cost while preserving the full 9-state app contract.
