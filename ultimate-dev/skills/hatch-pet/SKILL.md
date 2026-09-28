---
name: hatch-pet
description: Create, repair, validate, visually QA, and package Codex-compatible animated pets and pet spritesheets from character art, generated images, company or prospect brand cues, or visual references. Use when a user wants a lightweight-worker Codex pet workflow, a non-pixel custom pet style, a prospect or company mascot pet, or a full 8x9 animated pet atlas with transparent unused cells, QA contact sheets, and pet.json packaging. This skill composes the installed $imagegen system skill for visual generation and uses bundled scripts for deterministic spritesheet assembly.
---

# Hatch Pet

## Overview

Create a Codex-compatible animated pet from a concept, brand cue, company/prospect name, one or more reference images, or any combination of those inputs. This workflow keeps the deterministic hatch-pet pipeline for atlas geometry, validation, visual QA, and packaging, while using concise state-specific prompts and allowing any pet-safe visual style.

User-facing inputs are optional. If the user omits a pet name, infer one from the concept, brand, company, or reference filenames; if that is not possible, choose a short friendly name. If the user omits a description, infer one from the concept or references. If the user omits reference images, generate the base pet from text first, then use that base as the canonical reference for every animation row.

## Generation Delegation

Use `$imagegen` for all normal visual generation.

Before generating base art, row strips, or repair rows, load and follow the installed image generation skill:

```text
${CODEX_HOME:-$HOME/.codex}/skills/.system/imagegen/SKILL.md
```

Do not call the Image API, image CLI, or any other image-generation path directly. Let `$imagegen` choose its own built-in-first path and fallback rules. If `$imagegen` says a fallback requires confirmation, ask the user before continuing.

When invoking `$imagegen`, pass the generated pet prompt as the authoritative visual spec. Pet prompts should stay concise, state-specific, sprite-production oriented, and grounded in the listed input images. Keep longer policy and QA rules in this skill and the deterministic review scripts rather than expanding them into every image prompt. Do not wrap prompts in the generic `$imagegen` shared prompt schema.

Use this skill's scripts for deterministic image work only: preparing layout guides and prompts, mirroring approved `running-left`, extracting frames, validating rows, composing the final atlas, and creating contact-sheet plus motion-preview QA media. Parent-owned shell/`jq` steps handle manifest updates, packaging, and cleanup.

## Storage Controls

The built-in `$imagegen` path stores generated PNG bytes in the rollout that invokes it, even when it also writes a file under `${CODEX_HOME:-$HOME/.codex}/generated_images`. Deleting files later reduces filesystem use, but it does not shrink an already-written rollout. Keep image generation isolated and bounded:

- Use one lightweight generation worker per visual job. Do not batch multiple base/row jobs into the same worker.
- Workers must return only `selected_source=...` and `qa_note=...`; they must not include Markdown image previews, base64, or extra visual attachments in their final response.
- The parent must not open every generated PNG visually. Use worker QA for each job and inspect only the final contact sheet.
- After copying the selected generated output into `decoded/`, remove the selected original from `${CODEX_HOME:-$HOME/.codex}/generated_images` when it lives there, then remove its now-empty generation directory if possible.
- For storage-sensitive full runs, ask the user whether to use the `$imagegen` CLI fallback when available. That path requires local API credentials and explicit user confirmation, but it can avoid built-in image payloads being embedded in rollout events.

## Brand Discovery

Detail moved verbatim to `references/brand-discovery.md`. Load it when this section matters and the pointer is not enough.

## Pet-Safe Styles

Default style is `auto`: infer the pet's style from the user's prompt and references, then preserve that style across every row. If the user names a style, honor it. Supported style presets include `pixel`, `plush`, `clay`, `sticker`, `flat-vector`, `3d-toy`, `painterly`, `brand-inspired`, and `auto`.

Any style is acceptable when it remains pet-safe:

- compact whole-body silhouette readable inside a `192x208` cell
- consistent face, proportions, material, palette, and props across all rows
- clean removable chroma-key background
- details large enough to read at pet size
- no text, labels, UI, or readable logos unless the user explicitly provides approved reference art and asks for them

Non-pixel styles are first-class. Plush, clay, sticker, vector, 3D toy, painterly mascot, ink, and brand-inspired looks should be accepted when they satisfy the atlas and readability constraints.

## Transparency And Effects

Detail moved verbatim to `references/transparency-and-effects.md`. Load it when this section matters and the pointer is not enough.

## Visible Progress Plan

For every pet run, keep a visible checklist so the user can see where the work is up to. Create the checklist before starting, keep one step active at a time, and update it as each step finishes.

Use this checklist for a normal pet run, replacing `<Pet>` with the pet's name or `your pet`:

1. Getting `<Pet>` ready.
2. Imagining `<Pet>`'s main look.
3. Picturing `<Pet>`'s poses.
4. Hatching `<Pet>`.

What each step means:

