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

# A heading only counts if it means "when to call me". The earlier pattern also
# accepted bare "trigger", "triggers" and "invocation", and those are ordinary
# words inside a domain: `## Trigger` in an email role is a template field,
# `## Trigger Points` is that role's subject matter, and `### When to Use
# Platform Events vs Change Data Capture` is a Salesforce comparison. All four
# were extracted as dispatch conditions, and a table fragment is worse than a
# restatement because it looks like a decision.
TRIGGER_HEADINGS = re.compile(
    r"^#{2,3}\s*(delegate when|when to delegate|dispatch when|when to dispatch|"
    r"call when|when to call|use when|when to use this|"
    r"when you should (?:use|call|delegate)|"
    r"when this role (?:applies|is needed|is the right))\b",
    re.IGNORECASE,
)
# A table row, a code fence, a bracketed template, a shell variable, or a
# fill-in-the-blank angle placeholder is not a sentence. Every one of these
# turned up as extracted "prose" before the filter existed, and a leaked template
# is worse than a restatement because it looks decided.
NOT_PROSE = re.compile(
    r"^\s*[|`>]|```|\$\{?[A-Z_]{3,}\}?|\[[^\]]*\]|<[^>]+>|"
    r"[─-╿]{4,}|"          # box-drawing rules used as section separators
    r"\bTEMPLATE\b|\bFORMAT\b\s*[:—-]|\bEXAMPLE\b\s*[:—-]|"
    r"^\s*(?:target|path|precondition|mechanism|impact|fix|residual)\s{2,}"
)

HEADING_LEVEL = re.compile(r"^(#{2,6})\s")

# "What you must not do" is the heading 272 of the 286 roles actually use, and
# it is the strongest statement any of them makes about when NOT to reach for
# them. The earlier pattern was anchored to the start of the heading text, so it
# matched "## Prohibitions" and missed "## What you must not do" -- 191 of which
# open with a warning sign and so needed a glyph allowance before the keyword.
STOP_HEADING = re.compile(
    r"^#{2,3}\s*[^\w\n]{0,4}(?:\*\*)?(?:what you )?"
    r"(?:prohibitions?|do not|don't|never|must not|should not|when not to|"
    r"out of scope|not for|limits?|boundaries|scope discipline|when to avoid)\b",
    re.IGNORECASE,
)

# The situation half. 186 roles write "## Your Core Mission"; the rest use a
# neighbour, sometimes with an adjective in front ("## Review Scope") and often
# glyph-prefixed (191 of them open with a warning sign).
MISSION_HEADING = re.compile(
    r"^#{2,3}\s*[^\w\n]{0,4}(?:\*\*)?(?:your |the )?[a-z ]{0,18}?"
    r"(?:core mission|mission|scope|core responsibilities|what to look for|"
    r"domain expertise|core capabilities|responsibilities|what you do|"
    r"approach|operating modes?|capabilities)\b",
    re.IGNORECASE,
)
# What the role hands back. 192 roles write "## Your Output Contract".
OUTPUT_HEADING = re.compile(
    r"^#{2,3}\s*[^\w\n]{0,4}(?:\*\*)?(?:your |the )?[a-z ]{0,18}?"
    r"(?:output(?: contract| format)?|technical deliverables|deliverables?|"
    r"what a finding looks like|verdicts?|result format|response format|"
    r"deliverable template)\b",
    re.IGNORECASE,
)


