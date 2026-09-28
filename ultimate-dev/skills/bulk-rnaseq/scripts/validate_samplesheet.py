#!/usr/bin/env python3
"""Validate an nf-core/rnaseq samplesheet before committing compute.

What it does
------------
Checks a CSV samplesheet against the format ``nf-core/rnaseq`` requires, and
against the experimental-design rules this skill holds the study to:

* header present, and carrying ``sample``, ``fastq_1``, ``fastq_2``,
  ``strandedness`` (extra columns are reported, not rejected)
* every ``fastq_1`` present on disk, and gzipped
* ``fastq_2`` empty (single-end) or also present
* sample IDs usable, with repeated IDs recognised as multi-lane rows rather than
  an error
* ``strandedness`` one of auto / forward / reverse / unstranded
* at least 3 biological replicates per condition group, read off the sample ID
  convention (everything before the final ``_REP<n>``-style token)
* condition and batch are not perfectly confounded, judged from a ``batch``
  column if one is present

Expected input
--------------
A CSV with a header row, in the shape documented in ``references/upstream-nfcore.md``::

    sample,fastq_1,fastq_2,strandedness
    CONTROL_REP1,/data/ctrl1_R1.fastq.gz,/data/ctrl1_R2.fastq.gz,auto

Usage
-----
    python scripts/validate_samplesheet.py --samplesheet samplesheet.csv

Exit codes: 0 no problems, 1 problems found, 2 the file could not be read.

Provenance
----------
Reconstructed to check the samplesheet contract this skill's SKILL.md and
``references/upstream-nfcore.md`` describe. The group- and batch-contingency
checks are this file's own reading of ``references/design-and-qc.md``, and they
work from the sample-ID convention rather than from a metadata file, because the
samplesheet has no group column in the nf-core format.
"""

from __future__ import annotations

import argparse
import csv
import os
import re
import sys
from collections import defaultdict

REQUIRED_COLUMNS = ("sample", "fastq_1", "fastq_2", "strandedness")
VALID_STRANDEDNESS = {"auto", "forward", "reverse", "unstranded"}
MIN_REPLICATES = 3
# CONTROL_REP1, treated_rep3, D0_R2 ... — the trailing token is the replicate.
GROUP_SPLIT = re.compile(r"^(?P<group>.+?)[._-]?(?:rep)?[._-]?(?P<rep>\d+)$", re.IGNORECASE)


class Report:
    """Collects problems and warnings, and prints them in a stable order."""

    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.notes: list[str] = []

    def error(self, message: str) -> None:
        self.errors.append(message)

    def warn(self, message: str) -> None:
        self.warnings.append(message)

    def note(self, message: str) -> None:
        self.notes.append(message)

    def emit(self) -> None:
        for message in self.errors:
            print(f"error: {message}")
        for message in self.warnings:
            print(f"warning: {message}")
        for message in self.notes:
            print(f"note: {message}")
        print(
            f"\n{len(self.errors)} error(s), {len(self.warnings)} warning(s), "
            f"{len(self.notes)} note(s)"
        )


