#!/usr/bin/env python3
"""Inventory one or more FCS datasets. Metadata by default, statistics on request.

What it does
------------
Prints, per dataset: the FCS version and byte offsets, the channel count and
event count, every channel's PnN / PnS / PnR / PnE / PnG, the derived
scatter / fluorescence / time index groups, the spillover string if present, and
the ANALYSIS segment.

By default it reads metadata only (``only_text=True``) and prints channel labels
without dumping TEXT or ANALYSIS values, and it refuses files over a
configurable size limit. Those three defaults are deliberate: an unrestricted
metadata dump of an FCS file can carry subject, sample, operator, institution,
and instrument serial numbers, and a full DATA read allocates
``event_count * channel_count * 8`` bytes of ``float64`` on top of the encoded
array. Inventory does not need either.

Usage
-----
    python scripts/inspect_fcs.py sample.fcs
    python scripts/inspect_fcs.py sample.fcs --include-text
    python scripts/inspect_fcs.py sample.fcs --stats
    python scripts/inspect_fcs.py sample.fcs --stats --raw
    python scripts/inspect_fcs.py *.fcs --format json --out inventory.json
    python scripts/inspect_fcs.py multi.fcs --list-data-sets
    python scripts/inspect_fcs.py sample.fcs --max-bytes 50000000

Exit codes: 0 every file inspected, 1 some failed, 2 bad input.

Provenance
----------
Reconstructed to match the invocations and the default posture documented in
this skill's SKILL.md under "Bundled Inspector", and the field semantics in
``references/fcs_semantics.md``. The actual parsing is delegated to the
installed ``flowio`` package (1.4.0), so every structural fact printed here is
flowio's own reading of the file, not a second parser. The report layout, the
size and memory guards, the statistics, and the offset-recovery warnings are
this file's own.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
from pathlib import Path

# A dataset larger than this is refused before flowio opens it. Normal
# FlowData construction reads the whole DATA segment into memory and
# as_array() then allocates a second float64 copy, so the guard is on the file
# size rather than on the event count, which is not known until after the read.
DEFAULT_MAX_BYTES = 512 * 1024 * 1024

# The additional float64 array as_array() allocates, per event per channel.
FLOAT64_BYTES_PER_VALUE = 8

# PnN substrings that conventionally mean scatter, fluorescence, or time. These
# are conveniences: vendor-specific panels do not always classify as expected,
# so the report says which convention matched and nothing more.
SCATTER_HINTS = ("fsc", "ssC", "ssc", "fsc-a", "fsc-h", "ssc-a", "ssc-h", "scatter")
FLUORO_HINTS = ("fl", "fl1", "fl2", "fl3", "fl4", "cd", "pe", "apc", "vi", "fitc", "pacific")
TIME_HINTS = ("time", "timestep")

# Offset-recovery flags. Each one changes which bytes are read as events, so the
# report names any that are in effect rather than using them silently.
OFFSET_FLAGS = (
    "ignore_offset_error",
    "ignore_offset_discrepancy",
    "use_header_offsets",
)

# ANALYSIS and TEXT keys that usually carry identifying information. Their
# presence is reported; their values are only printed with --include-text.
IDENTIFYING_KEY_HINTS = (
    "tube", "patient", "subject", "sample", "operator", "institution", "insurer",
    "hospital", "clinic", "physician", "doctor", "technician", "serial", "sn:",
    "sponsor", "study", "site", "volunteer", "donor", "name", "email", "phone",
    "address", "birth", "sex:", "gender",
)


def log(message: str) -> None:
    print(message, file=sys.stderr, flush=True)


def import_flowio():
    """Import flowio, or explain how to get it."""
    try:
        from flowio import FlowData, read_multiple_data_sets
    except ImportError:
        raise SystemExit(
            "error: flowio is not installed. Run `uv run --no-project --with "
            '"flowio==1.4.0" python scripts/inspect_fcs.py <file>`, or '
            "`uv pip install flowio==1.4.0` in your environment."
        )
    return FlowData, read_multiple_data_sets


def active_offset_flags() -> list[str]:
    """Which recovery flags the caller turned on, read from this process's argv."""
    argv = set(sys.argv[1:])
    return [name for name in OFFSET_FLAGS if f"--{name.replace('_', '-')}" in argv]


def looks_identifying(key: str) -> bool:
    lowered = key.lower()
    return any(hint in lowered for hint in IDENTIFYING_KEY_HINTS)


