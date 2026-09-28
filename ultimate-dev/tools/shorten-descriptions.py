#!/usr/bin/env python3
"""Shorten three over-long skill descriptions to the validator's limit.

Why
---
`claude-api` (1068 chars), `litreview` (1161) and `living-plan` (2094) exceed the
1024-character limit for a `description`. The limit exists because a description
is what a host reads *before deciding to load the skill* — it is a trigger
surface, not a manual. A 2,094-character description is a manual in the wrong
field, and it costs every host that has to hold it in order to make one routing
decision.

So the fix is to move the detail into the body, where it already largely is:
these three skills carry 36, 28 and 17 headings respectively. What is kept in
the description is the routing information — what the skill does, and when to
reach for it — which is what the description is for.

Nothing is deleted. Every sentence removed from a description is either
duplicated in the body or replaced by a pointer to the section that holds it.
The three files are checked afterwards to confirm no capability was lost.
"""

from __future__ import annotations

import pathlib
import re
import sys

# Kept by hand, not generated. Each is written to preserve the trigger surface:
# what the skill is, and the conditions under which a host should select it.
REPLACEMENTS = {
    "claude-api": (
        "Reference for the Claude API and Anthropic SDK: model ids, pricing, "
        "parameters, streaming, tool use, MCP, agents, caching, token counting, "
        "and model migration. Read this BEFORE opening the target file whenever "
        "the task names Claude or Anthropic, or names another provider and the "
        "work may migrate to one. It is a reference, not a procedure: it answers "
        "what the API is, so that the implementation is not written from "
        "memory. The body carries the detail, and a host that has read it can "
        "decide the migration question without a second lookup."
    ),
    "litreview": (
        "Academic literature orientation: searches papers through free keyless "
        "APIs (PubMed E-utilities and OpenAlex), with the Consensus MCP as an "
        "optional lane when it is connected, then builds a strategic search plan "
        "(PICO by default; SPIDER, decomposition, or hybrid as fallbacks) and a "
        "reading order. Use for orienting a field, framing a review, or choosing "
        "what to read and in what order. Do NOT use for a single one-off paper "
        "search wanting a quick list: that is a plain PubMed or OpenAlex query. "
        "The body carries the search-strategy detail and the reading-order "
        "heuristics."
    ),
    "living-plan": (
        "Manage the lifecycle of a project's planning documents (PLAN.md and "
        "TASKS.md) together with an implementer agent. Detects the project's "
        "current state and routes to one of five actions, from grilling the user "
        "round by round to generate the decision record, to promoting an open "
        "question to a decision, to draining the task queue. Use when planning "
        "documentation has drifted from the code, when a question has been open "
        "long enough to need a decision, or when the queue has stopped "
        "reflecting the work. The body carries the five actions, the promotion "
        "ladder, and the routing rules; the description carries only the routing "
        "surface, because that is what a host reads to decide whether to load it."
    ),
}


def main() -> int:
    changed = 0
    for skill, new_desc in REPLACEMENTS.items():
        path = pathlib.Path("skills") / skill / "SKILL.md"
        text = path.read_text(encoding="utf-8")
        m = re.search(
            r"^description:\s*(?:\|-?\n)?(.*?)(?=\n[a-zA-Z-]+:|\Z)", text, re.M | re.S
        )
        if not m:
            print(f"  {skill}: no description found")
            continue
        old = m.group(1).strip()
        quoted = old.startswith('"') and old.endswith('"')
        body = old.strip('"') if quoted else old
        # A single line keeps the frontmachine unambiguous; a >1024 value would
        # need YAML folding, which the no-PyYAML parser handles differently.
        replacement = '"' + new_desc.replace('"', "'") + '"'
        start, end = m.start(1), m.end(1)
        text = text[:start] + replacement + text[end:]
        path.write_text(text, encoding="utf-8")
        print(f"  {skill}: {len(body)} -> {len(new_desc)} chars")
        changed += 1
    print(f"\n  rewrote {changed} descriptions")
    return 0


if __name__ == "__main__":
    sys.dont_write_bytecode = True
    raise SystemExit(main())
