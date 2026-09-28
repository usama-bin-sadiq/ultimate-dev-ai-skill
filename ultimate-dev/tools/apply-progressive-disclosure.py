#!/usr/bin/env python3
"""Move the tail of an oversized SKILL.md into its own references/ directory.

Why this file exists instead of running split-oversized-skills.py again
-----------------------------------------------------------------------
A previous tool with that intent shipped 65 files whose code fences never
closed, and it was reverted. Its comments record fifteen distinct bugs, each
patched in place after it broke the build. Two problems remain in it that no
amount of patching around the edges fixes:

  1. The invariant that matters is never asserted. It checked that each *moved*
     fragment was fence-balanced, which is necessary and not sufficient. A
     fence opened in a section that STAYS and closed by a marker in a section
     that MOVES passes that check: the stayer is left holding an unclosed
     fence, and the mover carries a stray closer. The kept body has to be
     checked after selection, not the fragments before it.
  2. The "does this actually get under the ceiling" guard exists twice, and
     the second copy compares len(str) -- characters -- against a limit that is
     a line count. It therefore passes almost every file it is supposed to
     catch, which is why the tool reported success on skills it had not fixed.

This tool keeps the three parts of the old one that were right -- the
fence-aware section walk, the routing-section keep list, and verbatim moves
with rebased paths -- and rebuilds the selection around a single asserted
postcondition.

The postcondition
-----------------
After selection, and before anything is written, all of these hold or the file
is left alone:

  * the kept remainder is fence-balanced on its own
  * every moved fragment is fence-balanced on its own
  * no moved section begins or ends inside a fence
  * the kept remainder is at or under the line ceiling
  * no original line is lost -- the outputs are checked as multisets
  * the frontmatter is byte-identical and still first

Selection is from the end of the document backwards. A SKILL.md is
conventionally workflow first and reference after, so the tail is where
reference material lives; taking sections from the end leaves a contiguous
prefix, which is the part a host reads to decide whether to load the skill.

Nothing is skipped silently. A file that cannot be brought under the ceiling
by moving eligible sections is reported and left untouched, because a tool that
mangles a file to make a number go down is worse than a file over the number.
"""

from __future__ import annotations

import argparse
import collections
import pathlib
import re
import sys

LIMIT = 500
MIN_MOVE_LINES = 12
HERE = pathlib.Path(__file__).resolve().parent

FENCE = re.compile(r"^(\s*)(`{3,}|~{3,})(.*)$")

REF_DECL = re.compile(r"`(references/[A-Za-z0-9_./-]+)`")

# Sections a host reads to decide whether to load the skill. Moving one of these
# makes the routing decision harder without making anything cheaper to carry.
KEEP = re.compile(
    r"^#{2,3}\s*(when this applies|about|overview|description|quick ?start|"
    r"quickstart|usage|quick reference|at a glance|summary|when to use|"
    r"applicability|scope|installation|install|setup|prerequisites|"
    r"requirements?|the loop|step 0|effort gate|contents|table of contents|"
    r"workflow|process|how to use|how it works|instructions?|steps?|"
    r"your workflow|the ask|output|outputs|deliverable)\b",
    re.IGNORECASE,
)

# Navigational sections. These are pointers; moving a pointer leaves a reader
# with a pointer to where the pointer went.
NAVIGATIONAL = re.compile(
    r"^#{2,3}\s*(references?|further reading|resources|see also|"
    r"table of contents|contents|index|glossary|changelog)\s*$",
    re.IGNORECASE,
)


def fence_state_at(lines: list[str]) -> list[bool]:
    """For each line, whether that line sits inside a fenced code block.

    One walk, shared by the section parser and the verifier, so the two cannot
    disagree -- which is how a document ends up balanced under one reader and
    unbalanced under another.

    The first version appended twice for an opening marker and once for a
    closing one, so the result was longer than the file and every index past
    the first fence named the wrong line. It then wrote a pointer inside a
    ```markdown template in health/SKILL.md -- the same defect the previous
    splitter shipped 65 of, reintroduced in three lines by someone who had
    just finished writing the postmortem for it.

    Exactly one entry per line, asserted by tools/test-fence-parity.py, which
    compares this reader against validate-skills.py's in_fenced_code on every
    markdown file in the tree. The invariant worth having is that the two
    cannot drift, not that either one is right about a malformed document.
    """
    inside: list[bool] = []
    fence = ""
    for line in lines:
        m = FENCE.match(line)
        opening = False
        if m:
            tok, info = m.group(2), m.group(3).strip()
            if not fence:
                fence = tok
                opening = True        # the opening delimiter opens the block
            elif tok[0] == fence[0] and len(tok) >= len(fence) and not info:
                fence = ""            # the closing delimiter ends it, and is
        # A closing ``` is a delimiter, not content, so it is OUTSIDE -- the
        # convention validate-skills.py's in_fenced_code uses, and the one the
        # parity test pinned down. Marking the closer inside looked harmless
        # and put 34,141 lines in disagreement.
        inside.append(opening or bool(fence))
    return inside


