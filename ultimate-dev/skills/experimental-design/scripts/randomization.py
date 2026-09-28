"""Seeded, reproducible randomization and allocation schedules.

Public functions
----------------
``simple_randomization``            permute arm labels for n independent units
``block_randomization``             permuted blocks, so arms stay balanced as you enrol
``stratified_block_randomization``  randomize within strata, balancing a prognostic factor
``cluster_randomization``           randomize whole clusters; the cluster is the unit
``assign_factorial_runs``           attach a randomized run order to a DOE matrix
``arm_balance``                     counts per arm, and how far off balance the schedule is

Why seeding is not optional here
--------------------------------
Every function takes a ``seed`` and every one of them is a pure function of
(seed, arguments). That is what makes a schedule archivable and regenerable: a
trial registration, a lab notebook, and a reanalysis three years later all have
to produce the identical schedule, and "the same code" is not enough unless the
seed is written down next to it. The seed is returned in ``schedule.attrs``
so it can be archived with the layout rather than remembered separately.

Units of randomization
----------------------
The unit that is randomized is the unit in the analysis. When treatment is
delivered to a group, the group is the unit, and ``cluster_randomization`` is
the only correct call — randomizing individuals inside a cluster and then
analysing at cluster level is pseudoreplication, and no analysis recovers from
it.

Provenance
----------
Reconstructed to match the API documented in this skill's SKILL.md and
``references/randomization_and_blocking.md``. The scheduling algorithms are
standard (permuted blocks of random size, stratified permuted blocks, complete
randomization of clusters); the implementation and the balance diagnostics are
this file's own.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

# A permuted block's size. Variable block sizes hide the assignment pattern from
# whoever is enrolling; a fixed size is guessable from the previous few
# assignments, which is the reason variable sizes exist.
MIN_BLOCK = 4
MAX_BLOCK = 6


def _rng(seed: int | None) -> np.random.Generator:
    """One generator per call, so a function's output depends only on its seed."""
    return np.random.default_rng(seed)


def _schedule(assignments: list[str], unit_ids: list, seed: int | None, method: str) -> pd.DataFrame:
    """Build the standard schedule frame and record the seed on it."""
    frame = pd.DataFrame({"unit": unit_ids, "arm": assignments})
    frame.attrs["seed"] = seed
    frame.attrs["method"] = method
    return frame


def _check_arms(arms) -> list[str]:
    arms = [str(arm) for arm in arms]
    if len(arms) < 2:
        raise ValueError("at least two arms are needed for a comparison")
    if len(set(arms)) != len(arms):
        raise ValueError("arm names must be distinct")
    return arms


def simple_randomization(n: int, arms, seed: int | None = None) -> pd.DataFrame:
    """Assign n independent units to arms by permutation.

    Fine for large n. At small n it can leave the arms badly unbalanced — with
    n=12 and two arms, a 9/3 split is a real possibility and not a bug — and it
    is predictable for small numbers of arms, which is a practical problem in
    unblinded enrolment. Use ``block_randomization`` when n is small or enrolment
    is sequential.
    """
    if n < 1:
        raise ValueError("n must be at least 1")
    arms = _check_arms(arms)
    labels = np.repeat(np.array(arms, dtype=object), int(np.ceil(n / len(arms))))[:n]
    generator = _rng(seed)
    generator.shuffle(labels)
    return _schedule(list(labels), list(range(1, n + 1)), seed, "simple_randomization")