- `Getting <Pet> ready.` Choose or confirm the pet name, description, source images, style preset, style notes, and working folder. For bare brand/product/company requests, first run the brand discovery worker and capture the compact brand brief, source URLs, and avatar seed.
- `Imagining <Pet>'s main look.` Generate the pet's main reference image. This becomes the visual source of truth.
- `Picturing <Pet>'s poses.` Generate pose rows through lightweight workers, starting with `idle` and `running-right` to confirm identity and gait. Only mirror `running-left` if `running-right` clearly works when flipped.
- `Hatching <Pet>.` Turn the approved poses into final pet files, review the contact sheet, previews, and validation results, fix any broken parts, save `pet.json` and `spritesheet.webp`, then report the output paths.

Only mark a step complete when the real file, image, or decision exists. If this is a repair run, start from the first relevant step instead of restarting the whole checklist.

## Default Workflow

Detail moved verbatim to `references/default-workflow.md`. Load it when this section matters and the pointer is not enough.

## Lightweight Visual Workers

Use lightweight subagents for image-heavy work by default. This bounds each `$imagegen` rollout to one selected image, keeps contact-sheet vision payloads out of the parent thread, and reduces cost while preserving the full 9-state app contract.

## Subagent Delegation

Unless explicitly forbidden by the user, use subagents for this run. If the user has not allowed the use of subagents, or the intent on subagent use is vague, then ask the user for permission to spawn subagents for parallel lanes of work.

Parent responsibilities:

- run the brand discovery worker before preparation when the user provides a bare brand/product/company/prospect name
- prepare the run and inspect `imagegen-jobs.json`
- assign the base job, row jobs, and final contact-sheet QA to lightweight workers
- copy selected worker outputs into their decoded paths and mark jobs complete in `imagegen-jobs.json`
- create the base frame, written to `references/canonical-base.png`, from the
  selected base output — this is the output directory, and the file is absent
  until the step above has run
- run the approved `running-left` mirror derivation when appropriate
- run deterministic image processing, packaging, repair regeneration, and cleanup

Base worker responsibilities:

- handle only the `base` job
- read `prompts/base-pet.md` and use any listed reference images
- use `$imagegen` only
- honor any compact brand inspiration line in the prompt as broad visual/personality guidance, without copying logos, readable marks, UI screenshots, slogans, or text
- return only `selected_source=/absolute/path/to/selected-output.png` and `qa_note=<one sentence>`

Row worker responsibilities:

- handle exactly one row job
- read the row prompt and use all listed input images
- use `$imagegen` only; do not draw, edit, tile, or synthesize sprites locally
- perform a quick visual sanity check for frame count, identity, chroma background, spacing, clipping, and detached effects
- enforce the row prompt's transparency and effects rules, including no detached effects, no wave marks for `waving`, no speed lines or dust for directional running rows, no literal foot-running for the non-directional `running` row, and only attached opaque sprite-like tears/smoke/stars when allowed by the state prompt
- return only `selected_source=/absolute/path/to/selected-output.png` and `qa_note=<one sentence>`

Final visual QA worker responsibilities:

- inspect `qa/contact-sheet.png` plus the row GIFs under `qa/previews/`, with `qa/review.json` and `final/validation.json` as text context when useful
- verify all 9 rows match the Codex app state contract and the same pet identity
- return a compact result: `visual_qa=pass` or `visual_qa=fail`, plus row-specific repair notes when failing
- do not edit files, queue repairs, package, or clean up

Model choice for workers:

- Prefer a smaller capable model for brand discovery, since it returns a compact research brief rather than doing orchestration.
- Prefer a smaller capable model for visual workers, such as `gpt-5.4-mini` with medium reasoning, when model override is available.
- Use the parent/default model only for orchestration or when a smaller worker model is unavailable.
- Keep at most two generation workers active at once unless the user explicitly asks for higher parallelism. Run final visual QA as a single worker after deterministic image processing. Close workers after their result has been consumed.

Use this base worker prompt:

```text
Generate the hatch-pet base image.

Run dir: <absolute run dir>
Job id: base
Prompt file: <absolute base prompt file>
Input images:
- <absolute path> — <role>

Use $imagegen only. Read the base prompt and attach every listed input image. If the prompt contains brand inspiration, use it only as broad mascot-safe guidance; do not copy logos, readable marks, UI screenshots, slogans, or text. Before returning, visually check that the result is one centered full-body pet on a flat chroma background, with no text, scenery, shadows, or detached effects.

Do not edit manifests, copy into decoded, mark jobs complete, generate rows, run image-processing scripts, repair, package, or open unrelated files.
Do not include Markdown image previews, base64, or extra attachments in the final response.

Return exactly:
selected_source=/absolute/path/to/selected-output.png
qa_note=<one sentence>
```

Use this row worker prompt:

