#!/usr/bin/env python3
"""Validate BAM, bigWig, and BED files before running deepTools.

What it does
------------
For every file given, checks that it exists and is readable, reports its size,
sniffs the container format, and checks the index or companion file deepTools
needs:

* **BAM** — BGZF magic, and a ``.bai`` (or ``.bam.bai`` / ``.csi``) index. Also
  reports the first record's header, if ``pysam`` is installed, so you can confirm
  the sort order and reference build.
* **bigWig** — bigWig magic, and a companion ``.bw``-adjacent ``.bigwig`` header
  check where possible.
* **BED** — column count against the declared columns, sorted start/end
  coordinates, no negative or reversed intervals.

It is a preflight check, not a replacement for ``samtools quickcheck`` or
pysam. Nothing is modified and no index is created.

Usage
-----
    python scripts/validate_files.py --bam sample1.bam sample2.bam --bed regions.bed
    python scripts/validate_files.py --bam *.bam --bed peaks.bed --bigwig signal.bw
    python scripts/validate_files.py --bam in.bam --expect-build hg38

Exit codes: 0 all files usable, 1 problems found, 2 bad input.

Provenance
----------
Reconstructed from the "File Validation" and "scripts/validate_files.py" sections
of this skill's SKILL.md, which name the checks: existence, readability, BAM
indices, BED format, and file size. The format sniffers and the BED coordinate
checks are this file's own.
"""

from __future__ import annotations

import argparse
import gzip
import os
import struct
import sys
from pathlib import Path

# A BAM file is BGZF-compressed, whose member header starts with the gzip magic.
GZIP_MAGIC = b"\x1f\x8b"
# little-endian magic for the uncompressed BAM stream
BAM_MAGIC = b"BAM\x01"
BIGWIG_MAGIC = b"\x26\xfc\x8f\x88"
BED_MIN_COLUMNS = 3
MAX_BED_LINES = 5_000_000
EMPTY_SIZE = 0
# A file under this size is almost always truncated rather than legitimately small.
SUSPICIOUSLY_SMALL_BAM = 1024
SUSPICIOUSLY_SMALL_BIGWIG = 100
BED_CHROM_COLUMN = 0
BED_START_COLUMN = 1
BED_END_COLUMN = 2

HUMAN = 100 * 1024 * 1024


class Report:
    """One entry per file, with the findings accumulated against it."""

    def __init__(self, path: str, kind: str) -> None:
        self.path = path
        self.kind = kind
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.notes: list[str] = []

    def error(self, message: str) -> None:
        self.errors.append(message)

    def warn(self, message: str) -> None:
        self.warnings.append(message)

    def note(self, message: str) -> None:
        self.notes.append(message)

    def ok(self) -> bool:
        return not self.errors

    def render(self) -> str:
        status = "OK" if self.ok() else "FAIL"
        lines = [f"[{status}] {self.kind}: {self.path}"]
        for note in self.notes:
            lines.append(f"    note: {note}")
        for warning in self.warnings:
            lines.append(f"    warning: {warning}")
        for error in self.errors:
            lines.append(f"    error: {error}")
        return "\n".join(lines)


def human_size(size: int) -> str:
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if size < 1024 or unit == "TB":
            return f"{size:.1f} {unit}" if unit != "B" else f"{size} B"
        size /= 1024
    return f"{size:.1f} TB"


def check_readable(path: str, report: Report) -> bool:
    """Existence, type, and read permission, in that order."""
    file_path = Path(path)
    if not file_path.exists():
        report.error("file does not exist")
        return False
    if file_path.is_dir():
        report.error("path is a directory, not a file")
        return False
    if not os.access(file_path, os.R_OK):
        report.error("file is not readable by the current user")
        return False
    size = file_path.stat().st_size
    if size == EMPTY_SIZE:
        report.error("file is empty")
        return False
    report.note(f"size {human_size(file_path.stat().st_size)}")
    return True


def find_index(bam_path: Path) -> Path | None:
    """The index deepTools or samtools will look for."""
    for candidate in (
        bam_path.with_suffix(bam_path.suffix + ".bai"),
        bam_path.with_suffix(".bai"),
        bam_path.with_suffix(".csi"),
        bam_path.with_suffix(bam_path.suffix + ".csi"),
    ):
        if candidate.is_file():
            return candidate
    return None


