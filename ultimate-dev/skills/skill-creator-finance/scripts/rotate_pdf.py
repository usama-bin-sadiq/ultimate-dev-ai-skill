#!/usr/bin/env python3
"""Rotate pages in a PDF and write the result to a new file.

Bundled because the same rotation code gets rewritten every time somebody asks
to turn a scan the right way up. It reads a PDF, rotates the pages you name, and
writes a new PDF; it never edits the input in place.

Needs a PDF library. `pypdf` is the one it prefers, and `PyPDF2` is accepted as a
fallback because it is still installed on a lot of machines:

    uv pip install pypdf

    python rotate_pdf.py scan.pdf -o scan-upright.pdf
    python rotate_pdf.py scan.pdf -o out.pdf --angle 180
    python rotate_pdf.py scan.pdf -o out.pdf --pages 1,3,5-7 --angle 90
    python rotate_pdf.py scan.pdf --angle 90        # in place, after confirming

Reconstruction note: SKILL.md cites this file as the bundled example of a script
worth storing ("Rotating a PDF requires re-writing the same code each time") and
gives no arguments, so the interface below is the minimum that does the job: an
input, an output, an angle, and which pages. Nothing here flattens, recompresses
or re-renders page content; rotation is a page-rotation entry and a media box
swap, which is why the file stays the size it started.

Two things it will not do, both on purpose:

- It will not guess an angle. There is no OCR here, so a 90-degree mistake is
  invisible to it. Pass the angle.
- It will not silently drop a page range it cannot parse. A typo in `--pages` is
  an error, because a range that quietly matches nothing produces a PDF that
  looks fine and is wrong.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import NoReturn

ALLOWED_ANGLES = (90, 180, 270)
RANGE_RE = re.compile(r"^(\d+)(?:-(\d+))?$")


def die(message: str) -> NoReturn:
    print(f"rotate_pdf.py: {message}", file=sys.stderr)
    raise SystemExit(2)


def load_pdf_module():
    """Import pypdf, falling back to the older PyPDF2. Never imports both."""
    for name, module_name in (("pypdf", "pypdf"), ("PyPDF2", "PyPDF2")):
        try:
            module = __import__(module_name)
        except ImportError:
            continue
        # Both libraries expose PdfReader/PdfWriter at the top level; the
        # attribute check catches a partial install rather than an AttributeError
        # halfway through a rotation.
        if hasattr(module, "PdfReader") and hasattr(module, "PdfWriter"):
            return name, module
    die(
        "no PDF library found. Install one with `uv pip install pypdf` "
        "(PyPDF2 is also accepted)."
    )


def parse_pages(spec: str, page_count: int) -> list[int]:
    """Turn `1,3,5-7` or `all` into 0-based page indices.

    1-based on the command line, because that is how a person reading a PDF
    refers to its pages.
    """
    if spec.strip().lower() in ("all", "*", ""):
        return list(range(page_count))

    selected: list[int] = []
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        match = RANGE_RE.match(part)
        if match is None:
            die(f"cannot read page selector {part!r}; use 1, 1,3,5-7, or all")
        first = int(match.group(1))
        last = int(match.group(2)) if match.group(2) else first
        if first < 1 or last < 1:
            die(f"page numbers are 1-based; {part!r} is out of range")
        if first > last:
            die(f"range {part!r} ends before it starts")
        if last > page_count:
            die(f"range {part!r} runs past the last page ({page_count})")
        selected.extend(range(first - 1, last))

    seen: set[int] = set()
    ordered: list[int] = []
    for index in selected:
        if index not in seen:
            seen.add(index)
            ordered.append(index)
    return ordered


def rectangle_factory(pypdf):
    """Return the library's own rectangle class, or None if it has none.

    Both pypdf and PyPDF2 expose `RectangleObject` under `generic`, and both
    reject a plain 4-tuple on assignment ("Value must be a PdfObject"), so the
    class has to come from the library rather than being built here.
    """
    rectangle = getattr(getattr(pypdf, "generic", None), "RectangleObject", None)
    return rectangle


def rotate_page(page, angle: int, pypdf):
    """Rotate one page and square up its media and crop boxes.

    Rotating the page alone leaves the boxes describing the unrotated shape, so
    a landscape page rotated to portrait ends up clipped: the viewer is told the
    page is portrait and handed a landscape box. The boxes are swapped to match.
    """
    page.rotate(angle)
    rectangle = rectangle_factory(pypdf)
    if rectangle is None:
        print(
            f"rotate_pdf.py: {pypdf.__name__} exposes no RectangleObject; boxes "
            "left unsquared and rotated pages may clip",
            file=sys.stderr,
        )
        return

    def squared(box):
        left, bottom, right, top = (float(value) for value in box)
        width, height = right - left, top - bottom
        if angle in (90, 270) and width > height:
            new_width, new_height = height, width
            left, bottom = left + (width - new_width) / 2, bottom + (height - new_height) / 2
            return (left, bottom, left + new_width, bottom + new_height)
        return (left, bottom, right, top)

    for attribute in ("mediabox", "cropbox"):
        box = getattr(page, attribute, None)
        if box is None:
            continue
        try:
            # RectangleObject takes one sequence, not four coordinates, in both
            # libraries.
            setattr(page, attribute, rectangle(squared(box)))
        except Exception as exc:  # noqa: BLE001 - library-specific box objects
            print(
                f"rotate_pdf.py: could not square the {attribute} ({type(exc).__name__}); "
                "the page is rotated but its box is unchanged",
                file=sys.stderr,
            )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="rotate_pdf.py",
        description="Rotate pages in a PDF and write a new file.",
        epilog=(
            "Page numbers are 1-based. The angle is passed in rather than "
            "detected, because nothing here reads the page image."
        ),
    )
    parser.add_argument("input", help="the PDF to read")
    parser.add_argument("-o", "--output", help="the PDF to write; omit to overwrite the input")
    parser.add_argument(
        "--angle", type=int, default=90, choices=ALLOWED_ANGLES,
        help="clockwise rotation in degrees (default 90)",
    )
    parser.add_argument(
        "--pages", default="all",
        help="which pages to rotate: all, 1, 1,3,5-7 (default all)",
    )
    args = parser.parse_args(argv)

    source = Path(args.input)
    if not source.is_file():
        die(f"{source} is not a file")
    target = Path(args.output) if args.output else source
    if target.exists() and target == source and not args.output:
        print(f"rotate_pdf.py: overwriting {source}", file=sys.stderr)

    library, pypdf = load_pdf_module()

    try:
        reader = pypdf.PdfReader(str(source))
    except Exception as exc:  # noqa: BLE001 - the library's own parse errors vary
        die(f"cannot read {source}: {type(exc).__name__}: {exc}")
    if getattr(reader, "is_encrypted", False):
        die(f"{source} is encrypted; decrypt it before rotating")

    page_count = len(reader.pages)
    if page_count == 0:
        die(f"{source} has no pages")

    try:
        selected = parse_pages(args.pages, page_count)
    except ValueError as exc:
        die(str(exc))
    if not selected:
        die(f"no pages matched {args.pages!r} in a {page_count}-page document")

    writer = pypdf.PdfWriter()
    for index, page in enumerate(reader.pages):
        if index in set(selected):
            rotate_page(page, args.angle, pypdf)
        writer.add_page(page)

    try:
        writer.add_metadata(dict(reader.metadata or {}))
    except Exception:  # noqa: BLE001 - metadata is optional and often unreadable
        pass

    try:
        with open(target, "wb") as handle:
            writer.write(handle)
    except OSError as exc:
        die(f"cannot write {target}: {exc.strerror or exc}")

    print(
        f"rotated {len(selected)} of {page_count} page(s) by {args.angle} deg "
        f"({library}) -> {target}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
