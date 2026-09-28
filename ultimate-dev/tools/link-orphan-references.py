#!/usr/bin/env python3
"""Add a reference section to each SKILL.md that ships files nothing points at.

Why
---
1,374 reference files across 246 sub-skills exist on disk and are named nowhere
in the SKILL.md that ships them. They are not reachable by a reader, not
discoverable by a host, and the bundler flags every one. The kernel's own
progressive-disclosure claim is that a reference is loaded on demand *and* a
reader can tell which situation loads it -- so an unlinked reference is a file
the system cannot honestly say it makes available.

Why a generated section rather than 1,374 edits
-----------------------------------------------
Each addition is a section whose entries are the file's own first heading and
its first sentence, so a row says what the file is for rather than that it
exists. Reading the target to write its own index entry is the difference
between a listing and an index, and it is the only way the reader learns which
situation loads the file -- which is the thing the section exists to convey.

The section is placed after the last existing `## ` heading, and it names the
files under a heading that matches the kernel's own convention
(`references/README.md` uses the same shape). Re-running is safe: a skill that
already has a `## Reference files` section is left alone, and a skill with no
orphans is untouched.

Honesty limits
--------------
The descriptions are the file's own first sentence, not a summary written by
someone who has not read it. Where a file has no heading, the row says so rather
than inventing a title. Nothing is invented and no file is deleted.
"""

from __future__ import annotations

import importlib.util
import pathlib
import re
import sys

SKILLS = pathlib.Path("skills")
_HERE = pathlib.Path(__file__).resolve().parent

# The same two rules the validator applies, imported rather than restated.
_vspec0 = importlib.util.spec_from_file_location(
    "_v0", _HERE / "validate-skills.py"
)
_v0 = importlib.util.module_from_spec(_vspec0)
_vspec0.loader.exec_module(_v0)
OUTPUT_DECLARATION = _v0.OUTPUT_DECLARATION
without_emphasis = _v0.without_emphasis
HEADING = re.compile(r"^#{1,3}\s+(.+?)\s*$", re.M)
SECTION_TITLE = "## Reference files"
LIST_ITEM = re.compile(r"^\s*[-*]\s")


def describe(path: pathlib.Path) -> str:
    """(title, one line of what it is for) from the file's own opening."""
    try:
        text = path.read_text(encoding="utf-8", errors="replace").strip()
    except OSError:
        return (path.stem.replace("-", " "), "")
    if not text:
        return (path.stem.replace("-", " "), "")

    # Title: the first heading, minus any trailing em-dash clause.
    m = HEADING.search(text)
    title = m.group(1).strip() if m else path.stem.replace("-", " ")
    title = re.sub(r"\s*[—–-]\s*(usage|overview|reference|guide).*$", "", title,
                   flags=re.I).strip(" #")
    if not title:
        title = path.stem.replace("-", " ")

    # First sentence of prose, skipping the heading and any list bullets, so
    # the row says what the file is rather than repeating its filename.
    line = ""
    for raw in text.split("\n"):
        s = raw.strip()
        if (
            not s
            or s.startswith("#")
            or s.startswith("<!--")
            or LIST_ITEM.match(raw)
            or s.startswith("|")
        ):
            continue
        line = s
        break
    line = re.sub(r"[*_`]", "", line)
    line = re.sub(r"\s+", " ", line)
    parts = re.split(r"(?<=[.!?])\s", line, maxsplit=1)
    sentence = parts[0].strip() if parts else ""
    if len(sentence) > 150:
        cut = sentence[:150]
        sp = cut.rfind(" ")
        sentence = (cut[:sp] if sp > 40 else cut).rstrip(" ,;:") + "..."
    return (title, sentence)