def check_bam(path: str, report: Report, expect_build: str | None) -> None:
    """BGZF magic, index presence, and, with pysam, sort order and build."""
    if not check_readable(path, report):
        return
    file_path = Path(path)
    size = file_path.stat().st_size
    if size < SUSPICIOUSLY_SMALL_BAM:
        report.warn(
            f"file is only {size} bytes; a BAM with any alignments is larger than this. "
            "Check that the file finished transferring."
        )

    with file_path.open("rb") as handle:
        magic = handle.read(4)
    if magic[:2] != GZIP_MAGIC:
        report.error(
            f"does not start with the gzip/BGZF magic bytes (found {magic!r}). "
            "If this is a SAM file, convert it with `samtools view -b`."
        )
    else:
        try:
            with gzip.open(file_path, "rb") as stream:
                stream_magic = stream.read(4)
        except OSError as exc:
            report.error(f"BGZF stream is unreadable, which usually means truncation: {exc}")
        else:
            if stream_magic != BAM_MAGIC:
                report.error(
                    f"BGZF stream does not start with {BAM_MAGIC!r} (found {stream_magic!r}); "
                    "it is a compressed SAM, not a BAM"
                )
            else:
                report.note("BGZF and BAM magic bytes are correct")

    index = find_index(file_path)
    if index is None:
        report.error(
            "no BAM index found. deepTools and samtools both need one; create it with "
            f"`samtools index {file_path.name}`"
        )
    else:
        report.note(f"index {index.name} present")

    try:
        import pysam
    except ImportError:
        report.note("pysam is not installed, so the header and sort order were not read")
        return
    try:
        with pysam.AlignmentFile(str(file_path), "rb") as bam:
            sort_order = bam.header.get("HD", {}).get("SO", "unspecified")
            references = list(bam.references)
            report.note(f"sort order: {sort_order}")
            if sort_order not in ("coordinate",):
                report.warn(
                    f"BAM is sorted by {sort_order}. Almost every deepTools command needs a "
                    "coordinate-sorted BAM; re-sort with `samtools sort`."
                )
            if not references:
                report.error("header lists no reference sequences")
            else:
                report.note(f"{len(references)} reference sequence(s), first is {references[0]}")
                for name in references[:3]:
                    if expect_build and name.startswith(expect_build.replace("hg", "chr")):
                        report.note(f"reference {name} matches the expected build {expect_build}")
                if expect_build:
                    prefix = "chr" if references[0].startswith("chr") else ""
                    if not any(name.startswith(f"{prefix}{expect_build.lstrip('hg')[:2]}") for name in references):
                        report.warn(
                            f"no reference name looks like {expect_build} "
                            f"(first reference is {references[0]}). A BAM and a BED file on "
                            "different builds will produce empty or nonsense regions."
                        )
    except Exception as exc:  # pysam raises a variety of types on malformed BAM
        report.error(f"pysam could not open the BAM: {exc}")


def check_bigwig(path: str, report: Report) -> None:
    """bigWig magic; a bigWig is not compressed, so this is a direct read."""
    if not check_readable(path, report):
        return
    file_path = Path(path)
    size = file_path.stat().st_size
    if size < SUSPICIOUSLY_SMALL_BIGWIG:
        report.warn(f"file is only {size} bytes, which is too small to be a usable bigWig")

    with file_path.open("rb") as handle:
        magic = handle.read(4)
    if magic == BIGWIG_MAGIC:
        report.note("bigWig magic bytes are correct")
        if size > 64:
            with file_path.open("rb") as handle:
                handle.seek(4)
                (version, zoom_levels) = struct.unpack("<HH", handle.read(4))
            report.note(f"bigWig version {version}, {zoom_levels} zoom level(s)")
            if version == 0:
                report.warn(
                    "version 0 bigWigs predate header compression and are slower to read; "
                    "regenerate with the current deepTools"
                )
    elif magic == GZIP_MAGIC:
        report.error(
            "file starts with gzip bytes. A bedGraphToBigWig output is not gzipped; this may "
            "be a compressed bedGraph. Convert it with bedGraphToBigWig."
        )
    else:
        report.error(
            f"does not start with the bigWig magic bytes (found {magic!r}); it may be a "
            "bedGraph, a wig, or a truncated file"
        )


