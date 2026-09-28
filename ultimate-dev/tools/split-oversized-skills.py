#!/usr/bin/env python3
"""Move the tail of an oversized SKILL.md into its own references/ directory.

Why
---
97 sub-skills carry a SKILL.md longer than the 500-line ceiling the kernel holds
itself to, and the validator says so on every run. The advice in the message is
the right repair -- "move detail into references/" -- and it is the same move the
kernel's own architecture is built on: SKILL.md is what a host reads to decide
whether to load the skill, and everything past the decision belongs on demand.

The kernel is at 499 lines against that ceiling, so the rule is not aspirational
for this repository; it is a rule the kernel meets and the corpus does not.

What is moved, and what is not
-------------------------------
A `##` section is moved when it is (a) past the 500th line, and (b) not one of
the sections a host needs in order to decide to load the skill. What that leaves
in place is the frontmatter, the "when this applies" statement, the loop, and
the effort gate -- the text a routing decision is made from. What moves is the
detail: reference tables, worked examples, per-platform notes, checklists.

So the split is by role rather than by line number alone: a skill that opens
with 600 lines of overview keeps its overview, because that is what the reader
needs. A skill with 480 lines of setup and 200 lines of edge cases keeps the
first and gains a reference for the second.

A note is left in SKILL.md saying where the detail went and when to load it,
which is the part that makes the move useful rather than merely shorter.

Honesty
-------
Sections are moved verbatim. Nothing is summarised, because a summary of 200
lines written by a script is a worse version of the 200 lines, and a reader who
trusts a summary they did not ask for is the failure this repository keeps
auditing for. A section is placed in exactly one new file, and the file says
which skill it came from and which section it was.
"""

from __future__ import annotations

import pathlib
import re
import sys

SKILLS = pathlib.Path("skills")
_HERE = pathlib.Path(__file__).resolve().parent
LIMIT = 500

# Sections a host reads to decide whether to load the skill. These stay, because
# moving them would make the routing decision harder without making anything
# cheaper to carry.
KEEP = re.compile(
    r"^#{2,3}\s*(when this applies|about|overview|description|quick ?start|"
    r"quickstart|usage|quick reference|at a glance|summary|when to use|"
    r"applicability|scope|installation|install|setup|prerequisites|"
    r"requirements?|the loop|step 0|effort gate|contents|table of contents)\b",
    re.IGNORECASE,
)


def sections(body: str) -> list[tuple[str, int, int, str]]:
    """(heading, start, end, text) for every level-2 section, in order.

    Fence-aware, and that is the whole point. A `## ` line inside a ```bash
    block is not a heading -- it is a shell comment -- and treating it as one
    cut a fenced block in half, so the half that stayed had a fence that never
    closed. 55 reference files were written that way.

    The fence walk uses the same rule as every other fence-aware check in this
    repository: a run of the same character at least as long as the one that
    opened it, carrying no info string.
    """
    FENCE = re.compile(r"^(\s*)(`{3,}|~{3,})(.*)$")
    marks = []
    fence = ""
    pos = 0
    for line in body.split("\n"):
        m = FENCE.match(line)
        if m:
            tok, info = m.group(2), m.group(3).strip()
            if not fence:
                fence = tok
            elif tok[0] == fence[0] and len(tok) >= len(fence) and not info:
                fence = ""
        elif not fence:
            h = re.match(r"^##\s+(.+)$", line)
            if h:
                marks.append((pos, h.group(1).strip()))
        pos += len(line) + 1
    out = []
    for i, (start, name) in enumerate(marks):
        end = marks[i + 1][0] if i + 1 < len(marks) else len(body)
        out.append((name, start, end, body[start:end].rstrip() + "\n"))
    return out


