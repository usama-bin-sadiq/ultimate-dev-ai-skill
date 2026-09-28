<!-- Moved verbatim from hatch-pet/SKILL.md, the
     'default-workflow' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Default Workflow

1. Prepare a pet run folder and imagegen job manifest:

```bash
SKILL_DIR="${CODEX_HOME:-$HOME/.codex}/skills/hatch-pet"
python "$SKILL_DIR/scripts/prepare_pet_run.py" \
  --pet-name "<Name>" \
  --description "<one sentence>" \
  --reference /absolute/path/to/reference.png \
  --output-dir /absolute/path/to/run \
  --pet-notes "<stable pet description>" \
  --brand-discovery-file /absolute/path/to/brand-discovery.md \
  --brand-name "<optional researched brand name>" \
  --brand-brief "<optional compact researched brand cue sentence>" \
  --brand-source "https://example.com/source" \
  --style-preset auto \
  --style-notes "<optional freeform style notes>" \
  --force
```

All arguments above are optional except any flags needed to express user constraints. For text-only requests, pass the concept through `--pet-notes` and omit `--reference`; `prepare_pet_run.py` will infer a name, description, chroma key, and output directory as needed.
For brand-only requests, run the discovery worker first, save the markdown brief, then pass the brief path through `--brand-discovery-file`, `avatar_seed` through `--pet-notes`, `brand_name` through `--brand-name`, `brand_brief` through `--brand-brief`, and each source URL through repeated `--brand-source`.

2. Inspect `imagegen-jobs.json` for the next ready `$imagegen` jobs. A job is ready when its `status` is not `complete` and every id in `depends_on` is already complete. Prefer reading the manifest directly with `jq` or the editor instead of adding helper scripts for status display:

```bash
jq '.jobs[] | {id, kind, status, depends_on, prompt_file, retry_prompt_file, input_images, output_path, derivation_policy}' /absolute/path/to/run/imagegen-jobs.json
```

3. Generate visual jobs with lightweight workers by default:

- Generate and copy `base` first, using a lightweight base worker.
- Generate and copy `idle` and `running-right` next as the identity and gait check, using one lightweight worker per row.
- Inspect `running-right`; mirror `running-left` only when visual identity, prop placement, markings, lighting, and direction semantics remain correct.
- Generate `running-left` normally with a lightweight worker when mirroring would change meaning or identity.
- Generate the remaining rows with lightweight workers, using every input image listed for each job.

For each ready visual job, invoke `$imagegen` with the prompt file listed in `imagegen-jobs.json`, every listed input image with its role label, and the default built-in `image_gen` path unless `$imagegen` itself routes otherwise. The parent agent must keep its own image handling minimal: do not open every generated base or row in the parent rollout. Workers return only the selected source path and a one-sentence QA note; the parent records the selected source path in the manifest.

`prepare_pet_run.py` creates 9 row-specific layout guide images under `references/layout-guides/`, one per animation state. Row jobs attach the matching guide as a layout-only input so the model can follow the correct frame count, spacing, centering, and safe padding. Treat these guides as invisible construction references: the generated row strip must not include visible boxes, borders, center marks, labels, guide colors, or the guide background.

When generating row strips, keep the identity lock in the row prompt authoritative. Preserve the same style, face, markings, palette, materials, prop design, body proportions, and silhouette from the canonical base. Row jobs attach the layout guide and canonical base by default; the decoded base is kept in the run folder for deterministic processing rather than sent as a redundant generation input.

If `$imagegen` returns a transport-level `Bad Request` for a row, retry that same row once with its generated `retry_prompt_file`. The retry prompt preserves the row id, frame count, chroma key, canonical-base identity, and state action. Keep the canonical base attached. If the retry still fails, stop and report the failing row and prompt paths instead of switching to any other generation path.

4. After selecting a generated output for a job, copy it into the decoded output path and mark the job complete. For `base`, also create the canonical identity reference:

