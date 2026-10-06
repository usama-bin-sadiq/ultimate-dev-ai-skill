# T7 — Annotate skills whose bundled assets were never vendored

## Status

open

## Problem

63 skills ship instructions that reference files that do not exist in this
repository: 103 broken markdown links and 46 broken script paths. None were ever
in git, so nothing is recoverable. Two examples:

- `geniml` documents six scripts (`corpus_auditor.py`, `tokenizer_compatibility.py`, ...)
  and ships none of them, only its `references/`.
- `deep-learning-book` links 23 chapter files that live at
  deeplearningbook.org, not here.

These skills were imported from upstream plugin collections without their
scripts and templates. A user who follows the instructions gets a command that
cannot run.

## Options

1. **Vendor** - fetch each asset from its upstream repository. Needs a
   per-repo decision on licence and version pinning. Largest effort, restores
   real capability.
2. **Annotate** - add one provenance note per skill stating the tooling ships
   upstream and is not bundled here. Cheap, truthful, keeps the reference
   material useful.
3. **Leave** - rely on `tools/check-links.py` as a standing worklist.

Recommended: 2 for the scripts (they are genuinely upstream tools), 3 for the
book chapters (they are external reading, already described as such in prose).

## Acceptance

- `python ultimate-dev/tools/check-links.py --quiet` drops to a count that is
  explained line by line, with zero unexplained breakage
- Every remaining entry is classified in `evals/.results/known-missing.md`
