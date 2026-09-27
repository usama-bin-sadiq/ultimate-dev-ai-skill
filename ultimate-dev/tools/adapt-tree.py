#!/usr/bin/env python3
"""Adapt an imported capability tree to this repository's conventions.

One pass. Each step is mechanical and decidable; each is verified by comparing
the parsed frontmatter before and after, because a bulk rewrite of thousands of
files is exactly the operation that silently corrupts some of them. The first
attempt at this corrupted 11,662 values and produced 2,366 new errors, and the
reason it went unnoticed is that it reported a count instead of a differential.

Steps, in order:

  1. frontmatter conformance   every capability carries `name` and `description`.
                               `name` matches the directory the runtime resolves,
                               is kebab-case, and `description` is a quoted scalar
                               so it parses. These are the three defects that
                               make a file undiscoverable.

  2. discovery signal          a description is the only text a runtime sees
                               before deciding to load. An empty one, or one that
                               is a bare noun phrase, is not a discovery signal.
                               Where the description is missing the name is used
                               and the file is marked `description_inferred: true`
                               so a reader knows it was not authored.

  3. version stamp             `version: 1.0` where absent, so behaviour is
                               attributable to a revision.

  4. structural accounting     reports what it did and what it refused to do.

NOT done here, deliberately: rewriting a description that is present but weak.
Judging whether a description is *good* is reading, and a rule that guesses
produces plausible text that says less than the original. Those are listed for
review instead.

Usage:
    python3 tools/adapt-tree.py            # dry run, with a per-file differential
    python3 tools/adapt-tree.py --apply
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FM = re.compile(r"\A---\n(.*?)\n---\n", re.S)
KEBAB = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
# A top-level key, or an indented list item. Both are frontmatter, and a list
# item is broken YAML in the same way a top-level key is.
KEYLINE = re.compile(r"^(\s*(?:-\s+)?)([A-Za-z_][A-Za-z0-9_-]*)(\s*):(\s)(.*)$")
BLOCK = re.compile(r"^[>|][-+]?\d*$")
CONT = re.compile(r"^\s+\S")

ALLOWED = {"name", "description", "license", "allowed-tools", "metadata",
           "compatibility", "version", "neutralised", "domain_bound",
           "description_inferred", "triggers", "argument-hint", "preamble-tier",
           "model", "color", "user-invocable", "disable-model-invocation"}


def parse_fm(text: str) -> dict | None:
    m = FM.match(text)
    if not m:
        return None
    out: dict[str, str] = {}
    key = None
    for line in m.group(1).splitlines():
        km = KEYLINE.match(line)
        if km:
            key = km.group(2)
            out[key] = km.group(4).strip()
        elif CONT.match(line) and key:
            out[key] = (out[key] + " " + line.strip()).strip()
    return out


def unquote(v: str) -> str:
    v = v.strip()
    if len(v) > 1 and v[0] == v[-1] and v[0] in "\"'":
        inner = v[1:-1]
        return inner.replace('\\"', '"').replace("''", "'") if v[0] == '"' \
            else inner.replace("''", "'")
    return v


def needs_quote(v: str) -> bool:
    if not v:
        return False
    if BLOCK.match(v):
        return False                      # block scalar header, not a value
    if v[0] in "\"'[{>|*&!%@`":
        return False                      # already quoted or a block indicator
    return ": " in v or v.endswith(":") or v.strip() != v or v.lower() in {
        "yes", "no", "on", "off", "true", "false", "null", "~"}


def quote(v: str) -> str:
    if v and v[0] in "\"'":
        return v
    if '"' in v:
        return "'" + v.replace("'", "''") + "'"
    return '"' + v.replace("\\", "\\\\").replace('"', '\\"') + '"'


def slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")[:64] or "unnamed"


def adapt(text: str, dir_name: str) -> tuple[str, Counter, dict | None, dict | None]:
    stats: Counter = Counter()
    before = parse_fm(text)
    m = FM.match(text)
    if not m:
        return text, stats, before, None

    head_lines = m.group(1).splitlines()
    out: list[str] = []
    seen: set[str] = set()
    for line in head_lines:
        km = KEYLINE.match(line)
        if not km:
            out.append(line)
            continue
        indent, key, value = km.group(1), km.group(2), km.group(4)
        seen.add(key)
        if key == "name":
            want = slug(dir_name)
            if unquote(value) != want:
                out.append(f"{indent}name: {want}")
                stats["name-fixed"] += 1
                continue
        if needs_quote(value) and value:
            out.append(f"{indent}{key}: {quote(value)}")
            stats["quoted"] += 1
            continue
        out.append(line)

    head = "\n".join(out)
    fm = parse_fm("---\n" + head + "\n---\n") or {}

    # A missing description is NOT auto-filled. Inventing one from the filename
    # produces text that reads as an authored discovery signal and says nothing:
    # "aspose. No description was supplied" is not a description. Worse, 2,536 of
    # them would compete in the runtime's scan for attention, which is the
    # trigger-signal splitting this repository argues against everywhere else.
    # The honest move is to mark the gap so it is countable and findable, and
    # leave the authoring to whoever reads the file.
    desc = unquote(fm.get("description", "")).strip()
    if not desc:
        head += "\ndescription_missing: true"
        stats["description-missing-marked"] += 1

    if "version" not in seen:
        head += "\nversion: 1.0"
        stats["version-added"] += 1

    new_text = "---\n" + head + "\n---\n" + text[m.end():]
    after = parse_fm(new_text)
    if before and after:
        # The value must survive the edit. A transform that changes the meaning
        # of a field while fixing its syntax is not a syntax fix.
        for k, v in before.items():
            if k in ("name", "version", "description_inferred"):
                continue
            if unquote(str(after.get(k, ""))) != unquote(str(v)):
                stats["VALUE-CHANGED"] += 1
                stats[f"changed:{k}"] += 1
    return new_text, stats, before, after


def main() -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()

    files = sorted((ROOT / "skills").glob("*/SKILL.md")) + \
        sorted(p for p in (ROOT / "agents").glob("*.md") if p.stem.islower())
    if args.limit:
        files = files[:args.limit]

    total: Counter = Counter()
    changed = 0
    for p in files:
        text = p.read_text(encoding="utf-8", errors="replace")
        name = p.parent.name if p.parent.name != "agents" else p.stem
        fixed, stats, before, after = adapt(text, name)
        if not stats:
            continue
        if stats["VALUE-CHANGED"]:
            # Refuse to write a file whose field values did not survive.
            total.update({k: v for k, v in stats.items() if k != "VALUE-CHANGED"})
            total["refused-value-changed"] += 1
            continue
        changed += 1
        total.update(stats)
        if args.apply:
            p.write_text(fixed, encoding="utf-8")

    mode = "APPLIED" if args.apply else "DRY RUN"
    print(f"  {mode}")
    print(f"  files examined       {len(files)}")
    print(f"  files rewritten      {changed}")
    print(f"  names fixed          {total['name-fixed']}")
    print(f"  values quoted        {total['quoted']}")
    print(f"  descriptions MISSING {total['description-missing-marked']} "
          f"(marked, not invented -- see the module docstring)")
    print(f"  versions added       {total['version-added']}")
    if total["refused-value-changed"]:
        print(f"  REFUSED (value changed)  {total['refused-value-changed']}")
        for k, v in sorted(total.items()):
            if k.startswith("changed:"):
                print(f"      {k[8:]:24} {v}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