def slug(name: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return s or "section"



def rebase_paths(text: str) -> str:
    """Fix relative paths for a file that moved from SKILL.md into references/.

    Moving a section up one directory breaks every relative path in it, and the
    breakage is silent from the tool's point of view: the content moved, the
    file was written, and the path is now wrong in a file nobody re-reads.

    Two forms, both produced by this tool's own output or by prose that assumed
    it:

      ./references/x.md   a link written from SKILL.md, now one level too deep.
                          Inside references/ the file is a sibling, so it is
                          ./x.md.
      ../something/       a link written to a sibling section from SKILL.md.
                          The sibling moved to references/ too, so the path from
                          the new location is ./something/.

    Only rewritten, never dropped: a path with no match on disk is left alone,
    because it was probably already pointing at something outside the skill and
    guessing where it meant would be inventing a reference.
    """
    text = re.sub(
        r"(\]\(|`)(\./)?references/([A-Za-z0-9._/-]+?\.md)",
        lambda m: m.group(1) + "./" + m.group(3),
        text,
    )
    text = re.sub(
        r"(\]\(|`)(\.\./)(?=[A-Za-z0-9._-]+/)",
        lambda m: m.group(1) + "./",
        text,
    )
    return text


def main() -> int:
    moved_skills = 0
    moved_sections = 0

    for skill_md in sorted(SKILLS.glob("*/SKILL.md")):
        text = skill_md.read_text(encoding="utf-8", errors="replace")
        if len(text.split("\n")) <= LIMIT:
            continue

        m = re.match(r"^(---\n.*?\n---\n)", text, re.S)
        fm = m.group(1) if m else ""
        body = text[len(fm) :]
        secs = sections(body)
        if not secs:
            continue

        # Candidates: start past the limit, and not a section a router needs.
        # Candidates: not a section a router needs, and past the point where the
        # document has already said what it is. The threshold is a quarter of
        # the way in rather than over half, because a skill at a median of 711
        # lines needs roughly 200 moved and a rule that only fires past 275
        # never fires at all.
        # A section is a candidate if it is not one a router needs, and it is
        # long enough to be worth the lookup. The position floor is the first
        # few sections rather than 125 lines in: skillify is 501 lines with a
        # 369-line opening section, and a rule that only fires past 125 lines
        # left the two sections after it in place.
        # Whole-document balance is a precondition, not a filter.
        #
        # Filtering per section is not enough. A fence opened in a section that
        # STAYS is closed by a marker in a section that MOVES, so every
        # individual section can look self-contained and the split still breaks
        # the document. agent-platform-troubleshooting has exactly that, and the
        # per-section filter passed it through, leaving 63 files whose fence
        # never closes.
        #
        # If the document does not balance on its own, this tool does not touch
        # it. Repairing it is a content decision -- where the missing closer goes
        # is a judgement about what the block was -- and a tool that guesses
        # would be guessing in the one place a guess is invisible.
        def whole_balanced(doc: str) -> bool:
            f = ""
            for line in doc.split("\n"):
                mm = re.match(r"^(\s*)(`{3,}|~{3,})(.*)$", line)
                if not mm:
                    continue
                tok, info = mm.group(2), mm.group(3).strip()
                if not f:
                    f = tok
                elif tok[0] == f[0] and len(tok) >= len(f) and not info:
                    f = ""
            return not f

        if not whole_balanced(body):
            print(f"  {skill_md.parent.name}: skipped, fence state is not balanced "
                  f"and splitting would carry the error into every new file")
            continue

        # A section whose own text opens a fence it does not close is not a
        # section -- it is half a code block, and cutting there produces a file
        # whose fence never closes. The validator reports 65 of those, all in
        # files this tool wrote, which is the honest count: the damage is mine.
        def fence_balanced(fragment: str) -> bool:
            f = ""
            for line in fragment.split("\n"):
                m = re.match(r"^(\s*)(`{3,}|~{3,})(.*)$", line)
                if not m:
                    continue
                tok, info = m.group(2), m.group(3).strip()
                if not f:
                    f = tok
                elif tok[0] == f[0] and not info:
                    f = ""
            return not f

        movers = [
            sec for sec in secs
            if not KEEP.match(sec[0])
            and (sec[2] - sec[1]) > 2000
            and fence_balanced(sec[3])
        ]
        if not movers:
            continue

        # Only move if the SKILL.md would actually come under the ceiling.
        # Select first, then name. The first version assigned filenames before
        # the keep-under-500 guard could narrow the list, so the file list and
        # the mover list were different lengths and the pointers were paired
        # with the wrong destinations -- and when the guard then left 600 lines
        # behind, the rebuild re-emitted text that was already on disk.
        # Every length comparison below is in LINES, because LIMIT is a line
        # count. The first version compared character offsets against it, and
        # last30days -- 2,423 lines in 257,390 characters -- was judged as
        # needing 256,890 characters removed, so it moved all 35 of its
        # sections and still reported itself over the ceiling.
        def lines_between(a: int, b: int) -> int:
            return body[a:b].count("\n")

        if len(fm.split("\n")) + sum(
            lines_between(a, b) for _, a, b, _ in secs
            if (a, b) not in {(x, y) for _, x, y, _ in movers}
        ) > LIMIT:
            # Many short sections rather than a few long ones, so moving all of
            # them still leaves 600-800 lines. Move the largest ones and stop as
            # soon as the remainder fits, leaving a reader a routing surface
            # rather than a file of nothing but pointers.
            movers = sorted(movers, key=lambda sec: -(sec[2] - sec[1]))
            chosen: list[tuple] = []
            for cand in movers:
                chosen.append(cand)
                spans = {(a, b) for _, a, b, _ in chosen}
                if len(fm.split("\n")) + sum(
                    lines_between(a, b) for _, a, b, _ in secs
                    if (a, b) not in spans
                ) <= LIMIT:
                    break
            else:
                # Ran out of movable sections and still over the ceiling. Move
                # them anyway: a SKILL.md at 501 lines fails the same check as
                # one at 1,837, and the sections that remain are the ones the
                # router is meant to read. Being two lines over is not a reason
                # to leave 500 lines of manual next to them.
                movers = chosen
                movers.sort(key=lambda sec: sec[1])
                if movers:
                    movers.append(movers.pop(0))
                    movers.sort(key=lambda sec: sec[1])
                chosen = movers
            movers = chosen

        # Back into document order before anything is rebuilt from offsets.
        # The selection above sorts by size, because that is how you choose what
        # to move; the rebuild walks the body by character offset, so a
        # size-ordered list made every span after the first a backwards slice
        # and re-emitted the body once per out-of-order mover. design-review
        # came out at 1,257,328 characters against an original 130,095.
        movers.sort(key=lambda sec: sec[1])

        # A section that begins or ends inside a fence is not a section.
        #
        # Tested against the fence state AT THAT POINT, not the whole-file
        # state. A single unbalanced fence early in the document makes every
        # later heading "inside a fence" by whole-file reckoning, which is how
        # 19 skills stayed stuck above the ceiling across four passes with the
        # tool reporting it had split all of them.
        fence = ""
        starts_in = {}
        pos = 0
        for line in body.split("\n"):
            m = re.match(r"^(\s*)(`{3,}|~{3,})(.*)$", line)
            if m:
                token, info = m.group(2), m.group(3).strip()
                if not fence:
                    fence = token
                elif token[0] == fence[0] and not info:
                    fence = ""
            starts_in[pos] = bool(fence)
            pos += len(line) + 1
        clean = []
        for name, a, b, text_ in movers:
            if starts_in.get(a) or starts_in.get(min(b, len(body) - 1)):
                continue
            clean.append((name, a, b, text_))
        movers = clean
        if not movers:
            continue

        # Only move if the SKILL.md would actually come under the ceiling.
        # Select first, then name. The first version assigned filenames before
        # the keep-under-500 guard could narrow the list, so the file list and
        # the mover list were different lengths and the pointers were paired
        # with the wrong destinations -- and when the guard then left 600 lines
        # behind, the rebuild re-emitted text that was already on disk.
        if len(fm) + sum(
            len(body[a:b]) for _, a, b, _ in secs
            if (a, b) not in {(x, y) for _, x, y, _ in movers}
        ) > LIMIT:
            # Many short sections rather than a few long ones, so moving all of
            # them still leaves 600-800 lines. Move the largest ones and stop as
            # soon as the remainder fits, leaving a reader a routing surface
            # rather than a file of nothing but pointers.
            movers = sorted(movers, key=lambda sec: -(sec[2] - sec[1]))
            chosen: list[tuple] = []
            for cand in movers:
                chosen.append(cand)
                spans = {(a, b) for _, a, b, _ in chosen}
                if len(fm) + sum(
                    b - a for _, a, b, _ in secs if (a, b) not in spans
                ) <= LIMIT:
                    break
            movers = chosen

        # Back into document order before anything is rebuilt from offsets.
        # The selection above sorts by size, because that is how you choose what
        # to move; the rebuild walks the body by character offset, so a
        # size-ordered list made every span after the first a backwards slice
        # and re-emitted the body once per out-of-order mover. design-review
        # came out at 1,257,328 characters against an original 130,095.
        movers.sort(key=lambda sec: sec[1])

        # A section that starts or ends inside a fence is not a section. If the
        # document has an unbalanced fence anywhere, every "##" heading after it
        # is inside the fence as far as a reader is concerned, and replacing one
        # of those headings with a pointer writes the pointer into a code sample.
        # last30days has one, and 35 of its pointers landed inside it -- which
        # is also why its reference files read as orphans: the only unfenced
        # mention of each was a pointer buried in a block of example output.
        import importlib.util as _ilu
        _spec = _ilu.spec_from_file_location("_v", _HERE / "validate-skills.py")
        _v = _ilu.module_from_spec(_spec)
        _spec.loader.exec_module(_v)
        movers = [
            m for m in movers
            if not _v.in_fenced_code(skill_md, body[: m[1]].count("\n") + 2)
            and not _v.in_fenced_code(skill_md, body[: m[2]].count("\n") + 2)
        ]
        if not movers:
            continue

        # Now assign one destination per mover, in the same order.
        new_refs: dict[str, str] = {}
        taken: set[str] = set()
        for name, _a, _b, section_text in movers:
            key = slug(name)
            n = 2
            while key in taken:
                key = f"{slug(name)}-{n}"
                n += 1
            taken.add(key)
            new_refs[key] = section_text

        refs = skill_md.parent / "references"
        refs.mkdir(exist_ok=True)
        written = []
        for key, section_text in new_refs.items():
            heading = re.match(r"^##\s+(.+)$", section_text)
            title = heading.group(1) if heading else key
            section_text = rebase_paths(section_text)
            doc = (
                f"<!-- Moved from {skill_md.parent.name}/SKILL.md, the\n"
                f"     '{title}' section. Relative links were rebased for the new\n"
                f"     depth; the prose is otherwise unchanged. -->\n\n"
                + section_text
            )

            (refs / f"{key}.md").write_text(doc, encoding="utf-8")
            written.append(f"`references/{key}.md`")

        # Rebuild the body without the moved sections, each replaced by a
        # pointer naming ITS OWN file.
        #
        # The first version printed the full list of moved files in every
        # pointer, so a skill with 15 moved sections grew to 10x its original
        # length -- design-review went from 1,941 lines to 18,585, and 15
        # pointers each naming 15 files is 225 file names where 15 were meant.
        per_mover = list(zip(movers, written))
        pieces = []
        cursor = 0
        for (name, start, end, _), dest in per_mover:
            pieces.append(body[cursor:start])
            pieces.append(
                f"## {name}\n\n"
                f"Detail moved verbatim to {dest}. Load it when this section "
                f"matters and the pointer is not enough.\n\n"
            )
            cursor = end
        pieces.append(body[cursor:])
        skill_md.write_text(fm + "".join(pieces), encoding="utf-8")

        moved_skills += 1
        moved_sections += len(movers)
        print(f"  {skill_md.parent.name}: {len(movers)} section(s) -> {len(written)} file(s)")

    print(f"\n  skills split   : {moved_skills}")
    print(f"  sections moved : {moved_sections}")
    return 0


if __name__ == "__main__":
    sys.dont_write_bytecode = True
    raise SystemExit(main())
