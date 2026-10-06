#!/usr/bin/env python3
"""Repoint broken relative links that resolve uniquely elsewhere in the skill.

Flattening and re-importing the collection left some links pointing at the old
layout. A link like `./api.md` may still be satisfied, just one directory
deeper (`references/api/api.md`). This walks every broken relative link and:

  * repoints it when exactly ONE file in the same skill matches the basename
  * leaves it alone when the match is ambiguous (several candidates) or when
    nothing matches — those need a human decision

Only links whose target is a plain relative path are touched. URLs,
placeholders and `${VAR}` targets are skipped.

Usage:
    python3 tools/repair-links.py --dry-run
    python3 tools/repair-links.py
"""

import argparse
import collections
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("check_links", ROOT / "tools" / "check-links.py")
cl = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cl)


# Basenames too generic to resolve a link by name alone.
GENERIC_BASES = {"SKILL.md", "README.md", "readme.md", "index.md", "LICENSE"}


def skill_root_of(doc: Path) -> Path | None:
    """skills/<name>/... -> skills/<name>; agents/ and root files -> None."""
    try:
        rel = doc.relative_to(ROOT / "skills")
    except ValueError:
        return None
    return ROOT / "skills" / rel.parts[0]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    fixed = collections.Counter()
    ambiguous: list[str] = []
    unresolved: list[str] = []

    for doc in cl.docs():
        raw = doc.read_text(errors="ignore")
        clean = cl.strip_code(raw)
        sroot = skill_root_of(doc)
        if sroot is None or not sroot.is_dir():
            continue

        targets = []
        for t in cl.LINK.findall(clean):
            t = t.split("#")[0].strip()
            if not t or t.startswith(("http://", "https://", "mailto:", "#", "/")):
                continue
            if cl.PLACEHOLDER.search(t) or "${" in t:
                continue
            if (doc.parent / t).exists():
                continue
            targets.append(t)
        if not targets:
            continue
        if doc.name.endswith(("_template.md", ".template.md")):
            continue  # a generator template's links describe its output

        changed = False
        for t in sorted(set(targets)):
            base = t.rsplit("/", 1)[-1]
            # Generic basenames match almost anything, and a match on the
            # document's own path is a self-link, not a repair.
            if base in GENERIC_BASES:
                unresolved.append(f"{doc.relative_to(ROOT)}: {t} (generic basename)")
                continue
            candidates = [p for p in sroot.rglob(base) if p.is_file()]
            # ignore anything inside a nested copy of a different skill
            candidates = [p for p in candidates if sroot in p.parents]
            # never repoint a link at the file that contains it
            candidates = [p for p in candidates if p.resolve() != doc.resolve()]
            if len(candidates) == 1:
                newt = Path(
                    __import__("os").path.relpath(candidates[0], doc.parent)
                ).as_posix()
                # replace only the exact link target, longest-first to avoid
                # clobbering a longer path that shares this prefix
                old_md = f"]({t})"
                new_md = f"]({newt})"
                if old_md in raw:
                    raw = raw.replace(old_md, new_md)
                    changed = True
                    fixed[f"{t} -> {newt}"] += 1
            elif len(candidates) > 1:
                ambiguous.append(f"{doc.relative_to(ROOT)}: {t} -> {len(candidates)} candidates")
            else:
                unresolved.append(f"{doc.relative_to(ROOT)}: {t}")

        if changed and not a.dry_run:
            doc.write_text(raw)

    total = sum(fixed.values())
    print(f"links repointed: {total}")
    print(f"ambiguous (left for a human): {len(ambiguous)}")
    print(f"no match anywhere (left for a human): {len(unresolved)}")
    if a.dry_run:
        print("\nsample repoints:")
        for k, v in list(fixed.items())[:20]:
            print(f"  {v:>3}  {k}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
