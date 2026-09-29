#!/usr/bin/env python3
"""Measure whether the judge is consistent with itself, before trusting it.

This is the gate every other number in this repository sits behind.

The question the corpus asks is "did the kernel pick the right architecture for
this task", and answering it means comparing the kernel's choice against a
declared correct one. That comparison is made by a judge -- a model, or a
person, or a rule. A judge that gives a different answer when asked the same
question twice makes every agreement number derived from it meaningless, and the
failure is silent: the numbers still print.

Measured elsewhere in the literature: inter-rater reliability computed on LLM
judges ranged from 0.167 to 1.00 across runs that differed only in random seed.
A metric built on a judge with that much seed variance measures the seed.

So there are three separate things, and only the first is a prerequisite:

  consistency  Does this judge give the same answer when asked the same
               question again? McDonald's omega over repeated judgements.
               This is a property of the judge ALONE and needs no ground truth.

  agreement    Do this judge and another rater agree on the answers? This needs
               Krippendorff's alpha, and the metric depends on the rating
               design -- Cohen's kappa for exactly two fixed raters, Fleiss for
               a fixed-size panel, Krippendorff for ordinal scales, varying
               panel membership, or missing data. Using the wrong one is a
               silent validity failure.

  accuracy     Does the judge's answer match the declared oracle? Only
               meaningful once the two above are reported.

`measure-judge.py` does the first and refuses to let the third be quoted
without it. It writes a verdict file; `run-bench.py` reads it and declines to
print an accuracy figure if the verdict is absent or below threshold.

Thresholds are declared here rather than tuned to a result, which is the only
way a threshold stays honest:

  omega >= 0.70   the judge agrees with itself across repeats
  alpha  >= 0.80   the judge agrees with an independent rater

Both are the values recommended in the psychometric literature for this design.
Neither has been met here, and this script does not pretend otherwise: with
nothing to measure, it writes `not-measured` and exits 1.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import statistics
import sys

OMEGA_FLOOR = 0.70
ALPHA_FLOOR = 0.80

VERDICT_PATH = pathlib.Path(__file__).resolve().parent / "judge-verdict.json"

# Cronbach's alpha / McDonald's omega, ordinal ratings on a small fixed scale.
# Implemented here rather than pulled in, because a gate that cannot run in the
# environment it guards is a gate that gets skipped.


def _ordinal_distance(a: int, b: int, k: int) -> float:
    """Normalised disagreement between two ordinal scores, 0 .. 1."""
    return abs(a - b) / max(1, k - 1)


def krippendorff_alpha(
    ratings: list[list[int | None]], scale: list[int]
) -> tuple[float | None, str]:
    """Krippendorff's alpha for ordinal data, with missing values allowed.

    `ratings[i]` is one item's ratings across raters/replicates; None is a
    missing rating. Ordinal metric: disagreement is the normalised distance
    between ranks, so two raters one step apart disagree less than two raters
    at opposite ends -- a distinction binary mismatch throws away, and the
    divergence between the two metrics is itself diagnostic.

    Returns (alpha, reason). alpha is None when it is not computable, with the
    reason, because a gate that returns a number it cannot justify is the defect
    this repository keeps finding.
    """
    k = len(scale)
    usable = [r for r in ratings if any(v is not None for v in r)]
    if len(usable) < 2:
        return None, f"only {len(usable)} item(s) with at least one rating"

    # Observed disagreement: every within-item pair, weighted by distance.
    observed_num = 0.0
    observed_pairs = 0.0
    for row in usable:
        vals = [v for v in row if v is not None]
        for i in range(len(vals)):
            for j in range(i + 1, len(vals)):
                observed_num += _ordinal_distance(vals[i], vals[j], k)
                observed_pairs += 1
    if observed_pairs == 0:
        return None, "no item received two ratings, so agreement is not observable"

    # Expected disagreement: the same distance over the observed value
    # distribution, which is what two raters would produce by chance given the
    # marginals.
    flat = [v for row in usable for v in row if v is not None]
    counts = {s: flat.count(s) for s in scale}
    total = sum(counts.values())
    if total < 2:
        return None, "fewer than two ratings in total"
    expected_num = 0.0
    for s1, c1 in counts.items():
        for s2, c2 in counts.items():
            if s1 == s2:
                continue
            pairs = c1 * c2
            expected_num += pairs * _ordinal_distance(s1, s2, k)
    expected_pairs = total * (total - 1)
    if expected_pairs == 0 or expected_num == 0:
        # Every rating identical: perfect agreement, and the correction is
        # undefined. This is a real outcome, not an error.
        if observed_num == 0:
            return 1.0, "all ratings identical"
        return None, "expected disagreement is zero; alpha undefined"

    alpha = 1.0 - (observed_num / observed_pairs) / (expected_num / expected_pairs)
    return alpha, f"n_items={len(usable)} n_ratings={total}"


def consistency_from_ratings(ratings: list[list[int | None]], scale: list[int]) -> dict:
    """Self-consistency: the judge's agreement with itself across repeats."""
    alpha, why = krippendorff_alpha(ratings, scale)
    verdict = {
        "metric": "krippendorff_alpha_ordinal",
        "role": "self-consistency across repeats",
        "value": alpha,
        "floor": OMEGA_FLOOR,
        "detail": why,
    }
    verdict["meets_floor"] = alpha is not None and alpha >= OMEGA_FLOOR
    return verdict


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--ratings", type=pathlib.Path,
                    help="JSON: {item: [score, ...]} one list per item")
    ap.add_argument("--scale", default="0,1,2",
                    help="comma-separated ordinal scale, lowest first")
    ap.add_argument("--out", type=pathlib.Path, default=VERDICT_PATH)
    ap.add_argument("--require", action="store_true",
                    help="exit 1 unless every measure meets its floor")
    args = ap.parse_args()

    if not args.ratings or not args.ratings.is_file():
        payload = {
            "status": "not-measured",
            "reason": ("no ratings supplied. Run the benchmark's repeat arms and "
                       "pass --ratings to convert this into a number."),
            "self_consistency": None,
            "agreement_with_independent_rater": None,
            "accuracy_may_be_quoted": False,
        }
        args.out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        print("  judge consistency: NOT MEASURED")
        print(f"    wrote {args.out}")
        print("  accuracy figures are blocked until this is a number.")
        return 1

    scale = [int(x) for x in args.scale.split(",")]
    data = json.loads(args.ratings.read_text(encoding="utf-8"))
    ratings = [data[k] for k in sorted(data)]

    self_consistency = consistency_from_ratings(ratings, scale)
    payload = {
        "status": "measured",
        "self_consistency": self_consistency,
        "agreement_with_independent_rater": {
            "metric": "krippendorff_alpha_ordinal",
            "value": None,
            "floor": ALPHA_FLOOR,
            "detail": ("not measured. Needs a second, independent rater scoring the "
                       "same items. A single rater cannot produce an agreement "
                       "statistic, and reporting one would be reporting a "
                       "consistency figure under a second name."),
            "meets_floor": False,
        },
        "accuracy_may_be_quoted": self_consistency["meets_floor"],
    }
    args.out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    sc = payload["self_consistency"]
    print(f"  self-consistency  alpha={sc['value']}  floor={OMEGA_FLOOR}  "
          f"({'meets' if sc['meets_floor'] else 'BELOW'})")
    print(f"    {sc['detail']}")
    print("  agreement with an independent rater: NOT MEASURED")
    print(f"  wrote {args.out}")
    if not sc["meets_floor"]:
        print("  accuracy figures remain blocked: the judge is not yet shown to be")
        print("  consistent with itself, so agreement with it would not be evidence.")

    if args.require and not sc["meets_floor"]:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
