#!/usr/bin/env python3
"""Build a gene x sample counts matrix and a metadata template for PyDESeq2.

This is the reads -> DE bridge this skill owns: nothing upstream or downstream in
the repo does it. It reads one of three quantifier outputs and writes the two
files the ``pydeseq2`` skill wants.

Modes
-----
``--from salmon``
    Per-sample ``quant.sf`` files, aggregated to gene level with ``pytximport``
    using ``counts_from_abundance="length_scaled_tpm"`` and a ``--tx2gene`` map.
``--from star``
    ``*.ReadsPerGene.out.tab``, taking the column that matches ``--strandedness``.
``--from featurecounts``
    A single combined featureCounts matrix (``--counts-file``).

Outputs
-------
``counts.csv``
    Genes x samples, integers. Salmon estimates are rounded because PyDESeq2
    requires integers; with ``length_scaled_tpm`` the library size and
    transcript-length effects are already folded in, so rounding is a defensible
    approximation. Never feed TPM/FPKM here.
``metadata_template.csv``
    One row per sample with the design columns to fill in. The DE step transposes
    ``counts.csv``; keep it genes x samples and transpose once, not twice.

Usage
-----
    python scripts/build_counts_matrix.py --from salmon \\
        --quant-dir quant/ --tx2gene tx2gene.tsv --output-dir counts/
    python scripts/build_counts_matrix.py --from star \\
        --quant-dir star/ --strandedness reverse --output-dir counts/
    python scripts/build_counts_matrix.py --from featurecounts \\
        --counts-file counts/featureCounts.txt --output-dir counts/

Provenance
----------
Reconstructed to match the three input shapes and the two outputs documented in
``references/counts-and-handoff.md``. The salmon path really does call
``pytximport.tximport`` with the documented arguments; the STAR and featureCounts
parsers are this file's own.
"""

from __future__ import annotations

import argparse
import csv
import os
import sys
from pathlib import Path

STRANDEDNESS_COLUMNS = {"unstranded": 1, "forward": 2, "reverse": 3}
# STAR writes four summary rows before the gene table.
STAR_SUMMARY_PREFIXES = ("N_unmapped", "N_multimapping", "N_noFeature", "N_ambiguous")
# The metadata template's design columns, per references/design-and-qc.md.
DESIGN_COLUMNS = ("sample", "condition", "batch")


def log(message: str) -> None:
    print(message, file=sys.stderr, flush=True)


def _import_pandas():
    try:
        import pandas as pd
    except ImportError:
        raise SystemExit(
            "error: pandas is not installed. Run `uv pip install pytximport pandas` "
            "from the repo root."
        )
    return pd


def find_salmon_quants(quant_dir: Path) -> list[Path]:
    """Every ``quant.sf`` under quant_dir, one per sample directory."""
    quants = sorted(quant_dir.glob("*/quant.sf"))
    if not quants:
        quants = sorted(quant_dir.glob("**/quant.sf"))
    if not quants:
        raise SystemExit(
            f"error: no quant.sf found under {quant_dir}. Salmon writes one per sample "
            "directory, e.g. quant/<sample>/quant.sf."
        )
    return quants


