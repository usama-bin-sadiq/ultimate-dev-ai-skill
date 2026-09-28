<!-- Moved verbatim from design-consultation/SKILL.md, the 'section' section. Relative links were rebased for the new depth; the prose is otherwise unchanged. -->

# Phase 0: Pre-checks

**Check for existing DESIGN.md:**

```bash
ls DESIGN.md design-system.md 2>/dev/null || echo "NO_DESIGN_FILE"
```

If either exists, read it and AskUserQuestion: "Want to **update**, **start fresh**, or **cancel**?" DESIGN.md is authoritative if both exist. A lone design-system.md supplies prior context but stays untouched; Phase 6 targets DESIGN.md. Route that answer before any other probe:

- **Cancel:** STOP the skill now, with no file changes or further probes.
- **Update:** carry the existing decisions into Q1 as constraints; ask what should change, preserve the rest. If DESIGN.md exists, run the Update-only format check immediately below; if only design-system.md exists, skip that check.
- **Start fresh:** set aside prior visual choices except constraints the user keeps. Skip the format question; propose a new open-format file, replacing nothing until Q-final.
- **No existing file:** continue with a new open-format proposal.

All conversion, marker and design writes wait for Q-final; Phase 0 only reads and records choices.

**Update-only gate:** Only **Update** with DESIGN.md enters this block (command and all result branches). **Start fresh**, **No existing file**, or a lone design-system.md: skip to **Gather product context from the codebase**. **Cancel** has already stopped the skill.

```bash
bun --no-env-file run $HOME/<agent-config-dir>/gstack/bin/gstack-design-md.ts check DESIGN.md
```

- `DESIGN_MD_FORMAT: spec` → already the open format; `bun --no-env-file run $HOME/<agent-config-dir>/gstack/bin/gstack-design-md.ts tokens DESIGN.md` prints the flat token map. Update tokens in the front matter, rationale in the sections.
- `legacy` with `DESIGN_MD_MARKER: none` → ask once (AskUserQuestion): **A) Convert** (recommended; preview with `bun --no-env-file run $HOME/<agent-config-dir>/gstack/bin/gstack-design-md.ts convert`, without `--write`) **B) Keep legacy** (retain its prose structure) **C) Start fresh** (take Phase 0's fresh path). Record the choice for Q-final. Obey an existing marker silently.
- **Convert/Keep legacy:** After Q-final approval outside plan mode, `bun --no-env-file run $HOME/<agent-config-dir>/gstack/bin/gstack-design-md.ts convert --write` keeps a `.legacy.bak` and every section, or `bun --no-env-file run $HOME/<agent-config-dir>/gstack/bin/gstack-design-md.ts mark legacy-keep` persists the choice. In plan mode, record the chosen format in Proposed DESIGN.md instead.
- `unknown` → preserve its prose shape for Update; disclose `DESIGN_MD_REASON`. `DESIGN_MD_CONVERT_REFUSED` → leave unchanged, ask whether to keep its shape or start fresh, then resume the proposal.
- `missing` → Phase 6 writes one. Exit 3 (`DESIGN_MD_INTERNAL_ERROR`) is a gstack bug: report it, do not retry.

**End of Update-only format check.**

**Gather product context from the codebase:**

```bash
cat PRODUCT.md 2>/dev/null | head -120 || echo "NO_PRODUCT_MD"
cat README.md 2>/dev/null | head -50
cat package.json 2>/dev/null | head -20
ls src/ app/ pages/ components/ 2>/dev/null | head -30
```

A `PRODUCT.md` (impeccable's product-context file) already answers the product questions below: treat it as the user's prior answers, confirm them in one line, and do not re-ask. Never open `<agent-config-dir>/impeccable/**` or any other skill's files; PRODUCT.md and DESIGN.md are the shared surface.

Look for office-hours output:

```bash
setopt +o nomatch 2>/dev/null || true  # zsh compat
eval "$(~/<agent-config-dir>/gstack/bin/gstack-slug 2>/dev/null)"
ls ~/.gstack/projects/$SLUG/*office-hours* 2>/dev/null | head -5
ls .context/*office-hours* .context/attachments/*office-hours* 2>/dev/null | head -5
```

If office-hours output exists, read it — the product context is pre-filled.

If the codebase is empty and purpose is unclear, say: *"I don't have a clear picture of what you're building yet. Want to explore first with `/office-hours`? Once we know the product direction, we can set up the design system."*

**Check the Aside browser (optional — enables visual competitive research):**

The browser is optional here. Probe Aside first. On any non-READY result, resolve `$B` in Browser fallback. If `$B` says `NEEDS_SETUP`, do not build or offer a build: tell the user once that visual research is unavailable, skip Phase 2 Step 2, use host WebSearch for Step 1 if available, and fill remaining gaps from design knowledge.
