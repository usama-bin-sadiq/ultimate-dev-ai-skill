#!/usr/bin/env python3
"""Generate an HTML report from run_loop.py output.

Takes the JSON written by ``run_loop.py`` and renders one row per description
attempt, with a pass/fail cell per eval. Train and held-out evals are shown
separately, and the summary states how the loop exited and whether the
description actually changed.

The report is a static file. Nothing here starts a server or opens a browser.

Usage:
    python scripts/generate_report.py results.json -o report.html
    cat results.json | python scripts/generate_report.py - -o report.html
"""

import argparse
import html
import json
import sys
from pathlib import Path

if __package__ in (None, ""):  # allow `python scripts/generate_report.py`
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def _split_queries(data: dict) -> tuple[list[dict], list[dict]]:
    """Recover (train, held-out) query descriptors from the loop history.

    ``run_loop`` evaluates train and held-out evals in one batch, so the split
    is recovered from the recorded ``test_size``.
    """
    history = data.get("history") or []
    if not history:
        return [], []

    results = history[0].get("results") or []
    queries = [
        {"query": r.get("query", ""), "should_trigger": bool(r.get("should_trigger", True))}
        for r in results
    ]
    test_size = data.get("test_size") or 0
    if not test_size:
        return queries, []
    split = max(0, len(queries) - test_size)
    return queries[:split], queries[split:]


def _cell(record: dict | None, test: bool = False) -> str:
    """One result cell. Renders n/a rather than a number when unmeasured."""
    record = record or {}
    did_pass = record.get("pass")
    runs = record.get("runs", 0)
    observed = record.get("trigger_observed")
    rate = f"{observed}/{runs}" if observed is not None else "n/a"

    if did_pass is None:
        css_class, icon = "skip", "-"
    else:
        css_class, icon = ("pass", "&#10003;") if did_pass else ("fail", "&#10007;")
    extra = " test-result" if test else ""
    return (
        f'                <td class="result{extra} {css_class}">{icon}'
        f'<span class="rate">{html.escape(rate)}</span></td>\n'
    )


