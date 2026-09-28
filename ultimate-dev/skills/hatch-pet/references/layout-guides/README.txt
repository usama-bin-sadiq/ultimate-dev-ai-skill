Generated layout guides
========================

Provenance
----------
This README is authored, not recovered. It exists because the work list calls for
a file at references/layout-guides/ and the only thing that belongs there is
generated output. The guides themselves are PNGs, which this tree does not ship;
they are written by the run, and this text file is here so the directory is not
mistaken for a set of hand-drawn references.

This directory holds the row-specific layout guide images for a pet run. It is
not a shipped asset directory: every file in it is produced at run time by

    python scripts/prepare_pet_run.py --name <pet-name> --out <run-dir>

which writes one guide per animation state under

    <run-dir>/references/layout-guides/<state>.png

There are nine states, one per row of the sprite atlas: base, idle,
running-right, running-left, and the remaining rows defined in ROWS inside
prepare_pet_run.py. Each guide is a transparent-construction image at the
atlas cell size for that row's frame count, drawn with:

  * a 2px cell border per frame, so the model can count frames;
  * an inner safe area inset by LAYOUT_GUIDE_SAFE_MARGIN_X / _Y, in a guide
    blue, marking the padding a character must not cross;
  * dashed horizontal and vertical center marks through each cell.

The guides are layout-only inputs. A generated row strip must not reproduce any
of it: no visible boxes, no borders, no center marks, no guide colours, no
labels, no guide background. A strip carrying guide pixels has failed QA, and
validate_atlas.py will not pass it.

Nothing in this directory is checked in. If you are reading this file in a fresh
clone and the directory is otherwise empty, that is correct: run
prepare_pet_run.py first, and the guides appear inside the run directory, not
here.