```bash
RUN_DIR=/absolute/path/to/run
JOB_ID=<job-id>
SOURCE=/absolute/path/to/generated-output.png
OUTPUT_REL=$(jq -r --arg id "$JOB_ID" '.jobs[] | select(.id == $id) | .output_path' "$RUN_DIR/imagegen-jobs.json")
mkdir -p "$(dirname "$RUN_DIR/$OUTPUT_REL")"
cp "$SOURCE" "$RUN_DIR/$OUTPUT_REL"
```

```bash
if [ "$JOB_ID" = "base" ]; then mkdir -p "$RUN_DIR/references"; cp "$RUN_DIR/$OUTPUT_REL" "$RUN_DIR/references/canonical-base.png"; fi

The PNG is **output, not input**: the block above writes it, so it does not
exist until a run has produced it. Nothing needs to be supplied, and no
reference sprite ships with the skill — the base frame is whatever the render
produced. The step that creates it is listed under **Base frame** below.
```

```bash
UPDATED_AT=$(date -u +%Y-%m-%dT%H:%M:%SZ)
TMP_MANIFEST=$(mktemp)
jq --arg id "$JOB_ID" --arg source "$SOURCE" --arg at "$UPDATED_AT" '(.jobs[] | select(.id == $id)) += {status: "complete", source_path: $source, completed_at: $at}' "$RUN_DIR/imagegen-jobs.json" > "$TMP_MANIFEST"
mv "$TMP_MANIFEST" "$RUN_DIR/imagegen-jobs.json"
```

If the copied source is under `${CODEX_HOME:-$HOME/.codex}/generated_images`, delete the original generated file after the decoded copy exists:

```bash
GENERATED_ROOT="${CODEX_HOME:-$HOME/.codex}/generated_images"
case "$SOURCE" in
  "$GENERATED_ROOT"/*)
    rm -f "$SOURCE"
    rmdir "$(dirname "$SOURCE")" 2>/dev/null || true
    ;;
esac
```

5. Derive `running-left` only when it is visually safe:

```bash
python "$SKILL_DIR/scripts/derive_running_left_from_running_right.py" \
  --run-dir /absolute/path/to/run \
  --confirm-appropriate-mirror \
  --decision-note "<why mirroring preserves this pet's identity>"
```

That script mirrors each generated frame slot in place so the leftward row preserves the rightward row's temporal order. Do not replace it with a whole-strip mirror that reverses animation timing.

6. When all jobs are complete, run the image-processing scripts directly:

```bash
RUN_DIR=/absolute/path/to/run
mkdir -p "$RUN_DIR/final" "$RUN_DIR/qa"
```

```bash
python "$SKILL_DIR/scripts/extract_strip_frames.py" \
  --decoded-dir "$RUN_DIR/decoded" \
  --output-dir "$RUN_DIR/frames" \
  --states all \
  --method auto
```

```bash
python "$SKILL_DIR/scripts/inspect_frames.py" \
  --frames-root "$RUN_DIR/frames" \
  --json-out "$RUN_DIR/qa/review.json" \
  --require-components
```

```bash
python "$SKILL_DIR/scripts/compose_atlas.py" \
  --frames-root "$RUN_DIR/frames" \
  --output "$RUN_DIR/final/spritesheet.png" \
  --webp-output "$RUN_DIR/final/spritesheet.webp"
```

```bash
python "$SKILL_DIR/scripts/validate_atlas.py" \
  "$RUN_DIR/final/spritesheet.webp" \
  --json-out "$RUN_DIR/final/validation.json"
```

```bash
python "$SKILL_DIR/scripts/make_contact_sheet.py" \
  "$RUN_DIR/final/spritesheet.webp" \
  --output "$RUN_DIR/qa/contact-sheet.png"
```

```bash
python "$SKILL_DIR/scripts/render_animation_previews.py" \
  --frames-root "$RUN_DIR/frames" \
  --output-dir "$RUN_DIR/qa/previews"
```