def read_samplesheet(path: str, report: Report) -> list[dict] | None:
    """Read the CSV into dicts with lowercase, stripped keys."""
    if not os.path.isfile(path):
        report.error(f"samplesheet not found: {path}")
        return None
    with open(path, newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            report.error(f"{path} is empty; a header row is required")
            return None
        headers = {name.strip().lower() for name in reader.fieldnames if name}
        missing = [name for name in REQUIRED_COLUMNS if name not in headers]
        if missing:
            report.error(
                f"{path} is missing required column(s) {', '.join(missing)}; "
                f"nf-core/rnaseq requires {', '.join(REQUIRED_COLUMNS)}"
            )
            return None
        rows = []
        for raw in reader:
            row = {
                (key.strip().lower() if key else ""): (value or "").strip()
                for key, value in raw.items()
            }
            if any(row.values()):
                rows.append(row)
    if not rows:
        report.error(f"{path} has a header but no data rows")
        return None
    extra = headers - set(REQUIRED_COLUMNS)
    if extra:
        report.note(f"extra column(s) carried through: {', '.join(sorted(extra))}")
    return rows


def check_fastq(path: str, report: Report, label: str, required: bool) -> None:
    """Confirm one FASTQ path exists and looks gzipped."""
    if not path:
        if required:
            report.error(f"{label} is empty")
        return
    if not os.path.exists(path):
        report.error(f"{label} does not exist: {path}")
        return
    if os.path.isdir(path):
        report.error(f"{label} is a directory, not a FASTQ file: {path}")
        return
    if not (path.endswith(".gz") or path.endswith(".bz2") or path.endswith(".xz")):
        report.warn(f"{label} is not compressed; nf-core/rnaseq expects gzipped FASTQ: {path}")


def group_of(sample: str) -> str:
    """Read the condition group off a sample ID, e.g. CONTROL_REP1 -> CONTROL."""
    match = GROUP_SPLIT.match(sample)
    if match:
        return match.group("group").strip("._-").upper() or sample.upper()
    return sample.upper()


def check_replication(rows: list[dict], report: Report) -> dict[str, set[str]]:
    """Report the replicate count per condition group, read off the sample IDs."""
    samples_by_group: dict[str, set[str]] = defaultdict(set)
    lanes_by_sample: dict[str, int] = defaultdict(int)
    for row in rows:
        sample = row["sample"]
        samples_by_group[group_of(sample)].add(sample)
        lanes_by_sample[sample] += 1

    for sample, lanes in sorted(lanes_by_sample.items()):
        if lanes > 1:
            report.note(
                f"{sample} appears on {lanes} lanes; nf-core/rnaseq merges rows that "
                "share a sample ID, which is correct for multi-lane sequencing"
            )

    if len(samples_by_group) < 2:
        report.warn(
            f"only one condition group was detected ({', '.join(samples_by_group)}). "
            "Differential expression needs at least two."
        )

    for group, samples in sorted(samples_by_group.items()):
        count = len(samples)
        if count < MIN_REPLICATES:
            report.error(
                f"group {group} has {count} biological replicate(s); {MIN_REPLICATES} is the "
                "floor for a differential-expression comparison"
            )
        else:
            report.note(f"group {group}: {count} replicate(s)")
    return samples_by_group


def check_confounding(rows: list[dict], report: Report) -> None:
    """If a batch column exists, check it is not perfectly aligned with condition."""
    if "batch" not in rows[0]:
        report.note(
            "no 'batch' column. Batch is anything technical that varies across samples "
            "(day, lane, kit lot, operator); record it in the DE metadata and model it "
            "as ~batch + condition if it is not confounded with condition."
        )
        return

    cells: dict[tuple[str, str], int] = defaultdict(int)
    for row in rows:
        batch = row.get("batch", "").strip() or "unrecorded"
        cells[(group_of(row["sample"]), batch)] += 1

    batches_by_group = defaultdict(set)
    groups_by_batch = defaultdict(set)
    for (group, batch) in cells:
        batches_by_group[group].add(batch)
        groups_by_batch[batch].add(group)

    for batch, groups in sorted(groups_by_batch.items()):
        if len(groups) == 1 and len(batches_by_group) > 1:
            offenders = ", ".join(sorted(groups))
            report.error(
                f"batch {batch} contains only {offenders}; condition and batch are "
                "confounded and the effect is mathematically unrecoverable"
            )
    for group, batches in sorted(batches_by_group.items()):
        if len(batches) == 1 and len(batches_by_group) > 1:
            report.error(
                f"group {group} was run in a single batch ({next(iter(batches))}); "
                "condition and batch are confounded"
            )
    report.note(
        "batch x condition cells: "
        + ", ".join(f"{group}/{batch}={count}" for (group, batch), count in sorted(cells.items()))
    )


def check_strandedness(rows: list[dict], report: Report) -> None:
    values = {row.get("strandedness", "").lower() for row in rows if row.get("strandedness")}
    unknown = sorted(values - VALID_STRANDEDNESS)
    if unknown:
        report.error(
            f"unrecognised strandedness value(s) {', '.join(unknown)}; expected one of "
            f"{', '.join(sorted(VALID_STRANDEDNESS))}"
        )
    if values == {"auto"}:
        report.note(
            "strandedness is 'auto' throughout; the pipeline will infer it with Salmon and "
            "warn on a mismatch. TruSeq stranded mRNA is typically 'reverse'."
        )
    mixed = values - {"auto"}
    if len(mixed) > 1:
        report.error(
            f"mixed strandedness across samples ({', '.join(sorted(values))}); quantify every "
            "sample the same way, or the library geometry will not be comparable"
        )


def check_samples(rows: list[dict], report: Report) -> None:
    seen: set[str] = set()
    for index, row in enumerate(rows, start=2):
        sample = row.get("sample", "")
        if not sample:
            report.error(f"line {index}: 'sample' is empty")
            continue
        if sample in seen:
            report.note(f"line {index}: sample {sample} repeats (treated as another lane)")
        seen.add(sample)
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", sample):
            report.warn(
                f"line {index}: sample ID {sample!r} contains characters nf-core may not "
                "accept in output filenames; prefer letters, digits, dot, underscore, hyphen"
            )
        check_fastq(row.get("fastq_1", ""), report, f"line {index} fastq_1", required=True)
        check_fastq(row.get("fastq_2", ""), report, f"line {index} fastq_2", required=False)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate an nf-core/rnaseq samplesheet before launching the pipeline.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--samplesheet", required=True, help="CSV samplesheet to validate")
    args = parser.parse_args(argv)

    report = Report()
    rows = read_samplesheet(args.samplesheet, report)
    if rows is None:
        report.emit()
        return 2

    check_samples(rows, report)
    check_strandedness(rows, report)
    check_replication(rows, report)
    check_confounding(rows, report)

    report.emit()
    return 1 if report.errors else 0


if __name__ == "__main__":
    sys.exit(main())
