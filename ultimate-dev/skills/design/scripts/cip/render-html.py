#!/usr/bin/env python3
"""Render an HTML presentation of generated CIP mockups.

What it does
------------
Scans a directory of generated mockup images, matches each filename back to its
deliverable through the CIP catalogue, and writes a single self-contained HTML
file: a cover, a grid of deliverable cards grouped by CIP group, a per-item
detail view, and the style and colour decisions the set was generated with.

The output is one file with no build step and no network dependency, so it opens
from disk, prints to PDF from a browser, and can be sent to a client as an
attachment.

Usage
-----
    python3 scripts/cip/render-html.py --brand "TopGroup" --industry "consulting" \\
        --images /path/to/cip-output
    python3 scripts/cip/render-html.py --brand "TopGroup" --images ./cip-output \\
        -o cip.html --title "Corporate Identity Program"
    python3 scripts/cip/render-html.py --brand "TopGroup" --images ./cip-output \\
        --open   # also open it in the default browser

Exit codes: 0 HTML written, 1 no images found, 2 bad input.

Provenance
----------
Reconstructed to match the invocation in this skill's SKILL.md
(``--brand``, ``--industry``, ``--images``). The layout, grouping, and output are
this file's own.
"""

from __future__ import annotations

import argparse
import html
import json
import sys
import webbrowser
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from core import DELIVERABLES, INDUSTRIES, STYLES, resolve  # noqa: E402

IMAGE_EXTS = (".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg")
GROUP_ORDER = [
    "Core identity",
    "Stationery",
    "Printed collateral",
    "Office environment",
    "Apparel",
    "Vehicle branding",
    "Digital",
    "Retail and packaging",
    "Signage and membership",
    "Events and promotional",
]


def log(message: str) -> None:
    print(message, file=sys.stderr, flush=True)


def find_images(directory: Path) -> list[Path]:
    """Every image in the directory, sorted; the CIP scripts write flat."""
    if not directory.is_dir():
        raise SystemExit(
            f"error: --images is not a directory: {directory}. Point it at the "
            "--output-dir you generated into, not at a single file."
        )
    return sorted(
        path for path in directory.iterdir()
        if path.is_file() and path.suffix.lower() in IMAGE_EXTS
    )


def match_deliverable(path: Path) -> tuple[str | None, dict | None]:
    """Map a filename back to a catalogue deliverable by slug overlap.

    Generated files are named ``<brand>-<deliverable>.png``, so a substring match
    on the deliverable slug is enough and does not need the brand prefix.
    """
    stem = path.stem.lower()
    best_name = None
    for name in sorted(DELIVERABLES, key=len, reverse=True):
        if name in stem:
            return name, DELIVERABLES[name]
    if best_name:  # pragma: no cover - unreachable while the loop returns on match
        return best_name, DELIVERABLES[best_name]
    return None, None


def collect(images: list[Path]) -> list[dict]:
    items = []
    for path in images:
        name, entry = match_deliverable(path)
        items.append({
            "file": path.name,
            "deliverable": name,
            "group": entry["group"] if entry else "Unmatched",
            "best_for": entry["best_for"] if entry else "",
            "spec": entry["spec"] if entry else "",
        })
    return items


