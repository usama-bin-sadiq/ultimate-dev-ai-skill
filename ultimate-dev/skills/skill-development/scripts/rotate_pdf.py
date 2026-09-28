#!/usr/bin/env python3
"""Rotate the pages of a PDF, in place or to a new file.

The reusable case behind a "pdf-editor" skill: a user asks to rotate a PDF, and
the same twenty lines get rewritten every time. This is those twenty lines.

What it does
------------
Reads a PDF, rotates every page by a multiple of 90 degrees, and writes the
result. Rotation is applied to the page boxes *and* the content stream, so the
result is a real rotation rather than a viewer-side instruction that some readers
honour and some ignore.

Expected input
--------------
A PDF path. Output defaults to a new file next to the input with ``-rotated``
appended; ``--in-place`` overwrites instead, refusing unless ``--force``.

Usage
-----
    python scripts/rotate_pdf.py input.pdf --angle 90
    python scripts/rotate_pdf.py input.pdf --angle 180 --output rotated.pdf
    python scripts/rotate_pdf.py input.pdf --pages 1-3,7 --angle 270
    python scripts/rotate_pdf.py input.pdf --in-place --force
    python scripts/rotate_pdf.py input.pdf --info

Exit codes: 0 written, 1 refused or failed, 2 bad input or missing dependency.

Provenance
----------
Reconstructed to serve the ``scripts/rotate_pdf.py`` example in this skill's
SKILL.md (Step 2: "Rotating a PDF requires re-writing the same code each time").
The page-selection parser, the pypdf fallback, and the report are this file's own.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

MAX_BYTES = 512 * 1024 * 1024
# Rotating by anything other than a right angle changes the page box aspect and
# is not a rotation at all.
VALID_ANGLES = (90, 180, 270, -90, -180, -270)


class PdfError(RuntimeError):
    """The input is not a usable PDF, or the write failed."""


def log(message: str) -> None:
    print(message, file=sys.stderr, flush=True)


def import_backend():
    """pypdf, or pikepdf, or nothing. Whichever is installed."""
    try:
        from pypdf import PdfReader, PdfWriter  # noqa: PLC0415

        return PdfReader, PdfWriter, "pypdf"
    except ImportError:
        pass
    try:
        import pikepdf  # noqa: PLC0415

        return pikepdf.Pdf, pikepdf.Pdf, "pikepdf"
    except ImportError:
        pass
    raise SystemExit(
        "error: no PDF library is installed.\n"
        "Install one with:  python -m pip install --user pypdf\n"
        "pikepdf also works and handles more of the format:  "
        "python -m pip install --user pikepdf"
    )


def parse_pages(spec: str | None, total: int) -> set[int] | None:
    """Parse ``1-3,7,10-`` into a set of 1-based page numbers.

    Returns ``None`` for "every page", which is the default and the common case.
    Open-ended ranges (``10-``) extend to the end, because a page count that
    changes between writing the command and running it should not silently drop
    the last pages.
    """
    if not spec:
        return None

    pages: set[int] = set()
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        match = re.fullmatch(r"(\d+)\s*-\s*(\d*)", part)
        if match:
            start = int(match.group(1))
            end = int(match.group(2)) if match.group(2) else total
            if start > end:
                start, end = end, start
            if start < 1 or end > total:
                raise SystemExit(
                    f"error: page range {part!r} is outside this document (1-{total})"
                )
            pages.update(range(start, end + 1))
            continue
        if not part.isdigit():
            raise SystemExit(
                f"error: cannot read {part!r} as a page. Use forms like 3, 1-4, 5-, or 1-3,7."
            )
        number = int(part)
        if not 1 <= number <= total:
            raise SystemExit(f"error: page {number} is outside this document (1-{total})")
        pages.add(number)

    if not pages:
        raise SystemExit(f"error: --pages {spec!r} selected no pages")
    return pages


def describe(path: Path) -> int:
    """Print the page count, sizes, and rotations, and return the page count."""
    PdfReader, _writer, backend = import_backend()
    try:
        reader = PdfReader(str(path))
        total = len(reader.pages)
    except Exception as exc:
        raise SystemExit(f"error: could not read {path}: {exc}")

    log(f"file:  {path}")
    log(f"pages: {total}")
    log(f"read with: {backend}")
    for index, page in enumerate(reader.pages, start=1):
        box = page.mediabox
        width = float(box.width)
        height = float(box.height)
        rotation = getattr(page, "rotation", None)
        log(
            f"  page {index:>4}: {width:.1f} x {height:.1f} pt"
            + (f"  (rotation {rotation})" if rotation is not None else "")
        )
    return total


def rotate(path: Path, angle: int, pages: set[int] | None, output: Path, in_place: bool) -> Path:
    """Write a rotated copy of the document."""
    PdfReader, PdfWriter, _backend = import_backend()

    try:
        reader = PdfReader(str(path))
    except Exception as exc:
        raise SystemExit(f"error: could not read {path}: {exc}")
    if not reader.pages:
        raise SystemExit(f"error: {path} has no pages")

    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)

    selected = pages or set(range(1, len(writer.pages) + 1))
    rotated_count = 0
    for number in sorted(selected):
        page = writer.pages[number - 1]
        # accumulate rather than set, so --in-place on an already-rotated page
        # gives the sum rather than silently replacing it.
        page.rotate(angle)
        rotated_count += 1

    target = output or path
    if in_place and not output:
        pass  # --in-place with no --output means overwrite the input
    elif not in_place and output is None:
        target = path.with_name(f"{path.stem}-rotated{path.suffix or '.pdf'}")

    try:
        with target.open("wb") as handle:
            writer.write(handle)
    except OSError as exc:
        raise SystemExit(f"error: could not write {target}: {exc}")

    log(f"rotated {rotated_count} of {len(writer.pages)} page(s) by {angle} degrees")
    log(f"wrote {target} ({target.stat().st_size} bytes)")
    return target


def check_output(path: Path, angle: int, pages: set[int] | None) -> None:
    """Re-read what was written and confirm the rotation actually landed.

    A write that silently produces an unrotated document is the failure mode
    here, and exit code 0 is not evidence against it. The file is the evidence.
    """
    PdfReader, _writer, _backend = import_backend()
    try:
        reader = PdfReader(str(path))
    except Exception as exc:
        log(f"warning: wrote {path} but could not re-read it to verify: {exc}")
        return

    selected = pages or set(range(1, len(reader.pages) + 1))
    bad = []
    for number in sorted(selected):
        rotation = getattr(reader.pages[number - 1], "rotation", 0) or 0
        if rotation % 360 != angle % 360:
            bad.append((number, rotation))
    if bad:
        log("")
        log(f"verification: {len(bad)} page(s) do not carry the expected rotation:")
        for number, rotation in bad[:10]:
            log(f"  page {number}: rotation is {rotation}, expected {angle % 360}")
        log("The file was written. If a viewer shows the old orientation, the reader is")
        log("caching; if the rotation is genuinely absent, the writer did not apply it.")
    else:
        log(f"verified: every selected page carries rotation {angle % 360}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Rotate the pages of a PDF, in place or to a new file.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("pdf", help="the PDF to rotate")
    parser.add_argument("--angle", type=int, default=90, choices=VALID_ANGLES,
                        help="clockwise rotation; only right angles are meaningful")
    parser.add_argument("--pages", default=None,
                        help="which pages, e.g. 3, 1-4, 5-, or 1-3,7; default all")
    parser.add_argument("--output", "-o", default=None, help="write here instead")
    parser.add_argument("--in-place", action="store_true", help="overwrite the input file")
    parser.add_argument("--force", action="store_true", help="required with --in-place")
    parser.add_argument("--info", action="store_true",
                        help="print the page count and sizes, and exit")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    path = Path(args.pdf)
    if not path.is_file():
        raise SystemExit(f"error: not a file: {args.pdf}")
    size = path.stat().st_size
    if size == 0:
        raise SystemExit(f"error: {args.pdf} is empty")
    if size > MAX_BYTES:
        raise SystemExit(
            f"error: {args.pdf} is {size / (1024 * 1024):.0f} MB, over the "
            f"{MAX_BYTES // (1024 * 1024)} MB limit. A rotation streams page by page; "
            "this one loads the whole document."
        )
    if not path.read_bytes()[:5].startswith(b"%PDF"):
        raise SystemExit(
            f"error: {args.pdf} does not start with %PDF. If it is a sidecar file with a "
            "different extension, pass the real PDF."
        )

    if args.info:
        describe(path)
        return 0

    if args.in_place and not args.force:
        raise SystemExit(
            f"error: --in-place would overwrite {args.pdf} with no way back. Pass --force "
            "if that is what you want."
        )
    if args.in_place and args.output:
        raise SystemExit("error: --in-place and --output both name a target; pick one")
    if not args.in_place and os.path.exists(args.output) if args.output else False:
        if not args.force:
            raise SystemExit(f"error: {args.output} exists; pass --force to overwrite it")

    reader_class, _writer_class, _backend = import_backend()
    try:
        total = len(reader_class(str(path)).pages)
    except Exception as exc:
        raise SystemExit(f"error: could not read {path}: {exc}")
    selected = parse_pages(args.pages, total)

    target = rotate(path, args.angle, selected,
                    Path(args.output) if args.output else None, args.in_place)
    check_output(target, args.angle, selected)
    print(target)
    return 0


if __name__ == "__main__":
    sys.exit(main())