def section_items(
    body: str,
    heading_rx: "re.Pattern[str]",
    limit: int,
    min_len: int = 30,
) -> list[str]:
    """List items under the first matching heading, descending into subsections.

    A `###` immediately after a `##` is the common shape -- "## Your Core
    Mission", then "### Land-and-Expand Execution" -- and an earlier version
    broke on any heading and so returned nothing, which is why a hundred-odd
    roles silently fell through to their description. This descends into
    subsections and stops at the same level or higher.
    """
    lines = body.split("\n")
    for i, line in enumerate(lines):
        if not heading_rx.match(line):
            continue
        depth = len(HEADING_LEVEL.match(line).group(1))
        out: list[str] = []
        for follow in lines[i + 1:]:
            h = HEADING_LEVEL.match(follow)
            if h and len(h.group(1)) <= depth:
                break
            if h:
                continue
            item = re.sub(r"^[-*]\s*", "", follow.strip())
            item = re.sub(r"^\d+\.\s*", "", item).strip()
            item = re.sub(r"\*\*(.+?)\*\*", r"\1", item).strip()
            if len(item) >= min_len and not NOT_PROSE.search(item):
                out.append(item)
            if len(out) >= limit:
                break
        if out:
            return out
    return []


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
        if NOT_A_CONDITION.search(text):
            return None
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


def mission_bullets(body: str, limit: int = 3) -> list[str]:
    """The role's own statements of the work it does, in its own words.

    This is the situation half of a dispatch condition. A `description:` says what
    a role IS; the mission bullets say what work arrives at its desk. Those are
    different sentences, which is why deriving from the description produced a
    table where every row was reachable and none was choosable.
    """
    return section_items(body, MISSION_HEADING, limit)


def output_contract(body: str) -> str | None:
    """The role's own statement of what it hands back.

    The previous derivation put the prohibition here and left the Produces cell
    as the literal string "Per its output contract" for all 267 rows -- a
    placeholder in the column whose whole job is to be specific.
    """
    items = section_items(body, OUTPUT_HEADING, 2, min_len=20)
    return "; ".join(items)[:180] if items else None


LEADING_VERB = re.compile(
    r"^(?:\w+\s+){0,3}?(?:design|build|create|write|develop|implement|manage|"
    r"monitor|track|analy[sz]e|review|ensure|provide|generate|produce|"
    r"conduct|perform|execute|support|maintain|help|offer|handle|"
    r"optimi[sz]e|improve|identify|assess|investigate|diagnose|debug|test|"
    r"verify|validate|deploy|configure|set up|define|deliver|lead|advise|"
    r"recommend|coordinate|facilitate|plan|report|act as|act as a|"
    r"specialize|focus on|own|drive|shape|map|translate|apply|"
    r"and|or|then|the|a|an)\b\s*",
    re.IGNORECASE,
)


def as_situation(bullet: str) -> str:
    """Turn an imperative mission bullet into the topic the request is about.

    "Design and execute expansion playbooks tailored to account maturity" is a
    task. "expansion playbooks tailored to account maturity" is the thing a
    caller would recognise the request as being about. The rewrite is mechanical
    and imperfect -- it keeps the role's own nouns and strips a leading verb
    phrase -- so the generated block is marked derived and is meant to be edited.
    """
    s = bullet.strip().rstrip(".")
    for _ in range(4):                      # "Design and execute X" -> "X"
        nxt = LEADING_VERB.sub("", s, count=1).strip()
        if nxt == s or not nxt:
            break
        s = nxt
    return s or bullet.rstrip(".")


def clean_cell(text: str) -> str:
    """Make a value safe to sit in one markdown table cell, and whole.

    A `|` inside a cell ends the column and the remainder of the row parses as a
    further column, which is how template text carrying a pipe leaked a cell
    into the table. Truncation lands on a word boundary for the same reason: an
    earlier version cut mid-phrase and shipped rows reading "a default, a
    guarantee, or a, or README".
    """
    s = re.sub(r"\s+", " ", (text or "")).replace("|", "/").strip()
    # A quoted fill-in-the-blank is still a placeholder. A role that shows a
    # mail template -- "I work at [company]" -- put one into its Produces cell
    # and it read as an unfinished row.
    s = re.sub(r"\s*\[[^\]]*\]\s*", " ", s)
    # The gate forbids emoji in the kernel specification documents, and a role
    # that uses them in its own prose will otherwise smuggle them into the
    # dispatch table. Strip rather than fail: the emoji carries no dispatch
    # information, and three rows failed the gate on it before this existed.
    s = "".join(ch for ch in s if ord(ch) <= 0x2100)
    s = re.sub(r"\s*[,;:]\s*(?:[.,;:]|$)", ".", s)
    s = re.sub(r"\s{2,}", " ", s).strip()
    if len(s) > 300:
        cut = s[:300]
        sp = cut.rfind(" ")
        s = (cut[:sp] if sp > 0 else cut).rstrip(" ,;:.") + " ..."
    return s or "The role file states nothing usable; read it before dispatching"


