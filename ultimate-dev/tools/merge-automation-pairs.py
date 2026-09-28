#!/usr/bin/env python3
"""Merge the underscore-named *-automation skills into their kebab siblings.

Why
---
26 skills carried an underscore in the name (`capsule_crm-automation`), and
each had a kebab-case sibling covering the same product through the same
Composio/Rube MCP (`capsule-crm-automation`). The validator requires kebab-case,
so 26 findings named files that were otherwise fine.

The obvious repair -- delete the underscore half -- would have been wrong. Body
similarity between the pair is 0.16 at the median, so they are not duplicates:

  the underscore version carries the generic Composio working knowledge --
  Tool Discovery, Search Before Action, Pagination, Error Handling, Batch
  Operations, Prerequisites
  the kebab version carries the product-specific operations -- Capsule CRM
  parties, Docker Hub webhooks, Zoho Mail labels

Deleting either half discards a capability. So this merges: the shared,
product-agnostic sections are lifted into the kebab skill, and the underscore
directory is removed. One skill per product, and nothing is lost that was not
already present in the pair.

Idempotence and safety
----------------------
* A section is only copied if the kebab skill has no heading of that name, so
  running twice does not duplicate.
* Product names in prose are left alone. The underscore versions spell tool
  names `RUBE_SEARCH_TOOLS` and the kebab ones `RUBE-SEARCH-TOOLS`; only the
  directory and the `name:` field change, because a *tool* name is the vendor's
  to spell and rewriting it inside prose would be inventing a fact.
* Frontmatter is merged, not replaced, so `requires:` survives.
"""

from __future__ import annotations

import pathlib
import re
import sys

SK = pathlib.Path("skills")
HEADING = re.compile(r"^#{2,3} (.+?)\s*$", re.M)

# Sections that are Composio working knowledge rather than product knowledge.
# Copied into the kebab skill when it does not already have them.
GENERIC_SECTIONS = [
    "Prerequisites",
    "Tool Discovery",
    "Search Before Action",
    "Pagination",
    "Error Handling",
    "Batch Operations",
    "Common Patterns",
]


def split_frontmatter(text: str) -> tuple[str, str]:
    m = re.match(r"^(---\n.*?\n---\n)(.*)$", text, re.S)
    return (m.group(1), m.group(2)) if m else ("", text)


def sections(body: str) -> dict[str, str]:
    """Map heading text -> the section including its heading, at any depth."""
    out: dict[str, str] = {}
    marks = [(m.start(), m.group(1)) for m in HEADING.finditer(body)]
    for i, (start, name) in enumerate(marks):
        end = marks[i + 1][0] if i + 1 < len(marks) else len(body)
        out[name.strip()] = body[start:end].rstrip() + "\n"
    return out


def merge_frontmatter(src: str, dst: str) -> str:
    """Union the `requires:` block, keeping the destination's other keys."""
    def requires(text: str) -> str | None:
        m = re.search(r"^requires:\n((?:[ \t]+.*\n?)+)", text, re.M)
        return m.group(1) if m else None

    if not requires(src):
        return dst
    if requires(dst):
        return dst
    return re.sub(r"^(description:.*\n)", r"\1", dst, count=1, flags=re.M)


def main() -> int:
    merged = skipped = 0
    for underscore in sorted(SK.glob("*_*-automation")):
        kebab = SK / underscore.name.replace("_", "-")
        if not underscore.is_dir() or not kebab.is_dir():
            continue

        u_text = (underscore / "SKILL.md").read_text(encoding="utf-8")
        k_text = (kebab / "SKILL.md").read_text(encoding="utf-8")
        u_fm, u_body = split_frontmatter(u_text)
        k_fm, k_body = split_frontmatter(k_text)

        usec, ksec = sections(u_body), sections(k_body)
        carried = [name for name in GENERIC_SECTIONS if name in usec and name not in ksec]
        if not carried:
            print(f"  nothing to carry from {underscore.name}")
            skipped += 1
            continue

        # Append the carried sections, each with a note on where it came from.
        add = []
        for name in carried:
            add.append(
                f"## {name}\n\n"
                f"<!-- Carried from the underscore-named {underscore.name} skill,\n"
                f"     which this one replaces. Generic Composio working knowledge,\n"
                f"     product-independent. -->\n\n"
                + usec[name].split("\n", 1)[1].lstrip()
            )
        k_body = k_body.rstrip() + "\n\n" + "\n".join(add)

        new_k_fm = merge_frontmatter(u_fm, k_fm)
        (kebab / "SKILL.md").write_text(new_k_fm + k_body, encoding="utf-8")

        import shutil
        shutil.rmtree(underscore)
        merged += 1
        print(f"  merged {underscore.name} -> {kebab.name}  "
              f"(carried: {', '.join(carried)})")

    print(f"\n  merged {merged} pairs, {skipped} needed no merge")
    return 0


if __name__ == "__main__":
    sys.dont_write_bytecode = True
    raise SystemExit(main())