def classify(labels: list[str]) -> dict[str, list[str]]:
    """Group channel labels by convention. A convenience, clearly labelled as one."""
    groups: dict[str, list[str]] = {"scatter": [], "fluorescence": [], "time": []}
    for label in labels:
        if not label:
            continue
        lowered = label.lower()
        if any(hint in lowered for hint in TIME_HINTS):
            groups["time"].append(label)
        elif any(hint in lowered for hint in SCATTER_HINTS):
            groups["scatter"].append(label)
        elif any(hint in lowered for hint in FLUORO_HINTS):
            groups["fluorescence"].append(label)
    return groups


def channel_rows(flow, null_channels: list[str]) -> list[dict]:
    """One row per channel, labelled with both index systems.

    flowio exposes one-based parameter numbers through ``channels`` and zero-based
    indices through the array columns and the ``*_indices`` attributes. Both are
    printed, because a mismatch between them is a common and silent source of
    off-by-one errors in analysis code.
    """
    pnn = list(getattr(flow, "pnn_labels", []) or [])
    pns = list(getattr(flow, "pns_labels", []) or [])
    channels = getattr(flow, "channels", {}) or {}

    rows: list[dict] = []
    for array_index, label in enumerate(pnn):
        parameter_number = array_index + 1
        entry = channels.get(parameter_number, {}) or {}
        rows.append({
            "parameter_number": parameter_number,
            "array_index": array_index,
            "pnn": label,
            "pns": pns[array_index] if array_index < len(pns) else "",
            "pnr": entry.get("PnR", ""),
            "pne": entry.get("PnE", ""),
            "png": entry.get("PnG", ""),
        })
    if null_channels:
        rows.append({
            "_null_channels_supplied": null_channels,
            "_note": "null_channel_list excludes these from the derived index groups; "
                     "it does not remove columns from the event data",
        })
    return rows


def statistics(flow, preprocess: bool) -> list[dict]:
    """Per-channel finite-value statistics over the array.

    ``preprocess=True`` applies flowio's time scaling, log conversion from PnE
    and PnR, and gain division. ``preprocess=False`` reads the encoded values as
    stored. Both are worth looking at: the difference between them is exactly
    what the metadata says the instrument did, and a channel whose preprocessed
    values are wildly out of scale usually has bad PnE or PnR rather than bad
    data.
    """
    try:
        array = flow.as_array(preprocess=preprocess)
    except Exception as exc:
        log(f"warning: as_array(preprocess={preprocess}) failed: {exc}")
        return []

    pnn = list(getattr(flow, "pnn_labels", []) or [])
    rows: list[dict] = []
    for index in range(array.shape[1]):
        column = array[:, index]
        finite = column[~_isnan(column)]
        if finite.size == 0:
            rows.append({
                "array_index": index,
                "pnn": pnn[index] if index < len(pnn) else f"channel_{index + 1}",
                "n_events": int(array.shape[0]),
                "n_finite": 0,
                "note": "no finite values; a constant channel, a null channel, or a "
                        "logically offset channel with no PnE metadata",
            })
            continue
        rows.append({
            "array_index": index,
            "pnn": pnn[index] if index < len(pnn) else f"channel_{index + 1}",
            "n_events": int(array.shape[0]),
            "n_finite": int(finite.size),
            "min": float(finite.min()),
            "max": float(finite.max()),
            "mean": float(finite.mean()),
            "median": float(_median(finite)),
            "p01": float(_quantile(finite, 0.01)),
            "p99": float(_quantile(finite, 0.99)),
            "std": float(finite.std()) if finite.size > 1 else 0.0,
            "n_infinite": int(_isinf(column).sum()),
        })
    return rows


def _isnan(column):
    import numpy as np

    return np.isnan(column)


def _isinf(column):
    import numpy as np

    return np.isinf(column)


def _quantile(values, probability: float) -> float:
    import numpy as np

    return float(np.quantile(values, probability))


def _median(values) -> float:
    import numpy as np

    return float(np.median(values))