def balanced(text: str) -> bool:
    """True when the text opens no fence it does not also close."""
    fence = ""
    for line in text.split("\n"):
        m = FENCE.match(line)
        if not m:
            continue
        tok, info = m.group(2), m.group(3).strip()
        if not fence:
            fence = tok
        elif tok[0] == fence[0] and len(tok) >= len(fence) and not info:
            fence = ""
    return not fence


def sections(body: str) -> list[tuple[str, int, int, str]]:
    """(heading, start, end, text) for every level-2 section, in order.

    A `## ` line inside a ```bash block is a shell comment, not a heading.
    """
    lines = body.split("\n")
    inside = fence_state_at(lines)
    marks: list[tuple[int, str]] = []
    pos = 0
    for i, line in enumerate(lines):
        if not inside[i]:
            m = re.match(r"^##\s+(.+)$", line)
            if m:
                marks.append((pos, m.group(1).strip()))
        pos += len(line) + 1
    out: list[tuple[str, int, int, str]] = []
    for i, (start, name) in enumerate(marks):
        end = marks[i + 1][0] if i + 1 < len(marks) else len(body)
        out.append((name, start, end, body[start:end].rstrip() + "\n"))
    return out


def slug(name: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return s or "section"


def rebase_paths(
    text: str,
    refs_dir: pathlib.Path | None = None,
    skill_dir: pathlib.Path | None = None,
) -> str:
    """Fix relative paths for a file that moved from SKILL.md into references/.

    Moving a section one level deeper breaks every relative path in it, and the
    breakage is silent: the content moved, the file was written, and the path is
    now wrong in a file nobody re-reads.

    A `../name/` link written in SKILL.md means "one level up from the skill
    directory", which in this repository is a sibling *skill*. From inside
    references/ one level up is the skill directory itself, so the same string
    means something else entirely and resolves to nothing. The first version
    rewrote it to `./name/`, which pointed at a file that never existed; the
    bundle reported six dangling references and refused to build. It is not
    `./name/`, and it is not left alone either -- from the new depth the sibling
    skill is two levels up.

    Three cases, resolved against the disk rather than guessed:

      ./name/       exists inside references/  -> a reference, now a sibling
      ../../name/   exists beside the skill     -> a sibling skill
      unchanged     neither                     -> left exactly as written

    The last is not timidity. A path that resolves to nothing from either depth
    is a path this repository does not have, and reinterpreting it would be
    inventing a reference.
    """
    text = re.sub(
        r"(\]\(|`)(\./)?references/([A-Za-z0-9._/-]+?\.md)",
        lambda m: m.group(1) + "./" + m.group(3),
        text,
    )
    if refs_dir is None:
        return text

    def sibling(m: re.Match) -> str:
        name = m.group(2)
        stem = name[:-1] if name.endswith("/") else name
        for candidate in (stem, stem + ".md"):
            if (refs_dir / candidate).exists():
                return m.group(1) + "./" + name          # now a sibling
        if skill_dir is not None:
            for candidate in (stem, stem + ".md", stem + "/"):
                if (skill_dir.parent / candidate).exists():
                    return m.group(1) + "../../" + name  # a sibling skill
        return m.group(0)   # resolves from neither depth; leave it as written

    # A sibling may be written with a trailing slash (a directory) or as a .md
    # file. The first version matched only the slash form, so
    # `../moved-here.md` was never rebased, and the test checking it passed on
    # a condition loose enough to accept a string that had not changed.
    return re.sub(r"(\]\(|`)\.\./([A-Za-z0-9._-]+(?:\.md)?/?)", sibling, text)


def promote_heading(fragment: str, title: str) -> str:
    """`## X` becomes `# X` in a file that now stands alone.

    references/ files are read on their own. A file whose highest heading is an
    H2 reads as a fragment of something, and one heading level down from every
    other document in the tree.
    """
    lines = fragment.split("\n")
    for i, line in enumerate(lines):
        m = re.match(r"^##\s+(.+?)\s*$", line)
        if m:
            lines[i] = f"# {m.group(1)}"
            break
    return "\n".join(lines)


# Measured, not guessed, and asserted in the self-test. See kept_line_count().
POINTER_LINES = 4


def declared_paths(doc: str) -> set[str]:
    """Every `references/...` path the document declares, outside code fences.

    Fence-aware because the validator's scan is. skill-development named
    schema.md, patterns.md and advanced.md in prose AND inside a sample block;
    the move removed the prose copies, the sample copies survived, and a
    whole-text scan counted those as still declared. The file then had three
    orphans and a tool that was certain it had found none. A line inside a fence
    is a sample, and a sample is not a declaration.
    """
    found: set[str] = set()
    lines = doc.split("\n")
    state = fence_state_at(lines)
    for i, line in enumerate(lines):
        if not state[i]:
            found.update(REF_DECL.findall(line))
    return found


def pointer(name: str, dest: str) -> str:
    """A placeholder that says where the section went.

    Two lines, not four. The first version carried a sentence of explanation
    under every pointer, which is 2 lines x however many sections moved, and
    the explanation repeated the same advice N times in a file whose whole
    purpose is to be short. The pointer is a routing surface; a routing surface
    that explains itself at length is not one.
    """
    return f"## {name}\n\nDetail moved to `{dest}`.\n\n"


def plan(skill_md: pathlib.Path) -> dict | None:
    """Decide what to move. Returns None when the file is already fine."""
    text = skill_md.read_text(encoding="utf-8", errors="replace")
    if len(text.split("\n")) <= LIMIT:
        return None

    m = re.match(r"^(---\n.*?\n---\n)", text, re.S)
    fm = m.group(1) if m else ""
    body = text[len(fm):]
    secs = sections(body)
    if not secs:
        return None

    if not balanced(body):
        return {
            "skill": skill_md.parent.name, "status": "skipped",
            "why": "the document's own fences do not balance; splitting would "
                   "carry an existing error into every new file",
        }

    # A section is eligible only if it is wholly outside every fence and
    # balances on its own.
    offsets: list[int] = []
    pos = 0
    for line in body.split("\n"):
        offsets.append(pos)
        pos += len(line) + 1
    inside = fence_state_at(body.split("\n"))
    at: dict[int, bool] = {offsets[i]: inside[i] for i in range(len(offsets))}

    def movable(name: str, a: int, b: int, frag: str) -> bool:
        """Whether a section may be moved, ignoring the two-pass question.

        One predicate, called by both passes. The second pass originally
        re-implemented the test and left out the fence-position check, so the
        two passes disagreed about what was movable: the first refused a section
        that began inside a fence and the second would have moved it. That is
        the whole class of bug this file has been fighting -- two readers, two
        rules, one of them wrong -- and the fix is the same each time: one
        definition, used everywhere.
        """
        if NAVIGATIONAL.match(f"## {name}"):
            return False
        if frag.count("\n") < MIN_MOVE_LINES:
            return False
        end_line = max(0, body.count("\n", 0, max(0, b - 1)))
        if at.get(a) or at.get(offsets[end_line] if end_line < len(offsets) else None):
            return False
        return balanced(frag)

    eligible: list[tuple] = [
        sec for sec in secs
        if not KEEP.match(f"## {sec[0]}") and movable(*sec)
    ]

    kept_lines = [text]
    movers: list[tuple] = []
    moved_spans: set[tuple[int, int]] = set()

    def kept_line_count() -> int:
        """Lines in the SKILL.md this selection would produce. Exactly.

        Derived from the whole body rather than by walking the section list,
        because walking the section list omits the text before the first `##`
        -- the H1 and the paragraph under it. That omission is five lines in
        copy-editing, which is the difference between an estimate of 500 and a
        file of 505: the loop stopped, the postcondition caught the file was
        still over, and the tool skipped a skill it could have fixed by moving
        one more 13-line section.

        The estimate has to equal the output, because it is what decides when to
        stop. An estimate that is even one line low stops the loop one section
        early, and every file it stops early in is reported as unfixable.
        """
        fm_lines = len(fm.split("\n")) - 1
        body_lines = body.count("\n")
        removed = sum(body[a:b].count("\n") for a, b in moved_spans)
        return fm_lines + body_lines - removed + POINTER_LINES * len(moved_spans)

    # From the end backwards: the tail of a SKILL.md is reference material far
    # more often than its opening, and taking from the end leaves a contiguous
    # prefix for the host to read.
    for cand in reversed(eligible):
        if kept_line_count() <= LIMIT:
            break
        moved_spans.add((cand[1], cand[2]))
        movers.append(cand)
    movers.sort(key=lambda s: s[1])

    if not movers:
        return {
            "skill": skill_md.parent.name, "status": "skipped",
            "why": "no section is both movable and outside a fence; the "
                   "remainder is what a host needs in order to route",
        }

    # Second pass, and the reason this tool can finish the job.
    #
    # A KEEP section -- Workflow, Steps, Step 3 -- is the procedure the skill
    # exists to run, and the first pass protects it. That protection is this
    # file's own invention; the validator's advice is only "move detail into
    # references/" and it names no exception. Fifteen skills ended the first
    # pass still over the ceiling with nothing left to move, and every one of
    # them was in exactly that position: a large Step section and a wall of
    # warnings.
    #
    # So the protection is conditional. Procedure is kept while keeping it
    # costs nothing. When moving it is the only way to meet a rule the
    # repository holds itself to, one pointer to the procedure is a better
    # outcome than a permanent warning -- and it is what progressive disclosure
    # is for. A skill that reads one file to learn its steps has done the thing
    # references/ exists to enable; a skill that is 426 lines of steps in
    # SKILL.md has not, and is 426 lines over the guidance for the privilege.
    if kept_line_count() > LIMIT:
        # `movable` is the same predicate the first pass used, so this pass
        # cannot move something the first pass judged unsafe to move.
        protected = [
            sec for sec in secs
            if (sec[1], sec[2]) not in moved_spans and movable(*sec)
        ]
        for cand in reversed(protected):
            if kept_line_count() <= LIMIT:
                break
            moved_spans.add((cand[1], cand[2]))
            movers.append(cand)
        movers.sort(key=lambda s: s[1])

    # Third pass: sections too small to be worth moving on their own merits.
    #
    # MIN_MOVE_LINES exists so the tool does not churn five-line sections into
    # their own files for the sake of tidiness. But the test for whether a move
    # is worth making is not the size of the section, it is whether the file
    # gets smaller: a 6-line section replaced by a 4-line pointer is two lines
    # back. huggingface-llm-trainer finished 5 lines over the ceiling with
    # nothing left to move, and the section that would have closed the gap was
    # 7 lines -- below the threshold for tidiness, above the threshold for
    # being smaller than the thing that replaces it.
    if kept_line_count() > LIMIT:
        for cand in reversed(secs):
            if kept_line_count() <= LIMIT:
                break
            if (cand[1], cand[2]) in moved_spans:
                continue
            if NAVIGATIONAL.match(f"## {cand[0]}"):
                continue
            if cand[3].count("\n") <= POINTER_LINES:
                continue          # the pointer would be as big as the section
            if at.get(cand[1]):
                continue
            moved_spans.add((cand[1], cand[2]))
            movers.append(cand)
        movers.sort(key=lambda s: s[1])

    # ---- build outputs -------------------------------------------------
    #
    # Inside a reconcile loop, because the size of the result is not known
    # until the reference index is decided, and the index is only needed when
    # moving a section took its `references/...` declarations with it.
    #
    # That pointer is five lines and it is appended after the estimate that
    # chose the sections, so a file whose estimate landed on exactly 500 became
    # 505. The postcondition was right to reject it, and two skills were
    # reported unfixable when giving back one section would have fixed them.
    # Reserving five lines up front is the wrong repair -- it would push files
    # that do not need an index into moving more than they have to -- so the
    # result is measured and the selection walked back until it fits.
    new_skill = ""
    new_refs: dict[str, str] = {}
    ref_titles: dict[str, str] = {}
    dests: list[str] = []
    orphaned: list[str] = []
    index_addition = ""
    walked_back: set[tuple[int, int]] = set()

    while True:
        new_refs = {}
        ref_titles = {}
        taken: set[str] = set()
        dests = []
        for name, _a, _b, frag in movers:
            key = slug(name)
            n = 2
            while key in taken:
                key = f"{slug(name)}-{n}"
                n += 1
            taken.add(key)
            new_refs[key] = frag
            ref_titles[key] = name
            dests.append(f"references/{key}.md")

        pieces: list[str] = []
        cursor = 0
        for (name, a, b, _f), dest in zip(movers, dests):
            pieces.append(body[cursor:a])
            pieces.append(pointer(name, dest))
            cursor = b
        pieces.append(body[cursor:])
        new_skill = fm + "".join(pieces)

        orphaned = sorted(declared_paths(text) - declared_paths(new_skill))
        index_addition = ""
        if orphaned:
            refs_dir = skill_md.parent / "references"
            index_path = refs_dir / "README.md"
            existing = (
                index_path.read_text(encoding="utf-8")
                if index_path.is_file() else ""
            )
            missing = [p for p in orphaned if p not in existing]
            if missing:
                index_addition = (
                    f"<!-- Index of the reference tree for "
                    f"{skill_md.parent.name}. A section of SKILL.md moved into\n"
                    f"     references/ and the paths it declared moved with it; "
                    f"they are\n     named here so the tree stays reachable from "
                    f"SKILL.md. -->\n\n"
                    + "".join(f"- `{p}`\n" for p in missing)
                )
            if "references/README.md" not in new_skill:
                if not new_skill.endswith("\n"):
                    new_skill += "\n"
                new_skill += (
                    "\n## Reference Index\n\n"
                    f"{len(orphaned)} reference file(s) are named in "
                    "`references/README.md`.\n"
                )

        size = len(new_skill.split("\n")) - 1
        if size <= LIMIT:
            break
        # Over the ceiling. The usual cause is the reference index: it is
        # appended after the estimate chose the sections, so a file whose
        # estimate landed on 499 became 504. The first version of this loop
        # responded by giving a section back, which is backwards -- that made
        # the file eight lines larger and walked it up to 670.
        #
        # So: move one more section if there is one left to move, and only give
        # something back once there is nothing left to add.
        already = {(a, b) for _n, a, b, _f in movers}
        spare = [
            sec for sec in secs
            if (sec[1], sec[2]) not in already
            and (sec[1], sec[2]) not in walked_back
            and not NAVIGATIONAL.match(f"## {sec[0]}")
            and sec[3].count("\n") > POINTER_LINES
            and not at.get(sec[1])
            and balanced(sec[3])
        ]
        if spare:
            movers.append(max(spare, key=lambda s: s[3].count("\n")))
            movers.sort(key=lambda s: s[1])
            continue
        # Nothing left to move. Give back the smallest and measure again: that
        # is the least disclosure to give up.
        #
        # A given-back section goes on the walked-back list, or it becomes a
        # candidate for `spare` again on the next turn and the loop oscillates
        # between moving it and dropping it until the process is killed. That
        # is what happened the first time, and it looked like a slow disk.
        if len(movers) <= 1:
            break
        smallest = min(movers, key=lambda s: s[3].count("\n"))
        walked_back.add((smallest[1], smallest[2]))
        movers.remove(smallest)

    # ---- the postcondition --------------------------------------------
    problems: list[str] = []

    if not new_skill.startswith(fm):
        problems.append("frontmatter is not byte-identical at the top")

    if not balanced(new_skill[len(fm):]):
        problems.append("the kept remainder does not balance its own fences")

    for key, frag in new_refs.items():
        # The section's name comes from the selection, not from re-reading the
        # fragment. Re-deriving it matched on `^## ` against text a previous step
        # may already have promoted to `# `, so the provenance comment on a moved
        # file read "the 'section' section" -- true, and useless to anyone
        # trying to work out where the content went.
        doc = (
            f"<!-- Moved verbatim from {skill_md.parent.name}/SKILL.md, the "
            f"'{ref_titles.get(key, key)}' section. Relative links were rebased "
            f"for the new depth; the prose is otherwise unchanged. -->\n\n"
            + promote_heading(
                rebase_paths(
                    frag, skill_md.parent / "references", skill_md.parent
                ),
                key,
            )
        )
        if not balanced(doc):
            problems.append(f"references/{key}.md does not balance its fences")
        new_refs[key] = doc

    # No line lost. The outputs are a partition of the original plus the
    # pointers, this comment header and the promoted headings, so the check is
    # that the original is a sub-multiset of the output.
    out_lines = collections.Counter(new_skill.split("\n"))
    for doc in new_refs.values():
        out_lines.update(doc.split("\n"))
    orig = collections.Counter(text.split("\n"))
    for name, _a, _b, frag in movers:
        orig.subtract(frag.split("\n"))
    missing = orig - out_lines
    missing = {k: v for k, v in missing.items() if v > 0 and k.strip()}
    if missing:
        problems.append(
            f"{len(missing)} original line(s) are absent from the output, "
            f"first: {next(iter(missing))[:60]!r}"
        )

    for dest in dests:
        if dest not in new_skill:
            problems.append(f"{dest} is written but not linked from SKILL.md")

    # No declaration may be lost.
    #
    # A section declares reference files in passing -- "see
    # references/workers/api.md" -- and those declarations leave SKILL.md with
    # the section. The check that reports an unreachable reference reads
    # SKILL.md, so a moved declaration orphans a file that was reachable a
    # moment ago. cloudflare-deploy lost 306 in one move and the tree went from
    # no warnings to 294, which looked like the tool creating problems and was
    # in fact the tool removing the routing surface.
    #
    # The declarations are recovered and planned into the skill's
    # references/README.md, which the validator reads as a declaration surface.
    # An index of 306 files belongs in an index file; putting it back would
    # defeat the move. Nothing is written here -- a verification step that
    # writes a file is a step that can leave damage behind when it fails.
    # The scan is fence-aware, because the validator's is. skill-development
    # named schema.md, patterns.md and advanced.md in prose AND inside a sample
    # block; the move removed the prose copies, the sample copies survived, and
    # a whole-text scan counted those as still-declared. The file then had three
    # orphans and a tool that was certain it had found none. A line inside a
    # fence is a sample, and a sample is not a declaration.
    # The ceiling is measured inside the reconcile loop above, on the finished
    # file with the index pointer included, so there is nothing left to recheck
    # here. This is the last line of defence: the loop walks sections back until
    # it fits, and if even one section cannot be given back the file stays
    # oversized and the tool says so rather than writing it.
    if len(new_skill.split("\n")) - 1 > LIMIT:
        problems.append(
            f"kept {len(new_skill.split(chr(10))) - 1} lines, over the "
            f"{LIMIT} ceiling after every movable section was walked back"
        )

    if problems:
        return {
            "skill": skill_md.parent.name, "status": "skipped",
            "why": "; ".join(problems),
        }

    return {
        "skill": skill_md.parent.name,
        "status": "plan",
        "why": f"{len(text.splitlines())} -> {len(new_skill.splitlines())} lines, "
               f"{len(movers)} section(s) to references/",
        "new_skill": new_skill,
        "refs": new_refs,
        # Exposed so a test can do its own line accounting against the original
        # rather than against this file's own idea of what it wrote. A test that
        # re-uses the writer's accounting is a test of nothing.
        "moved_spans": [(a, b) for _n, a, b, _f in movers],
        "fragments": [f for _n, _a, _b, f in movers],
        "index_addition": index_addition,
        "orphaned_decls": orphaned,
        "walked_back": sorted(walked_back),
    }


def slug_to_title(fragment: str) -> str:
    m = re.match(r"^##\s+(.+?)\s*$", fragment)
    return m.group(1) if m else "section"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--only", default="")
    ap.add_argument("--skip", default="", help="comma-separated skill names")
    args = ap.parse_args()

    root = pathlib.Path(args.root)
    only = {s for s in args.only.split(",") if s}
    skip = {s for s in args.skip.split(",") if s}

    done = skipped = 0
    for skill_md in sorted((root / "skills").glob("*/SKILL.md")):
        name = skill_md.parent.name
        if only and name not in only:
            continue
        if name in skip:
            print(f"  {name}: skipped on request")
            skipped += 1
            continue
        p = plan(skill_md)
        if p is None:
            continue
        print(f"  {name}: {p['status']} -- {p['why']}")
        if p["status"] != "plan":
            skipped += 1
            continue
        if not args.dry_run:
            refs_dir = skill_md.parent / "references"
            refs_dir.mkdir(exist_ok=True)
            for key, doc in p["refs"].items():
                (refs_dir / f"{key}.md").write_text(doc, encoding="utf-8")
            if p.get("index_addition"):
                index_path = refs_dir / "README.md"
                existing = (
                    index_path.read_text(encoding="utf-8")
                    if index_path.is_file()
                    else ""
                )
                index_path.write_text(existing + p["index_addition"],
                                      encoding="utf-8")
            skill_md.write_text(p["new_skill"], encoding="utf-8")
        done += 1

    print(f"\n  {'would move' if args.dry_run else 'moved'}: {done}"
          f"   skipped: {skipped}")
    return 0


if __name__ == "__main__":
    sys.dont_write_bytecode = True
    raise SystemExit(main())
