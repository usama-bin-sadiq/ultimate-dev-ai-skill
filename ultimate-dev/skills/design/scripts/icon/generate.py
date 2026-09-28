#!/usr/bin/env python3
"""Generate SVG icons with Gemini 3.1 Pro Preview.

What it does
------------
Asks a text model for SVG markup — SVG is XML, so no image generation is involved
— and sanitises what comes back before writing it. The model is asked for a single
root ``<svg>`` with a ``<title>`` element, ``currentColor`` for the colour, and a
consistent stroke, and the post-processing enforces those requirements rather
than trusting the output.

Every flag documented in ``references/icon-design.md`` is implemented: ``--prompt``,
``--name``, ``--style``, ``--category``, ``--color``, ``--size``, ``--viewbox``,
``--output``, ``--output-dir``, ``--batch``, ``--sizes``, plus ``--list-styles``
and ``--list-categories``.

Usage
-----
    python3 scripts/icon/generate.py --prompt "settings gear" --style outlined
    python3 scripts/icon/generate.py --prompt "shopping cart" --style filled --color "#6366F1"
    python3 scripts/icon/generate.py --name "dashboard" --category navigation --style duotone
    python3 scripts/icon/generate.py --prompt "cloud upload" --batch 4 --output-dir ./icons
    python3 scripts/icon/generate.py --prompt "user profile" --sizes "16,24,32,48" --output-dir ./icons
    python3 scripts/icon/generate.py --list-styles
    python3 scripts/icon/generate.py --list-categories

Exit codes: 0 every requested icon written, 1 some failed, 2 bad input or missing key.

Provenance
----------
Reconstructed to match the CLI options and the 15 styles and 12 categories in
``references/icon-design.md`` and this skill's SKILL.md. The style and category
tables, the prompt templates, and the SVG sanitiser are this file's own.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

# The model documented for this workflow. It is text-only: SVG is XML text.
MODEL = "gemini-3.1-pro-preview"
ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models"
REQUEST_TIMEOUT = 120

# 15 styles, with the stroke and fill behaviour the reference prescribes.
STYLES: dict[str, dict] = {
    "outlined": {"stroke": "2", "fill": "none", "best_for": "UI interfaces, web apps",
                "note": "stroke-linecap and stroke-linejoin set to round, so corners do not spike at small sizes"},
    "filled": {"stroke": "0", "fill": "solid", "best_for": "mobile apps, nav bars",
               "note": "solid silhouette; interior detail fills in below 16px, so keep it simple"},
    "duotone": {"stroke": "0", "fill": "dual", "best_for": "marketing, landing pages",
                "note": "two tones of currentColor at different opacities"},
    "thin": {"stroke": "1.25", "fill": "none", "best_for": "luxury brands, editorial",
             "note": "1-1.5px; below 1px it disappears on a non-retina display"},
    "bold": {"stroke": "3", "fill": "none", "best_for": "headers, hero sections",
             "note": "3px; strong at large sizes, cramped inside a 16px box"},
    "rounded": {"stroke": "2", "fill": "none", "best_for": "friendly apps, health",
                "note": "round caps and joins plus generous corner radii"},
    "sharp": {"stroke": "2", "fill": "none", "best_for": "tech, fintech, enterprise",
              "note": "miter joins, zero corner radius, orthogonal geometry"},
    "flat": {"stroke": "0", "fill": "solid", "best_for": "Material design, Google-style",
             "note": "material conventions, 24px grid, no gradient"},
    "gradient": {"stroke": "0", "fill": "gradient", "best_for": "modern brands, SaaS",
                 "note": "linearGradient; test it in greyscale, because it is often the only thing distinguishing it"},
    "glassmorphism": {"stroke": "1", "fill": "semi", "best_for": "modern UI, overlays",
                      "note": "semi-transparent fill; only legible on a busy or photographic ground"},
    "pixel": {"stroke": "0", "fill": "solid", "best_for": "gaming, retro",
              "note": "hard pixel edges on an integer grid; do not scale smoothly"},
    "hand-drawn": {"stroke": "varies", "fill": "none", "best_for": "artisan, creative",
                   "note": "varying stroke width; the irregularity is the point"},
    "isometric": {"stroke": "1.5", "fill": "partial", "best_for": "tech docs, infographics",
                  "note": "30-degree isometric projection; needs a larger viewBox than 24"},
    "glyph": {"stroke": "0", "fill": "solid", "best_for": "system UI, compact",
              "note": "a single filled shape, no interior lines"},
    "animated-ready": {"stroke": "2", "fill": "varies", "best_for": "interactive UI, onboarding",
                       "note": "layered groups with ids, so CSS or SMIL can target the parts"},
}

CATEGORIES: dict[str, list[str]] = {
    "navigation": ["arrows", "menus", "home", "chevrons"],
    "action": ["edit", "delete", "save", "download", "upload"],
    "communication": ["email", "chat", "phone", "notification"],
    "media": ["play", "pause", "volume", "camera"],
    "file": ["document", "folder", "archive", "cloud"],
    "user": ["person", "group", "profile", "settings"],
    "commerce": ["cart", "bag", "wallet", "credit card"],
    "data": ["chart", "graph", "analytics", "dashboard"],
    "development": ["code", "terminal", "bug", "git", "API"],
    "social": ["heart", "star", "bookmark", "trophy"],
    "weather": ["sun", "moon", "cloud", "rain"],
    "map": ["pin", "location", "compass", "globe"],
}

# best_for phrases keyed by style, folded into the prompt so the model gets the
# same guidance the reference gives the designer.
STYLE_HINT = {
    "outlined": "outlined style: 2px stroke, no fill, round line caps and joins",
    "filled": "filled style: solid shapes, no strokes, a bold silhouette",
    "duotone": "duotone style: two tones of the same colour at different opacities",
    "thin": "thin style: 1.25px stroke, no fill, delicate and editorial",
    "bold": "bold style: 3px stroke, no fill, strong at large sizes",
    "rounded": "rounded style: 2px stroke with round caps, joins, and corner radii",
    "sharp": "sharp style: 2px stroke, miter joins, no corner radius, orthogonal geometry",
    "flat": "flat style: solid shapes on a 24px grid, Material conventions, no gradient",
    "gradient": "gradient style: a two-stop linearGradient from the given colour to a lighter one",
    "glassmorphism": "glassmorphism style: 1px stroke and a semi-transparent fill",
    "pixel": "pixel style: hard pixel edges on an integer grid, no antialiasing",
    "hand-drawn": "hand-drawn style: a single sketch-like stroke of varying weight",
    "isometric": "isometric style: 30-degree projection, 1.5px strokes, partial fills",
    "glyph": "glyph style: one filled shape, no interior lines, as compact as possible",
    "animated-ready": "animated-ready style: grouped and layered with ids so each part can be animated",
}

# Things that must never survive into a written file. An icon generator that
# can emit a script tag can emit anything.
FORBIDDEN_SVG = re.compile(
    r"<\s*(script|foreignObject|iframe|object|embed|audio|video|animate|set|handler)\b",
    re.IGNORECASE,
)
EVENT_HANDLER = re.compile(r"\son[a-z]+\s*=\s*[\"'][^\"']*[\"']", re.IGNORECASE)
EXTERNAL_REF = re.compile(r"(?:href|xlink:href)\s*=\s*[\"'](?!#)[^\"']*[\"']", re.IGNORECASE)


def log(message: str) -> None:
    print(message, file=sys.stderr, flush=True)


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.strip().lower()).strip("-")
    return slug or "icon"


def build_prompt(
    description: str,
    style: str,
    category: str | None,
    color: str,
    size: int,
    viewbox: int,
) -> str:
    """The instruction sent to the model. Everything it needs, and nothing else."""
    context = ""
    if category:
        context = (
            f"This is a {category} icon. Typical subjects in this category: "
            f"{', '.join(CATEGORIES[category])}. "
        )
    return (
        f"{context}Write one SVG icon representing: {description}.\n\n"
        f"Hard requirements, all of them:\n"
        f"- Return only the SVG markup. No prose before or after it, no markdown fence.\n"
        f"- A single root <svg> element with viewBox=\"0 0 {viewbox} {viewbox}\", "
        f'width="{size}" height="{size}", and fill="none".\n'
        f"- Style: {STYLE_HINT[style]}.\n"
        f'- Include a <title> element with a short accessible name, as the first child.\n'
        f'- Use the colour {color} for strokes and fills, so the icon inherits a CSS colour.\n'
        f"- Geometry must sit inside the viewBox with at least 1 unit of margin, and must "
        f"stay legible at {max(16, size // 2)}px as well as at {size * 2}px.\n"
        f"- Prefer a few path elements over many primitives. No embedded fonts, no raster "
        f"images, no base64 data, no external references, no CSS, no scripts, no animation.\n"
        f"- No text elements; a label is the consumer's job, not the icon's.\n"
        f"- Symmetric where the subject is symmetric; a drawing that is not quite balanced "
        f"reads as a mistake at 16px.\n"
    )


def call_model(prompt: str, api_key: str) -> str:
    """One text-generation call, returning the raw text."""
    try:
        from google import genai
    except ImportError:
        raise SystemExit(
            "error: google-genai is not installed. Run `pip install google-genai`."
        )
    client = genai.Client(api_key=api_key)
    try:
        response = client.models.generate_content(model=MODEL, contents=prompt)
    except Exception as exc:
        raise SystemExit(f"error: Gemini request failed: {exc}")
    return getattr(response, "text", "") or ""


def extract_svg(text: str) -> str:
    """Pull the SVG out of a model response, tolerating a stray code fence."""
    fenced = re.search(r"```(?:svg|xml|html)?\s*(<svg.*?</svg>)\s*```", text, re.DOTALL | re.IGNORECASE)
    if fenced:
        return fenced.group(1).strip()
    start = text.lower().find("<svg")
    if start == -1:
        raise SystemExit(
            "error: the model returned no SVG. Ask for the icon again, or write the path "
            "data by hand; a text model asked for markup will occasionally return prose."
        )
    end = text.lower().rfind("</svg>")
    return text[start:end + 6].strip() if end != -1 else text[start:].strip()


def sanitize(svg: str, viewbox: int, size: int, title: str) -> str:
    """Enforce the requirements, and refuse anything executable.

    The model is asked for a single-colour icon; this makes the file match,
    because a prompt is a request and a shipped file is a fact.
    """
    if FORBIDDEN_SVG.search(svg):
        found = FORBIDDEN_SVG.search(svg).group(1)
        raise SystemExit(
            f"error: the returned SVG contains a <{found}> element, which has no place in an "
            "icon. Regenerate, or hand-write the path data."
        )
    if EVENT_HANDLER.search(svg):
        raise SystemExit("error: the returned SVG contains an inline event handler; refusing to write it.")
    if EXTERNAL_REF.search(svg):
        raise SystemExit("error: the returned SVG references an external resource; refusing to write it.")
    if re.search(r"base64", svg, re.IGNORECASE):
        raise SystemExit("error: the returned SVG embeds binary data; refusing to write it.")

    # Normalise the root element: one viewBox, one xmlns, explicit size, no fill
    # on the root so currentColor inheritance works from the parent. Duplicate
    # attributes are a hard XML parse error, so the model's are removed rather
    # than overwritten.
    head = svg[: svg.lower().find(">") + 1] if ">" in svg else svg
    body = svg[len(head):]
    for attribute in ("width", "height", "viewbox", "xmlns", "xmlns:xlink", "fill", "class", "style"):
        head = re.sub(rf"\s{attribute}\s*=\s*[\"'][^\"']*[\"']", "", head, flags=re.IGNORECASE)
    head = re.sub(r"\s+", " ", head).strip()
    head = re.sub(r"^<\s*svg\b", "", head, flags=re.IGNORECASE)
    root = (
        f'<svg width="{size}" height="{size}" viewBox="0 0 {viewbox} {viewbox}" '
        f'fill="none" xmlns="http://www.w3.org/2000/svg"{head}>'
    )
    svg = root + body
    if "<title" not in svg.lower():
        svg = svg.replace(">", f"><title>{title}</title>", 1)
    return svg if svg.endswith("</svg>") else svg.rstrip() + "\n</svg>\n"


def write_icon(svg: str, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(svg if svg.endswith("\n") else svg + "\n", encoding="utf-8")
    return path


def list_catalogues() -> None:
    print(f"styles ({len(STYLES)}):")
    for name in sorted(STYLES):
        entry = STYLES[name]
        print(f"  {name:<16} stroke {entry['stroke']:<6} fill {entry['fill']:<8} {entry['best_for']}")
    print(f"\ncategories ({len(CATEGORIES)}):")
    for name in sorted(CATEGORIES):
        print(f"  {name:<16} {', '.join(CATEGORIES[name])}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate SVG icons with Gemini 3.1 Pro Preview.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--prompt", "-p", default=None, help="what the icon depicts")
    parser.add_argument("--name", "-n", default=None, help="icon name, used for the filename")
    parser.add_argument("--style", "-s", choices=sorted(STYLES), default="outlined", help="icon style")
    parser.add_argument("--category", "-c", choices=sorted(CATEGORIES), default=None,
                        help="category, for context in the prompt")
    parser.add_argument("--color", default="currentColor",
                        help="primary colour; currentColor lets CSS inherit it")
    parser.add_argument("--size", type=int, default=24, help="display size in px")
    parser.add_argument("--viewbox", type=int, default=24, help="SVG viewBox size")
    parser.add_argument("--output", "-o", default=None, help="output file path")
    parser.add_argument("--output-dir", default="./icons", help="output directory")
    parser.add_argument("--batch", type=int, default=1, help="number of variations")
    parser.add_argument("--sizes", default=None, help="comma-separated sizes to export")
    parser.add_argument("--list-styles", action="store_true", help="list the styles and exit")
    parser.add_argument("--list-categories", action="store_true", help="list the categories and exit")
    parser.add_argument("--dry-run", action="store_true", help="print the prompt and exit")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.list_styles or args.list_categories:
        list_catalogues()
        return 0
    if not args.prompt and not args.name:
        raise SystemExit("error: give --prompt (what it depicts), --name, or both")
    if args.size < 1 or args.viewbox < 1:
        raise SystemExit("error: --size and --viewbox must be positive")

    description = args.prompt or args.name
    name = slugify(args.name or description)
    title = (args.name or description).strip().replace("&", "and")[:60]

    sizes = [int(part) for part in args.sizes.split(",")] if args.sizes else [args.size]
    if any(size < 1 for size in sizes):
        raise SystemExit("error: --sizes must be positive integers")
    variations = max(1, args.batch)

    if args.dry_run:
        print(build_prompt(description, args.style, args.category, args.color, sizes[0], args.viewbox))
        print(f"# style: {args.style}\n# variations: {variations}\n# sizes: {sizes}\n"
              f"# output dir: {args.output_dir}", file=sys.stderr)
        return 0

    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        raise SystemExit(
            "error: GEMINI_API_KEY is not set. Get one at https://aistudio.google.com/apikey"
        )

    output = Path(args.output) if args.output else None
    written = 0
    failures = 0

    for variation in range(1, variations + 1):
        prompt = build_prompt(description, args.style, args.category, args.color, sizes[0], args.viewbox)
        if variations > 1:
            prompt += (
                f"\nThis is variation {variation} of {variations}. Take a clearly different "
                "approach from the obvious one: change the composition, not just the angle.\n"
            )
        try:
            svg = sanitize(
                extract_svg(call_model(prompt, key)),
                args.viewbox, sizes[0], title,
            )
        except SystemExit as exc:
            failures += 1
            log(str(exc))
            continue

        if output and variations == 1 and not args.sizes:
            write_icon(svg, output)
            log(f"wrote {output}")
            written += 1
            continue

        for size in sizes:
            sized = svg.replace(
                f'width="{sizes[0]}" height="{sizes[0]}"',
                f'width="{size}" height="{size}"',
            )
            suffix = f"-{variation}" if variations > 1 else ""
            ext = ".svg"
            path = Path(args.output_dir) / f"{name}-{size}px{suffix}{ext}"
            write_icon(sized, path)
            log(f"wrote {path}")
            written += 1

    log(f"{written} file(s) written, {failures} failure(s)")
    log("Open each SVG and check it at 16px. A model will happily return a shape that "
        "only reads at 256px, and an icon set is judged at the smallest size in it.")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
