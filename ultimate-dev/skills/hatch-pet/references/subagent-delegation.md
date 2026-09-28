<!-- Moved verbatim from hatch-pet/SKILL.md, the
     'subagent-delegation' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

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
