#!/usr/bin/env python3
"""Generate a suppressed aggregate cohort table from aggregate cells.

What it does
------------
Reads a JSON declaration of groups, characteristics, and aggregate cell counts,
applies a disclosure policy, and writes a releasable table as CSV plus a JSON
record of what was suppressed and why.

Disclosure controls, in order:
1. **Primary suppression** — a nonzero cell below ``minimum_cell_size`` is
   suppressed, as is a zero cell smaller than the threshold.
2. **Complementary suppression** — if a row has exactly one suppressed cell and
   the rest sum to a published row total, that one value is recoverable by
   subtraction, so a second cell is suppressed to break it.
3. **Group-level suppression** — a group whose denominator is below the threshold
   is suppressed entirely, because every cell in it is disclosive by proxy.

It also reports denominators and missingness, and never emits a raw value that
was suppressed.

What the default threshold is not
---------------------------------
The default of 11 is a conservative operational safeguard. It is not a HIPAA rule,
not a universal small-cell rule, and not a guarantee. It does not address
differencing across releases, linkage, longitudinal, geographic, genomic, or
rare-combination risk. The data steward selects the policy and privacy review
signs off.

Usage
-----
    python3 scripts/cohort_table_generator.py assets/aggregate_cohort_table_template.json
    python3 scripts/cohort_table_generator.py table.json --minimum-cell-size 5 --out-dir release/

Input is aggregate cells only. Row-level data is refused: common person-level keys
are rejected on load. Not for patient care or live clinical use.

Provenance
----------
Reconstructed from the Disclosure Controls section of references/cohort_evaluation.md
and the Aggregate Disclosure section of references/privacy_and_disclosure.md. The
suppression algorithm and the default of 11 are this file's own.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

MAX_FILE_BYTES = 4 * 1024 * 1024
MAX_GROUPS = 200
MAX_ROWS = 100_000
MAX_CELLS = 200_000
DEFAULT_MINIMUM_CELL_SIZE = 11
SUPPRESSED = "suppressed"

PERSON_LEVEL_KEYS = frozenset({
    "patient_id", "patientid", "mrn", "medical_record_number", "ssn", "dob", "date_of_birth",
    "address", "phone", "email", "name", "first_name", "last_name", "free_text", "note",
    "notes", "narrative", "identifier", "subject_id", "person_id", "row_id", "record_id",
})


class TableError(Exception):
    """A problem with the input declaration; reported as a finding, not a crash."""


def log(message: str) -> None:
    print(message, file=sys.stderr, flush=True)


def reject_person_level(node, path: str = "$") -> None:
    """Refuse row-level or person-linked keys in the data-bearing sections.

    Scoped to ``cells`` and ``groups``: those are where a per-person record would
    arrive. The schema sections are declared structure and use keys like
    ``name`` for a characteristic label, which is not a person-level field.
    """
    if isinstance(node, dict):
        for key, value in node.items():
            if str(key).lower() in PERSON_LEVEL_KEYS:
                raise TableError(
                    f"{path}.{key}: row-level or person-linked keys are not accepted. "
                    "Supply aggregate cells only; a cell with one record in it is a "
                    "disclosure, not a cell."
                )
            reject_person_level(value, f"{path}.{key}")
    elif isinstance(node, list):
        for index, value in enumerate(node[:MAX_CELLS]):
            reject_person_level(value, f"{path}[{index}]")


def check_for_person_level(declaration: dict) -> None:
    """Apply the row-level screen to the parts of the declaration that hold data."""
    for key in ("cells", "groups"):
        if key in declaration:
            reject_person_level(declaration[key], f"$.{key}")


def load_declaration(path: str) -> dict:
    if path.startswith(("http://", "https://", "file://")):
        raise SystemExit(f"error: {path} looks like a URL; this helper reads local files only")
    file_path = Path(path)
    if not file_path.is_file():
        raise SystemExit(f"error: table declaration not found: {path}")
    if file_path.stat().st_size > MAX_FILE_BYTES:
        raise SystemExit(f"error: {path} is larger than {MAX_FILE_BYTES} bytes")
    try:
        with file_path.open(encoding="utf-8") as handle:
            declaration = json.load(handle)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"error: {path} is not valid JSON: {exc}")
    if not isinstance(declaration, dict):
        raise SystemExit("error: the table declaration must be a JSON object")
    try:
        check_for_person_level(declaration)
    except TableError as exc:
        raise SystemExit(f"error: {exc}")
    return declaration


def resolve_policy(declaration: dict, override: int | None) -> dict:
    policy = declaration.get("disclosure_policy")
    policy = policy if isinstance(policy, dict) else {}
    minimum = override if override is not None else policy.get("minimum_cell_size", DEFAULT_MINIMUM_CELL_SIZE)
    try:
        minimum = int(minimum)
    except (TypeError, ValueError):
        raise SystemExit(f"error: minimum_cell_size must be an integer, got {minimum!r}")
    if minimum < 1:
        raise SystemExit("error: minimum_cell_size must be at least 1")
    return {
        "minimum_cell_size": minimum,
        "primary_suppression": bool(policy.get("primary_suppression", True)),
        "complementary_suppression": bool(policy.get("complementary_suppression", True)),
        "group_level_suppression": bool(policy.get("group_level_suppression", True)),
        "policy_source": policy.get("policy_source", "not documented"),
        "approved_by": policy.get("approved_by", "not documented"),
    }


def build_grid(declaration: dict) -> tuple[list[str], list[dict], dict]:
    """Index the aggregate cells by (characteristic, category, group)."""
    groups = declaration.get("groups")
    if not isinstance(groups, list) or not groups:
        raise TableError("groups must be a non-empty list of group names")
    if len(groups) > MAX_GROUPS:
        raise TableError(f"{len(groups)} groups exceeds the cap of {MAX_GROUPS}")
    groups = [str(group) for group in groups]

    characteristics = declaration.get("characteristics")
    if not isinstance(characteristics, list) or not characteristics:
        raise TableError("characteristics must be a non-empty list")

    rows: list[dict] = []
    for characteristic in characteristics:
        if not isinstance(characteristic, dict):
            raise TableError("each characteristic must be an object with name and categories")
        name = characteristic.get("name")
        if not name:
            raise TableError("each characteristic needs a name")
        if not isinstance(name, str) or len(name) > 200:
            raise TableError(f"characteristic name {name!r} is missing or too long")
        for category in characteristic.get("categories", []) or []:
            rows.append({
                "characteristic": name,
                "category": str(category),
                "kind": characteristic.get("type", "categorical"),
            })
    if len(rows) > MAX_ROWS:
        raise TableError(f"{len(rows)} table rows exceeds the cap of {MAX_ROWS}")

    cells = declaration.get("cells")
    if not isinstance(cells, list) or not cells:
        raise TableError("cells must be a non-empty list of aggregate counts")
    if len(cells) > MAX_CELLS:
        raise TableError(f"{len(cells)} cells exceeds the cap of {MAX_CELLS}")

    grid: dict[tuple[str, str, str], dict] = {}
    for index, cell in enumerate(cells):
        if not isinstance(cell, dict):
            raise TableError(f"cells[{index}] must be an object")
        key = (str(cell.get("characteristic")), str(cell.get("category")), str(cell.get("group")))
        if key in grid:
            raise TableError(f"cells[{index}] duplicates the cell for {key}")
        if key[2] not in groups:
            raise TableError(f"cells[{index}] names group {key[2]!r}, which is not in groups")
        try:
            count = int(cell.get("n", 0))
            denominator = int(cell.get("denominator", 0))
        except (TypeError, ValueError):
            raise TableError(f"cells[{index}] n and denominator must be integers")
        if count < 0 or denominator < 0:
            raise TableError(f"cells[{index}] counts must not be negative")
        if count > denominator:
            raise TableError(
                f"cells[{index}] has n={count} against a denominator of {denominator}; a cell "
                "cannot exceed its denominator"
            )
        grid[key] = {"n": count, "denominator": denominator}
    return groups, rows, grid


def apply_suppression(
    groups: list[str],
    rows: list[dict],
    grid: dict,
    policy: dict,
) -> tuple[list[dict], list[dict]]:
    """Apply the three suppression passes, returning released rows and the log."""
    minimum = policy["minimum_cell_size"]
    log_entries: list[dict] = []
    state: dict[tuple[str, str, str], str] = {}

    # Group-level: a denominator below the threshold discloses every cell in it.
    denominators: dict[str, int] = {}
    for (characteristic, category, group), value in grid.items():
        denominators[group] = max(denominators.get(group, 0), value["denominator"])
    suppressed_groups: set[str] = set()
    if policy["group_level_suppression"]:
        for group in groups:
            if denominators.get(group, 0) < minimum:
                suppressed_groups.add(group)
                log_entries.append({
                    "level": "group",
                    "group": group,
                    "reason": f"denominator {denominators.get(group, 0)} is below the minimum "
                              f"cell size of {minimum}",
                })

    # Primary: any cell below the threshold, zero included, is withheld.
    for (characteristic, category, group), value in grid.items():
        if group in suppressed_groups:
            state[(characteristic, category, group)] = SUPPRESSED
            continue
        if value["n"] < minimum:
            state[(characteristic, category, group)] = SUPPRESSED
            if policy["primary_suppression"]:
                log_entries.append({
                    "level": "primary",
                    "cell": {"characteristic": characteristic, "category": category, "group": group},
                    "n": value["n"],
                    "reason": f"n={value['n']} is below the minimum cell size of {minimum}",
                })

    # Complementary: one suppressed cell in a row is recoverable from the row total.
    if policy["complementary_suppression"]:
        for row in rows:
            for group in groups:
                key = (row["characteristic"], row["category"], group)
                if key not in grid or state.get(key) == SUPPRESSED:
                    continue
                row_keys = [
                    (other["characteristic"], other["category"], group)
                    for other in rows
                    if other["characteristic"] == row["characteristic"]
                ]
                hidden = [k for k in row_keys if k in grid and state.get(k) == SUPPRESSED]
                visible = [k for k in row_keys if k in grid and state.get(k) != SUPPRESSED]
                if len(hidden) == 1 and visible:
                    # Suppress the smallest visible cell in the row.
                    victim = min(visible, key=lambda k: grid[k]["n"])
                    state[victim] = SUPPRESSED
                    log_entries.append({
                        "level": "complementary",
                        "cell": {
                            "characteristic": victim[0],
                            "category": victim[1],
                            "group": victim[2],
                        },
                        "n": grid[victim]["n"],
                        "reason": "a second cell in the row is suppressed so the first cannot be "
                                  "recovered by subtraction from the row total",
                    })

    released = []
    for row in rows:
        for group in groups:
            key = (row["characteristic"], row["category"], group)
            if key not in grid:
                continue
            released.append({
                "characteristic": row["characteristic"],
                "category": row["category"],
                "group": group,
                "value": SUPPRESSED if state.get(key) == SUPPRESSED else grid[key]["n"],
                "denominator": SUPPRESSED if group in suppressed_groups else grid[key]["denominator"],
                "suppressed": state.get(key) == SUPPRESSED,
            })
    return released, log_entries


def write_csv(released: list[dict], groups: list[str], out_dir: Path) -> list[Path]:
    """Write the released table and its denominators as two CSVs.

    Denominators are reported separately rather than inside the count table so a
    reader can see each cell's base without inferring it from a row total, which
    is the subtraction the suppression rule is designed to prevent.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    index: dict[tuple[str, str], dict[str, dict]] = {}
    for cell in released:
        index.setdefault((cell["characteristic"], cell["category"]), {})[cell["group"]] = cell

    keys = list(index)
    path = out_dir / "cohort_table.csv"
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["characteristic", "category", *groups])
        for (characteristic, category), cells in index.items():
            writer.writerow([
                characteristic,
                category,
                *[cells.get(group, {}).get("value", "") for group in groups],
            ])

    denom_path = out_dir / "cohort_table_denominators.csv"
    with denom_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["characteristic", "category", *groups])
        for (characteristic, category), cells in index.items():
            writer.writerow([
                characteristic,
                category,
                *[cells.get(group, {}).get("denominator", "") for group in groups],
            ])
    return [path, denom_path]


