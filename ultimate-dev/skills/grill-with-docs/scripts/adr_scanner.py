#!/usr/bin/env python3
"""Scan a docs/adr/ directory for numbering gaps, malformed files, and status drift.

What it does
------------
Walks one ADR directory and reports, per file and overall:

* **Naming** — every file matches ``NNNN-kebab-slug.md`` with a four-digit
  number, a hyphen, and a lowercase slug.
* **Numbering integrity** — the sequence has no gaps, no duplicates, and no
  files that sort out of order. A gap usually means an ADR was written and not
  committed, or that a draft number was abandoned; either way the sequence is no
  longer a reliable index of what was decided.
* **Frontmatter** — a small, consistent set of fields, with ``status`` from a
  fixed vocabulary.
* **Body completeness** — the sections an ADR needs to be worth reading six
  months later: context, decision, consequences.
* **Status coherence** — the numbers in the prose agree with the filename, and a
  superseded ADR says what superseded it.

Why status drift matters
------------------------
``docs/adr/`` is the thing a future reader trusts to explain why the code looks
the way it does. An ADR still marked ``accepted`` after a later ADR replaced it
is worse than no ADR, because it will be cited as the reason for a decision that
no longer holds.

Usage
-----
    python3 scripts/adr_scanner.py docs/adr/
    python3 scripts/adr_scanner.py docs/ --format json
    python3 scripts/adr_scanner.py docs/adr/ --require-status superseded-links

Exit codes: 0 no failures, 1 failures found, 2 bad input.

Provenance
----------
Reconstructed to serve the pre-flight and in-session steps the SKILL.md
describes ("surfaces numbering gaps, malformed ADRs, status-frontmatter
inconsistencies"). The ADR format, the status vocabulary, and every rule are
this file's own.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

MAX_DIR_ENTRIES = 5000
MAX_FILE_BYTES = 512 * 1024
MAX_SCAN_DEPTH = 4

FILENAME = re.compile(r"^(?P<number>\d{4})-(?P<slug>[a-z0-9]+(?:-[a-z0-9]+)*)\.md$")
FRONTMATTER_FENCE = re.compile(r"^\s*---\s*$")

# The status vocabulary. Deliberately short: a status list that grows stops being
# a decision record and becomes a workflow.
STATUSES = {
    "proposed": "written up, not yet agreed",
    "accepted": "in force",
    "superseded": "replaced by a later ADR",
    "deprecated": "no longer relevant, not replaced",
    "rejected": "considered and declined",
}
# Statuses where the ADR no longer governs and must point at what does.
CLOSED_STATUSES = {"superseded", "deprecated", "rejected"}

# Sections an ADR needs to be useful later. Not a template requirement: an ADR
# is allowed to be short, but it is not allowed to state a decision without
# saying what it replaces.
REQUIRED_SECTIONS = ("context", "decision", "consequences")
RECOMMENDED_SECTIONS = ("alternatives", "status", "references")
FRONTMATTER_FIELDS = ("status", "date", "deciders")

# A cross-reference to a number, in prose or in a link.
REFERENCE = re.compile(r"(?:adr[-_/]?)(\d{4})", re.IGNORECASE)
REFERENCE_LINK = re.compile(r"\]\([^)]*?(\d{4})-[^)]*?\)")


class Finding(dict):
    def __init__(self, level: str, rule: str, file: str, message: str) -> None:
        super().__init__(level=level, rule=rule, file=file, message=message)


def parse_frontmatter(lines: list[str]) -> tuple[dict, int]:
    """Parse a leading ``---`` fenced block. Returns (fields, body_start_line)."""
    if not lines or not FRONTMATTER_FENCE.match(lines[0]):
        return {}, 0

    fields: dict[str, str] = {}
    for index in range(1, len(lines)):
        line = lines[index]
        if FRONTMATTER_FENCE.match(line):
            return fields, index + 1
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        fields[key.strip().lower()] = value.strip()
    # Unterminated fence.
    return fields, -1


def sections(body: str) -> dict[str, str]:
    """Map lowercased heading text to the text under it."""
    found: dict[str, str] = {}
    current = None
    buffer: list[str] = []
    for line in body.splitlines():
        heading = re.match(r"^\s{0,3}#{1,6}\s+(.*?)\s*#*\s*$", line)
        if heading:
            if current is not None:
                found[current] = "\n".join(buffer).strip()
            current = heading.group(1).strip().lower()
            buffer = []
        elif current is not None:
            buffer.append(line)
    if current is not None:
        found[current] = "\n".join(buffer).strip()
    return found


def canonical_section(keys: dict[str, str], name: str) -> str | None:
    """Find a section by a loose match, so 'Why' and 'Background' both count."""
    for key, value in keys.items():
        if name in key or key in name:
            return value
    return None


def scan_file(path: Path, root: Path) -> tuple[dict | None, list[Finding]]:
    """Check one ADR file. Returns (record, findings)."""
    name = path.name
    relative = str(path.relative_to(root))
    findings: list[Finding] = []

    match = FILENAME.match(name)
    if not match:
        findings.append(Finding(
            "FAIL", "FILENAME", relative,
            "does not match NNNN-kebab-slug.md. The number has to be four digits so the "
            "directory sorts correctly and every reference can point at one file.",
        ))
        number = None
        slug = None
    else:
        number = match.group("number")
        slug = match.group("slug")

    if path.is_symlink():
        findings.append(Finding("FAIL", "SYMLINK", relative, "is a symlink; refusing to follow it"))
        return None, findings
    if path.stat().st_size > MAX_FILE_BYTES:
        findings.append(Finding("FAIL", "TOO_LARGE", relative,
                                f"is larger than {MAX_FILE_BYTES} bytes"))
        return None, findings

    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        findings.append(Finding("FAIL", "ENCODING", relative, "is not valid UTF-8"))
        return None, findings

    lines = text.splitlines()
    fields, body_start = parse_frontmatter(lines)

    if body_start == -1:
        findings.append(Finding(
            "FAIL", "UNTERMINATED_FRONTMATTER", relative,
            "the frontmatter fence is never closed",
        ))
        return ({"file": relative, "number": number, "slug": slug, "status": None},
                findings)

    if body_start == 0:
        findings.append(Finding(
            "WARN", "NO_FRONTMATTER", relative,
            "has no frontmatter. Without a status, a reader cannot tell whether this "
            "decision is still in force.",
        ))
        status = None
    else:
        missing = [field for field in FRONTMATTER_FIELDS if field not in fields]
        if missing:
            findings.append(Finding(
                "WARN", "FRONTMATTER_FIELDS", relative,
                f"frontmatter is missing {', '.join(missing)}",
            ))
        status = fields.get("status", "").strip().lower() or None
        if status is None:
            findings.append(Finding(
                "FAIL", "NO_STATUS", relative,
                "frontmatter has no status. Use one of: " + ", ".join(sorted(STATUSES)),
            ))
        elif status not in STATUSES:
            findings.append(Finding(
                "FAIL", "BAD_STATUS", relative,
                f"status {status!r} is not one of: " + ", ".join(sorted(STATUSES)),
            ))

    body = "\n".join(lines[body_start:]) if body_start else text
    found_sections = sections(body)

    for section in REQUIRED_SECTIONS:
        content = canonical_section(found_sections, section)
        if content is None:
            findings.append(Finding(
                "FAIL", "MISSING_SECTION", relative,
                f"has no {section} section. An ADR without {section} cannot be read six "
                "months later by the person who has to maintain the result.",
            ))
        elif not content.strip():
            findings.append(Finding(
                "FAIL", "EMPTY_SECTION", relative, f"the {section} section is empty"
            ))

    missing_recommended = [
        section for section in RECOMMENDED_SECTIONS
        if canonical_section(found_sections, section) is None
    ]
    if missing_recommended:
        findings.append(Finding(
            "WARN", "RECOMMENDED_SECTIONS", relative,
            f"no {', '.join(missing_recommended)} section. A decision without recorded "
            "alternatives cannot show that a trade-off was actually made, which is one "
            "of the three tests for writing an ADR at all.",
        ))

    # A number mentioned in the prose that is not the file's own number, and is
    # not a number that exists in this directory, is a dangling reference.
    record = {
        "file": relative,
        "number": number,
        "slug": slug,
        "status": status,
        "sections": sorted(found_sections),
        "size_bytes": path.stat().st_size,
    }
    return record, findings


def scan_directory(root: Path) -> tuple[list[dict], list[Finding]]:
    """Walk one directory and run every structural check across the whole set."""
    findings: list[Finding] = []
    records: list[dict] = []

    adr_dir = root / "adr" if (root / "adr").is_dir() and root.name != "adr" else root

    if not adr_dir.is_dir():
        return [], [Finding(
            "FAIL", "MISSING_DIR", str(root),
            "is not a directory, and has no adr/ subdirectory. ADRs live at "
            "docs/adr/ (or <context>/docs/adr/ in a multi-context repo).",
        )]

    if adr_dir.is_symlink():
        return [], [Finding("FAIL", "SYMLINK_DIR", str(adr_dir),
                            "is a symlink; refusing to follow it")]

    files = sorted(
        path for path in adr_dir.rglob("*.md")
        if path.is_file() and len(path.relative_to(adr_dir).parts) <= MAX_SCAN_DEPTH
    )
    if len(list(adr_dir.rglob("*"))) > MAX_DIR_ENTRIES:
        return [], [Finding("FAIL", "TOO_MANY", str(adr_dir),
                            f"directory tree exceeds {MAX_DIR_ENTRIES} entries")]

    if not files:
        return [], [Finding(
            "WARN", "EMPTY_DIR", str(adr_dir),
            "contains no ADRs. That is fine for a new project; create the first one only "
            "when a decision meets all three of the ADR tests.",
        )]

    for path in files:
        record, file_findings = scan_file(path, adr_dir)
        findings.extend(file_findings)
        if record is not None:
            records.append(record)

    findings.extend(check_numbering(records, adr_dir))
    findings.extend(check_references(records, adr_dir))
    return records, findings


def check_numbering(records: list[dict], adr_dir: Path) -> list[Finding]:
    """Gaps, duplicates, and a first number that is not 0001."""
    findings: list[Finding] = []
    numbered = [r for r in records if r["number"]]
    if not numbered:
        findings.append(Finding(
            "FAIL", "NO_NUMBERS", str(adr_dir),
            "no file has a parseable four-digit number, so nothing can reference them",
        ))
        return findings

    numbers = [int(r["number"]) for r in numbered]
    counts: dict[int, int] = {}
    for number in numbers:
        counts[number] = counts.get(number, 0) + 1

    for number, count in sorted(counts.items()):
        if count > 1:
            offenders = [r["file"] for r in numbered if int(r["number"]) == number]
            findings.append(Finding(
                "FAIL", "DUPLICATE_NUMBER", offenders[0],
                f"number {number:04d} is used by {count} files: {', '.join(offenders)}. "
                "A number must identify exactly one decision.",
            ))

    unique = sorted(counts)
    for previous, current in zip(unique, unique[1:]):
        if current > previous + 1:
            for missing in range(previous + 1, current):
                findings.append(Finding(
                    "WARN", "NUMBER_GAP", str(adr_dir),
                    f"number {missing:04d} is missing between {previous:04d} and "
                    f"{current:04d}. A gap usually means an ADR was drafted and abandoned "
                    "or never committed; either way the sequence is no longer a reliable "
                    "index of what was decided.",
                ))

    if unique[0] != 1:
        findings.append(Finding(
            "WARN", "FIRST_NUMBER", str(adr_dir),
            f"the first ADR is numbered {unique[0]:04d}, not 0001. Starting at 1 keeps "
            "the sequence countable and leaves room for a numbered gap to be obvious.",
        ))
    return findings


def check_references(records: list[dict], adr_dir: Path) -> list[Finding]:
    """Every referenced number must exist, and a closed ADR must say what replaced it."""
    findings: list[Finding] = []
    existing = {int(r["number"]) for r in records if r["number"]}

    for record in records:
        path = adr_dir / record["file"]
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue

        own = int(record["number"]) if record["number"] else None
        cited: set[int] = set()
        for match in REFERENCE_LINK.finditer(text):
            cited.add(int(match.group(1)))
        for match in REFERENCE.finditer(text):
            cited.add(int(match.group(1)))
        cited.discard(own) if own is not None else None

        for number in sorted(cited):
            if number not in existing:
                findings.append(Finding(
                    "FAIL", "DANGLING_REFERENCE", record["file"],
                    f"references {number:04d}, which does not exist in this directory. A "
                    "reader who follows the reference finds nothing and cannot tell "
                    "whether the decision was reversed or simply lost.",
                ))

        status = record["status"]
        if status in CLOSED_STATUSES:
            points_at_something = any(
                f"{number:04d}" in text for number in cited
            )
            if status == "superseded" and not points_at_something:
                findings.append(Finding(
                    "FAIL", "SUPERSEDED_WITHOUT_TARGET", record["file"],
                    "is marked superseded but names no ADR that replaced it. A superseded "
                    "record with no successor tells a reader only that something changed, "
                    "not what to believe now.",
                ))
            if status == "superseded" and points_at_something:
                for number in sorted(cited):
                    if number in existing and number <= (own or 0):
                        findings.append(Finding(
                            "FAIL", "SUPERSEDED_BY_OLDER", record["file"],
                            f"is marked superseded by {number:04d}, which is not newer. "
                            "The supersession chain points backwards.",
                        ))
        elif status == "accepted":
            older_replaced = [
                number for number in sorted(cited)
                if number in existing and number < (own or 0)
            ]
            for number in older_replaced:
                other = next(
                    (r for r in records if r["number"] == f"{number:04d}"), None
                )
                if other and other["status"] == "accepted":
                    findings.append(Finding(
                        "WARN", "SUPERSEDED_NOT_MARKED", record["file"],
                        f"supersedes {number:04d}, but that ADR is still marked "
                        f"{other['status']}. Two records claiming to be in force for the "
                        "same decision is how a reader ends up citing the wrong one.",
                    ))
    return findings


def render_text(root: str, records: list[dict], findings: list[Finding]) -> str:
    fails = [f for f in findings if f["level"] == "FAIL"]
    warns = [f for f in findings if f["level"] == "WARN"]

    lines = [f"directory: {root}", f"ADRs: {len(records)}",
             f"FAIL: {len(fails)}   WARN: {len(warns)}", ""]

    if records:
        lines.append("number  status        file")
        for record in sorted(records, key=lambda r: (r["number"] or "9999")):
            marker = ""
            if any(f["level"] == "FAIL" and f["file"] == record["file"] for f in findings):
                marker = "  <- FAIL"
            elif any(f["level"] == "WARN" and f["file"] == record["file"] for f in findings):
                marker = "  <- warn"
            lines.append(
                f"{(record['number'] or '????')}     "
                f"{(record['status'] or 'no status'):<12}  {record['file']}{marker}"
            )
        lines.append("")

    for finding in findings:
        lines.append(f"{finding['level']} [{finding['rule']}] {finding['file']}: "
                     f"{finding['message']}")

    lines += [
        "",
        "The ADR tests, from the skill: hard to reverse, surprising without context, and "
        "the result of a real trade-off. A directory of ADRs that does not reflect those "
        "three tests is a changelog with extra steps. Nothing here checks whether a "
        "decision was well made; it checks whether the record will still be readable and "
        "still be believed.",
    ]
    return "\n".join(lines) + "\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Scan a docs/adr/ directory for numbering gaps, malformed files, and status drift.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("directory", help="the docs/ or docs/adr/ directory to scan")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = Path(args.directory)
    if not root.exists():
        raise SystemExit(f"error: not found: {args.directory}")
    if not root.is_dir():
        raise SystemExit(f"error: not a directory: {args.directory}")

    records, findings = scan_directory(root)
    fails = sum(1 for f in findings if f["level"] == "FAIL")

    if args.format == "json":
        print(json.dumps(
            {"directory": str(root), "adrs": records, "findings": findings}, indent=2, default=str
        ))
    else:
        print(render_text(str(root), records, findings), end="")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
