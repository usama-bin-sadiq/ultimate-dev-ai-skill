#!/usr/bin/env python3
"""Derive a dispatch condition for any agent role that lacks one.

What this is for now
--------------------
The job this tool was written for is done. All 286 roles have a row in
`references/delegation.md`: 19 written by hand, 267 derived by an earlier run of
this script. The kernel's rule -- "a role with no dispatch condition is not
available, however good it is" -- is now satisfied for every shipped role, and
`validate-skills.py` fails the build if it stops being true. So this is no longer
a scaffolding step to run once; it is a repair tool, and it only does anything
when someone adds a role without a row.

That is the correct steady state for a script that rewrites a hand-maintained
document. It stays because the failure it repairs is silent and total: a new
role with no row is a role the kernel will never call, and nothing else in the
repository notices.

Running it rewrites `references/delegation.md`. Read the diff before committing
it. Every derived row is visibly mechanical, and the generated block says so, so
a hand-written condition and a derived one are distinguishable at a glance -- the
script is meant to be run, reviewed, and then edited.

Why derived, not written
------------------------
A dispatch condition is a claim about when to reach for a role, and a claim
written without reading the role is a guess with a table row's authority. Each
derived condition is assembled from what the role file already states about
itself:

  * its `description:` frontmatter, which is the role's own one-line purpose
  * the "Delegate when" or equivalent trigger sentence in its body, if it has one
  * its prohibitions, which are the clearest statement of when NOT to use it

The generated text is therefore a compression of the role, not an invention.

What it does not claim
----------------------
It does not claim these conditions are good. Most of the 267 rows currently in
the table restate the role's own description rather than deciding anything --
`index-tree.py` measures that split and reports it as a band, and the band is low.
A mechanically derived row makes a role *reachable*; it does not make the
decision about when delegation pays. Those rows are written to be edited, and
rewriting them is the real remaining work on the dispatch table.
"""

from __future__ import annotations

import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
AGENTS = ROOT / "agents"
DELEGATION = ROOT / "references" / "delegation.md"
DERIVED_HEADING = "## Every shipped role"

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

    # The steady state is an empty `missing`. Appending a second generated block
    # then would duplicate the section and read as though something new had been
    # routed, so an unchanged table is reported and left alone. A repair tool that
    # rewrites a document when there is nothing to repair is a tool that will
    # eventually rewrite one when there is.
    if not missing:
        # Everything has a row, so nothing is written. The useful output is now
        # how much of the existing table is considered rather than merely derived:
        # that split is the real remaining work, and it is what this tool used to
        # be mistaken for having finished.
        hand, _, derived_block = text.partition(DERIVED_HEADING)
        hand_written = len(
            set(re.findall(r"`agents/([a-z0-9_-]+)\.md`", hand))
        )
        derived = len(
            set(re.findall(r"`agents/([a-z0-9_-]+)\.md`", derived_block))
        )
        print(
            f"  every role already has a dispatch row: {len(routed)} of "
            f"{len(roles)}"
        )
        print("  nothing to do; references/delegation.md not modified")
        print(
            f"  {hand_written} written by hand, {derived} derived. The derived "
            "rows are reachable but mostly restate the role's own description; "
            "rewriting them into conditions that decide is manual work this "
            "tool will not do for you."
        )
        return 0

    lines = [
        "",
        "## Every shipped role, and when to call it",
        "",
        "The rows above the marker were written by hand and are the ones this",
        "repository relies on. The rows below cover the",
        f"{len(missing)} role file(s) that had no dispatch condition, so that no",
        "shipped role is unreachable: a role with no dispatch condition is not",
        "available, however good it is.",
        "",
        "**These conditions are derived, not considered.** Each was compressed",
        "from the role file's own `description:` and any trigger sentence it",
        "wrote about itself. They make every role reachable; they are not",
        f"{len(missing)} decisions about when delegation pays. Read a row, and",
        "rewrite it if the role deserves better -- the table is meant to be",
        "edited, and a mechanically derived row is visibly mechanical on purpose.",
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