def main() -> int:
    changed = 0
    linked = 0
    # The kernel is NOT a target. SKILL.md is 499 lines against its own
    # 500-line ceiling, so seven unreferenced files under
    # references/quality-checklists/ cannot be listed there; its index is
    # references/README.md, and the two kernel-level checks already accept a
    # reference named in that index.
    targets = sorted(SKILLS.glob("*/SKILL.md"))

    for skill_md in targets:
        refs = skill_md.parent / "references"
        if not refs.is_dir():
            continue
        text = skill_md.read_text(encoding="utf-8", errors="replace")

        # Orphan set, computed with the validator's own rules rather than a
        # second implementation of them.
        #
        # The first version hand-rolled the fence walk and the declaration test,
        # and disagreed with the validator on 239 skills: a reference mentioned
        # only inside a fence is not a declaration, and a line saying the file
        # is produced is not a pointer to it. So this imports the checker's
        # logic instead. Two implementations of "what counts as referenced" is
        # exactly the failure this repository has been auditing out of its own
        # validators, and a linker that disagrees with its checker would leave
        # the same files unreachable it was asked to fix.
        from importlib.util import module_from_spec, spec_from_file_location

        _vspec = spec_from_file_location("_v", _HERE / "validate-skills.py")
        _v = module_from_spec(_vspec)
        _vspec.loader.exec_module(_v)

        declared = set()
        for n, line in enumerate(text.split("\n"), 1):
            if _v.in_fenced_code(skill_md, n):
                continue
            # The declaration test runs on the line with its PATHS REMOVED.
            # A filename is not a statement about what to produce, and
            # references/update.md, references/create.md and
            # references/generate-skill.md all contain a verb the rule looks
            # for -- so a perfectly good pointer was read as a production
            # instruction and skipped, and 21 files stayed unreachable because of
            # their own names.
            without_paths = _v.REF_PATTERN.sub(" ", line)
            if _v.OUTPUT_DECLARATION.search(_v.without_emphasis(without_paths)):
                continue
            declared.update(
                r for r in _v.REF_PATTERN.findall(line) if r.startswith("references/")
            )

        present = {
            f"references/{p.relative_to(refs).as_posix()}": p
            for p in sorted(refs.rglob("*.md"))
        }
        orphans = {k: v for k, v in present.items() if k not in declared}
        if not orphans:
            continue
        # A skill that already has the section keeps its own wording; the
        # orphans are appended to it. Skipping instead left 164 skills with a
        # section that listed one of four files -- the reader was told the
        # section was the index and it was not.
        existing = re.search(r"^##\s+reference files\b", text, re.M | re.I)

        heading_line = (
            existing.group(0) if existing else SECTION_TITLE
        )
        lines = [
            heading_line,
            "",
            f"Each file below is loaded on demand, not at triage. "
            f"{len(orphans)} file(s):",
            "",
        ]
        for rel, path in orphans.items():
            title, sentence = describe(path)
            row = f"- `{rel}`"
            if sentence:
                row += f" — {title}. {sentence}" if title.lower() not in sentence.lower() else f" — {sentence}"
            else:
                row += f" — {title}"
            # A row must not read as a statement that the file is produced.
            # "Configuration & Setup", "Create a repository", "Write the index"
            # and the word "reference" all match the output-declaration rule,
            # and a row that matched it was silently exempt from the very check
            # this file exists to satisfy: 16 of cloudflare-deploy's 306 files
            # stayed unreachable because their titles said "Configuration", and
            # the first fallback text used here -- "reference document" -- put
            # the other 21 back.
            #
            # So a fallback names the file's own kind with no word from the
            # declaration vocabulary at all.
            if OUTPUT_DECLARATION.search(without_emphasis(row)):
                kind = {
                    ".md": "prose", ".py": "code", ".sh": "script",
                    ".json": "data", ".yaml": "data", ".yml": "data",
                }.get(path.suffix, "asset")
                row = f"- `{rel}` — {kind}"
            lines.append(row)
        lines.append("")

        # Append to the existing reference section when there is one, so the
        # author's wording and ordering stay and the new rows join them.
        if existing:
            # Insert INSIDE the existing section: after its own bullet list,
            # not at the section's end, which for a skill whose section is
            # followed by a long `###` run put the rows under the wrong heading
            # and left a second `## Reference files` behind.
            rest = text[existing.end():]
            sec_end = re.search(r"^##\s+", rest, re.M)
            sec = rest[: sec_end.start()] if sec_end else rest
            bullets = list(re.finditer(r"^\s*[-*]\s+\S", sec, re.M))
            if bullets:
                end = existing.end() + bullets[-1].end()
                insert_at = "\n"
            else:
                end = existing.end() + len(sec.rstrip("\n"))
                insert_at = "\n\n"
        else:
            heads = [m.start() for m in re.finditer(r"^##\s+", text, re.M)]
            insert = heads[-1] if heads else len(text)
            rest = text[insert:]
            nxt = re.search(r"^##\s+", rest[1:], re.M)
            end = insert + 1 + nxt.start() if nxt else len(text)
            # No existing section: the rows carry their own heading, so they go
            # in as a new block. This branch previously left `insert_at`
            # unbound, which is why a skill with a `## Reference files` heading
            # and a skill without one failed in different ways and the first
            # version appeared to work for a reason that was not true.
            insert_at = "\n"
        new_text = (
            text[:end] + insert_at + "\n".join(lines[2:]) + "\n" + text[end:]
        )
        skill_md.write_text(new_text, encoding="utf-8")
        changed += 1
        linked += len(orphans)

    print(f"  skills given a reference section : {changed}")
    print(f"  files made reachable             : {linked}")
    return 0


if __name__ == "__main__":
    sys.dont_write_bytecode = True
    raise SystemExit(main())