def from_salmon(quant_dir: Path, tx2gene: str, output_dir: Path) -> None:
    """Aggregate Salmon transcript estimates to gene level with pytximport."""
    try:
        from pytximport import tximport
    except ImportError:
        raise SystemExit(
            "error: pytximport is not installed. Run `uv pip install pytximport pandas` "
            "from the repo root, or use --from star / --from featurecounts instead."
        )
    if not os.path.isfile(tx2gene):
        raise SystemExit(
            f"error: tx2gene map not found: {tx2gene}. It is a two-column "
            "transcript_id/gene_id table; see references/counts-and-handoff.md for how "
            "to build one from your annotation GTF."
        )

    quant_files = [str(path) for path in find_salmon_quants(quant_dir)]
    # The sample name is the directory holding quant.sf, which is the convention
    # Salmon and nf-core both use.
    samples = [Path(path).parent.name for path in quant_files]
    if len(set(samples)) != len(samples):
        raise SystemExit("error: two quant.sf files resolve to the same sample directory name")

    log(f"pytximport over {len(quant_files)} sample(s) with length_scaled_tpm")
    txi = tximport(
        quant_files,
        data_type="salmon",
        transcript_gene_map=tx2gene,
        counts_from_abundance="length_scaled_tpm",
        output_type="xarray",
        ignore_transcript_version=True,
    )
    counts = txi.counts
    # xarray gives (gene, sample); name the sample axis from the directories.
    genes = [str(gene) for gene in getattr(counts, "genes", getattr(counts, "index", []))]
    sample_axis = [str(name) for name in getattr(counts, "sample", samples)]
    if sample_axis != samples:
        # pytximport names samples after the file stems; re-map to directory names
        # in the order they were passed, which is the documented convention.
        sample_axis = samples
    values = [[float(v) for v in row] for row in counts.values]

    write_outputs(
        output_dir,
        genes,
        sample_axis,
        values,
        tool="salmon+pytximport",
        extra=f"counts_from_abundance=length_scaled_tpm; tx2gene={tx2gene}",
    )


def from_star(quant_dir: Path, strandedness: str, output_dir: Path) -> None:
    """Read each ReadsPerGene.out.tab and take the column for the library geometry."""
    column = STRANDEDNESS_COLUMNS[strandedness]
    files = sorted(quant_dir.glob("**/*ReadsPerGene.out.tab"))
    if not files:
        raise SystemExit(
            f"error: no *ReadsPerGene.out.tab found under {quant_dir}. STAR writes one "
            "per sample when run with --quantMode GeneCounts."
        )

    genes: list[str] | None = None
    samples: list[str] = []
    columns: list[list[float]] = []
    for path in files:
        rows: list[tuple[str, list[float]]] = []
        with path.open(encoding="utf-8") as handle:
            for line in handle:
                if line.startswith("#") or not line.strip():
                    continue
                fields = line.rstrip("\n").split("\t")
                if fields[0] in STAR_SUMMARY_PREFIXES:
                    continue
                if len(fields) < 4:
                    continue
                rows.append((fields[0], [float(value) for value in fields[1:4]]))
        if not rows:
            raise SystemExit(f"error: {path} has no gene rows after removing STAR's summary rows")
        if genes is None:
            genes = [name for name, _ in rows]
        elif [name for name, _ in rows] != genes:
            raise SystemExit(
                f"error: {path} has a different gene set from the first STAR file. "
                "Quantify every sample against the same reference; mixing references "
                "makes the matrix meaningless."
            )
        samples.append(path.name.replace(".ReadsPerGene.out.tab", ""))
        columns.append([row[1][column - 1] for row in rows])

    log(f"{len(files)} STAR file(s), strandedness={strandedness} (column {column})")
    write_outputs(output_dir, genes or [], samples, columns, tool="star",
                  extra=f"strandedness={strandedness}; column={column}")


def _featurecounts_sample_name(header: str) -> str:
    """Turn a BAM path header into a sample ID (basename, .bam stripped)."""
    name = Path(header.strip()).name
    for suffix in (".bam", ".sam", ".cram"):
        if name.endswith(suffix):
            name = name[: -len(suffix)]
    return name


