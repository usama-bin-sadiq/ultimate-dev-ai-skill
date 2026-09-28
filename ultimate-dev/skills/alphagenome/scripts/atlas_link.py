#!/usr/bin/env python3
"""Build AlphaGenome Atlas portal deep links. Offline: no API key, no network.

The AlphaGenome Atlas portal reads its state from query parameters, so a link is
just a URL. This builds one for a variant, a locus, or a gene, and prints it so it
can be attached to a variant report.

Reconstruction note: this file was written from SKILL.md and references/atlas.md
rather than recovered from upstream, so it is a reasoned reconstruction and not a
verified original. The filter and layout vocabularies below are exactly the ones
references/atlas.md documents; anything the portal accepts beyond them is not
guessed at here. Run with --help for the full surface.

    python atlas_link.py variant chr22:36201698:A>C --biosample colon \\
        --modalities RNA_SEQ,DNASE,CHIP_TF
    python atlas_link.py locus chr11:5225727-5226575 --tf GATA1
    python atlas_link.py gene HBB --markdown

Research and theoretical modelling only; outputs are not for diagnostic
procedures or medical decisions.
"""

from __future__ import annotations

import argparse
import re
import sys
from typing import NoReturn
from urllib.parse import urlencode

DEFAULT_BASE = "https://deepmind.google.com/science/alphagenome/atlas"
PREDICTIONS_BASE = "https://alphagenome.google/atlas/track-predictions"

# `lItems` values documented in references/atlas.md: `avi` plus one
# `section:<SCORER>` per modality panel, and `pinned:<track key>` for one track.
AVI_ITEM = "avi"

# The only SCORER_MODALITY values references/atlas.md spells out. RNA-seq and
# DNase tracks carry no transcription-factor or histone code, so a filter made
# only of assay predicates hides them; the reference requires the modality
# predicates to be added alongside an assay predicate, and this module does that
# automatically. Other modalities are passed through to `lItems` only, where the
# scorer name is the documented spelling and no invented predicate is needed.
SCORER_MODALITY = {
    "RNA_SEQ": "RNA-seq",
    "DNASE": "DNase",
}

ASSAY_TRANSCRIPTOR_FACTOR = "ASSAY_TRANSCRIPTOR_FACTOR"
ASSAY_HISTONE_MARK = "ASSAY_HISTONE_MARK"
BIOSAMPLE_NAME = "BIOSAMPLE_NAME"
BIOSAMPLE_TYPE = "BIOSAMPLE_TYPE"
GENE_NAME = "GENE_NAME"

VARIANT_RE = re.compile(r"^chr[^:]+:\d+:[ACGTNacgtn]>[ACGTNacgtn]$")
INTERVAL_RE = re.compile(r"^chr[^:]+:\d+-\d+$")
ENSEMBL_GENE_ID_RE = re.compile(r"^ENSG\d{6,}$")
RSID_RE = re.compile(r"^rs\d+$", re.IGNORECASE)
SPLIT_LIST_RE = re.compile(r"[,\s]+")


def die(message: str) -> NoReturn:
    """Report a usage problem on stderr and exit non-zero."""
    print(f"atlas_link.py: {message}", file=sys.stderr)
    raise SystemExit(2)


def split_list(value: str) -> list[str]:
    """Split a comma- or whitespace-separated list, dropping empty entries."""
    return [item for item in SPLIT_LIST_RE.split(value.strip()) if item]


def check_variant(text: str) -> str:
    """Validate a 1-based `chr:pos:ref>alt` string.

    The Atlas key is `chromosome:position:alt` on GRCh38, so the REF allele is
    implied by the reference. A swapped REF therefore returns a wrong-but-
    plausible record rather than an error, which is why the spelling is checked
    here and why rsIDs are refused outright.
    """
    if RSID_RE.match(text):
        die(
            f"{text!r} looks like an rsID. The Atlas API and portal do not accept "
            "rsIDs; resolve it to GRCh38 coordinates first."
        )
    if not VARIANT_RE.match(text):
        die(
            f"{text!r} is not 1-based `chr:pos:ref>alt` on GRCh38, for example "
            "chr22:36201698:A>C."
        )
    return text


def check_interval(text: str) -> tuple[str, int, int]:
    """Validate a 1-based closed `chr:start-end` interval and return its bounds."""
    if not INTERVAL_RE.match(text):
        die(f"{text!r} is not 1-based closed `chr:start-end`, for example chr11:5225727-5226575.")
    chrom, start, end = text.split(":")[0], *text.split(":")[1].split("-")
    start_i, end_i = int(start), int(end)
    if end_i < start_i:
        die(f"{text!r} ends before it starts.")
    return chrom, start_i, end_i


def viewport(interval: str) -> str:
    """The viewport (`i`) needed before motif instances render for an interval."""
    return interval