If the preview GIFs show size popping or baseline jumps caused by per-frame fit-to-cell extraction, and the original row strip itself had stable scale and placement, rerun frame extraction with the explicit row-stability mode and then re-run inspection, atlas composition, validation, contact sheet generation, and previews:

```bash
python "$SKILL_DIR/scripts/extract_strip_frames.py" \
  --decoded-dir "$RUN_DIR/decoded" \
  --output-dir "$RUN_DIR/frames" \
  --states all \
  --method stable-slots
```

```bash
python "$SKILL_DIR/scripts/inspect_frames.py" \
  --frames-root "$RUN_DIR/frames" \
  --json-out "$RUN_DIR/qa/review.json" \
  --require-components \
  --allow-stable-slots
```

Use `stable-slots` as a deliberate QA-driven correction, not the default. It should reduce extraction-induced motion pops without hiding clipped wide poses or bad source strips.

Expected output before cleanup:

```text
run/
  pet_request.json
  imagegen-jobs.json
  prompts/
  decoded/
  frames/frames-manifest.json
  final/spritesheet.webp
  final/validation.json
  qa/contact-sheet.png
  qa/previews/*.gif
  qa/review.json
  qa/run-summary.json
```

Package output is written outside the run directory by default. If `CODEX_HOME` is set, use it; otherwise use `$HOME/.codex`.

```text
${CODEX_HOME:-$HOME/.codex}/pets/<pet-name>/
  pet.json
  spritesheet.webp
```

Package with shell and `jq`:

```bash
RUN_DIR=/absolute/path/to/run
PET_ID=$(jq -r '.pet_id' "$RUN_DIR/pet_request.json")
DISPLAY_NAME=$(jq -r '.display_name' "$RUN_DIR/pet_request.json")
DESCRIPTION=$(jq -r '.description' "$RUN_DIR/pet_request.json")
PET_DIR="${CODEX_HOME:-$HOME/.codex}/pets/$PET_ID"
mkdir -p "$PET_DIR"
cp "$RUN_DIR/final/spritesheet.webp" "$PET_DIR/spritesheet.webp"
jq -n --arg id "$PET_ID" --arg displayName "$DISPLAY_NAME" --arg description "$DESCRIPTION" '{id: $id, displayName: $displayName, description: $description, spritesheetPath: "spritesheet.webp"}' > "$PET_DIR/pet.json"
```

Write `qa/run-summary.json` after packaging:

```bash
jq -n --arg run_dir "$RUN_DIR" --arg spritesheet "$RUN_DIR/final/spritesheet.webp" --arg validation "$RUN_DIR/final/validation.json" --arg contact_sheet "$RUN_DIR/qa/contact-sheet.png" --arg review "$RUN_DIR/qa/review.json" --arg package "$PET_DIR" '{ok: true, run_dir: $run_dir, spritesheet: $spritesheet, validation: $validation, contact_sheet: $contact_sheet, review: $review, package: $package}' > "$RUN_DIR/qa/run-summary.json"
```

After deterministic image processing, inspect `qa/contact-sheet.png` and `qa/previews/*.gif` with a lightweight visual QA worker before accepting the pet. Deterministic validation is necessary but not sufficient. Block acceptance if any row changes species/body type, face, markings, palette, material, prop design, style, prop side unexpectedly, or overall silhouette. Motion previews must also reject unintended size popping, reversed or stagnant directional cadence, wrong facing direction, and idle loops that are technically different but visually inert.

After model visual QA accepts the contact sheet, remove intermediate run artifacts:

Keep `pet_request.json`, `final/spritesheet.webp`, `final/validation.json`, `qa/contact-sheet.png`, `qa/previews/`, `qa/review.json`, and `qa/run-summary.json`. Remove generated prompt files, layout guides, decoded row strips, extracted frames, `final/spritesheet.png`, and the imagegen job manifest. Skip cleanup when the user wants debug artifacts or the run still needs repair.