def from_featurecounts(counts_file: str, output_dir: Path) -> None:
    """Parse a combined featureCounts matrix, keeping Geneid and the count columns."""
    if not os.path.isfile(counts_file):
        raise SystemExit(f"error: featureCounts file not found: {counts_file}")
    with open(counts_file, encoding="utf-8") as handle:
        lines = [line for line in handle if not line.startswith("#")]
    if not lines:
        raise SystemExit(f"error: {counts_file} holds no data lines")

    header = lines[0].rstrip("\n").split("\t")
    # Geneid, Chr, Start, End, Strand, Length, then one column per BAM.
    if len(header) < 7 or header[0].strip().lower() != "geneid":
        raise SystemExit(
            f"error: {counts_file} does not look like featureCounts output; expected a "
            "Geneid, Chr, Start, End, Strand, Length header followed by one column per BAM"
        )
    sample_headers = header[6:]
    samples = [_featurecounts_sample_name(name) for name in sample_headers]
    if len(set(samples)) != len(samples):
        raise SystemExit(
            f"error: two BAM columns in {counts_file} reduce to the same sample name; "
            "rename the BAMs so each sample is unambiguous"
        )

    genes: list[str] = []
    columns: list[list[float]] = [[] for _ in samples]
    for line in lines[1:]:
        fields = line.rstrip("\n").split("\t")
        if len(fields) < 7:
            continue
        genes.append(fields[0])
        for index in range(len(samples)):
            columns[index].append(float(fields[6 + index]))

    log(f"{len(samples)} featureCounts column(s), {len(genes)} gene(s)")
    write_outputs(output_dir, genes, samples, columns, tool="featurecounts",
                  extra=f"source={counts_file}")


def write_outputs(
    output_dir: Path,
    genes: list[str],
    samples: list[str],
    columns: list[list[float]],
    tool: str,
    extra: str,
) -> None:
    """Write counts.csv (genes x samples, integers) and metadata_template.csv."""
    if not genes:
        raise SystemExit("error: no genes were collected; nothing to write")
    if len(samples) != len(columns):
        raise SystemExit(
            f"error: {len(samples)} sample names but {len(columns)} count columns"
        )

    output_dir.mkdir(parents=True, exist_ok=True)
    counts_path = output_dir / "counts.csv"
    rounded = [[int(round(value)) for value in column] for column in columns]
    with counts_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["gene_id", *samples])
        for index, gene in enumerate(genes):
            writer.writerow([gene, *[column[index] for column in rounded]])

    meta_path = output_dir / "metadata_template.csv"
    with meta_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(DESIGN_COLUMNS)
        for sample in samples:
            group = sample.rsplit("_", 1)[0] if "_" in sample else sample
            writer.writerow([sample, group, ""])

    total = sum(sum(column) for column in rounded)
    log(f"wrote {counts_path} ({len(genes)} genes x {len(samples)} samples, {total} total counts)")
    log(f"wrote {meta_path} (fill in condition, and batch if one is not confounded)")
    log(f"source: {tool}; {extra}")
    if tool.startswith("salmon"):
        log(
            "Salmon counts are length-scaled estimates and were rounded to integers for "
            "PyDESeq2. Do not substitute TPM/FPKM here."
        )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build a gene x sample counts matrix and metadata template for PyDESeq2.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--from",
        dest="source",
        required=True,
        choices=("salmon", "star", "featurecounts"),
        help="quantifier output to read",
    )
    parser.add_argument("--quant-dir", default=None, help="directory of per-sample quant output")
    parser.add_argument("--tx2gene", default=None, help="transcript_id/gene_id map (salmon only)")
    parser.add_argument(
        "--strandedness",
        default="unstranded",
        choices=tuple(STRANDEDNESS_COLUMNS),
        help="library geometry, selects the STAR column (star only)",
    )
    parser.add_argument(
        "--counts-file", default=None, help="combined featureCounts matrix (featurecounts only)"
    )
    parser.add_argument(
        "--output-dir", default="counts", help="directory for counts.csv and metadata_template.csv"
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    output_dir = Path(args.output_dir)

    if args.source == "salmon":
        if not args.quant_dir or not args.tx2gene:
            raise SystemExit("error: --from salmon needs --quant-dir and --tx2gene")
        from_salmon(Path(args.quant_dir), args.tx2gene, output_dir)
    elif args.source == "star":
        if not args.quant_dir:
            raise SystemExit("error: --from star needs --quant-dir")
        from_star(Path(args.quant_dir), args.strandedness, output_dir)
    else:
        if not args.counts_file:
            raise SystemExit("error: --from featurecounts needs --counts-file")
        from_featurecounts(args.counts_file, output_dir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