def block_randomization(
    n: int,
    arms,
    seed: int | None = None,
    block_size: int | None = None,
) -> pd.DataFrame:
    """Permuted-block randomization: blocks that are small and of random size.

    Every complete block holds a whole number of each arm, so the arms are
    balanced at every multiple of the block size rather than only at the end.
    That is the point: in a trial stopped early for benefit or harm, the
    participants already enrolled are still balanced.

    A final incomplete block is filled as evenly as possible; it cannot be a
    whole block, and the imbalance it leaves is reported by ``arm_balance``.
    """
    if n < 1:
        raise ValueError("n must be at least 1")
    arms = _check_arms(arms)
    generator = _rng(seed)
    k = len(arms)
    if block_size is None:
        block_size = 2 * k
    if block_size % k:
        raise ValueError(f"block_size={block_size} is not a multiple of {k} arms")
    if block_size < k:
        raise ValueError(f"block_size must be at least {k} for {k} arms")

    assignments: list[str] = []
    while len(assignments) < n:
        size = block_size
        if block_size > MIN_BLOCK * k:
            # Vary the size in multiples of k, so every block is still whole.
            multiples = block_size // k
            size = int(generator.integers(max(1, multiples // 2), multiples + 1)) * k
        per_arm = size // k
        block = np.repeat(np.array(arms, dtype=object), per_arm)
        generator.shuffle(block)
        assignments.extend(str(label) for label in block[: n - len(assignments)])

    return _schedule(assignments, list(range(1, n + 1)), seed, "block_randomization")


def stratified_block_randomization(
    strata_sizes: dict,
    arms,
    ratio=None,
    seed: int | None = None,
) -> pd.DataFrame:
    """Randomize within each stratum, so a prognostic factor is balanced too.

    ``strata_sizes`` maps stratum label to the number of units in it (site, sex
    band, disease severity band, and so on). ``ratio`` gives the intended arm
    allocation, e.g. ``(2, 1)`` for two treated per one placebo. Each stratum is
    independently permuted-block randomized at the same ratio, which is what
    makes the factor orthogonal to treatment by construction rather than by hope.

    A stratum whose size is not a whole multiple of the ratio is allocated as
    evenly as its remainder allows, and the remainder is reported.
    """
    arms = _check_arms(arms)
    if ratio is None:
        ratio = tuple([1] * len(arms))
    ratio = tuple(int(value) for value in ratio)
    if len(ratio) != len(arms):
        raise ValueError("ratio must have one entry per arm")
    if any(value < 1 for value in ratio):
        raise ValueError("every ratio entry must be at least 1")

    generator = _rng(seed)
    unit_ratio = sum(ratio)
    rows: list[dict] = []
    unit_number = 1

    for stratum, size in strata_sizes.items():
        size = int(size)
        if size < 1:
            raise ValueError(f"stratum {stratum!r} has size {size}")
        # As many whole ratio-blocks as fit, then the remainder filled as evenly
        # as possible.
        blocks, remainder = divmod(size, unit_ratio)
        labels: list[str] = []
        for _ in range(blocks):
            block: list[str] = []
            for arm, weight in zip(arms, ratio):
                block.extend([arm] * weight)
            generator.shuffle(block)
            labels.extend(block)
        if remainder:
            fill = _largest_remainder_fill(remainder, arms, ratio)
            generator.shuffle(fill)
            labels.extend(fill)

        for label in labels[:size]:
            rows.append({"unit": unit_number, "stratum": stratum, "arm": label})
            unit_number += 1

    frame = pd.DataFrame(rows, columns=["unit", "stratum", "arm"])
    frame.attrs["seed"] = seed
    frame.attrs["method"] = "stratified_block_randomization"
    frame.attrs["ratio"] = ratio
    return frame


def _largest_remainder_fill(size: int, arms: list[str], ratio: tuple) -> list[str]:
    """Split an incomplete block across arms as evenly as the ratio allows."""
    exact = [size * weight / sum(ratio) for weight in ratio]
    counts = [int(value) for value in exact]
    shortfall = size - sum(counts)
    order = sorted(range(len(arms)), key=lambda i: (-(exact[i] - counts[i]), i))
    for position in range(shortfall):
        counts[order[position % len(order)]] += 1
    fill: list[str] = []
    for arm, count in zip(arms, counts):
        fill.extend([arm] * count)
    return fill


def cluster_randomization(
    clusters,
    seed: int | None = None,
    arms=None,
) -> pd.DataFrame:
    """Randomize whole clusters to arms; the cluster is the unit.

    With a handful of clusters, plain randomization can put two clusters in the
    same arm. That is not a nuisance — it is a design failure, because an arm
    with one cluster has no within-arm variance to compare against. Clusters are
    therefore allocated in blocks covering each arm once, so every arm ends up
    with a whole number of clusters wherever the counts allow.

    Fewer clusters than arms is infeasible rather than a reason to drop an arm,
    so this raises and says so.
    """
    clusters = [str(cluster) for cluster in clusters]
    if len(clusters) < 2:
        raise ValueError("at least two clusters are needed")
    if len(set(clusters)) != len(clusters):
        raise ValueError("cluster names must be distinct")
    if arms is None:
        arms = ["arm_a", "arm_b"] if len(clusters) <= 9 else [
            "arm_a", "arm_b", "arm_c", "arm_d"
        ]
    arms = _check_arms(arms)
    if len(clusters) < len(arms):
        raise ValueError(
            f"{len(clusters)} clusters cannot fill {len(arms)} arms. Either reduce the "
            "number of arms or add clusters; an arm with no cluster is an arm with no "
            "within-cluster variance, which makes the comparison uninterpretable."
        )

    generator = _rng(seed)
    pool = list(arms)
    assignments: list[str] = []
    remaining = list(clusters)
    while remaining:
        block_size = min(len(pool), len(remaining))
        block = list(pool[:block_size])
        generator.shuffle(block)
        generator.shuffle(remaining)
        assignments.extend(block[:block_size])
        remaining = remaining[block_size:]

    order = {name: index for index, name in enumerate(clusters)}
    frame = _schedule(assignments, clusters, seed, "cluster_randomization")
    frame = frame.sort_values("unit", key=lambda column: column.map(order)).reset_index(drop=True)
    return frame


def assign_factorial_runs(
    design: pd.DataFrame,
    seed: int | None = None,
    block_column: str | None = None,
) -> pd.DataFrame:
    """Add a randomized run order to a DOE matrix.

    Randomizing run order is what stops a factor from being confounded with time.
    Machine warm-up, reagent aging, operator drift and plate position all move
    with run number, so a design executed in the order it was written in is a
    design in which run order is a factor you did not declare.

    ``block_column`` randomizes within blocks and keeps the blocks in order, for
    the case where a block is a batch or a day that genuinely cannot be
    interleaved.
    """
    if design.empty:
        raise ValueError("the design is empty")

    frame = design.copy()
    generator = _rng(seed)

    if block_column and block_column in frame.columns:
        frame = frame.sort_values(block_column, kind="stable")
        order = []
        for _block, group in frame.groupby(block_column, sort=True):
            indices = group.index.to_numpy().copy()
            generator.shuffle(indices)
            order.extend(indices.tolist())
        frame = frame.loc[order]
    else:
        indices = frame.index.to_numpy().copy()
        generator.shuffle(indices)
        frame = frame.loc[indices]

    frame = frame.reset_index(drop=True)
    # doe_designs already stamps a "run" column; replace it rather than colliding,
    # so a design can be passed straight through without the caller stripping it.
    if "run" in frame.columns:
        frame = frame.drop(columns=["run"])
    frame.insert(0, "run", range(1, len(frame) + 1))
    frame.attrs["seed"] = seed
    frame.attrs["method"] = "assign_factorial_runs"
    return frame


def arm_balance(schedule: pd.DataFrame) -> dict:
    """Count the arms and report how far from balanced the schedule is.

    The max-minus-min spread is the number that matters: a 2:1 allocation on an
    odd n is off by one by construction, and a spread of one in that case is
    correct, not a defect. A large spread on a completed schedule is the thing
    to look at.
    """
    if "arm" not in schedule.columns:
        raise ValueError("the schedule has no 'arm' column")
    counts = schedule["arm"].value_counts().sort_index()
    n = int(counts.sum())
    spread = int(counts.max() - counts.min()) if len(counts) else 0
    shares = {str(arm): round(float(value) / n, 4) for arm, value in counts.items()} if n else {}

    report = {
        "n": n,
        "counts": {str(arm): int(value) for arm, value in counts.items()},
        "shares": shares,
        "max_min_spread": spread,
        "seed": schedule.attrs.get("seed"),
        "method": schedule.attrs.get("method"),
    }

    if "stratum" in schedule.columns:
        per_stratum = schedule.groupby("stratum")["arm"].value_counts().unstack(fill_value=0)
        stratum_spreads = {
            str(stratum): int(row.max() - row.min()) for stratum, row in per_stratum.iterrows()
        }
        report["per_stratum_spread"] = stratum_spreads
        report["worst_stratum_spread"] = max(stratum_spreads.values(), default=0)
    return report