def build_html(brand: str, items: list[dict], industry: str | None, style: str | None, title: str | None) -> str:
    """One self-contained HTML document: cover, grouped grid, detail per item."""
    esc = html.escape
    style_entry = STYLES[style] if style else None
    industry_entry = INDUSTRIES[industry] if industry else None

    grouped: dict[str, list[dict]] = {}
    for item in items:
        grouped.setdefault(item["group"], []).append(item)
    ordered_groups = [name for name in GROUP_ORDER if name in grouped]
    ordered_groups += [name for name in sorted(grouped) if name not in GROUP_ORDER]

    cards = []
    for group in ordered_groups:
        block = [f'<section class="group"><h2>{esc(group)}</h2><div class="grid">']
        for item in grouped[group]:
            label = esc((item["deliverable"] or Path(item["file"]).stem).replace("-", " "))
            spec = f'<p class="spec">{esc(item["spec"])}</p>' if item["spec"] else ""
            block.append(
                f'<figure class="card" data-src="{esc(item["file"])}">'
                f'<img loading="lazy" src="{esc(item["file"])}" alt="{label} mockup">'
                f"<figcaption><h3>{label}</h3>"
                f'<p class="fits">{esc(item["best_for"])}</p>{spec}'
                f'<button class="detail" data-target="{esc(item["file"])}">View</button>'
                f"</figcaption></figure>"
            )
        block.append("</div></section>")
        cards.append("\n".join(block))

    decision_rows = []
    if style_entry:
        for key, label in (("colors", "Colours"), ("typography", "Typography"),
                           ("materials", "Materials"), ("finishes", "Finishes")):
            decision_rows.append(f"<tr><th>{label}</th><td>{esc(style_entry[key])}</td></tr>")
    if industry_entry:
        decision_rows.append(f"<tr><th>Sector</th><td>{esc(industry_entry['best_for'])}</td></tr>")
        decision_rows.append(f"<tr><th>Sector caution</th><td>{esc(industry_entry['caution'])}</td></tr>")
    decisions = (
        "<table class='decisions'>" + "".join(decision_rows) + "</table>" if decision_rows else ""
    )

    images_json = json.dumps([item["file"] for item in items])
    headings = ", ".join(esc((item["deliverable"] or "").replace("-", " ")) for item in items[:12])

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title or f"{brand} — Corporate Identity Program")}</title>
<style>
  :root {{
    --ink: #14131a;
    --muted: #6b6880;
    --paper: #faf9f7;
    --card: #ffffff;
    --line: #e6e3dd;
    --accent: #2f6f6b;
  }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0;
    background: var(--paper);
    color: var(--ink);
    font: 16px/1.6 -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  }}
  header.cover {{
    padding: 96px 48px 72px;
    border-bottom: 1px solid var(--line);
    background: linear-gradient(160deg, #ffffff 0%, #f2efe9 100%);
  }}
  .cover h1 {{ font-size: clamp(2rem, 5vw, 3.5rem); margin: 0 0 .25em; letter-spacing: -.02em; }}
  .cover p {{ color: var(--muted); margin: 0; max-width: 60ch; }}
  .cover .count {{ margin-top: 2rem; font-size: .875rem; letter-spacing: .08em;
                    text-transform: uppercase; color: var(--muted); }}
  main {{ max-width: 1240px; margin: 0 auto; padding: 48px 24px 96px; }}
  section.group {{ margin-bottom: 64px; }}
  section.group h2 {{
    font-size: 1.125rem; text-transform: uppercase; letter-spacing: .08em;
    color: var(--muted); border-bottom: 1px solid var(--line); padding-bottom: 12px;
  }}
  .grid {{ display: grid; gap: 32px; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); }}
  .card {{
    margin: 0; background: var(--card); border: 1px solid var(--line);
    border-radius: 10px; overflow: hidden; display: flex; flex-direction: column;
  }}
  .card img {{ width: 100%; aspect-ratio: 4/3; object-fit: contain; background: #f4f2ee; }}
  .card figcaption {{ padding: 16px 18px 20px; display: flex; flex-direction: column; gap: 8px; }}
  .card h3 {{ margin: 0; font-size: 1rem; text-transform: capitalize; }}
  .card .fits, .card .spec {{ margin: 0; font-size: .8125rem; color: var(--muted); }}
  .card .spec {{ font-size: .75rem; }}
  button.detail {{
    margin-top: 8px; align-self: flex-start; background: none; cursor: pointer;
    border: 1px solid var(--line); border-radius: 6px; padding: 6px 14px;
    font: inherit; font-size: .8125rem; color: var(--ink);
  }}
  button.detail:hover {{ border-color: var(--accent); color: var(--accent); }}
  .decisions {{ width: 100%; border-collapse: collapse; margin-top: 24px; font-size: .875rem; }}
  .decisions th, .decisions td {{ text-align: left; vertical-align: top; padding: 10px 16px 10px 0;
                                   border-bottom: 1px solid var(--line); }}
  .decisions th {{ width: 160px; color: var(--muted); font-weight: 500; }}
  dialog {{
    border: 0; padding: 0; max-width: 92vw; max-height: 92vh; background: #111;
    border-radius: 10px; overflow: auto;
  }}
  dialog::backdrop {{ background: rgba(10, 10, 12, .82); }}
  dialog img {{ display: block; max-width: 92vw; max-height: 78vh; object-fit: contain; }}
  dialog .close {{ position: sticky; top: 0; float: right; margin: 8px;
                   background: rgba(255,255,255,.9); border: 0; border-radius: 6px;
                   padding: 6px 12px; font: inherit; cursor: pointer; }}
  footer {{ border-top: 1px solid var(--line); padding: 32px 24px; color: var(--muted);
            font-size: .8125rem; text-align: center; }}
  @media (prefers-reduced-motion: reduce) {{
    * {{ transition-duration: .01ms !important; animation-duration: .01ms !important; }}
  }}
</style>
</head>
<body>
<header class="cover">
  <h1>{esc(brand)}</h1>
  <p>{esc(title or "Corporate Identity Program")}</p>
  <p class="count">{len(items)} deliverable mockups{esc(f" — {headings}…" if len(items) > 12 else "")}</p>
</header>
<main>
  {decisions}
  {"".join(cards)}
</main>
<footer>
  Generated mockups. Every image is a design proposal: check the logo is present and
  undistorted, and confirm specifications with the printer before production.
</footer>
<dialog id="lightbox">
  <button class="close" type="button">Close</button>
  <img alt="Mockup, enlarged">
</dialog>
<script>
  const files = {images_json};
  const dialog = document.getElementById('lightbox');
  const large = dialog.querySelector('img');
  document.querySelectorAll('button.detail').forEach((button) => {{
    button.addEventListener('click', () => {{
      large.src = button.dataset.target;
      large.alt = button.closest('figure').querySelector('h3').textContent;
      dialog.showModal();
    }});
  }});
  dialog.querySelector('.close').addEventListener('click', () => dialog.close());
  dialog.addEventListener('click', (event) => {{ if (event.target === dialog) dialog.close(); }});
  if (files.length) {{ console.log(files.length + ' mockup(s) in this deck'); }}
</script>
</body>
</html>
"""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Render an HTML presentation of generated CIP mockups.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--brand", required=True, help="brand name")
    parser.add_argument("--images", required=True, help="directory of generated mockup images")
    parser.add_argument("--industry", default=None, help="sector, for the decisions table")
    parser.add_argument("--style", default=None, help="CIP style, for the decisions table")
    parser.add_argument("--title", default=None, help="deck title")
    parser.add_argument("-o", "--output", default=None, help="output HTML path; default cip-presentation.html")
    parser.add_argument("--open", dest="open_browser", action="store_true",
                        help="open the result in the default browser")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    industry = None
    if args.industry:
        try:
            industry = resolve(args.industry, "industry")
        except KeyError as exc:
            log(f"warning: {exc.args[0]}; the decisions table will omit the sector")
    style = None
    if args.style:
        try:
            style = resolve(args.style, "style")
        except KeyError as exc:
            log(f"warning: {exc.args[0]}; the decisions table will omit the style")

    images = find_images(Path(args.images))
    if not images:
        raise SystemExit(
            f"error: no images found in {args.images}. Generate the mockups first with "
            "`scripts/cip/generate.py --set`."
        )

    items = collect(images)
    unmatched = [item["file"] for item in items if item["deliverable"] is None]
    if unmatched:
        log(f"note: {len(unmatched)} image(s) did not match a catalogue deliverable and are "
            f"grouped under 'Unmatched': {', '.join(unmatched[:5])}")

    output = Path(args.output or "cip-presentation.html")
    output.write_text(build_html(args.brand, items, industry, style, args.title), encoding="utf-8")
    log(f"wrote {output} ({len(items)} mockup(s))")
    log("Open it in a browser and check every image, then print to PDF if the client needs a deck.")
    if args.open_browser:
        webbrowser.open(output.resolve().as_uri())
    return 0


if __name__ == "__main__":
    sys.exit(main())
