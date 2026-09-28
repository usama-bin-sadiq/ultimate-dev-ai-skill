#!/usr/bin/env python3
"""Derive a dispatch condition for every agent role that lacks one.

Why
---
286 role files ship in `agents/`. Nineteen have a row in the dispatch table in
`references/delegation.md`, so 267 are unreachable: the role exists, its
procedure and output contract are verified, and no decision can ever call it.
The kernel is explicit that "a role with no dispatch condition is not available,
however good it is", which makes this the one place in the system where
machinery is complete and unused.

Why derived, not written
------------------------
A dispatch condition is a claim about when to reach for a role, and a claim
written without reading the role is a guess with a table row's authority. Each
condition below is assembled from what the role file already states about
itself:

  * its `description:` frontmatter, which is the role's own one-line purpose
  * the "Delegate when" or equivalent trigger sentence in its body, if it has one
  * its prohibitions, which are the clearest statement of when NOT to use it

The generated text is therefore a compression of the role, not an invention. It
is also visibly mechanical, and the header of the generated block says so, so a
reader can tell a derived condition from a considered one and rewrite the ones
that deserve it.

What it does not do
-------------------
It does not claim these conditions are good. A 267-row table derived
mechanically is a starting point that makes every role reachable; it is not
267 decisions about when to delegate. The table is written to be edited.
"""

from __future__ import annotations

import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
AGENTS = ROOT / "agents"
DELEGATION = ROOT / "references" / "delegation.md"

TRIGGER_HEADINGS = re.compile(
    r"^#{2,3}\s*(delegate when|when to delegate|use when|dispatch when|"
    r"when to use|invocation|triggers?)\b",
    re.IGNORECASE,
)
STOP_HEADING = re.compile(
    r"^#{2,3}\s*(prohibitions?|do not|never|must not|when not to|out of scope)\b",
    re.IGNORECASE,
)


def frontmatter(text: str) -> dict[str, str]:
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not m:
        return {}
    out: dict[str, str] = {}
    for key, value in re.findall(r"^([A-Za-z-]+):\s*(.+)$", m.group(1), re.M):
        out[key] = value.strip().strip('"')
    return out


def first_sentence(text: str, limit: int = 220) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) <= limit:
        return text
    cut = text[:limit]
    sp = cut.rfind(" ")
    return (cut[:sp] if sp > 0 else cut).rstrip(" ,;:") + " ..."


def stated_trigger(body: str) -> str | None:
    """The role's own 'when to use this' sentence, if it wrote one."""
    lines = body.split("\n")
    for i, line in enumerate(lines):
        if not TRIGGER_HEADINGS.match(line):
            continue
        chunk: list[str] = []
        for follow in lines[i + 1 : i + 14]:
            if follow.startswith("#"):
                break
            chunk.append(follow)
        text = " ".join(x.strip() for x in chunk if x.strip())
        # Drop the bullet glyphs and any leading role name.
        text = re.sub(r"^[-*]\s*", "", text).strip()
        if len(text) > 30:
            return first_sentence(text)
    return None


def stated_prohibition(body: str) -> str | None:
    lines = body.split("\n")
    for i, line in enumerate(lines):
        if not STOP_HEADING.match(line):
            continue
        for follow in lines[i + 1 : i + 8]:
            text = re.sub(r"^[-*]\s*", "", follow.strip()).strip()
            if len(text) > 25:
                return first_sentence(text, 150)
    return None


def condition_for(path: pathlib.Path) -> tuple[str, str]:
    """(condition, produces) derived from the role's own statements."""
    text = path.read_text(encoding="utf-8", errors="replace")
    fm = frontmatter(text)
    body = re.sub(r"^---\n.*?\n---\n", "", text, flags=re.S)

    trigger = stated_trigger(body)
    purpose = fm.get("description") or first_sentence(body, 180)

    if trigger:
        cond = trigger
    elif purpose:
        # Capitalise and frame it as a condition rather than a noun phrase.
        cond = first_sentence(purpose, 200)
        cond = cond[0].upper() + cond[1:]
    else:
        cond = "The role file states no trigger; read it before dispatching"

    produces = stated_prohibition(body)
    if produces:
        produces = f"Not: {produces}"
    else:
        produces = "Per its output contract"

    return cond, produces


def main() -> int:
    text = DELEGATION.read_text(encoding="utf-8")
    routed = set(re.findall(r"`agents/([a-z0-9_-]+)\.md`", text))

    roles = sorted(
        p.stem for p in AGENTS.glob("*.md")
        if p.stem.islower() and p.stem != "README"
    )
    missing = [r for r in roles if r not in routed]

    lines = [
        "",
        "## Every shipped role, and when to call it",
        "",
        "The nineteen rows above were written by hand and are the ones this",
        "repository relies on. The rows below cover the remaining",
        f"{len(missing)} role files so that no shipped role is unreachable: a role",
        "with no dispatch condition is not available, however good it is.",
        "",
        "**These conditions are derived, not considered.** Each was compressed",
        "from the role file's own `description:` and any trigger sentence it",
        "wrote about itself. They make every role reachable; they are not 267",
        "decisions about when delegation pays. Read a row, and rewrite it if the",
        "role deserves better -- the table is meant to be edited, and a",
        "mechanically derived row is visibly mechanical on purpose.",
        "",
        "| Role | Delegate when | Produces |",
        "|---|---|---|",
    ]
    for role in missing:
        cond, produces = condition_for(AGENTS / f"{role}.md")
        lines.append(f"| `agents/{role}.md` | {cond} | {produces} |")
    lines.append("")

    DELEGATION.write_text(text.rstrip("\n") + "\n" + "\n".join(lines), encoding="utf-8")
    print(f"  routed already      : {len(routed)}")
    print(f"  rows added          : {len(missing)}")
    print(f"  total routed now    : {len(routed) + len(missing)} of {len(roles)}")
    return 0


if __name__ == "__main__":
    sys.dont_write_bytecode = True
    raise SystemExit(main())
