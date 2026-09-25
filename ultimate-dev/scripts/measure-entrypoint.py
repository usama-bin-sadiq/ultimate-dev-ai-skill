#!/usr/bin/env python3
"""Measure and budget always-loaded agent entrypoints."""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_LIMITS = {
    "SKILL.md": 2400,
    "AGENTS.md": 3200,
    "AGENT.md": 200,
    "agents/orchestrator.md": 2400,
}


def measure() -> dict[str, Any]:
    entries = []
    for relative, limit in DEFAULT_LIMITS.items():
        path = ROOT / relative
        text = path.read_text(encoding="utf-8")
        words = len(text.split())
        entries.append({
            "file": relative,
            "lines": len(text.splitlines()),
            "words": words,
            "bytes": len(text.encode("utf-8")),
            "approx_tokens": math.ceil(words * 1.3),
            "word_limit": limit,
            "within_limit": words <= limit,
        })
    total_words = sum(item["words"] for item in entries)
    return {
        "entries": entries,
        "total_words": total_words,
        "approx_total_tokens": math.ceil(total_words * 1.3),
        "word_budget": sum(DEFAULT_LIMITS.values()),
        "within_budget": all(item["within_limit"] for item in entries),
        "note": "Approximate token counts are a local budget signal, not a host-model measurement.",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args(argv)
    result = measure()
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        for item in result["entries"]:
            marker = "PASS" if item["within_limit"] else "FAIL"
            print(f"{marker} {item['file']}: {item['words']} words / limit {item['word_limit']}")
        print(f"TOTAL: {result['total_words']} words; approx {result['approx_total_tokens']} tokens")
    return 1 if args.strict and not result["within_budget"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
