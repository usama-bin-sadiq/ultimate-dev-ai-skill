#!/usr/bin/env python3
"""Run a basic gene regulatory network inference with Arboreto.

What it does
------------
Reads an expression matrix, runs one tree-based regression per target gene
against a set of candidate regulators (GRNBoost2 or GENIE3, both exposed by
``arboreto.algo``), and writes the resulting regulatory links as a three-column
TSV: ``TF``, ``target``, ``importance``.

Expected input
--------------
A tab-separated file with **genes as columns** and observations (cells, samples,
conditions) as rows. The first row is the header and supplies the gene names::

    gene1    gene2    gene3
    4.21     0.13     9.88
    0.02     3.40     1.05

The TF list, when given, is a plain text file with one gene name per line;
blank lines and ``#`` comments are ignored.

Usage
-----
    python scripts/basic_grn_inference.py expression_data.tsv output_network.tsv
    python scripts/basic_grn_inference.py expression_data.tsv network.tsv \\
        --tf-file tfs.txt --seed 777 --limit 5000

Provenance
----------
This is a reconstructed convenience wrapper, not the upstream arboreto source.
It was written to match the CLI documented in this skill's SKILL.md and
``references/basic_inference.md``; it delegates the inference itself to the
installed ``arboreto`` package, so the network it produces is the real
arboreto network. Flag names and behaviour here are this file's own.
"""

from __future__ import annotations

import argparse
import sys

DESCRIPTION = "Infer a gene regulatory network with Arboreto (GRNBoost2 or GENIE3)."


def log(message: str) -> None:
    """Send progress and provenance to stderr so stdout stays clean for piping."""
    print(message, file=sys.stderr, flush=True)


def load_expression(path: str):
    """Load the expression matrix as a DataFrame with genes as columns."""
    import pandas as pd

    frame = pd.read_csv(path, sep="\t")
    if frame.empty:
        raise SystemExit(f"error: {path} contains no rows")
    if frame.shape[1] < 2:
        raise SystemExit(
            f"error: {path} has {frame.shape[1]} column(s); arboreto needs at "
            "least two genes to infer any relationship"
        )

    duplicated = frame.columns[frame.columns.duplicated()].tolist()
    if duplicated:
        log(f"warning: {len(duplicated)} duplicated column name(s) were made unique")
        frame = frame.loc[:, ~frame.columns.duplicated()]

    non_numeric = [
        str(name)
        for name in frame.columns
        if not pd.api.types.is_numeric_dtype(frame[name])
    ]
    if non_numeric:
        shown = ", ".join(non_numeric[:5])
        log(
            f"error: column(s) {shown} are not numeric. Arboreto expects the "
            "header row to be gene names and every other cell to be a number; "
            "transpose the matrix if observations are in rows."
        )
        raise SystemExit(2)

    return frame


def load_tf_names(path: str) -> list[str]:
    """Read a TF list: one gene name per line, blanks and # comments ignored."""
    names: list[str] = []
    seen: set[str] = set()
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            name = line.split("#", 1)[0].strip()
            if not name or name in seen:
                continue
            seen.add(name)
            names.append(name)
    if not names:
        raise SystemExit(f"error: {path} contains no gene names")
    return names


def resolve_tf_names(tf_names, gene_names: list[str]) -> list[str]:
    """Keep the TFs that are actually present as columns, reporting the rest."""
    if tf_names is None:
        log(f"no TF list given: every one of the {len(gene_names)} genes is a candidate regulator")
        return None

    columns = set(gene_names)
    present = [name for name in tf_names if name in columns]
    missing = [name for name in tf_names if name not in columns]
    if missing:
        log(
            f"warning: {len(missing)} of {len(tf_names)} TF name(s) are not columns "
            f"in the expression matrix and were dropped, e.g. {', '.join(missing[:5])}"
        )
    if not present:
        raise SystemExit(
            "error: none of the TF names appear in the expression matrix. TF names "
            "must match the column headers exactly (check case and Ensembl vs "
            "gene-symbol form)."
        )
    log(f"{len(present)} of {len(tf_names)} TF name(s) matched the expression matrix")
    return present


def run_inference(frame, algorithm: str, tf_names, seed, limit, address: str | None):
    """Call the requested arboreto entry point and return the links DataFrame."""
    if algorithm == "grnboost2":
        from arboreto.algo import grnboost2 as infer
    else:
        from arboreto.algo import genie3 as infer

    kwargs = {
        "expression_data": frame,
        "tf_names": tf_names,
        "seed": seed,
        "limit": limit,
    }

    if address:
        from distributed import Client

        log(f"connecting to Dask scheduler at {address}")
        client = Client(address)
        kwargs["client_or_address"] = client
        try:
            network = infer(**kwargs)
        finally:
            client.close()
        return network

    # A local Dask client is the default, matching arboreto's own behaviour.
    return infer(**kwargs)


def summarise(network, output_path: str) -> None:
    """Report the shape of the result and a few top links, to stderr."""
    total = len(network)
    log(f"wrote {total} regulatory link(s) to {output_path}")
    if total == 0:
        log(
            "warning: the network is empty. Check that the matrix has genes as "
            "columns, that observations are in rows, and that the TF names match "
            "the column headers."
        )
        return

    for column in ("TF", "target", "importance"):
        if column not in network.columns:
            raise SystemExit(
                f"error: arboreto returned no {column!r} column; got "
                f"{list(network.columns)}"
            )

    log(
        f"{network['TF'].nunique()} regulator(s), {network['target'].nunique()} "
        f"target(s), mean importance {network['importance'].mean():.4f}"
    )
    log("top 10 links by importance:")
    for row in network.nlargest(10, "importance").itertuples(index=False):
        log(f"  {row.TF}\t{row.target}\t{row.importance:.6f}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=DESCRIPTION,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "expression_data",
        help="TSV expression matrix, genes as columns, observations as rows",
    )
    parser.add_argument("output_network", help="TSV to write TF/target/importance to")
    parser.add_argument(
        "--tf-file",
        default=None,
        help="file with one transcription factor per line; omit to let every gene regulate",
    )
    parser.add_argument(
        "--algorithm",
        choices=("grnboost2", "genie3"),
        default="grnboost2",
        help="grnboost2 is the faster default; genie3 is the random-forest original",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="random seed; set it for reproducible results",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="return only the top N regulatory links globally",
    )
    parser.add_argument(
        "--address",
        default=None,
        help="Dask scheduler address, e.g. tcp://scheduler:8786; omit for a local cluster",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    try:
        import arboreto  # noqa: F401
    except ImportError:
        log(
            "error: arboreto is not importable. Install it first, for example "
            "`uv pip install arboreto` or `conda install -c bioconda arboreto`."
        )
        return 2

    log(f"arboreto {getattr(arboreto, '__version__', 'unknown')} from {arboreto.__file__}")
    log(f"reading {args.expression_data}")
    frame = load_expression(args.expression_data)
    gene_names = [str(name) for name in frame.columns]
    log(f"{frame.shape[0]} observation(s) x {frame.shape[1]} gene(s)")

    tf_names = load_tf_names(args.tf_file) if args.tf_file else None
    tf_names = resolve_tf_names(tf_names, gene_names)

    log(f"running {args.algorithm}")
    network = run_inference(frame, args.algorithm, tf_names, args.seed, args.limit, args.address)

    network.to_csv(args.output_network, sep="\t", index=False)
    summarise(network, args.output_network)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
