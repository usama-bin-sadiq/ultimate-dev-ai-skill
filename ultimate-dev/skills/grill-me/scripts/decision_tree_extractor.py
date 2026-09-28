#!/usr/bin/env python3
"""Extract the decision tree from a plan or design document.

Grill Me walks a plan branch by branch, resolving dependencies one at a time.
This script does the mechanical half of step 2 of the workflow: read the plan
and turn it into an ordered tree of decisions, so the interview has somewhere
to walk.

Reads a Markdown or plain-text plan (a path, or `-` for stdin) and emits a
depth-first ordered list of decisions. Each decision records the heading path it
was found under, whether it is a question already, whether it names something
the codebase could answer instead, and which other decisions it depends on.

Reconstruction note: SKILL.md says only "Run scripts/decision_tree_extractor.py
to extract branches" and describes the shape of the interview, so the parsing
heuristics and the output schema below are this file's own. They are tuned for
the document shapes a plan usually takes (headings, question lines, decision
markers, and indented sub-points) and are deliberately conservative: a line that
does not look like a decision is not turned into one.

    python decision_tree_extractor.py plan.md
    python decision_tree_extractor.py plan.md -o tree.json
    cat plan.md | python decision_tree_extractor.py - --json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from typing import Any, NoReturn

# A heading, at any depth.
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*\S)\s*$")
# A list item, capturing indent, marker, and body.
LIST_RE = re.compile(r"^(\s*)(?:[-*+]|\d+[.)])\s+(.*\S)\s*$")
# A bullet that is not a list item, e.g. "- [ ] decide X" handled above.
BULLET_RE = re.compile(r"^(\s*)[\u2022\u2013\u2014-]\s+(.*\S)\s*$")

# Words that mark a line as a decision rather than prose.
DECISION_MARKERS = (
    "decide", "decision", "choose", "choice", "pick", "select", "which",
    "should we", "do we", "will we", "must we", "need we", "trade-off",
    "tradeoff", "option", "approach", "strategy", "policy", "constraint",
)
# Phrases that mean "this was already settled", so it is not a live question.
RESOLVED_MARKERS = (
    "decided:", "tbd by", "to be decided", "already decided", "we will use",
    "we've chosen", "has been chosen", "settled:",
)
# Phrases that mean "go look it up rather than ask". Deliberately concrete:
# "existing" and "in the codebase" are true of almost every plan, and a false
# positive here costs a wasted turn.
CODEBASE_MARKERS = (
    "config file", "configuration file", "config value", "defined in",
    "set in", "in package.json", "in tsconfig", "in vite.config", "already shipped",
    "current setting", "current value", "default value", "grep the repo",
)

# A dependency: an explicit cross-reference, or a "depends on" clause.
DEPENDS_RE = re.compile(
    r"\b(?:depends?\s+(?:on|upon)|requires?|after|once)\b[:\s]+(?P<target>[^,.;]+)",
    re.IGNORECASE,
)
# A cross-reference by decision id, e.g. "see D3" or "(D3)".
CROSSREF_RE = re.compile(r"\bD(\d{1,3})\b")

MAX_INPUT_BYTES = 4 * 1024 * 1024


def die(message: str) -> NoReturn:
    print(f"decision_tree_extractor.py: {message}", file=sys.stderr)
    raise SystemExit(2)


def read_plan(source: str) -> str:
    """Read the plan text from a path or from stdin."""
    if source == "-":
        data = sys.stdin.read(MAX_INPUT_BYTES + 1)
        if len(data) > MAX_INPUT_BYTES:
            die("plan read from stdin exceeds 4 MiB; split it and extract each part.")
        return data
    try:
        with open(source, "r", encoding="utf-8", errors="replace") as handle:
            data = handle.read(MAX_INPUT_BYTES + 1)
    except OSError as exc:
        die(f"cannot read {source!r}: {exc.strerror or exc}")
    if len(data) > MAX_INPUT_BYTES:
        die(f"{source!r} exceeds 4 MiB; this script is for a plan, not a corpus.")
    return data


def indent_width(line: str) -> int:
    """Visual indent width, treating a tab as four columns."""
    stripped = line.lstrip(" \t")
    prefix = line[: len(line) - len(stripped)]
    return len(prefix.replace("\t", "    "))


MARKER_LABEL_RE = re.compile(
    r"^(?:\*\*|__)?\s*(decision|open question|question|q)\s*(?:\*\*|__)?\s*[:\-]\s*",
    re.IGNORECASE,
)
CHECKBOX_RE = re.compile(r"^\[[ xX]\]\s*")


def strip_marker(body: str) -> str:
    """Remove a leading `- [ ]`, `**Decision:**`, or similar wrapper."""
    return MARKER_LABEL_RE.sub("", CHECKBOX_RE.sub("", body.strip())).strip()


def looks_like_decision(text: str, labelled: bool = False) -> bool:
    """True when a line reads as a decision, question, or option.

    ``labelled`` is True when the line was introduced by an explicit
    `Decision:`-style marker, which makes it a decision whatever it looks like
    once the marker is stripped -- the author's intent is not in doubt.
    """
    lowered = text.lower()
    if any(marker in lowered for marker in RESOLVED_MARKERS):
        return False
    if labelled:
        return True
    if "?" in text:
        return True
    if any(lowered.startswith(marker) for marker in DECISION_MARKERS):
        return True
    if any(f" {marker} " in f" {lowered} " for marker in DECISION_MARKERS):
        return True
    # A short noun phrase naming an option is still a decision.
    words = lowered.split()
    return len(words) <= 10 and any(words[0] == w for w in ("strategy", "approach", "policy"))


FILE_RE = re.compile(r"\b[\w./-]+\.(?:ts|tsx|js|jsx|py|json|toml|ya?ml|md|sh|css)\b")
# An identifier worth grepping for: lowercase-leading, or carrying a separator.
# "Should" and "How" are nouns to neither a person nor a grep.
GREPPABLE_RE = re.compile(r"\b(?:[a-z][A-Za-z0-9]{2,}|[A-Za-z0-9]+[._/-][\w./-]+)\b")
STOPWORDS = frozenset("""
the and for with from into over under that this these those when what which who
how why does will would could should must have has had been being are was were
you your our their its it's they them then than also only just more most some
any all one two use used using keep keeps take takes make makes need needs
""".split())


def mentions_codebase(text: str) -> bool:
    """True when the line points at something the codebase could answer."""
    lowered = text.lower()
    if any(marker in lowered for marker in CODEBASE_MARKERS):
        return True
    return bool(FILE_RE.search(text))


def evidence_hint(text: str) -> str:
    """A concrete first command to try before asking the question."""
    files = FILE_RE.findall(text)
    if files:
        return f"Read {files[0]} before asking."
    backticked = [w.strip().strip("`'\"") for w in re.findall(r"`([^`]+)`", text)]
    if backticked:
        return f"Grep the repo for {backticked[0]!r} before asking."
    for word in GREPPABLE_RE.findall(text):
        if word.lower() not in STOPWORDS:
            return f"Grep the repo for {word!r} before asking."
    return "Explore the codebase for this before asking."


def dependencies(text: str) -> list[str]:
    """Ids this decision depends on, from an explicit clause or a D-ref."""
    found: list[str] = []

    clause = DEPENDS_RE.search(text)
    if clause:
        target = clause.group("target").strip()
        ref = CROSSREF_RE.search(target)
        if ref:
            found.append(f"D{int(ref.group(1)):03d}")
        else:
            # Not an id reference: keep the phrase so the coordinator can match
            # it against a sibling decision by hand.
            found.append(target[:60])

    for ref in CROSSREF_RE.finditer(text):
        candidate = f"D{int(ref.group(1)):03d}"
        if candidate not in found:
            found.append(candidate)
    return found


def extract(text: str) -> dict[str, Any]:
    """Turn plan text into an ordered decision tree."""
    decisions: list[dict[str, Any]] = []
    heading_path: list[str] = []
    section_stack: list[tuple[int, int]] = []  # (indent, decision index)

    for lineno, raw in enumerate(text.splitlines(), 1):
        if not raw.strip():
            continue

        heading = HEADING_RE.match(raw)
        if heading:
            level = len(heading.group(1))
            title = heading.group(2).strip()
            heading_path = heading_path[: level - 1] + [title]
            section_stack = [pair for pair in section_stack if pair[0] < 0]
            continue

        list_match = LIST_RE.match(raw) or BULLET_RE.match(raw)
        if not list_match:
            continue
        raw_body = list_match.group(2).strip()
        labelled = bool(MARKER_LABEL_RE.match(raw_body))
        body = strip_marker(raw_body)
        if not body:
            continue
        if not looks_like_decision(body, labelled=labelled):
            continue

        indent = indent_width(list_match.group(1))
        while section_stack and section_stack[-1][0] >= indent:
            section_stack.pop()
        parent = section_stack[-1][1] if section_stack else None

        index = len(decisions)
        decisions.append(
            {
                "id": f"D{index:03d}",
                "index": index,
                "line": lineno,
                "depth": len(section_stack),
                "parent": decisions[parent]["id"] if parent is not None else None,
                "heading_path": list(heading_path),
                "text": body,
                "is_question": "?" in body,
                "resolvable_from_codebase": mentions_codebase(body),
                "evidence_hint": evidence_hint(body),
                "depends_on": dependencies(body),
                "answer": None,
                "status": "open",
            }
        )
        section_stack.append((indent, index))

    # Depth-first order, so a branch is finished before the next one opens.
    children: dict[str | None, list[str]] = {}
    for node in decisions:
        children.setdefault(node["parent"], []).append(node["id"])
    order: list[str] = []

    def walk(parent: str | None) -> None:
        for child_id in children.get(parent, []):
            order.append(child_id)
            walk(child_id)

    walk(None)

    return {
        "schema": "grill-me/decision-tree/1",
        "decision_count": len(decisions),
        "order": order,
        "decisions": decisions,
    }


def render_text(tree: dict[str, Any]) -> str:
    """A readable depth-first listing with the question order marked."""
    by_id = {node["id"]: node for node in tree["decisions"]}
    lines: list[str] = []
    for position, node_id in enumerate(tree["order"], 1):
        node = by_id[node_id]
        indent = "  " * node["depth"]
        total = tree["decision_count"]
        marker = "Q" if node["is_question"] else "d"
        lines.append(f"{indent}{node_id}  {marker}[{position}/{total}]  {node['text']}")
        if node["parent"]:
            lines.append(f"{indent}    parent: {node['parent']}")
        if node["depends_on"]:
            lines.append(f"{indent}    depends on: {', '.join(node['depends_on'])}")
        if node["resolvable_from_codebase"]:
            lines.append(f"{indent}    {node['evidence_hint']}")
    if not lines:
        lines.append(
            "No decision-shaped lines found. Grill Me needs a plan with something "
            "to decide; if the plan is prose, add explicit decision lines first."
        )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="decision_tree_extractor.py",
        description="Extract an ordered decision tree from a plan or design document.",
        epilog=(
            "Depth-first by default: a branch is finished before the next one "
            "opens. A line that reads as already settled is not turned into a "
            "question."
        ),
    )
    parser.add_argument("plan", help="path to the plan, or - to read stdin")
    parser.add_argument("-o", "--output", help="write to this file instead of stdout")
    parser.add_argument("--json", action="store_true", help="emit the tree as JSON")
    args = parser.parse_args(argv)

    tree = extract(read_plan(args.plan))
    text = json.dumps(tree, indent=2) if args.json else render_text(tree)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as handle:
            handle.write(text + "\n")
        print(f"wrote {args.output} ({tree['decision_count']} decisions)", file=sys.stderr)
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
