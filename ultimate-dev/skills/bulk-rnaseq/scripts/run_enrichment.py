#!/usr/bin/env python3
"""Run pathway enrichment on a differential-expression result.

Two modes, matching the two things enrichment is asked for in an RNA-seq study:

``gsea``
    Preranked GSEA over the **full** gene list ranked by the DESeq2 Wald
    ``stat``. Do not threshold first: the rank statistic carries both the
    direction and the evidence, and thresholding throws that away.
``ora``
    Over-representation analysis on a **thresholded** hit list. Run up- and
    down-regulated sets separately when you want to see opposing signals.

Expected input
--------------
``--deseq2`` for GSEA: a results CSV with ``log2FoldChange``, ``pvalue``,
``padj``, and ``stat`` columns (the columns ``pydeseq2`` emits).
``--genes`` for ORA: a text file, one gene symbol per line. **Symbols, not
Ensembl IDs** — a mismatch here is the number-one reason enrichment returns
nothing, because MSigDB, Enrichr, and g:Profiler libraries are keyed on symbols.
Version suffixes (``ENSG00000141510.17``) are stripped automatically.

Usage
-----
    python scripts/run_enrichment.py gsea \\
        --deseq2 deseq2_results.csv --organism human --outdir enrichment/ --seed 123
    python scripts/run_enrichment.py ora \\
        --genes sig_symbols.txt --organism human --outdir enrichment/

Exit codes: 0 enrichment ran, 1 it ran and found nothing, 2 bad input.

Provenance
----------
Reconstructed to match the invocations documented in
``references/counts-and-handoff.md``. Enrichment itself is delegated to ``gseapy``
(``gseapy.prerank`` and ``gseapy.enrichr``), which is what the ``pathway-enrichment``
skill installs; the DESeq2 parsing, ranking, ID hygiene, and reporting here are
this file's own.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

# Enrichr library names per organism. Kept explicit so a typo in --organism is an
# error rather than a silent hit against the wrong species' gene sets.
ORGANISM_LIBRARIES = {
    "human": ("KEGG_2021_Human", "MSigDB_Hallmark_2020", "Reactome_2022", "GO_Biological_Process_2023"),
    "mouse": ("KEGG_2019_Mouse", "MSigDB_Mouse_Hallmark_2020", "Reactome_2022", "GO_Biological_Process_2023"),
    "rat": ("KEGG_2019_Rat", "Reactome_2022", "GO_Biological_Process_2023"),
    "zebrafish": ("KEGG_2019_Zebrafish", "Reactome_2022", "GO_Biological_Process_2023"),
    "drosophila": ("KEGG_2019_Drosophila", "Reactome_2022", "GO_Biological_Process_2023"),
    "worm": ("KEGG_2019_C. elegans", "Reactome_2022", "GO_Biological_Process_2023"),
    "yeast": ("KEGG_2019_Yeast", "Reactome_2022", "GO_Biological_Process_2023"),
    "arabidopsis": ("KEGG_2019_Arabidopsis", "Reactome_2022", "GO_Biological_Process_2023"),
}

# Enrichment runs use a seed for the permutation test; a fixed seed makes the
# reported normalised enrichment score and FDR reproducible.
DEFAULT_SEED = 123
ENSEMBL_VERSION = re.compile(r"\.\d+$")
ENSEMBL_LIKE = re.compile(r"^(ENSG|ENSMUSG|ENSRNOG|ENSMMUG)\d+", re.IGNORECASE)
# A NaN p-value with a present stat still yields a usable rank.
STAT_FALLBACK_ORDER = ("stat", "wald", "t", "score")


def log(message: str) -> None:
    print(message, file=sys.stderr, flush=True)


def _import_gseapy():
    try:
        import gseapy
    except ImportError:
        raise SystemExit(
            "error: gseapy is not installed. Run `uv pip install gseapy "
            "gprofiler-official`, or use the pathway-enrichment skill."
        )
    return gseapy


def strip_version(identifier: str) -> str:
    """Drop an Ensembl version suffix so IDs match the libraries."""
    return ENSEMBL_VERSION.sub("", identifier.strip())


def check_symbol_form(identifiers: list[str]) -> None:
    """Warn loudly if the list is Ensembl IDs rather than symbols."""
    if not identifiers:
        return
    ensembl = sum(1 for name in identifiers if ENSEMBL_LIKE.match(strip_version(name)))
    if ensembl * 2 > len(identifiers):
        raise SystemExit(
            f"error: {ensembl} of {len(identifiers)} input IDs look like Ensembl gene IDs. "
            "Enrichr, MSigDB, and g:Profiler libraries are keyed on gene symbols; map "
            "Ensembl to symbols first (the gget or database-lookup skill), or nothing "
            "will be enriched."
        )


def read_gene_list(path: str) -> list[str]:
    """One gene per line; blank lines and # comments ignored; order preserved."""
    names: list[str] = []
    seen: set[str] = set()
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            name = line.split("#", 1)[0].strip()
            if not name:
                continue
            if "\t" in name:
                name = name.split("\t")[0].strip()
            name = strip_version(name)
            if name and name not in seen:
                seen.add(name)
                names.append(name)
    if not names:
        raise SystemExit(f"error: {path} contains no gene names")
    return names


