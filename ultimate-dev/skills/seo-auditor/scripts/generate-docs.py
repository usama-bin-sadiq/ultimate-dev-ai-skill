#!/usr/bin/env python3
"""Generate the SEO documentation pages under docs/skills/ from SKILL.md files.

The site needs one page per skill. This script builds them from each skill's own
SKILL.md so the page, the metadata, and the skill cannot drift apart: the
frontmatter that triggers the skill is the same text the page advertises.

The pieces the SEO audit depends on, all in this file:

    DOMAIN_SEO_SUFFIX                  per-domain keyword suffixes for titles
    extract_description_from_frontmatter()  description -> meta description
    rewrite_skill_internal_links()     skill-relative links -> GitHub source URLs
    rewrite_relative_links()           ./ and ../ links -> docs-relative URLs
    build_title()                      "{Skill} - {differentiator} - {site}"

SKILL.md is never modified and an existing page is never overwritten without
--force, because a page that is already ranking is the one thing this pipeline is
not allowed to damage.

Reconstruction note: SKILL.md names this script and the three functions above,
and gives the title pattern and the meta-description length band, but not this
script's arguments. The CLI below is the minimum that can do the job: a source
directory, an output directory, and the site identity. The suffix table is this
file's own, built from the page types SKILL.md lists in its keyword table.

    python generate-docs.py ../skills -o docs/skills
    python generate-docs.py ../skills --site-name "Acme Docs" --repo-url https://github.com/acme/skills
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Iterable, NoReturn

# --- SEO bands the audit enforces -------------------------------------------

TITLE_MIN, TITLE_MAX = 50, 60
DESCRIPTION_MIN, DESCRIPTION_MAX = 120, 160

#: Per-domain keyword suffixes. Appended to a title only when the title would
#: otherwise land short of the band, so a page that already says what it is does
#: not get a keyword tail bolted on.
DOMAIN_SEO_SUFFIX: dict[str, str] = {
    "skills": "for AI coding agents",
    "agents": "AI coding agent",
    "commands": "slash command for Claude Code",
    "getting-started": "install and first run",
    "reference": "reference guide",
    "patterns": "implementation patterns",
}

# A skill name is kebab-case by convention; anything else is left alone.
KEBAB_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
FRONTMATTER_RE = re.compile(r"\A---\r?\n(.*?)\r?\n---[ \s]*(?:\r?\n|\Z)", re.DOTALL)
H1_RE = re.compile(r"^#\s+(.*\S)\s*$", re.MULTILINE)
FIRST_PARAGRAPH_RE = re.compile(r"\A(?!#|\s*$)(.+?)(?:\n\s*\n|\Z)", re.DOTALL)
MARKDOWN_LINK_RE = re.compile(r"\[([^\]]*)\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
# skill-internal targets that have no meaning on a docs site: bundled scripts,
# references, assets.
INTERNAL_TARGET_RE = re.compile(r"^(?:\.\./)*(?:scripts|references|assets|agents)/", re.IGNORECASE)

# Phrases a description must not open with.
DESCRIPTION_BANNED_OPENERS = ("this page", "this document", "this guide")


def die(message: str) -> NoReturn:
    print(f"generate-docs.py: {message}", file=sys.stderr)
    raise SystemExit(2)


# --- frontmatter -------------------------------------------------------------


def parse_frontmatter(text: str) -> dict[str, str]:
    """Parse the leading YAML frontmatter block as flat key/value pairs.

    Deliberately not a YAML parser: SKILL.md frontmatter is scalars and folded
    blocks, and pulling in a dependency to read it would make the doc build
    depend on the site build.
    """
    match = FRONTMATTER_RE.match(text)
    if match is None:
        return {}

    fields: dict[str, str] = {}
    key: str | None = None
    folded: list[str] = []

    def flush() -> None:
        nonlocal key, folded
        if key is not None:
            fields[key] = " ".join(part for part in folded if part).strip()
        key, folded = None, []

    for line in match.group(1).replace("\r\n", "\n").split("\n"):
        if not line.strip():
            continue
        if line[:1] in (" ", "\t") and key is not None:
            folded.append(line.strip())
            continue
        if line.lstrip().startswith("#"):
            continue
        head = re.match(r"^([A-Za-z0-9_.-]+)\s*:\s*(.*)$", line)
        if head is None:
            continue
        flush()
        key = head.group(1)
        value = head.group(2).strip()
        if value[:1] in "\"'":
            value = value.strip("\"'")
            fields[key] = value
            key = None
        else:
            folded = [value] if value else []
    flush()
    return fields


def extract_description_from_frontmatter(text: str) -> str:
    """Return the description a page should carry, or an empty string.

    In order: the frontmatter ``description``, then the first prose paragraph of
    the body. Never invents one from a heading, because a title repeated as a
    description is a duplicate-content signal.
    """
    fields = parse_frontmatter(text)
    description = (fields.get("description") or "").strip()
    if description:
        return re.sub(r"\s+", " ", description)

    body = FRONTMATTER_RE.sub("", text, count=1)
    paragraph = FIRST_PARAGRAPH_RE.search(body.lstrip())
    if paragraph is None:
        return ""
    return re.sub(r"\s+", " ", paragraph.group(1).replace("\n", " ")).strip()


def extract_title(text: str) -> str:
    """The human title of a skill: frontmatter ``title``, else the first H1."""
    fields = parse_frontmatter(text)
    if fields.get("title", "").strip():
        return fields["title"].strip()
    heading = H1_RE.search(text)
    return heading.group(1).strip() if heading else ""


# --- titles and descriptions -------------------------------------------------


def build_title(skill_name: str, differentiator: str, site_name: str) -> str:
    """Assemble `{Skill Name} - {Differentiator} - {site_name}`.

    The site name goes last because the static site generator appends it, and a
    title that already carries it reads as a duplicate in the listing. An em
    dash separates the skill from its differentiator; the site name is joined
    with a hyphen, which is the pattern the site uses.
    """
    head = " \u2014 ".join(part for part in (skill_name, differentiator) if part.strip())
    return f"{head} - {site_name.strip()}" if site_name.strip() else head


def _dedupe(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _truncate(value: str, limit: int) -> str:
    """Cut on a word boundary, never mid-word, and drop the trailing stop."""
    if len(value) <= limit:
        return value
    cut = value[:limit].rsplit(" ", 1)[0].rstrip(" ,;:.-")
    return cut + "..."


def page_differentiator(
    skill_name: str, description: str, domain: str | None = None
) -> str:
    """The middle of the title: what this page is for.

    Prefers the page's own summary, because two pages carrying the same generic
    keyword tail is exactly the duplicate-title finding the audit raises. Falls
    back to the first sentence of the description when the whole thing is too
    long, and to the domain's keyword suffix only when there is no description
    to work from at all.
    """
    summary = _dedupe(description)
    lowered = summary.lower()
    for opener in DESCRIPTION_BANNED_OPENERS:
        if lowered.startswith(opener):
            summary = summary[len(opener):].lstrip(" .")
            break
    if not summary:
        key = (domain or "").lower() or "skills"
        return DOMAIN_SEO_SUFFIX.get(key, DOMAIN_SEO_SUFFIX["skills"])

    first_sentence = summary.split(". ", 1)[0].rstrip(".")
    if len(summary) <= 60:
        return first_sentence
    return _truncate(first_sentence, 48)


def build_page_description(
    skill_name: str, description: str, differentiator: str
) -> str:
    """A meta description inside the band, unique per page, with a call to action."""
    body = _dedupe(description)
    lowered = body.lower()
    for opener in DESCRIPTION_BANNED_OPENERS:
        if lowered.startswith(opener):
            body = body[len(opener):].lstrip(" .")
            break

    candidate = f"{body} Read it before you use {skill_name}."
    candidate = _dedupe(candidate)
    if len(candidate) < DESCRIPTION_MIN:
        candidate = _dedupe(
            f"{candidate} See the full guide, worked examples, and the exact "
            "commands to run."
        )
    return _truncate(candidate, DESCRIPTION_MAX)


# --- links -------------------------------------------------------------------


def rewrite_skill_internal_links(
    body: str, repo_url: str | None, source_path: str = ""
) -> str:
    """Point bundled-resource links at the source repository.

    `scripts/foo.py` has no meaning on a docs site, so it becomes a link to the
    file in the repository. Without a repository URL the link is left exactly as
    written and reported, rather than rewritten to an empty target: an empty
    `[]()` is a broken link the audit cannot explain, and a link that still names
    the real file is a finding the audit's link check can act on.
    """
    if not repo_url:
        if INTERNAL_TARGET_RE.search(body) or "](references/" in body:
            print(
                "generate-docs.py: skill-internal links left unrewritten; pass "
                "--repo-url so they resolve",
                file=sys.stderr,
            )
        return body

    base = repo_url.rstrip("/")

    def replace(match: re.Match[str]) -> str:
        label, target = match.group(1), match.group(2)
        if not INTERNAL_TARGET_RE.match(target) and not target.startswith("references/"):
            return match.group(0)
        path = f"{source_path}/{target}" if source_path else target
        return f"[{label}]({base}/blob/main/{path.lstrip('/')})"

    return MARKDOWN_LINK_RE.sub(replace, body)


def rewrite_relative_links(body: str, page_relpath: str) -> str:
    """Resolve `./` and `../` links to docs-root-absolute paths.

    A skill's body is written relative to the skill directory; the generated page
    lives at `docs/skills/<name>.md`, so the same source link resolves elsewhere.
    Rewriting to a docs-root-absolute path (`/workflow.md`) is what MkDocs wants
    and is the one form that does not depend on where the page was written.
    """
    page_dir = Path(page_relpath).parent

    def replace(match: re.Match[str]) -> str:
        label, target = match.group(1), match.group(2)
        if re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:", target) or target.startswith("#"):
            return match.group(0)
        if not target.startswith("./") and not target.startswith("../"):
            return match.group(0)

        parts: list[str] = list(page_dir.parts)
        for part in Path(target).parts:
            if part in (".", ""):
                continue
            if part == "..":
                if parts:
                    parts.pop()
                continue
            parts.append(part)
        if target.endswith("/"):
            parts.append("index.md")
        elif not parts[-1].endswith(".md"):
            parts[-1] = parts[-1] + ".md"
        return f"[{label}](/{'/'.join(parts)})"

    return MARKDOWN_LINK_RE.sub(replace, body)


# --- page rendering ----------------------------------------------------------


def render_page(
    title: str,
    description: str,
    body: str,
    skill_name: str,
) -> str:
    """Assemble the generated Markdown page."""
    front = ["---", f'title: "{title.replace(chr(34), chr(39))}"',
             f'description: "{description.replace(chr(34), chr(39))}"', "---", ""]
    return "\n".join(front) + body.rstrip() + "\n"


def build_page(
    skill_dir: Path,
    out_dir: Path,
    site_name: str,
    repo_url: str | None,
    domain: str | None,
) -> tuple[Path, str, str]:
    """Build one page. Returns (path, title, rendered Markdown)."""
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.is_file():
        die(f"{skill_md} not found; every skill needs a SKILL.md")

    text = skill_md.read_text(encoding="utf-8", errors="replace")
    name = skill_dir.name
    description = extract_description_from_frontmatter(text)
    differentiator = page_differentiator(name, description, domain)
    title = build_title(name, differentiator, site_name)
    if len(title) > TITLE_MAX:
        title = _truncate(title, TITLE_MAX)
    page_description = build_page_description(name, description, differentiator)

    body = FRONTMATTER_RE.sub("", text, count=1).lstrip("\n")
    body = rewrite_skill_internal_links(body, repo_url, f"skills/{name}")
    page_relpath = f"{out_dir.name}/{name}.md"
    body = rewrite_relative_links(body, page_relpath)

    target = out_dir / f"{name}.md"
    return target, title, render_page(title, page_description, body, name)


def iter_skills(root: Path) -> Iterable[Path]:
    """Yield each skill directory under root, in name order."""
    if not root.is_dir():
        die(f"{root} is not a directory")
    for entry in sorted(root.iterdir()):
        if entry.is_dir() and (entry / "SKILL.md").is_file():
            if entry.name.startswith((".", "_")):
                continue
            if not KEBAB_RE.match(entry.name):
                continue
            yield entry


def read_site_name(mkdocs: Path | None) -> str:
    """Pull site_name out of mkdocs.yml when it is there."""
    if mkdocs is None or not mkdocs.is_file():
        return ""
    for line in mkdocs.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.strip().startswith("site_name:"):
            return line.split(":", 1)[1].strip().strip("\"'")
    return ""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="generate-docs.py",
        description="Generate docs/skills/ pages from SKILL.md files.",
        epilog="An existing page is left alone unless --force is given.",
    )
    parser.add_argument("skills", help="directory holding one subdirectory per skill")
    parser.add_argument("-o", "--out", default="docs/skills", help="output directory")
    parser.add_argument("--site-name", default="", help="appended to every title")
    parser.add_argument("--mkdocs", default="mkdocs.yml", help="read site_name from here")
    parser.add_argument(
        "--repo-url",
        default="",
        help="repository root that skill-internal links are rewritten to",
    )
    parser.add_argument(
        "--domain", default="skills", help="which DOMAIN_SEO_SUFFIX entry to use"
    )
    parser.add_argument("--force", action="store_true", help="overwrite existing pages")
    args = parser.parse_args(argv)

    site_name = args.site_name or read_site_name(Path(args.mkdocs))
    if not site_name:
        print("generate-docs.py: no site_name; titles will omit it", file=sys.stderr)
    repo_url = args.repo_url or None

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    written = skipped = 0
    for skill_dir in iter_skills(Path(args.skills)):
        target, title, content = build_page(
            skill_dir, out_dir, site_name, repo_url, args.domain
        )
        if target.exists() and not args.force:
            print(f"skip  {target} (exists; pass --force to replace)", file=sys.stderr)
            skipped += 1
            continue
        target.write_text(content, encoding="utf-8")
        written += 1
        print(f"write {target}  [{len(title)} chars]")

    print(f"\n{written} written, {skipped} skipped", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