def render_text(declaration: dict, released: list[dict], suppression: list[dict], policy: dict) -> str:
    """A readable summary for the reviewer, with the suppression ledger attached."""
    metadata = declaration.get("table_metadata", {})
    groups = [str(group) for group in declaration.get("groups", [])]
    lines = [
        f"table: {metadata.get('title', 'untitled')}",
        f"design: {metadata.get('design', 'not stated')}",
        f"population: {metadata.get('population', 'not stated')}",
        f"minimum cell size: {policy['minimum_cell_size']} "
        f"(policy source: {policy['policy_source']}; approved by: {policy['approved_by']})",
        "",
    ]

    width = max((len(group) for group in groups), default=10)
    lines.append("characteristic / category".ljust(46) + "  " + "  ".join(g.rjust(width) for g in groups))
    seen: list[tuple[str, str]] = []
    for cell in released:
        key = (cell["characteristic"], cell["category"])
        if key not in seen:
            seen.append(key)
    for characteristic, category in seen:
        cells = {c["group"]: c for c in released
                 if c["characteristic"] == characteristic and c["category"] == category}
        label = f"{characteristic} / {category}"[:44]
        values = "  ".join(
            (str(cells[group]["value"]) if group in cells else "-").rjust(width) for group in groups
        )
        lines.append(label.ljust(46) + "  " + values)

    lines += ["", f"suppressed cells: {sum(1 for c in released if c['suppressed'])} of {len(released)}"]
    for entry in suppression:
        cell = entry.get("cell", {})
        where = (
            f"{cell.get('characteristic', '?')} / {cell.get('category', '?')} / {cell.get('group', '?')}"
            if cell else entry.get("group", "?")
        )
        lines.append(f"  {entry['level']}: {where} - {entry['reason']}")

    lines += [
        "",
        "The minimum cell size above is an operational safeguard, not a HIPAA rule and not a "
        "guarantee. It does not address differencing across releases, linkage, longitudinal, "
        "geographic, genomic, or rare-combination risk. This table supports no action for any "
        "person and is not for patient care or live clinical use.",
    ]
    return "\n".join(lines) + "\n"