def check_bed(path: str, report: Report, expect_columns: int | None) -> None:
    """Column count, coordinate sanity, and a sortedness note."""
    if not check_readable(path, report):
        return

    lines = 0
    problems = 0
    previous_start: tuple[str, int] | None = None
    observed_columns: set[int] = set()
    opener = gzip.open if str(path).endswith(".gz") else open

    try:
        with opener(path, "rt", encoding="utf-8", errors="replace") as handle:  # type: ignore[operator]
            for number, line in enumerate(handle, start=1):
                if number == 1 and (line.startswith("track") or line.startswith("browser")
                                    or line.startswith("#")):
                    continue
                fields = line.rstrip("\n").split("\t")
                if len(fields) < BED_MIN_COLUMNS:
                    if problems < 3:
                        report.error(
                            f"line {number} has {len(fields)} column(s); BED needs at least "
                            f"{BED_MIN_COLUMNS} (chrom, start, end)"
                        )
                    problems += 1
                    continue
                observed_columns.add(len(fields))
                try:
                    start = int(fields[BED_START_COLUMN])
                    end = int(fields[BED_END_COLUMN])
                except ValueError:
                    if problems < 3:
                        report.error(
                            f"line {number} has a non-integer coordinate: "
                            f"{fields[BED_START_COLUMN]!r}-{fields[BED_END_COLUMN]!r}"
                        )
                    problems += 1
                    continue
                if start < 0:
                    report.error(f"line {number} has a negative start ({start})")
                    problems += 1
                if end <= start:
                    report.error(
                        f"line {number} has end ({end}) at or before start ({start}); BED "
                        "intervals are half-open and end must exceed start"
                    )
                    problems += 1
                key = (fields[BED_CHROM_COLUMN], start)
                if previous_start is not None and key < previous_start:
                    if problems < 3:
                        report.warn(
                            f"line {number} goes backwards: {fields[BED_CHROM_COLUMN]}:"
                            f"{start} follows {previous_start[0]}:{previous_start[1]}. "
                            "sort with `sort -k1,1 -k2,2n`"
                        )
                    problems += 1
                else:
                    previous_start = key
                lines += 1
                if lines >= MAX_BED_LINES:
                    report.note(f"stopped checking after {MAX_BED_LINES} intervals")
                    break
    except OSError as exc:
        report.error(f"could not read the file: {exc}")
        return

    if lines == 0:
        report.error("no data intervals found")
        return
    report.note(f"{lines} interval(s) checked")

    if observed_columns:
        widths = sorted(observed_columns)
        if len(widths) > 1:
            report.warn(
                f"rows have inconsistent column counts {widths}. deepTools reads BED6 for "
                "most tools and BED12 (BED6 + blockCount/blockSizes/blockStarts) for "
                "computeMatrix scale-regions; mixed widths will be read inconsistently."
            )
        columns = widths[0]
        report.note(f"{columns} column(s) per interval")
        if expect_columns and columns != expect_columns:
            report.error(
                f"expected {expect_columns} columns per interval (--expect-columns) but the "
                f"file has {columns}"
            )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate BAM, bigWig, and BED files before running deepTools.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--bam", nargs="+", default=[], help="BAM files to validate")
    parser.add_argument("--bigwig", nargs="+", default=[], help="bigWig files to validate")
    parser.add_argument("--bed", nargs="+", default=[], help="BED files to validate")
    parser.add_argument(
        "--expect-columns", type=int, default=None,
        help="require this many columns per BED interval (3, 6, or 12)",
    )
    parser.add_argument(
        "--expect-build", default=None,
        help="expected genome build, e.g. hg38, checked against the BAM reference names",
    )
    parser.add_argument(
        "--min-size", action="store_true",
        help="only report problems; skip the notes and sizes",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if not (args.bam or args.bigwig or args.bed):
        raise SystemExit("error: give at least one of --bam, --bigwig, or --bed")

    reports: list[Report] = []
    for path in args.bam:
        report = Report(path, "BAM")
        check_bam(path, report, args.expect_build)
        reports.append(report)
    for path in args.bigwig:
        report = Report(path, "bigWig")
        check_bigwig(path, report)
        reports.append(report)
    for path in args.bed:
        report = Report(path, "BED")
        check_bed(path, report, args.expect_columns)
        reports.append(report)

    failed = 0
    for report in reports:
        if not report.ok():
            failed += 1
        if args.min_size and report.ok() and not report.warnings:
            continue
        print(report.render())
        print()

    warnings = sum(len(report.warnings) for report in reports)
    print(f"{len(reports) - failed}/{len(reports)} file(s) usable, {warnings} warning(s)")
    if failed:
        print("\nFix the errors above before running deepTools. Every error here is one "
              "deepTools will report later as an opaque failure or, worse, as a silently "
              "empty result.")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