def build_filters(args: argparse.Namespace, modality_names: list[str]) -> list[str]:
    """Assemble the `f` predicates, in a stable order.

    Assay predicates (transcription factor, histone mark) carry no code for the
    RNA-seq and DNase panels, so the modality predicates are appended
    automatically rather than left to the caller to remember.
    """
    filters: list[str] = []
    if args.biosample:
        filters.append(f"{BIOSAMPLE_NAME}:{args.biosample}")
    if args.biosample_type:
        filters.append(f"{BIOSAMPLE_TYPE}:{args.biosample_type}")
    if args.tf:
        filters.append(f"{ASSAY_TRANSCRIPTOR_FACTOR}:{args.tf}")
    if args.histone_mark:
        filters.append(f"{ASSAY_HISTONE_MARK}:{args.histone_mark}")
    if args.gene:
        filters.append(f"{GENE_NAME}:{args.gene}")
    for extra in args.filter or []:
        if ":" not in extra:
            die(f"--filter {extra!r} is not `KEY:VALUE`.")
        filters.append(extra)
    assay_predicate = any(f.startswith((ASSAY_TRANSCRIPTOR_FACTOR, ASSAY_HISTONE_MARK)) for f in filters)
    if assay_predicate:
        for name in modality_names:
            value = SCORER_MODALITY.get(name)
            if value and f"SCORER_MODALITY:{value}" not in filters:
                filters.append(f"SCORER_MODALITY:{value}")
    return filters


def build_query(args: argparse.Namespace) -> tuple[str, str, str, str]:
    """Return (q, view, label, notes) for the requested target."""
    if args.command == "variant":
        target = check_variant(args.target)
        return target, "variant", target, "REF and ALT are both shown; the Atlas key is chr:pos:alt."
    if args.command == "locus":
        target = args.target
        check_interval(target)
        return target, "locus", target, "1-based closed interval on GRCh38."
    if RSID_RE.match(args.target):
        die(
            f"{args.target!r} looks like an rsID. The portal `q` parameter accepts a "
            "variant, an interval, a gene symbol, or an Ensembl gene ID, not an rsID."
        )
    if INTERVAL_RE.match(args.target):
        return args.target, "locus", args.target, "Read as an interval because it matches chr:start-end."
    return args.target, "entity", args.target, "Read as a gene symbol or Ensembl gene ID."


def build_url(args: argparse.Namespace) -> tuple[str, str, list[str]]:
    """Return (url, label, notes) for the requested link."""
    query, view, label, note = build_query(args)
    modality_names = split_list(args.modalities) if args.modalities else []

    params: dict[str, str] = {"q": query, "m": view}

    if args.motifs:
        view_items = ["motifs"]
    else:
        view_items = [AVI_ITEM] + [f"section:{name}" for name in modality_names]
    if view_items:
        params["lItems"] = ",".join(view_items)

    filters = build_filters(args, modality_names)
    if filters:
        params["f"] = ",".join(filters)

    interval = args.interval
    if interval is None and view == "locus":
        interval = args.target
    if interval is not None:
        check_interval(interval)
        params["i"] = viewport(interval)

    if args.predictions:
        base = args.predictions_base
        params["scores"] = query
        params["md"] = "1"
        params["tpRenames"] = "1"
        params["tpLegendTitle"] = "REF vs ALT"
    else:
        base = args.base

    url = f"{base}?{urlencode(params)}"
    notes = [note]
    if args.predictions:
        notes.append("Track-prediction view: REF and ALT tracks side by side.")
    if args.motifs:
        notes.append("Motif view needs a viewport (`i`) to render motif instances.")
    return url, label, notes


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="atlas_link.py",
        description="Build an AlphaGenome Atlas portal deep link. Offline: no API key, no network.",
        epilog=(
            "Human data is GRCh38 only. The portal does not accept rsIDs. A variant "
            "written with REF and ALT swapped, or written on GRCh37, opens a "
            "wrong-but-plausible page, so check REF against the reference before "
            "sharing a link."
        ),
    )
    sub = parser.add_subparsers(dest="command", required=True)

    def add_common(p: argparse.ArgumentParser) -> None:
        p.add_argument("target", help="variant, interval, gene symbol, or Ensembl gene ID")
        p.add_argument("--biosample", help=f"{BIOSAMPLE_NAME} filter, for example colon")
        p.add_argument("--biosample-type", help=f"{BIOSAMPLE_TYPE} filter")
        p.add_argument("--tf", help=f"{ASSAY_TRANSCRIPTOR_FACTOR} filter, for example GATA1")
        p.add_argument("--histone-mark", help=f"{ASSAY_HISTONE_MARK} filter, for example H3K27ac")
        p.add_argument("--gene", help=f"{GENE_NAME} filter, for example HBB")
        p.add_argument(
            "--filter",
            action="append",
            metavar="KEY:VALUE",
            help="extra portal filter predicate; repeatable",
        )
        p.add_argument(
            "--modalities",
            help="comma-separated scorer names shown as sections, for example RNA_SEQ,DNASE,CHIP_TF",
        )
        p.add_argument("--interval", help="viewport interval (`i`) as 1-based closed chr:start-end")
        p.add_argument("--motifs", action="store_true", help="open the motif view instead of the panels")
        p.add_argument(
            "--predictions",
            action="store_true",
            help="link the REF-versus-ALT track-prediction page rather than the panels",
        )
        p.add_argument("--base", default=DEFAULT_BASE, help="portal base URL")
        p.add_argument(
            "--predictions-base",
            default=PREDICTIONS_BASE,
            help="base URL for --predictions",
        )
        p.add_argument("--markdown", action="store_true", help="print a markdown link")

    add_common(sub.add_parser("variant", help="a single 1-based `chr:pos:ref>alt` variant"))
    add_common(sub.add_parser("locus", help="a 1-based closed `chr:start-end` interval"))
    add_common(sub.add_parser("gene", help="a gene symbol or Ensembl gene ID"))

    args = parser.parse_args(argv)
    url, label, notes = build_url(args)

    if args.markdown:
        print(f"**[{label}]({url})**")
    else:
        print(url)
        for note in notes:
            print(f"# {note}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