def inspect_one(
    path: str,
    include_text: bool,
    with_stats: bool,
    raw: bool,
    null_channel_list: list[str],
) -> dict:
    """Build the report for one dataset."""
    FlowData, _ = import_flowio()
    report: dict = {"file": os.path.abspath(path)}

    kwargs: dict = {"only_text": not with_stats}
    if null_channel_list:
        kwargs["null_channel_list"] = null_channel_list
    for flag in active_offset_flags():
        kwargs[flag] = True

    try:
        flow = FlowData(path, **kwargs)
    except Exception as exc:
        report["error"] = f"{type(exc).__name__}: {exc}"
        return report

    report.update(_structural_report(flow, include_text, data_loaded=not with_stats))

    if with_stats:
        report["statistics"] = {
            "source": "encoded" if raw else "preprocessed",
            "note": (
                "Encoded values are the bytes as stored. Preprocessed values apply "
                "time scaling from the timestep keyword, log conversion from PnE and PnR, "
                "and gain division from PnG. flowio does not apply spillover "
                "compensation, arcsinh or logicle transformation, normalization, "
                "debris removal, doublet exclusion, or gating."
            ),
            "channels": statistics(flow, preprocess=not raw),
        }
    return report


def _structural_report(flow, include_text: bool, data_loaded: bool = True) -> dict:
    """Header, TEXT, ANALYSIS, and channel inventory for one FlowData."""
    header = getattr(flow, "header", {}) or {}
    text = getattr(flow, "text", {}) or {}
    analysis = getattr(flow, "analysis", {}) or {}

    identifying = sorted(key for key in list(text) + list(analysis) if looks_identifying(key))

    report: dict = {
        # flowio exposes the version on the FlowData and repeats it in the
        # normalized header, not in TEXT under a "version" key.
        "fcs_version": getattr(flow, "version", None) or header.get("version"),
        "offsets": {
            key: value for key, value in sorted(header.items())
            if key.endswith(("_start", "_stop")) or key == "version"
        },
        "channel_count": getattr(flow, "channel_count", None),
        "event_count": getattr(flow, "event_count", None),
        "data_type": getattr(flow, "data_type", None),
        "file_size": getattr(flow, "file_size", None),
        "text_key_count": len(text),
        "analysis_key_count": len(analysis),
        "possibly_identifying_keys": identifying,
        "data_loaded": data_loaded,
    }

    labels = list(getattr(flow, "pnn_labels", []) or [])
    derived = {
        "scatter_indices": list(getattr(flow, "scatter_indices", []) or []),
        "fluoro_indices": list(getattr(flow, "fluoro_indices", []) or []),
        "time_indices": list(getattr(flow, "time_indices", []) or []),
    }
    report["derived_index_groups"] = derived
    report["label_based_groups"] = {
        name: values for name, values in classify(labels).items() if values
    }
    report["null_channels_supplied"] = list(getattr(flow, "null_channels", []) or [])

    spillover = text.get("spillover") or text.get("spill")
    if spillover:
        report["spillover"] = {
            "present": True,
            "first_item": spillover.split(",")[0] if isinstance(spillover, str) else None,
            "length": len(spillover) if isinstance(spillover, str) else None,
            "note": "flowio exposes the string but does not validate it and does not apply "
                    "it. Confirm the labels map to the event columns and the dimensions "
                    "match the parameter count before passing it downstream.",
        }

    if include_text:
        report["text"] = dict(text)
        report["analysis"] = dict(analysis)
        report["include_text_warning"] = (
            "This dump may contain subject, sample, operator, institution, and instrument "
            "identifiers. Read it before sharing it. flowio also strips every '$' from the "
            "decoded segment before splitting, so a literal '$' inside a value is lost and "
            "this mapping is not a lossless metadata archive."
        )
    else:
        report["text_keys"] = sorted(text)
        report["analysis_keys"] = sorted(analysis)

    report["channels"] = channel_rows(flow, report["null_channels_supplied"])
    return report


def _first(mapping: dict, key: str):
    value = mapping.get(key)
    if isinstance(value, (list, tuple)) and value:
        return value[0]
    return value


def _human_bytes(size) -> str:
    if not isinstance(size, (int, float)) or size <= 0:
        return "unknown"
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024 or unit == "GB":
            return f"{size:.1f} {unit}" if unit != "B" else f"{int(size)} B"
        size /= 1024
    return f"{size:.1f} GB"


def list_data_sets(path: str) -> int:
    """Report how many datasets a legacy multi-dataset file holds."""
    _FlowData, read_multiple_data_sets = import_flowio()
    try:
        flows = read_multiple_data_sets(path)
    except Exception as exc:
        log(f"error: {path}: {exc}")
        return 1
    flows = list(flows)
    print(f"{path}: {len(flows)} data set(s)")
    for index, flow in enumerate(flows):
        print(f"  [{index}] channels={getattr(flow, 'channel_count', '?')} "
              f"events={getattr(flow, 'event_count', '?')}")
    if len(flows) > 1:
        print(
            "\nFCS 3.1 deprecated $NEXTDATA. This file is a legacy multi-dataset file; "
            "inspect each data set separately, and note that the multi-dataset helper "
            "cannot reuse a closed file handle for its second data set in flowio 1.4.0 — "
            "pass paths, not open handles."
        )
    return 0