def generate(declaration: dict, minimum_override: int | None) -> tuple[str, list[dict], dict]:
    policy = resolve_policy(declaration, minimum_override)
    groups, rows, grid = build_grid(declaration)
    released, suppression = apply_suppression(groups, rows, grid, policy)
    return render_text(declaration, released, suppression, policy), released, suppression


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Generate a suppressed aggregate cohort table from aggregate cells.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("declaration", help="local JSON table declaration")
    parser.add_argument("--minimum-cell-size", type=int, default=None,
                        help="override the declared minimum cell size")
    parser.add_argument("--out-dir", default=None, help="write cohort_table.csv here")
    parser.add_argument("--json", dest="as_json", action="store_true",
                        help="emit the released cells and suppression log as JSON")
    args = parser.parse_args(argv)

    declaration = load_declaration(args.declaration)
    try:
        text, released, suppression = generate(declaration, args.minimum_cell_size)
    except TableError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    print(text, end="")
    if args.as_json:
        Path(args.out_dir or ".").mkdir(parents=True, exist_ok=True)
        payload = json.dumps(
            {"cells": released, "suppression": suppression}, indent=2
        ) + "\n"
        print(payload, end="")
    elif args.out_dir:
        paths = write_csv(released, [str(g) for g in declaration.get("groups", [])], Path(args.out_dir))
        for path in paths:
            log(f"wrote {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
