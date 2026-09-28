<!-- Moved verbatim from hatch-pet/SKILL.md, the
     'repair-workflow' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Repair Workflow

If frame inspection or final visual QA fails, read `qa/review.json`, regenerate the smallest failing scope, copy the replacement row into the same decoded output path, and keep that job marked complete with the new `source_path` and `completed_at`. Repair the failed row, not the whole sheet.

For identity repairs, use the canonical base image, original references, contact sheet, and exact row failure note as grounding context. Give the row worker the existing row prompt plus a compact repair note from `qa/review.json`; preserve the canonical pet identity and chosen style.

For extraction-induced motion popping, do not regenerate imagery first. If the source strip already preserves row-level scale and baseline, rerun the deterministic pipeline with `--method stable-slots`, inspect with `--allow-stable-slots`, then re-check the preview GIFs. Regenerate the row only when the original strip itself is clipped, unstable, or semantically wrong.