def render_text(reports: list[dict]) -> str:
    """A readable inventory. One block per dataset."""
    lines: list[str] = []
    for report in reports:
        lines.append("=" * 78)
        lines.append(report["file"])
        if "error" in report:
            lines.append(f"  ERROR: {report['error']}")
            lines.append("")
            continue

        lines.append(f"  FCS version          {report.get('fcs_version')}")
        lines.append(f"  channels             {report.get('channel_count')}")
        lines.append(f"  event count          {report.get('event_count')}")
        lines.append(f"  data type            {report.get('data_type')}")
        lines.append(f"  file size            {_human_bytes(report.get('file_size'))}")
        lines.append(f"  TEXT keys            {report.get('text_key_count')}")
        lines.append(f"  ANALYSIS keys        {report.get('analysis_key_count')}")
        lines.append(f"  DATA segment loaded  {report.get('data_loaded')}")

        offsets = report.get("offsets") or {}
        if offsets:
            lines.append("  offsets:")
            for key, value in sorted(offsets.items()):
                lines.append(f"    {key:<28} {value}")

        spillover = report.get("spillover")
        if spillover:
            lines.append(
                f"  spillover            present, {spillover['length']} chars, "
                f"first item = {spillover['first_item']!r}"
            )
            lines.append(f"    {spillover['note']}")

        if report.get("possibly_identifying_keys"):
            lines.append(
                "  possibly identifying keys (values withheld): "
                + ", ".join(report["possibly_identifying_keys"][:12])
                + ("..." if len(report["possibly_identifying_keys"]) > 12 else "")
            )

        derived = report.get("derived_index_groups") or {}
        if any(derived.values()):
            lines.append("  derived index groups (zero-based, flowio's inference):")
            for name, values in derived.items():
                if values:
                    lines.append(f"    {name:<20} {values}")
        label_groups = report.get("label_based_groups") or {}
        if label_groups:
            lines.append("  label-based groups (this script's convention matching):")
            for name, values in label_groups.items():
                lines.append(f"    {name:<20} {values}")
            lines.append(
                "    These are conventions, not a substitute for checking the instrument "
                "panel; vendor labels do not always classify as expected."
            )

        if report.get("null_channels_supplied"):
            lines.append(
                f"  null channels        {report['null_channels_supplied']} "
                "(excluded from the derived groups; columns are still present)"
            )

        lines.append("  channels:")
        for row in report.get("channels", []):
            if "pnn" not in row:
                lines.append(f"    {row}")
                continue
            line = (f"    P{row['parameter_number']:<3} idx {row['array_index']:<3} "
                    f"{row['pnn'][:28]:<28}")
            if row.get("pns"):
                line += f" S={row['pns'][:24]}"
            if row.get("pnr"):
                line += f" R={row['pnr']}"
            if row.get("pne"):
                line += f" E={row['pne']}"
            if row.get("png"):
                line += f" G={row['png']}"
            lines.append(line)

        statistics_block = report.get("statistics")
        if statistics_block:
            lines.append("")
            lines.append(f"  statistics ({statistics_block['source']} values):")
            header = (f"    {'idx':<5}{'PnN':<26}{'n':>10}{'min':>14}{'p50':>14}"
                      f"{'max':>14}{'mean':>14}{'std':>14}")
            lines.append(header)
            for row in statistics_block["channels"]:
                if "min" not in row:
                    lines.append(
                        f"    {row['array_index']:<5}{row['pnn'][:24]:<26}"
                        f"{row['n_finite']:>10}  {row.get('note', '')}"
                    )
                    continue
                lines.append(
                    f"    {row['array_index']:<5}{row['pnn'][:24]:<26}{row['n_finite']:>10}"
                    f"{row['min']:>14.4g}{row['median']:>14.4g}{row['max']:>14.4g}"
                    f"{row['mean']:>14.4g}{row['std']:>14.4g}"
                )
            lines.append(f"    {statistics_block['note']}")

        flags = active_offset_flags()
        if flags:
            lines.append("")
            lines.append(
                "  WARNING: offset recovery in effect: " + ", ".join(flags)
            )
            lines.append(
                "    Each of these changes which bytes are read as events. Validate the "
                "event count, the channel distributions, and any known control before "
                "trusting the data, and record why the file needed the recovery."
            )

        if report.get("text"):
            lines.append("")
            lines.append("  TEXT:")
            for key in sorted(report["text"]):
                lines.append(f"    {key} = {report['text'][key]}")
            lines.append(f"  {report['include_text_warning']}")
        elif "text_keys" in report:
            lines.append("")
            lines.append("  TEXT keys (values withheld; use --include-text to print them):")
            lines.append("    " + ", ".join(report["text_keys"]))

        lines.append("")

    lines.append("=" * 78)
    lines.append(
        "Nothing here validates the data scientifically. flowio does not compensate "
        "spillover, apply arcsinh or logicle transformation, normalize between files, "
        "identify acquisition anomalies, remove debris or doublets, or gate "
        "populations. Use a higher-level package such as FlowKit for any of those, and "
        "keep the uncompensated values and the original metadata for provenance."
    )
    return "\n".join(lines) + "\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Inventory FCS datasets: metadata by default, statistics on request.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("files", nargs="+", help="FCS files to inspect")
    parser.add_argument(
        "--include-text", action="store_true",
        help="print every normalized TEXT and ANALYSIS value; review for identifiers first",
    )
    parser.add_argument(
        "--stats", action="store_true",
        help="load events and compute per-channel finite-value statistics",
    )
    parser.add_argument(
        "--raw", action="store_true",
        help="with --stats, use encoded values instead of preprocessed ones",
    )
    parser.add_argument(
        "--null-channel", action="append", default=[], dest="null_channels",
        help="PnN label to exclude from the derived index groups; repeatable",
    )
    parser.add_argument(
        "--list-data-sets", action="store_true",
        help="report how many datasets each file holds, using read_multiple_data_sets",
    )
    parser.add_argument(
        "--max-bytes", type=int, default=DEFAULT_MAX_BYTES,
        help="refuse files larger than this before flowio opens them",
    )
    parser.add_argument("--format", choices=("text", "json"), default="text", help="output format")
    parser.add_argument("--out", default=None, help="write the report here; default stdout")
    return parser