```text
Generate one hatch-pet row.

Run dir: <absolute run dir>
Row id: <row-id>
Prompt file: <absolute prompt file>
Retry prompt file: <absolute retry prompt file>
Input images:
- <absolute path> — <role>
- <absolute path> — <role>

Use $imagegen only. Read the row prompt and attach every listed input image. If imagegen returns Bad Request, retry once with the retry prompt and the same input images.

Before returning, visually check: exact frame count, same pet identity as canonical base, flat chroma background, complete separated unclipped poses, and no detached effects or guide marks. The prompt's transparency and effects rules are mandatory: no detached effects, no wave marks for `waving`, no speed lines or dust for directional running rows, no literal foot-running for the non-directional `running` row, and only attached opaque sprite-like tears/smoke/stars when allowed by the state prompt.

Do not edit manifests, copy into decoded, mark jobs complete, mirror rows, run image-processing scripts, repair, package, or open unrelated files.
Do not include Markdown image previews, base64, or extra attachments in the final response.

Return exactly:
selected_source=/absolute/path/to/selected-output.png
qa_note=<one sentence>
```

Use this final visual QA worker prompt:

```text
Visually QA one finalized hatch-pet contact sheet.

Run dir: <absolute run dir>
Contact sheet: <absolute run dir>/qa/contact-sheet.png
Preview dir: <absolute run dir>/qa/previews
Review JSON: <absolute run dir>/qa/review.json
Validation JSON: <absolute run dir>/final/validation.json

Inspect the contact sheet and the preview GIFs visually. Confirm the same pet identity, style, palette, silhouette, face, proportions, and props across all rows:
0 idle, 1 running-right, 2 running-left, 3 waving, 4 jumping, 5 failed, 6 waiting, 7 running, 8 review.

Fail rows with identity drift, missing/blank frames, copied guide marks, white/nontransparent backgrounds, cropped bodies, slot overlap, detached effects, shadows/glows/smears/dust, chroma-key artifacts, motion that does not match the row state, unintended size popping, wrong facing direction, reversed or non-alternating gait, or idle loops that are effectively static.

Do not edit files, queue repairs, package, clean up, or inspect unrelated files.

Return exactly:
visual_qa=pass|fail
qa_note=<one sentence summary>
repair_rows=<comma-separated row ids, or none>
repair_notes=<short row-specific notes, or none>
```

## Repair Workflow

If frame inspection or final visual QA fails, read `qa/review.json`, regenerate the smallest failing scope, copy the replacement row into the same decoded output path, and keep that job marked complete with the new `source_path` and `completed_at`. Repair the failed row, not the whole sheet.

For identity repairs, use the canonical base image, original references, contact sheet, and exact row failure note as grounding context. Give the row worker the existing row prompt plus a compact repair note from `qa/review.json`; preserve the canonical pet identity and chosen style.

For extraction-induced motion popping, do not regenerate imagery first. If the source strip already preserves row-level scale and baseline, rerun the deterministic pipeline with `--method stable-slots`, inspect with `--allow-stable-slots`, then re-check the preview GIFs. Regenerate the row only when the original strip itself is clipped, unstable, or semantically wrong.

## Rules

Detail moved verbatim to `references/rules.md`. Load it when this section matters and the pointer is not enough.

## Acceptance Criteria

- Final atlas is PNG or WebP, `1536x1872`, transparent-capable, and based on `192x208` cells.
- Used cells are non-empty and unused cells are fully transparent.
- Atlas follows the row/frame counts in `references/animation-rows.md`.
- Contact sheet and per-row motion previews have been produced and inspected by a lightweight visual QA worker.
- `qa/review.json` has no errors.
- Row-by-row review confirms the animation cycles are complete enough for the Codex app.
- Motion previews do not show unintended size popping, reversed directional cadence, or wrong row semantics.
- Non-pixel styles are accepted when readable at pet size and consistent across rows.
- `${CODEX_HOME:-$HOME/.codex}/pets/<pet-name>/pet.json` and `${CODEX_HOME:-$HOME/.codex}/pets/<pet-name>/spritesheet.webp` are staged together for custom pets.

## Reference files

These ship with the skill and are read on demand; none is needed to
use it. Each answers one question the sections above do not.

- [`references/codex-pet-contract.md`](references/codex-pet-contract.md)
- [
Each file below is loaded on demand, not at triage. 9 file(s):

- `references/acceptance-criteria.md` — Acceptance Criteria. <!-- Moved verbatim from hatch-pet/SKILL.md, the
- `references/generation-delegation.md` — Generation Delegation. <!-- Moved verbatim from hatch-pet/SKILL.md, the
- `references/lightweight-visual-workers.md` — Lightweight Visual Workers. <!-- Moved verbatim from hatch-pet/SKILL.md, the
- `references/pet-safe-styles.md` — Pet-Safe Styles. <!-- Moved verbatim from hatch-pet/SKILL.md, the
- `references/reference-files.md` — Reference files. <!-- Moved verbatim from hatch-pet/SKILL.md, the
- `references/repair-workflow.md` — Repair Workflow. <!-- Moved verbatim from hatch-pet/SKILL.md, the
- `references/storage-controls.md` — Storage Controls. <!-- Moved verbatim from hatch-pet/SKILL.md, the
- `references/subagent-delegation.md` — Subagent Delegation. <!-- Moved verbatim from hatch-pet/SKILL.md, the
- `references/visible-progress-plan.md` — Visible Progress Plan. <!-- Moved verbatim from hatch-pet/SKILL.md, the

`references/qa-rubric.md`](references/qa-rubric.md)