def condition_for(path: pathlib.Path) -> tuple[str, str]:
    """(condition, produces) derived from the role's own statements.

    Three sources, in descending order of authority:

      1. a trigger the role states for itself -- considered, used verbatim
      2. its mission bullets for the situation, plus its own prohibition for
         the boundary -- derived, and the only source for 273 of the 286 roles,
         because 0 of them state a trigger
      3. its `description:` -- a restatement, and it says so

    The prohibition belongs in the condition because it is the strongest thing a
    role says about when NOT to reach for it, and a boundary is a real decision
    criterion where a capability list is not.
    """
    text = path.read_text(encoding="utf-8", errors="replace")
    fm = frontmatter(text)
    body = re.sub(r"^---\n.*?\n---\n", "", text, flags=re.S)

    trigger = stated_trigger(body)
    purpose = fm.get("description") or first_sentence(body, 180)
    prohibition = stated_prohibition(body)
    mission = mission_bullets(body)

    if trigger:
        cond = trigger
    elif mission:
        cond = f"The request is about {as_situation(mission[0])}"
        if len(mission) > 1:
            cond += f", or {as_situation(mission[1])}"
        if prohibition:
            boundary = re.sub(r"^\**\s*(never|do not|don't|always)\b\s*", "",
                              prohibition, flags=re.IGNORECASE).strip()
            boundary = boundary.rstrip(".")
            if boundary:
                cond += f". Not when {boundary[0].lower() + boundary[1:]}"
        cond += "."
    elif purpose:
        cond = f"The request is about {first_sentence(purpose, 180)}"
        cond = cond[0].upper() + cond[1:]
    else:
        cond = "The role file states no trigger; read it before dispatching"

    produces = output_contract(body)
    if not produces:
        produces = f"Not: {prohibition}" if prohibition else "Per its output contract"

    return clean_cell(cond), clean_cell(produces)


def derived_header(count: int) -> list[str]:
    return [
        "",
        "## Every shipped role, and when to call it",
        "",
        "The rows above this heading were written by hand and are the ones this",
        "repository relies on. The rows below cover the remaining",
        f"{count} role file(s), so that no shipped role is unreachable: a role",
        "with no dispatch condition is not available, however good it is.",
        "",
        "**These conditions are derived, not considered.** Each is assembled from",
        "the role's own mission bullets -- the work that arrives at its desk --",
        "and the prohibition it states about itself, which is inverted into the",
        "boundary the role draws. No role in this corpus states a dispatch trigger",
        "for itself, so there was nothing to quote and everything to derive.",
        "",
        "That makes them better than the descriptions they replace, which decided",
        "nothing, and it does not make them good. They are uniform because they",
        "were built by one rule, and a uniform rule is a hint that the row has not",
        "been read by a person. Read a row and rewrite it if the role deserves",
        "better. The four rows for the email, Salesforce, Bilibili and workflow",
        "roles were hand-upgraded after an earlier generation and are the model",
        "for what the rest should become.",
        "",
        "| Role | Delegate when | Produces |",
        "|---|---|---|",
    ]