def check_size(path: str, limit: int) -> str | None:
    """Refuse an oversized file before anything is read into memory."""
    if path.startswith(("http://", "https://")):
        return f"{path} is a URL; this inspector reads local files only"
    file_path = Path(path)
    if not file_path.is_file():
        return f"{path} is not a file"
    size = file_path.stat().st_size
    if size > limit:
        estimate = size / (1024 * 1024)
        return (
            f"{path} is {estimate:.0f} MB, over the --max-bytes limit of "
            f"{limit / (1024 * 1024):.0f} MB. Loading it would hold the DATA segment and "
            f"a float64 copy (about {size * FLOAT64_BYTES_PER_VALUE // (1024 * 1024)} MB "
            "of array alone) in memory. Raise the limit deliberately, or use a workflow "
            "that streams, which flowio 1.4.0 does not offer."
        )
    return None


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.max_bytes < 1:
        raise SystemExit("error: --max-bytes must be positive")

    if args.list_data_sets:
        failures = 0
        for path in args.files:
            problem = check_size(path, args.max_bytes)
            if problem:
                log(f"error: {problem}")
                failures += 1
                continue
            failures += list_data_sets(path)
        return 1 if failures else 0

    if args.raw and not args.stats:
        log("note: --raw only affects the values --stats computes, so it does nothing "
            "without --stats.")

    reports: list[dict] = []
    failures = 0
    for path in args.files:
        problem = check_size(path, args.max_bytes)
        if problem:
            reports.append({"file": os.path.abspath(path), "error": problem})
            failures += 1
            continue
        try:
            report = inspect_one(
                path, args.include_text, args.stats, args.raw, args.null_channels
            )
        except SystemExit:
            raise
        except Exception as exc:
            report = {"file": os.path.abspath(path), "error": f"{type(exc).__name__}: {exc}"}
        if "error" in report:
            failures += 1
        reports.append(report)

    if args.format == "json":
        text = json.dumps({"datasets": reports}, indent=2, default=str) + "\n"
    else:
        text = render_text(reports)

    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
        log(f"wrote {args.out}")
    else:
        print(text, end="")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