def generate_html(data: dict, auto_refresh: bool = False, skill_name: str = "") -> str:
    """Render the loop output as a standalone HTML document."""
    history = data.get("history", [])
    title_prefix = html.escape(skill_name + " \u2014 ") if skill_name else ""
    train_queries, test_queries = _split_queries(data)
    best_iteration = data.get("best_iteration")

    refresh_tag = '    <meta http-equiv="refresh" content="5">\n' if auto_refresh else ""

    html_parts = ["""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
""" + refresh_tag + """    <title>""" + title_prefix + """Skill Description Optimization</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@500;600&family=Lora:wght@400;500&display=swap" rel="stylesheet">
    <style>
        body {
            font-family: 'Lora', Georgia, serif;
            max-width: 100%;
            margin: 0 auto;
            padding: 20px;
            background: #faf9f5;
            color: #141413;
        }
        h1 { font-family: 'Poppins', sans-serif; color: #141413; }
        .explainer {
            background: white;
            padding: 15px;
            border-radius: 6px;
            margin-bottom: 20px;
            border: 1px solid #e8e6dc;
            color: #b0aea5;
            font-size: 0.875rem;
            line-height: 1.6;
        }
        .summary {
            background: white;
            padding: 15px;
            border-radius: 6px;
            margin-bottom: 20px;
            border: 1px solid #e8e6dc;
        }
        .summary p { margin: 5px 0; }
        .best { color: #788c5d; font-weight: bold; }
        .table-container {
            overflow-x: auto;
            width: 100%;
        }
        table {
            border-collapse: collapse;
            background: white;
            border: 1px solid #e8e6dc;
            border-radius: 6px;
            font-size: 12px;
            min-width: 100%;
        }
        th, td {
            padding: 8px;
            text-align: left;
            border: 1px solid #e8e6dc;
            white-space: normal;
            word-wrap: break-word;
        }
        th {
            font-family: 'Poppins', sans-serif;
            background: #141413;
            color: #faf9f5;
            font-weight: 500;
        }
        th.test-col {
            background: #6a9bcc;
        }
        th.query-col { min-width: 200px; }
        td.description {
            font-family: monospace;
            font-size: 11px;
            word-wrap: break-word;
            max-width: 400px;
        }
        td.result {
            text-align: center;
            font-size: 16px;
            min-width: 40px;
        }
        td.test-result {
            background: #f0f6fc;
        }
        .pass { color: #788c5d; }
        .fail { color: #c44; }
        .rate {
            font-size: 9px;
            color: #b0aea5;
            display: block;
        }
        tr:hover { background: #faf9f5; }
        .score {
            display: inline-block;
            padding: 2px 6px;
            border-radius: 4px;
            font-weight: bold;
            font-size: 11px;
        }
        .score-good { background: #eef2e8; color: #788c5d; }
        .score-ok { background: #fef3c7; color: #d97706; }
        .score-bad { background: #fceaea; color: #c44; }
        .train-label { color: #b0aea5; font-size: 10px; }
        .test-label { color: #6a9bcc; font-size: 10px; font-weight: bold; }
        .best-row { background: #f5f8f2; }
    td.result.skip { color: #b0aea5; }
    td.result .rate { font-size: 10px; opacity: 0.8; }
        th.positive-col { border-bottom: 3px solid #788c5d; }
        th.negative-col { border-bottom: 3px solid #c44; }
        th.test-col.positive-col { border-bottom: 3px solid #788c5d; }
        th.test-col.negative-col { border-bottom: 3px solid #c44; }
        .legend { font-family: 'Poppins', sans-serif; display: flex; gap: 20px; margin-bottom: 10px; font-size: 13px; align-items: center; }
        .legend-item { display: flex; align-items: center; gap: 6px; }
        .legend-swatch { width: 16px; height: 16px; border-radius: 3px; display: inline-block; }
        .swatch-positive { background: #141413; border-bottom: 3px solid #788c5d; }
        .swatch-negative { background: #141413; border-bottom: 3px solid #c44; }
        .swatch-test { background: #6a9bcc; }
        .swatch-train { background: #141413; }
    </style>
</head>
<body>
    <h1>""" + title_prefix + """Skill Description Optimization</h1>
    <div class="explainer">
        <strong>Optimizing your skill's description.</strong> This page updates automatically as agent runtime tests different versions of your skill's description. Each row is an iteration — a new description attempt. The columns show test queries: green checkmarks mean the skill triggered correctly (or correctly didn't trigger), red crosses mean it got it wrong. The "Train" score shows performance on queries used to improve the description; the "Test" score shows performance on held-out queries the optimizer hasn't seen. When it's done, agent runtime will apply the best-performing description to your skill.
    </div>
"""]

    # Summary section
    best_train = data.get("best_train") or {}
    best_test = data.get("best_test") or None
    if best_test:
        score_text = (
            f"{best_test.get('passed', 0)}/{best_test.get('total', 0)} held-out"
        )
    else:
        score_text = (
            f"{best_train.get('passed', 0)}/{best_train.get('total', 0)} train"
            " (no held-out set)"
        )
    changed = "yes" if data.get("improved") else "no"
    html_parts.append(f"""
    <div class="summary">
        <p><strong>Original:</strong> {html.escape(str(data.get('original_description', 'N/A')))}</p>
        <p class="best"><strong>Best:</strong> {html.escape(str(data.get('best_description', 'N/A')))}</p>
        <p><strong>Best score:</strong> {html.escape(score_text)} |
           <strong>Best iteration:</strong> {data.get('best_iteration', 'n/a')} |
           <strong>Description changed:</strong> {changed}</p>
        <p><strong>Iterations:</strong> {data.get('iterations_run', 0)} |
           <strong>Train evals:</strong> {data.get('train_size', 0)} |
           <strong>Held-out evals:</strong> {data.get('test_size', 0)} |
           <strong>Exit:</strong> {html.escape(str(data.get('exit_reason', 'n/a')))}</p>
    </div>
""")

    # Legend
    html_parts.append("""
    <div class="legend">
        <span style="font-weight:600">Query columns:</span>
        <span class="legend-item"><span class="legend-swatch swatch-positive"></span> Should trigger</span>
        <span class="legend-item"><span class="legend-swatch swatch-negative"></span> Should NOT trigger</span>
        <span class="legend-item"><span class="legend-swatch swatch-train"></span> Train</span>
        <span class="legend-item"><span class="legend-swatch swatch-test"></span> Test</span>
    </div>
""")

    # Table header
    html_parts.append("""
    <div class="table-container">
    <table>
        <thead>
            <tr>
                <th>Iter</th>
                <th>Train</th>
                <th>Test</th>
                <th class="query-col">Description</th>
""")

    # Add column headers for train queries
    for qinfo in train_queries:
        polarity = "positive-col" if qinfo["should_trigger"] else "negative-col"
        html_parts.append(f'                <th class="{polarity}">{html.escape(qinfo["query"])}</th>\n')

    # Add column headers for test queries (different color)
    for qinfo in test_queries:
        polarity = "positive-col" if qinfo["should_trigger"] else "negative-col"
        html_parts.append(f'                <th class="test-col {polarity}">{html.escape(qinfo["query"])}</th>\n')

    html_parts.append("""            </tr>
        </thead>
        <tbody>
""")

    # Add rows for each iteration
    for record in history:
        iteration = record.get("iteration", "?")
        train = record.get("train") or {}
        test = record.get("test") or {}
        description = record.get("description", "")

        def score_class(score: dict) -> str:
            total = score.get("total", 0)
            if not total:
                return "score-bad"
            ratio = score.get("passed", 0) / total
            if ratio >= 0.8:
                return "score-good"
            if ratio >= 0.5:
                return "score-ok"
            return "score-bad"

        metrics = record.get("trigger_metrics") or {}
        trigger_note = (
            f"trigger P={metrics.get('precision')} R={metrics.get('recall')}"
            if metrics.get("precision") is not None
            else "trigger detection not configured"
        )
        row_class = "best-row" if iteration == best_iteration else ""
        test_cell = (
            f'<span class="score {score_class(test)}">'
            f'{test.get("passed", 0)}/{test.get("total", 0)}</span>'
            if test else '<span class="score score-bad">n/a</span>'
        )
        html_parts.append(f"""            <tr class="{row_class}">
                <td>{html.escape(str(iteration))}</td>
                <td><span class="score {score_class(train)}">{train.get('passed', 0)}/{train.get('total', 0)}</span></td>
                <td>{test_cell}</td>
                <td class="description">{html.escape(str(description))}
                    <div class="train-label">{html.escape(trigger_note)}</div></td>
""")

        by_query = {r.get("query"): r for r in record.get("results") or []}
        for qinfo in train_queries:
            html_parts.append(_cell(by_query.get(qinfo["query"])))
        for qinfo in test_queries:
            html_parts.append(_cell(by_query.get(qinfo["query"]), test=True))

        html_parts.append("            </tr>\n")

    html_parts.append("""        </tbody>
    </table>
    </div>
""")

    html_parts.append("""
</body>
</html>
""")

    return "".join(html_parts)


def main():
    parser = argparse.ArgumentParser(description="Generate HTML report from run_loop output")
    parser.add_argument("input", help="Path to JSON output from run_loop.py (or - for stdin)")
    parser.add_argument("-o", "--output", default=None, help="Output HTML file (default: stdout)")
    parser.add_argument("--skill-name", default="", help="Skill name to include in the report title")
    args = parser.parse_args()

    if args.input == "-":
        data = json.load(sys.stdin)
    else:
        data = json.loads(Path(args.input).read_text())

    html_output = generate_html(data, skill_name=args.skill_name)

    if args.output:
        Path(args.output).write_text(html_output)
        print(f"Report written to {args.output}", file=sys.stderr)
    else:
        print(html_output)


if __name__ == "__main__":
    main()