def refresh(text: str, routed: set[str]) -> tuple[str, int]:
    """Rebuild the rows that decide nothing, and leave the rest alone.

    The distinction is measured rather than guessed from a template string. A row
    a person wrote is one that says something the role's own description does
    not -- the same test `tools/index-tree.py` applies when it reports the band,
    so "hand-written" and "decides something" cannot drift apart. Rows that only
    restate the description are exactly the ones this rebuilds.

    The first attempt inferred hand-written rows from the generator's own frame
    and got it exactly backwards: every restatement looked hand-written, so the
    nineteen considered rows were overwritten and the 263 useless ones kept. A
    rule that preserves the wrong side is worse than no rule.
    """
    head, marker, tail = text.partition(DERIVED_HEADING)
    if not marker:
        return text, 0

    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "_index_tree", pathlib.Path(__file__).with_name("index-tree.py")
    )
    index_tree = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(index_tree)

    # Roles already routed in the hand-written block must never be rebuilt.
    # The first run of --refresh did rebuild them and the table ended up with
    # 23 rows naming the same role twice: once as considered, once as derived.
    above = set(re.findall(r"`agents/([a-z0-9_-]+)\.md`", head))

    kept: dict[str, str] = {}
    for line in tail.splitlines():
        m = re.match(r"^\|\s*`agents/([a-z0-9_-]+)\.md`\s*\|(.*)\|\s*$", line)
        if not m:
            continue
        role, rest = m.group(1), m.group(2)
        parts = rest.split("|")
        cell = parts[0].strip()
        made = parts[1].strip() if len(parts) > 1 else ""
        path = AGENTS / f"{role}.md"
        description = frontmatter(path.read_text(encoding="utf-8")).get("description", "")
        if index_tree.condition_is_real(cell, description):
            # Re-emit through clean_cell rather than storing the line verbatim.
            # A kept row can still carry a stale Produces cell with a pipe in
            # it -- a template that escaped the filter in an earlier run -- and
            # preserving that would keep corrupting the table.
            kept[role] = (
                f"| `agents/{role}.md` | {clean_cell(cell)} | "
                f"{clean_cell(made) if made else 'Per its output contract'} |"
            )

    below = sorted(r for r in routed if r not in above)
    lines = derived_header(len(below))
    for role in below:
        if role in kept:
            lines.append(kept[role])
            continue
        cond, produces = condition_for(AGENTS / f"{role}.md")
        lines.append(f"| `agents/{role}.md` | {cond} | {produces} |")
    lines.append("")

    return head.rstrip("\n") + "\n" + "\n".join(lines), len(kept) + len(above)


def index_tree():
    """The shared novelty test, loaded from the tool that publishes the number.

    A second implementation here would drift from it, and the drift would show
    up as this tool disagreeing with the published band.
    """
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "_index_tree", pathlib.Path(__file__).with_name("index-tree.py")
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main() -> int:
    text = DELEGATION.read_text(encoding="utf-8")
    routed = set(re.findall(r"`agents/([a-z0-9_-]+)\.md`", text))

    roles = sorted(
        p.stem for p in AGENTS.glob("*.md")
        if p.stem.islower() and p.stem != "README"
    )
    missing = [r for r in roles if r not in routed]

    if "--refresh" in sys.argv:
        new_text, preserved = refresh(text, routed)
        DELEGATION.write_text(new_text, encoding="utf-8")
        print(f"  derived rows rebuilt : {len(routed) - preserved}")
        print(f"  hand-edited kept     : {preserved}")
        print(f"  total routed         : {len(routed)} of {len(roles)}")
        return 0

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
        print(
            f"  every role already has a dispatch row: {len(routed)} of "
            f"{len(roles)}"
        )
        print("  nothing to add; references/delegation.md not modified")
        # Read the cells exactly as tools/index-tree.py reads them, so the two
        # numbers cannot disagree. An earlier version read only the condition
        # column and reported 257 where the published band said 273 -- two
        # correct answers to two different questions, printed side by side.
        idx = index_tree()
        cells = idx.dispatch_rows()
        deciding = sum(
            1 for role in routed
            if idx.condition_is_real(
                cells.get(role, ""),
                frontmatter((AGENTS / f"{role}.md").read_text(
                    encoding="utf-8")).get("description", ""),
            )
        )
        print(
            f"  {deciding} of {len(routed)} conditions decide something; "
            f"{len(routed) - deciding} still restate the role's description."
        )
        print("  run with --refresh to rebuild the restatements from the role's")
        print("  own mission bullets and prohibitions, keeping the ones that decide.")
        return 0

    lines = derived_header(len(missing))
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
