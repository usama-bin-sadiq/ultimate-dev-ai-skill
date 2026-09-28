#!/usr/bin/env python3
"""Lint a CONTEXT.md glossary. PASS, WARN, or FAIL per rule.

What it does
------------
Checks one CONTEXT.md against the format this skill's interview loop depends on.
The rules, and why each exists:

PASS rules (a violation makes the file unusable as a grilling anchor)
  * the file exists and is non-empty
  * every ``**Bold Term**`` is defined by a ``:`` on the same logical entry
  * no term is defined twice, case-insensitively
  * no definition is empty
  * no term is a heading (a heading is a section, not a term)
  * term and definition are on the same line, so a term cannot be split from
    its definition by a line break
  * there is at least one term

WARN rules (a violation makes the glossary weaker, not wrong)
  * a term or definition contains an implementation detail
  * a definition is very long (a glossary entry that reads like a spec)
  * a term is in Title Case, which usually means it is a class name and not a
    domain term
  * a term contains a slash or a plural of another defined term

FAIL rules
  * unbalanced bold markers, or a ``**`` that opens without closing
  * the file is not valid UTF-8

Usage
-----
    python3 scripts/context_md_linter.py CONTEXT.md
    python3 scripts/context_md_linter.py CONTEXT.md --format json
    python3 scripts/context_md_linter.py src/ordering/CONTEXT.md --strict

Exit codes: 0 no FAIL findings (warnings allowed), 1 FAIL findings, 2 bad input.

Provenance
----------
Reconstructed to serve the pre-flight step this skill's SKILL.md describes
("confirms the glossary is well-formed before grilling against it"). The
CONTEXT.md format itself, the implementation-detail vocabulary, and every rule
here are this file's own. The upstream skill names a CONTEXT-FORMAT.md reference;
this file encodes that format directly so the linter has no dependency on it.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

MAX_FILE_BYTES = 512 * 1024
MAX_DEFINITION_CHARS = 400
MAX_TERM_CHARS = 60

# A glossary entry is `**Term**: definition`, on one line, definition optional in
# the Markdown but required in the glossary.
ENTRY = re.compile(r"^\s*[-*]?\s*\*\*(?P<term>[^*]+?)\*\*\s*:\s*(?P<definition>.*)$")
BOLD = re.compile(r"\*\*(?P<term>[^*]+?)\*\*")
HEADING = re.compile(r"^\s{0,3}#{1,6}\s")

# Words that indicate the entry has drifted from domain language into
# implementation. A glossary that names a class, a table, or a framework stops
# being usable as a challenge to a plan, because the plan is not about the
# implementation.
IMPLEMENTATION_HINTS = (
    "class", "function", "method", "module", "package", "import", "interface",
    "endpoint", "route", "controller", "handler", "middleware", "repository",
    "service ", "dao", "orm", "migration", "schema", "table", "column", "index",
    "row ", "cache", "redis", "postgres", "mysql", "kafka", "s3", "bucket",
    "lambda", "cluster", "node ", "env var", "environment variable", "flag",
    "config", "setting", "boolean", "string", "integer", "json", "http", "grpc",
    "sdk", "api", "framework", "library", "runtime", "thread", "socket",
    "docker", "kubernetes", "cron", "queue", "topic", "payload", "serialization",
    "serialize", "deserializ", "algorithm", "complexity", "latency", "throughput",
    "cache", "memoiz", "debounce", "throttle",
)


class Finding(dict):
    def __init__(self, level: str, rule: str, line: int, message: str) -> None:
        super().__init__(level=level, rule=rule, line=line, message=message)


def parse_entries(lines: list[str]) -> tuple[list[dict], list[Finding]]:
    """Extract glossary entries and the findings about their shape."""
    entries: list[dict] = []
    findings: list[Finding] = []
    in_fence = False

    for number, raw in enumerate(lines, start=1):
        stripped = raw.strip()

        if stripped.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue

        # Bold inside a heading is a section label, not a term.
        if HEADING.match(raw):
            for match in BOLD.finditer(raw):
                findings.append(Finding(
                    "FAIL", "TERM_IN_HEADING", number,
                    f"heading contains **{match.group('term')}**. A heading is a section, "
                    "not a term; terms belong in the glossary as entries.",
                ))
            continue

        markers = raw.count("**")
        if markers % 2:
            findings.append(Finding(
                "FAIL", "UNBALANCED_BOLD", number,
                f"odd number of '**' markers ({markers}); a bold span opens without closing",
            ))
            continue

        if not markers:
            continue

        match = ENTRY.match(raw)
        if match is None:
            for bold in BOLD.finditer(raw):
                findings.append(Finding(
                    "FAIL", "ENTRY_SHAPE", number,
                    f"**{bold.group('term')}** is not in '**Term**: definition' form on one "
                    "line, so it cannot be resolved to a definition",
                ))
            continue

        term = match.group("term").strip()
        definition = match.group("definition").strip()
        entries.append({"term": term, "definition": definition, "line": number})

    return entries, findings


def check_entries(entries: list[dict], findings: list[Finding]) -> None:
    """Per-entry rules, now that the entries are known."""
    seen: dict[str, dict] = {}

    for entry in entries:
        term = entry["term"]
        definition = entry["definition"]
        line = entry["line"]
        key = term.lower()

        if not definition:
            findings.append(Finding(
                "FAIL", "EMPTY_DEFINITION", line,
                f"**{term}** has no definition. A term with an empty definition is a term "
                "nobody can be challenged against.",
            ))
        elif len(definition) > MAX_DEFINITION_CHARS:
            findings.append(Finding(
                "WARN", "LONG_DEFINITION", line,
                f"definition of **{term}** is {len(definition)} characters. Long enough that "
                "it is probably a spec, an example, or a design note, none of which belong "
                "in a glossary.",
            ))

        if len(term) > MAX_TERM_CHARS:
            findings.append(Finding(
                "WARN", "LONG_TERM", line,
                f"term is {len(term)} characters. A glossary term is a name, not a phrase.",
            ))
        # Title Case with spaces, or a single CamelCase token: both usually mean
        # a class name rather than a domain term. A domain term names a thing in
        # the business and is written the way it is spoken.
        title_case = term == term.title() and " " in term
        camel_case = " " not in term and re.search(r"[a-z][A-Z]", term) is not None
        if title_case or camel_case:
            findings.append(Finding(
                "WARN", "TITLE_CASE_TERM", line,
                f"**{term}** is written like a code identifier, which usually means it is a "
                "class name rather than a domain term. A domain term names a thing in the "
                "business and is written the way it is spoken.",
            ))
        if "/" in term:
            findings.append(Finding(
                "WARN", "SLASH_TERM", line,
                f"**{term}** contains a slash. Two candidates for one term means the "
                "boundary between them has not been drawn yet, which is exactly the kind "
                "of ambiguity a glossary exists to remove.",
            ))

        if key in seen:
            findings.append(Finding(
                "FAIL", "DUPLICATE_TERM", line,
                f"**{term}** is already defined on line {seen[key]['line']} "
                f"(as **{seen[key]['term']}**). One term, one definition.",
            ))
        else:
            seen[key] = entry

        if definition:
            lowered = definition.lower()
            hints = [hint for hint in IMPLEMENTATION_HINTS
                     if re.search(rf"\b{re.escape(hint.strip())}\b", lowered)]
            if hints:
                findings.append(Finding(
                    "WARN", "IMPLEMENTATION_DETAIL", line,
                    f"definition of **{term}** mentions {', '.join(sorted(set(hints)))}. "
                    "CONTEXT.md is a glossary; implementation belongs in an ADR or in the "
                    "code.",
                ))

    for term, entry in seen.items():
        others = [
            other["term"] for other in seen.values()
            if other is not entry and (
                other["term"].lower().rstrip("s") == term.rstrip("s")
            )
        ]
        if others:
            findings.append(Finding(
                "WARN", "PLURAL_PAIR", entry["line"],
                f"**{entry['term']}** and **{', '.join(sorted(others))}** differ only by a "
                "trailing 's'. If they are the same thing, define one; if they are "
                "different, say how.",
            ))


def lint(path: str, strict: bool) -> tuple[list[dict], list[Finding]]:
    """Run every rule over one file. Returns (entries, findings)."""
    file_path = Path(path)
    if not file_path.is_file():
        return [], [Finding("FAIL", "MISSING", 0, f"{path} does not exist")]

    if file_path.stat().st_size > MAX_FILE_BYTES:
        return [], [Finding("FAIL", "TOO_LARGE", 0,
                            f"{path} is larger than {MAX_FILE_BYTES} bytes")]

    try:
        text = file_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return [], [Finding("FAIL", "ENCODING", 0, f"{path} is not valid UTF-8")]

    lines = text.splitlines()
    if not any(line.strip() for line in lines):
        return [], [Finding("FAIL", "EMPTY", 0, f"{path} is empty")]

    entries, findings = parse_entries(lines)
    check_entries(entries, findings)

    if not entries:
        findings.append(Finding(
            "FAIL", "NO_TERMS", 0,
            f"{path} defines no glossary terms. A CONTEXT.md with no terms cannot be "
            "challenged against, and cannot be updated inline during a session.",
        ))

    if strict:
        for finding in list(findings):
            if finding["level"] == "WARN":
                finding["level"] = "FAIL"

    return entries, findings


def render_text(path: str, entries: list[dict], findings: list[Finding]) -> str:
    fails = [f for f in findings if f["level"] == "FAIL"]
    warns = [f for f in findings if f["level"] == "WARN"]

    lines = [
        f"file: {path}",
        f"terms: {len(entries)}",
        f"FAIL: {len(fails)}   WARN: {len(warns)}",
        "",
    ]
    if entries:
        lines.append("terms defined:")
        for entry in entries:
            marker = "FAIL" if any(
                f["level"] == "FAIL" and f["line"] == entry["line"] for f in findings
            ) else ""
            definition = entry["definition"][:70] + ("..." if len(entry["definition"]) > 70 else "")
            lines.append(f"  {entry['line']:>4}  **{entry['term']}**  {definition}  {marker}")
        lines.append("")

    for finding in findings:
        where = f"line {finding['line']}" if finding["line"] else "file"
        lines.append(f"{finding['level']} [{finding['rule']}] {where}: {finding['message']}")

    lines += [
        "",
        "This linter checks the shape of the glossary, not the quality of the thinking in "
        "it. A file that passes still describes whatever its author believed; the value "
        "comes from the session that sharpens the terms against a plan.",
    ]
    return "\n".join(lines) + "\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Lint a CONTEXT.md glossary: PASS, WARN, or FAIL per rule.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("context", nargs="+", help="one or more CONTEXT.md files")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument("--strict", action="store_true", help="treat warnings as failures")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    reports: list[dict] = []
    total_fail = 0

    for path in args.context:
        entries, findings = lint(path, args.strict)
        total_fail += sum(1 for f in findings if f["level"] == "FAIL")
        reports.append({
            "file": path,
            "terms": [
                {"term": e["term"], "definition": e["definition"], "line": e["line"]}
                for e in entries
            ],
            "findings": findings,
        })

    if args.format == "json":
        print(json.dumps({"reports": reports}, indent=2, default=str))
    else:
        for index, report in enumerate(reports):
            if index:
                print()
            print(render_text(
                report["file"],
                [{"term": t["term"], "definition": t["definition"], "line": t["line"]}
                 for t in report["terms"]],
                report["findings"],
            ), end="")
    return 1 if total_fail else 0


if __name__ == "__main__":
    sys.exit(main())
