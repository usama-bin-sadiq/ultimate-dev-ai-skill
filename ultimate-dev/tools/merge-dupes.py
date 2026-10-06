#!/usr/bin/env python3
"""Merge the template-family duplicate pairs into a single canonical skill.

For each (winner, loser) pair this script:
  1. copies any file the loser owns and the winner lacks;
  2. ports the standard sections the winner lacks
     (Communication / Proactive Triggers / Output Artifacts);
  3. registers the copied files in the winner's own "loaded on demand" list
     and corrects that list's file count;
  4. removes the loser.

It never overwrites a file the winner already has. Run from anywhere:

    python3 tools/merge-dupes.py            # apply
    python3 tools/merge-dupes.py --dry-run  # report only
"""

import argparse
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "skills"

PORTED_SECTIONS = ("## Communication", "## Proactive Triggers", "## Output Artifacts")

# winner <- loser. Selected on evidence: the winner already carries the fuller
# procedure or the vendor-supplied asset; the loser contributes only files or
# boilerplate sections the winner lacks.
PAIRS = [
    ("emails", "email-sequence"),
    ("popups", "popup-cro"),
    ("paywalls", "paywall-upgrade-cro"),
    ("competitors", "competitor-alternatives"),
]

COUNT_RE = re.compile(r"(loaded on demand, not at triage\.\s+)(\d+)( file\(s\):)")


def split_sections(body: str) -> dict[str, str]:
    """Map '## Heading' -> full section text including its heading."""
    out: dict[str, str] = {}
    parts = re.split(r"(?m)^(## .+)$", body)
    # parts = [preamble, head1, text1, head2, text2, ...]
    for i in range(1, len(parts) - 1, 2):
        head = parts[i].strip()
        out[head] = head + "\n" + parts[i + 1]
    return out


def files_of(skill_dir: Path) -> list[Path]:
    return [p for p in skill_dir.rglob("*") if p.is_file() and p.name != "SKILL.md"]


def merge(winner: str, loser: str, dry: bool) -> list[str]:
    wdir, ldir = SKILLS / winner, SKILLS / loser
    notes: list[str] = []

    # --- 1. copy files the loser uniquely owns -------------------------
    copied: list[Path] = []
    for src in sorted(files_of(ldir)):
        rel = src.relative_to(ldir)
        if (wdir / rel).exists():
            continue
        copied.append(rel)
        if not dry:
            (wdir / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, wdir / rel)
    notes.append(
        f"files ported: {', '.join(str(c) for c in copied) if copied else 'none'}"
    )

    wbody = (wdir / "SKILL.md").read_text()
    lbody = (ldir / "SKILL.md").read_text()
    wsect, lsect = split_sections(wbody), split_sections(lbody)

    # --- 2. port the standard sections the winner lacks ----------------
    ported: list[str] = []
    for head in PORTED_SECTIONS:
        if head in wsect or head not in lsect:
            continue
        ported.append(head)
        anchor = "## Task-Specific Questions"
        if anchor not in wbody:
            anchor = "## Related Skills"
        if anchor in wbody:
            wbody = wbody.replace(anchor, lsect[head].rstrip() + "\n\n---\n\n" + anchor, 1)
        else:
            wbody = wbody.rstrip() + "\n\n---\n\n" + lsect[head].rstrip() + "\n"
    notes.append(
        "sections ported: " + (", ".join(ported) if ported else "none")
    )

    # --- 3. register copied files in the winner's own list --------------
    if copied and not COUNT_RE.search(wbody):
        # The winner carries no bundled-file list. Adopt the template family's
        # own "## Reference files" convention so the copied files stay
        # discoverable instead of becoming orphans.
        ported.append("## Reference files")
        bullets = "\n".join(f"- [`{c}`]({c})" for c in copied)
        block = (
            "## Reference files\n\nThese ship with the skill and are read on demand; "
            "none is needed to use it. Each answers one question the sections above "
            "do not.\n\n" + bullets + "\n\n---\n\n"
        )
        anchor = "## Related Skills"
        if anchor in wbody:
            wbody = wbody.replace(anchor, block + anchor, 1)
        else:
            wbody = wbody.rstrip() + "\n\n---\n\n" + block
        notes.append(f"created '## Reference files' list for {len(copied)} ported file(s)")
    elif copied and COUNT_RE.search(wbody):
        existing = re.findall(r"(?m)^- `([^`]+)`", wbody)
        add = [str(c) for c in copied if str(c) not in existing]
        if add:
            lines = "\n".join(
                f"- `{p}` — Ported from `{loser}` during duplicate consolidation."
                for p in add
            )
            # insert at end of the existing bullet list
            m = list(re.finditer(r"(?m)^- `([^`]+)`", wbody))[-1]
            wbody = wbody[: m.end()] + "\n" + lines + wbody[m.end() :]
            total = len(existing) + len(add)
            wbody = COUNT_RE.sub(lambda mm: f"{mm.group(1)}{total}{mm.group(3)}", wbody, count=1)
        notes.append(f"list entries added: {len(add)} (count -> {len(existing) + len(add)})")
    elif copied:
        notes.append("no bundled-file list to update")

    if not dry:
        (wdir / "SKILL.md").write_text(wbody)

    # --- 4. remove the loser -------------------------------------------
    if not dry:
        shutil.rmtree(ldir)
    notes.append(f"removed: skills/{loser}/")
    return notes


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    for winner, loser in PAIRS:
        if not (SKILLS / loser).is_dir():
            print(f"skip {loser}: already merged")
            continue
        if not (SKILLS / winner / "SKILL.md").is_file():
            print(f"FAIL {winner}: winner missing", file=sys.stderr)
            return 1
        print(f"\n{winner} <- {loser}")
        for note in merge(winner, loser, a.dry_run):
            print(f"    {note}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
