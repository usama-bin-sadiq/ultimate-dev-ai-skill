#!/usr/bin/env python3
"""Generate corporate identity mockups with Gemini Nano Banana (Flash or Pro).

What it does
------------
Builds one mockup prompt per deliverable from the CIP catalogue (see
``core.py``) and generates it. Passing the real logo file is strongly preferred:
the prompt then asks the model to place the supplied artwork, and says
explicitly not to redraw or restyle it. Without a logo, the prompt asks for a
correctly sized blank placement, so you get a usable mockup rather than an
invented logo.

``--set`` generates a full CIP set for the chosen industry: the industry's
priority deliverables plus one item from each remaining group.

Models
------
``flash``  default, ``gemini-2.5-flash-image``.
``pro``    ``gemini-3-pro-image-preview``. Slower and more expensive, and it
           renders small text more reliably — which matters for a letterhead or
           an invoice pad, where the type is the deliverable.

Usage
-----
    python3 scripts/cip/generate.py --brand "TopGroup" --logo /path/to/logo.png \\
        --deliverable "business card" --industry "consulting"
    python3 scripts/cip/generate.py --brand "TopGroup" --logo logo.png \\
        --industry "consulting" --set
    python3 scripts/cip/generate.py --brand "TopGroup" --logo logo.png \\
        --deliverable "business card" --model pro
    python3 scripts/cip/generate.py --brand "TechFlow" --deliverable "business card" \\
        --no-logo-prompt

Exit codes: 0 every requested mockup written, 1 some failed, 2 bad input or
missing key.

Provenance
----------
Reconstructed to match the invocations in this skill's SKILL.md and
``references/cip-design.md``. The catalogue, prompt assembly, and output handling
are in ``core.py`` and this file; the model names are the ones the skill documents.
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from core import (  # noqa: E402
    DELIVERABLES,
    MODELS,
    build_mockup_prompt,
    deliverables_for_set,
    resolve,
    search_domain,
)

ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models"
REQUEST_TIMEOUT = 240
IMAGE_SUFFIX = ".png"
LOGO_EXTS = (".png", ".jpg", ".jpeg", ".webp")


def log(message: str) -> None:
    print(message, file=sys.stderr, flush=True)


def slugify(value: str) -> str:
    import re

    slug = re.sub(r"[^a-z0-9]+", "-", value.strip().lower()).strip("-")
    return slug or "brand"


def check_logo(path: str) -> Path:
    """Confirm the logo file exists and is a plausible image before spending a call."""
    file_path = Path(path)
    if not file_path.is_file():
        raise SystemExit(f"error: logo not found: {path}")
    if file_path.suffix.lower() not in LOGO_EXTS:
        log(
            f"warning: {path} is not a recognised image extension. Image models generally "
            "accept PNG or JPEG; a PDF or SVG will be rejected by the provider."
        )
    return file_path


def load_reference_image(file_path: Path):
    """Read an image into the inline-data form the provider expects."""
    import base64

    mime = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
    }.get(file_path.suffix.lower(), "image/png")
    return {
        "inline_data": {
            "mime_type": mime,
            "data": base64.b64encode(file_path.read_bytes()).decode("ascii"),
        }
    }


def generate(prompt: str, logo: Path | None, model: str, api_key: str, output: Path) -> Path:
    """One provider call, one image out."""
    try:
        from google import genai
        from google.genai import types
    except ImportError:
        raise SystemExit(
            "error: google-genai is not installed. Run `pip install google-genai pillow`."
        )

    client = genai.Client(api_key=api_key)
    parts: list[object] = [types.Part.from_text(text=prompt)]
    if logo is not None:
        parts.append(types.Part.from_bytes(
            data=logo.read_bytes(),
            mime_type=load_reference_image(logo)["inline_data"]["mime_type"],
        ))

    try:
        response = client.models.generate_content(
            model=model,
            contents=[types.Content(role="user", parts=parts)],
            config=types.GenerateContentConfig(response_modalities=["IMAGE"]),
        )
    except Exception as exc:
        raise SystemExit(f"error: Gemini request failed: {exc}")

    for candidate in getattr(response, "candidates", []) or []:
        for part in getattr(candidate.content, "parts", []) or []:
            inline = getattr(part, "inline_data", None)
            if inline is not None and getattr(inline, "data", None):
                output.parent.mkdir(parents=True, exist_ok=True)
                output.write_bytes(inline.data)
                return output
    raise SystemExit(
        "error: the model returned no image data. With Pro, small text sometimes "
        "fails and comes back empty; try --model flash, or --deliverable for a piece "
        "with less type on it."
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate corporate identity mockups with Gemini Nano Banana.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--brand", required=True, help="brand name")
    parser.add_argument("--logo", default=None, help="path to the logo file to place on the piece")
    parser.add_argument("--deliverable", default=None,
                        help="one deliverable, e.g. 'business card' or 'letterhead'")
    parser.add_argument("--industry", default=None, help="sector, e.g. consulting")
    parser.add_argument("--style", default=None, help="CIP style; omit to infer from the query")
    parser.add_argument("--mockup", default=None, help="mockup setting; omit for a neutral scene")
    parser.add_argument("--set", dest="full_set", action="store_true",
                        help="generate a full CIP set for the industry")
    parser.add_argument("--limit-set", type=int, default=12,
                        help="maximum deliverables when --set is used")
    parser.add_argument("--model", choices=tuple(MODELS), default="flash",
                        help="flash, or pro for reliable small text")
    parser.add_argument("--no-logo-prompt", action="store_true",
                        help="ask for a blank logo placement instead of placing the logo")
    parser.add_argument("-o", "--output-dir", default="cip-output", help="directory for the images")
    parser.add_argument("--dry-run", action="store_true",
                        help="print the prompts and exit without calling the provider")
    parser.add_argument("--sleep", type=float, default=0.0,
                        help="seconds to wait between calls, to stay under a rate limit")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if not args.deliverable and not args.full_set:
        raise SystemExit("error: give --deliverable NAME, or --set for a full CIP set")

    logo = None
    if args.logo:
        logo = check_logo(args.logo)
    elif not args.no_logo_prompt:
        log(
            "note: no --logo given. The prompt will ask for a blank, correctly sized "
            "placement. Generate the logo first, or the mockup will carry a mark nobody approved."
        )
    with_logo = logo is not None and not args.no_logo_prompt

    query_parts = [part for part in (args.brand, args.industry, args.style, args.deliverable) if part]
    query = " ".join(query_parts)

    style = args.style
    if style is None:
        style = search_domain("style", query, limit=1)[0]["name"]
    industry = args.industry
    if industry is None:
        industry = search_domain("industry", query, limit=1)[0]["name"]

    try:
        style = resolve(style, "style")
        industry = resolve(industry, "industry")
    except KeyError as exc:
        raise SystemExit(f"error: {exc.args[0]}")

    if args.full_set:
        names = deliverables_for_set(industry)[: max(1, args.limit_set)]
    else:
        try:
            names = [resolve(args.deliverable, "deliverable")]
        except KeyError as exc:
            raise SystemExit(
                f"error: {exc.args[0]}\nRun `python3 scripts/cip/search.py --list` to see all "
                f"{len(DELIVERABLES)} deliverables."
            )

    output_dir = Path(args.output_dir)
    slug = slugify(args.brand)
    prompts = {
        name: build_mockup_prompt(args.brand, name, industry, style, args.mockup, with_logo)
        for name in names
    }

    if args.dry_run:
        print(f"# brand: {args.brand}\n# style: {style}\n# industry: {industry}")
        print(f"# model: {args.model} ({MODELS[args.model]})\n"
              f"# logo: {logo if with_logo else 'blank placement'}\n"
              f"# deliverables: {len(names)}")
        for name in names:
            print(f"\n## {name}\n")
            print(prompts[name])
        return 0

    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        raise SystemExit(
            "error: GEMINI_API_KEY is not set. Get one at https://aistudio.google.com/apikey"
        )

    failures = 0
    for position, name in enumerate(names, start=1):
        output = output_dir / f"{slug}-{name}{IMAGE_SUFFIX}"
        log(f"[{position}/{len(names)}] {name} -> {output}")
        try:
            generate(prompts[name], logo if with_logo else None, MODELS[args.model], key, output)
        except SystemExit as exc:
            failures += 1
            log(str(exc))
        if args.sleep and position < len(names):
            time.sleep(args.sleep)

    written = len(names) - failures
    log(f"\n{written}/{len(names)} mockup(s) written to {output_dir}")
    if failures:
        log("Some failed. Re-run only the missing ones with --deliverable NAME.")
    log(
        "Open every image and check the logo is present, undistorted, and the right way up; "
        "a stretched or invented mark is the failure mode here, and it is visible only "
        "by looking."
    )
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