def read_ranked_genes(path: str) -> tuple[list[str], list[float]]:
    """Read a DESeq2 results CSV and return genes ranked by the Wald stat.

    The rank statistic is preferred over log2FoldChange: it already carries the
    evidence, and ranking by fold change alone promotes precisely the genes with
    the widest intervals, which are the least reliable ones.
    """
    try:
        import pandas as pd
    except ImportError:
        raise SystemExit("error: pandas is not installed; run `uv pip install pandas`")

    frame = pd.read_csv(path)
    if frame.empty:
        raise SystemExit(f"error: {path} has no rows")
    if len(frame.columns) < 2:
        raise SystemExit(
            f"error: {path} has columns {list(frame.columns)}; expected a gene identifier "
            "column plus log2FoldChange, pvalue, padj, and stat"
        )

    gene_column = next(
        (name for name in frame.columns if str(name).lower() in
         ("gene", "gene_id", "gene_name", "symbol", "index", "feature")),
        frame.columns[0],
    )
    stat_column = next(
        (name for name in STAT_FALLBACK_ORDER if name in frame.columns), None
    )
    if stat_column is None:
        if "log2FoldChange" not in frame.columns:
            raise SystemExit(
                f"error: {path} has no 'stat' or 'log2FoldChange' column, so no ranking "
                "statistic is available. Columns found: " + ", ".join(map(str, frame.columns))
            )
        stat_column = "log2FoldChange"
        log("warning: no 'stat' column; ranking by log2FoldChange, which promotes the "
            "widest intervals as readily as the strongest evidence")

    frame = frame[[gene_column, stat_column]].copy()
    frame[stat_column] = frame[stat_column].astype(float)
    frame = frame.replace([float("inf"), float("-inf")], float("nan")).dropna()
    frame[gene_column] = frame[gene_column].map(strip_version)
    frame = frame.drop_duplicates(subset=[gene_column])
    frame = frame.sort_values(stat_column, ascending=False)

    if len(frame) < 20:
        log(f"warning: only {len(frame)} usable genes ranked; enrichment on a list this "
            "short is unlikely to be informative")

    return list(frame[gene_column]), [float(v) for v in frame[stat_column]]


def resolve_libraries(organism: str) -> list[str]:
    key = organism.strip().lower()
    if key not in ORGANISM_LIBRARIES:
        raise SystemExit(
            f"error: unknown organism {organism!r}. Known: "
            + ", ".join(sorted(ORGANISM_LIBRARIES))
        )
    return list(ORGANISM_LIBRARIES[key])


def run_gsea(args) -> int:
    """Preranked GSEA over the full gene list, ranked by the Wald stat."""
    gseapy = _import_gseapy()
    genes, scores = read_ranked_genes(args.deseq2)
    libraries = resolve_libraries(args.organism)
    check_symbol_form(genes)

    log(f"{len(genes)} genes ranked; primary library {libraries[0]}")
    log(
        "preranked GSEA: the full list is used, not a thresholded one. A t-test-style "
        "significance cut would discard the ranking information GSEA depends on."
    )

    try:
        result = gseapy.prerank(
            rnk=genes + scores,
            gene_sets=libraries[0],
            permutation_num=1000,
            seed=args.seed,
            min_size=10,
            max_size=500,
            outdir=None,
            threads=4,
            verbose=False,
        )
    except Exception as exc:
        raise SystemExit(f"error: gseapy.prerank failed: {exc}")

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    result.res2d.to_csv(outdir / "gsea_prerank.csv", index=False)
    log(f"wrote {outdir / 'gsea_prerank.csv'}")

    return report_gsea(result.res2d, outdir)


