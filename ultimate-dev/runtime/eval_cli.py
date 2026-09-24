"""Small provider-neutral evaluation CLI.

The CLI intentionally has no provider flags or credentials. It runs scripted
cases in no-provider mode unless a Python host embeds ``EvaluationRunner`` and
injects its callables.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from .evaluation import EvaluationRunner, load_cases


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run Ultimate-Dev scripted evaluation cases")
    parser.add_argument("--cases", type=Path, help="JSON/YAML case file; omitted means an empty run")
    parser.add_argument("--output", type=Path, help="write redacted JSON results to this path")
    parser.add_argument("--trials", type=int, default=1, help="trials per case (default: 1)")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    cases = load_cases(args.cases) if args.cases is not None else None
    result = EvaluationRunner(cases=cases, trials=args.trials).run()
    rendered = json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    if args.output is None:
        print(rendered, end="")
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    return 0


if __name__ == "__main__":  # pragma: no cover - exercised by CLI smoke tests
    raise SystemExit(main())
