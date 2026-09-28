#!/usr/bin/env python3
"""Turn a decision tree into the ordered question list, with recommendations.

Grill Me's rule is one question per turn, and every question carries a
recommended answer. "What do you think?" is the failure mode this script exists
to prevent: the interview stalls on the first branch where nobody has a view.

Reads the JSON that decision_tree_extractor.py emits and produces one turn per
decision, in the extractor's depth-first order, with dependencies already
hoisted: a decision never appears before the decision it depends on.

Reconstruction note: SKILL.md documents the shape of a turn
(`Q[i]/[total]: [question]` / `Recommended answer: [your call + 1-sentence
rationale]`) but not this script's arguments or how a recommendation is
derived, so both are this file's own. The recommendation is a reading of the
plan text, not a judgement about the design: the script cannot know the right
answer, and the coordinator replaces it with their own call before the question
is asked.

    python question_generator.py tree.json
    python question_generator.py tree.json --json -o questions.json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from typing import Any, NoReturn

MAX_INPUT_BYTES = 4 * 1024 * 1024

# The plan says this, so the plan is the recommendation until the coordinator
# overrides it. These are the fragments that mark a stated preference.
STANCE_MARKERS = (
    "we will", "we'll", "we are going to", "plan to", "planning to", "prefer",
    "chosen", "settled on", "using", "use the", "with the", "adopt", "adopting",
    "keep", "retain", "replace", "migrate", "start with", "begin with",
)
# Fragments that mark a cost or a constraint, which make the best rationale to
# hand back.
RATIONALE_MARKERS = (
    "because", "since", "so that", "in order to", "to avoid", "otherwise",
    "requirement", "required", "constraint", "must", "deadline", "budget",
    "latency", "compliance", "risk",
)
SENTENCE_RE = re.compile(r"(?<=[.!?])\s+")

# Question openers, so a question line is asked as a question rather than
# restated as a statement.
OPENERS = (
    ("which ", "Which "),
    ("what ", "What "),
    ("who ", "Who "),
    ("when ", "When "),
    ("where ", "Where "),
    ("how ", "How "),
    ("should ", "Should "),
    ("will ", "Will "),
    ("do ", "Do "),
    ("is ", "Is "),
    ("are ", "Are "),
    ("decide ", "Decide "),
    ("choose ", "Choose "),
    ("select ", "Select "),
    ("pick ", "Pick "),
)


def die(message: str) -> NoReturn:
    print(f"question_generator.py: {message}", file=sys.stderr)
    raise SystemExit(2)


def load_tree(path: str) -> dict[str, Any]:
    """Read the extractor's JSON tree, or accept a plan and extract it inline."""
    try:
        with open(path, "r", encoding="utf-8") as handle:
            data = handle.read(MAX_INPUT_BYTES + 1)
    except OSError as exc:
        die(f"cannot read {path!r}: {exc.strerror or exc}")
    if len(data) > MAX_INPUT_BYTES:
        die(f"{path!r} exceeds 4 MiB")
    try:
        tree = json.loads(data)
    except json.JSONDecodeError as exc:
        die(
            f"{path!r} is not the extractor's JSON ({exc}). Run "
            "decision_tree_extractor.py --json first."
        )
    if not isinstance(tree, dict) or "decisions" not in tree:
        die(f"{path!r} has no 'decisions' array; is it the extractor's output?")
    return tree


def order_decisions(tree: dict[str, Any]) -> list[dict[str, Any]]:
    """Depth-first order, with any unresolved dependency pulled ahead of its dependent."""
    by_id = {node["id"]: node for node in tree["decisions"]}
    order: list[str] = [node_id for node_id in tree.get("order", []) if node_id in by_id]
    order += [node["id"] for node in tree["decisions"] if node["id"] not in set(order)]

    placed: list[str] = []
    seen: set[str] = set()

    def place(node_id: str, stack: tuple[str, ...] = ()) -> None:
        if node_id in seen or node_id not in by_id:
            return
        if node_id in stack:
            # A dependency cycle in the plan text; ask the decision on its own
            # rather than looping.
            return
        for dependency in by_id[node_id].get("depends_on", []):
            if dependency in by_id:
                place(dependency, stack + (node_id,))
        if node_id not in seen:
            seen.add(node_id)
            placed.append(node_id)

    for node_id in order:
        place(node_id)
    return [by_id[node_id] for node_id in placed]