def report_gsea(res2d, outdir: Path) -> int:
    """Write a readable summary and return the process exit code."""
    try:
        significant = res2d[res2d["FDR q-val"] < 0.05]
    except (KeyError, TypeError):
        significant = res2d.iloc[0:0]
    log(f"{len(significant)} term(s) at FDR < 0.05")
    for row in significant.sort_values("FDR q-val").head(15).itertuples(index=False):
        nes = getattr(row, "NES", float("nan"))
        fdr = getattr(row, "_3", float("nan"))  # FDR q-val is the third after Term/ES/NES
        log(f"  {row[0]}  NES={nes:.3f}  FDR={fdr:.4g}")

    # Positive NES means enriched in the up direction relative to the rank sign.
    lines = ["# GSEA summary", "",
             f"- Gene sets: {outdir / 'gsea_prerank.csv'}",
             f"- Terms at FDR < 0.05: {len(significant)}", "",
             "Positive NES is enriched among genes with a high Wald stat (up in the first "
             "listed condition); negative NES is enriched among the down-regulated ones.", ""]
    for name in ("Up", "Down"):
        subset = significant[significant["NES"] > 0] if name == "Up" else significant[significant["NES"] < 0]
        lines.append(f"## Enriched in {name.lower()}-regulated genes")
        for row in subset.sort_values("FDR q-val").head(20).itertuples(index=False):
            lines.append(f"- {row[0]} (NES {row[2]:.3f})")
        lines.append("")
    (outdir / "gsea_summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return 0 if len(significant) else 1


def run_ora(args) -> int:
    """Over-representation analysis on a thresholded hit list."""
    gseapy = _import_gseapy()
    genes = read_gene_list(args.genes)
    libraries = resolve_libraries(args.organism)
    check_symbol_form(genes)

    log(f"{len(genes)} input genes; primary library {libraries[0]}")
    try:
        result = gseapy.enrichr(
            gene_list=genes,
            gene_sets=libraries[0],
            organism="Human" if args.organism.lower() == "human" else None,
            outdir=None,
            min_size=5,
            max_size=500,
            background=None,
            verbose=False,
        )
    except Exception as exc:
        raise SystemExit(f"error: gseapy.enrichr failed: {exc}")

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    result.results.to_csv(outdir / "ora_enrichr.csv", index=False)
    log(f"wrote {outdir / 'ora_enrichr.csv'}")

    adjusted = result.results
    if "Adjusted P-value" in adjusted.columns:
        try:
            adjusted = adjusted[adjusted["Adjusted P-value"] < 0.05]
        except TypeError:
            pass
    count = len(adjusted)
    log(f"{count} term(s) at adjusted p < 0.05")
    for row in adjusted.head(15).itertuples(index=False):
        log(f"  {row[0]}  overlap={row[1]}  p={row[-1]:.4g}")

    lines = ["# ORA summary", "",
             f"- Input: {os.path.abspath(args.genes)} ({len(genes)} genes)",
             f"- Gene sets: {outdir / 'ora_enrichr.csv'}",
             f"- Terms at adjusted p < 0.05: {count}", ""]
    for row in adjusted.head(30).itertuples(index=False):
        lines.append(f"- {row[0]} ({row[1]} / {row[2]}, adjusted p {row[-1]:.4g})")
    lines += ["",
              "ORA tests only the genes that passed the threshold, so the background is the "
              "thresholded list rather than the assay. Consider up- and down-regulated sets "
              "separately, and GSEA when the ranked list is the more honest input.", ""]
    (outdir / "ora_summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return 0 if count else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run GSEA or ORA on a differential-expression result.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    sub = parser.add_subparsers(dest="mode", required=True)

    gsea = sub.add_parser("gsea", help="preranked GSEA over the full gene list")
    gsea.add_argument("--deseq2", required=True, help="DESeq2/PyDESeq2 results CSV")
    gsea.add_argument("--organism", required=True, help="human, mouse, rat, zebrafish, drosophila, ...")
    gsea.add_argument("--outdir", required=True, help="directory for the result tables and summary")
    gsea.add_argument(
        "--seed", type=int, default=DEFAULT_SEED,
        help="permutation seed, so the NES and FDR are reproducible",
    )
    gsea.set_defaults(func=run_gsea)

    ora = sub.add_parser("ora", help="over-representation analysis on a hit list")
    ora.add_argument("--genes", required=True, help="text file, one gene symbol per line")
    ora.add_argument("--organism", required=True, help="human, mouse, rat, zebrafish, drosophila, ...")
    ora.add_argument("--outdir", required=True, help="directory for the result tables and summary")
    ora.set_defaults(func=run_ora)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