def to_question(text: str) -> tuple[str, str]:
    """Phrase a decision as a question, returning (question, context).

    A line that already asks its question — "Which isolation level? READ
    COMMITTED" — keeps only the question. The rest is context the caller reads
    when forming a recommendation, not a second question mark glued on the end.
    """
    sentence = re.sub(r"\s+", " ", text).strip()
    if "?" in sentence:
        question, _, context = sentence.partition("?")
        return question.strip() + "?", context.strip()
    sentence = sentence.rstrip(".")
    context = ""
    lowered = sentence.lower()
    for prefix, opener in OPENERS:
        if lowered.startswith(prefix):
            return opener + sentence[len(prefix):] + "?", context
    return f"Decision: {sentence} — what exactly is being chosen here, and why?", context


def recommended_answer(node: dict[str, Any], context: str = "") -> str:
    """A recommendation the coordinator can accept or overrule, never a blank."""
    text = re.sub(r"\s+", " ", node["text"]).strip().rstrip("?.")
    sentences = [s.strip() for s in SENTENCE_RE.split(text) if s.strip()]

    stance = next((s for s in sentences if any(m in s.lower() for m in STANCE_MARKERS)), None)
    rationale = next((s for s in sentences if any(m in s.lower() for m in RATIONALE_MARKERS)), None)

    if stance:
        call = f"Go with the plan as written: \"{stance}\"."
    else:
        call = f"Take the plan's own framing of \"{text}\" as the default and confirm it."

    if rationale:
        why = f" The plan's stated reason is: {rationale}"
    elif node.get("heading_path"):
        why = f" It sits under \"{node['heading_path'][-1]}\", so it is a precondition for the rest of that branch."
    else:
        why = " It is load-bearing for the decisions that depend on it, so settle it first."

    return call + why


def build_turns(tree: dict[str, Any]) -> list[dict[str, Any]]:
    """One turn per decision, in interview order."""
    decisions = order_decisions(tree)
    total = len(decisions)
    turns: list[dict[str, Any]] = []
    for position, node in enumerate(decisions, 1):
        question, context = to_question(node["text"])
        turn = {
            "position": position,
            "total": total,
            "id": node["id"],
            "depth": node.get("depth", 0),
            "parent": node.get("parent"),
            "depends_on": node.get("depends_on", []),
            "question": question,
            "plan_context": context or None,
            "recommended_answer": recommended_answer(node, context),
            "explore_codebase_first": bool(node.get("resolvable_from_codebase")),
            "evidence_hint": node.get("evidence_hint"),
            "status": node.get("status", "open"),
            "answer": node.get("answer"),
        }
        turns.append(turn)
    return turns


def render_text(turns: list[dict[str, Any]]) -> str:
    """The per-turn block from SKILL.md's Output Pattern."""
    lines: list[str] = []
    for turn in turns:
        if turn["explore_codebase_first"]:
            lines.append(
                f"Q{turn['position']}/{turn['total']}: (do not ask yet) "
                f"{turn['evidence_hint']} Then confirm or overrule."
            )
        else:
            lines.append(f"Q{turn['position']}/{turn['total']}: {turn['question']}")
        lines.append(f"Recommended answer: {turn['recommended_answer']}")
        if turn["depends_on"]:
            lines.append(f"Depends on: {', '.join(turn['depends_on'])}")
        lines.append("")
    if not turns:
        lines.append(
            "No questions to ask. The tree extractor found no decision-shaped "
            "lines; give it a plan that states what is being chosen."
        )
    return "\n".join(lines).rstrip() + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="question_generator.py",
        description="Produce the ordered question list, with a recommendation per question.",
        epilog=(
            "One question per turn, depth-first, dependencies first. Every turn "
            "carries a recommendation: an unanswered question is the failure "
            "this script exists to prevent."
        ),
    )
    parser.add_argument("tree", help="JSON from decision_tree_extractor.py --json")
    parser.add_argument("-o", "--output", help="write to this file instead of stdout")
    parser.add_argument("--json", action="store_true", help="emit the turns as JSON")
    args = parser.parse_args(argv)

    turns = build_turns(load_tree(args.tree))
    text = json.dumps({"schema": "grill-me/questions/1", "turns": turns}, indent=2) \
        if args.json else render_text(turns)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as handle:
            handle.write(text + "\n" if not text.endswith("\n") else text)
        print(f"wrote {args.output} ({len(turns)} questions)", file=sys.stderr)
    else:
        print(text, end="" if text.endswith("\n") else "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
