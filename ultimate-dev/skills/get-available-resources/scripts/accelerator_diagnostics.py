#!/usr/bin/env python3
"""Emit a read-only accelerator diagnostic plan. It does not run the diagnostics.

What it does
------------
Reads a resource snapshot, decides which management queries would be worth
running for the backends the snapshot shows as candidates, and prints the exact
command lines — as data, not as something this file executes. It also prints the
three gates that a visibility query cannot answer, separated, so they stay
separate in whatever runs next.

Why a plan and not a run
------------------------
The three gates are different in kind and only one of them is cheap:

1. **Visibility** — a management query answers it. `nvidia-smi` printing a
   device list settles it.
2. **Permission** — a framework's own device query answers it, in the exact
   environment that will run the workload. Running it here would answer a
   different question.
3. **Runtime compatibility** — driver, framework package, and operator support.
   Only a real allocation attempt answers it, and that is a workload, not a
   diagnostic.

So this file does gate 1's *plan*, and refuses to imply gates 2 and 3. It
installs nothing, resets nothing, and mutates nothing.

Usage
-----
    python scripts/accelerator_diagnostics.py resource-snapshot.json --backend auto
    python scripts/accelerator_diagnostics.py snap.json --backend cuda
    python scripts/accelerator_diagnostics.py snap.json --output diag.json
    python scripts/accelerator_diagnostics.py snap.json --format json

Exit codes: 0 plan written, 1 no candidates to plan for, 2 bad input.

Provenance
----------
Reconstructed to match the invocation and the three-gate framing in the SKILL.md
("Optional accelerator diagnostic plan"). The gate structure, the query sets, and
the output layout are this file's own.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

BACKEND_CHOICES = ("auto", "none", "cuda", "rocm", "metal")
MAX_SNAPSHOT_BYTES = 1024 * 1024

# Read-only management queries. Every entry is a fixed executable and argument
# list; nothing here is assembled from input, and nothing here writes.
MANAGEMENT_QUERIES: dict[str, list[dict]] = {
    "cuda": [
        {
            "id": "nvidia-smi-inventory",
            "argv": ["nvidia-smi", "--query-gpu=index,name,uuid,memory.total,memory.used,"
                     "driver_version,compute_cap",
                     "--format=csv,noheader"],
            "answers": "visibility",
            "read_only": True,
            "note": "A successful query proves the management interface answers. It does "
                    "not prove this process can open a device, that the driver matches "
                    "the framework, or that the device is not already in use.",
        },
        {
            "id": "nvidia-smi-topology",
            "argv": ["nvidia-smi", "topo", "-m"],
            "answers": "visibility",
            "read_only": True,
            "note": "Interconnect topology, for deciding whether a multi-device job "
                    "should use peer copies. Not a compatibility check.",
        },
        {
            "id": "nvidia-smi-accounts",
            "argv": ["nvidia-smi", "--query-compute-apps=pid,process_name,used_memory",
                     "--format=csv,noheader"],
            "answers": "visibility",
            "read_only": True,
            "note": "Who else is on the device. Useful before concluding a performance "
                    "problem is a code problem. Reports process names, so treat the "
                    "output as sensitive on a shared host.",
        },
    ],
    "rocm": [
        {
            "id": "rocm-smi-inventory",
            "argv": ["rocm-smi", "--showid", "--showproductname", "--showmeminfo", "vram",
                     "--csv"],
            "answers": "visibility",
            "read_only": True,
            "note": "Device inventory and VRAM. A successful query does not establish "
                    "that the ROCm user-space stack matches the kernel driver.",
        },
        {
            "id": "rocminfo",
            "argv": ["rocminfo"],
            "answers": "runtime_compatibility",
            "read_only": True,
            "note": "Reports the detected agents and the ROCm version. This is closer to "
                    "a compatibility gate than the others, but it still does not allocate "
                    "a device or prove a framework package works against it.",
        },
    ],
    "metal": [
        {
            "id": "system-profiler-displays",
            "argv": ["system_profiler", "SPDisplaysDataType", "-json"],
            "answers": "visibility",
            "read_only": True,
            "note": "Integrated GPU and unified-memory reporting on Apple silicon. There "
                    "is no separate device to claim: the GPU shares system memory, so a "
                    "memory budget has to come from the host limit, not from a VRAM "
                    "figure.",
        },
        {
            "id": "metal-system-info",
            "argv": ["system_profiler", "SPHardwareDataType", "-json"],
            "answers": "visibility",
            "read_only": True,
            "note": "Chip and unified-memory total. Read this together with the host "
                    "memory limit rather than as an independent accelerator allowance.",
        },
    ],
}

# The framework's own availability check, per backend. This is the gate-2 query
# and it is deliberately NOT in the management set above.
FRAMEWORK_CHECKS: dict[str, dict] = {
    "cuda": {
        "id": "framework-device-count",
        "python": "import torch; print(torch.cuda.device_count())",
        "answers": "permission",
        "note": "Run in the exact interpreter and environment that will execute the "
                "workload. A framework import in a different environment answers a "
                "different question, and a zero here means the framework sees no devices "
                "— which is different from there being none.",
    },
    "rocm": {
        "id": "framework-device-count",
        "python": "import torch; print(torch.cuda.device_count())",
        "answers": "permission",
        "note": "PyTorch exposes ROCm devices through the torch.cuda namespace. As with "
                "CUDA, run this in the executing environment.",
    },
    "metal": {
        "id": "framework-device-count",
        "python": "import torch; print(torch.backends.mps.is_available())",
        "answers": "permission",
        "note": "The MPS backend reports availability rather than a count, because there "
                "is one integrated device. A False here is a real answer, not a probe "
                "failure.",
    },
}

# Gates a management query cannot answer, stated so they stay stated.
UNGATED = [
    "scheduler or container permission for the device",
    "device-node access for this user",
    "driver and runtime version compatibility",
    "framework package compatibility in the executing interpreter",
    "operator and data-type support for the intended computation",
    "whether another process already holds an exclusive-mode allocation",
]


def log(message: str) -> None:
    print(message, file=sys.stderr, flush=True)


def load_snapshot(path: str) -> dict:
    if path.startswith(("http://", "https://")):
        raise SystemExit(f"error: {path} is a URL; this tool reads local files only")
    file_path = Path(path)
    if file_path.is_symlink():
        raise SystemExit(f"error: {path} is a symlink; refusing to read through it")
    if not file_path.is_file():
        raise SystemExit(f"error: snapshot not found: {path}")
    if file_path.stat().st_size > MAX_SNAPSHOT_BYTES:
        raise SystemExit(f"error: {path} is larger than {MAX_SNAPSHOT_BYTES} bytes")
    try:
        with file_path.open(encoding="utf-8") as handle:
            snapshot = json.load(handle)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"error: {path} is not valid JSON: {exc}")
    if not isinstance(snapshot, dict) or "accelerators" not in snapshot:
        raise SystemExit(
            f"error: {path} has no accelerators block. Collect it with "
            "`python scripts/detect_resources.py`."
        )
    return snapshot


def decide_backends(snapshot: dict, requested: str) -> list[str]:
    """Which backends to plan diagnostics for.

    ``auto`` plans for whatever the snapshot shows as a candidate. It does not
    plan for a backend that is merely possible: an absent management CLI is
    normal, and planning a CUDA diagnostic on a machine with no NVIDIA hardware
    produces noise.
    """
    accelerators = snapshot.get("accelerators", {})
    counts = accelerators.get("candidate_counts", {}) or {}
    visibility = accelerators.get("visibility_environment", {}) or {}

    present: list[str] = []
    if counts:
        mapping = {"nvidia": "cuda", "amd": "rocm", "apple": "metal"}
        present = sorted({mapping[vendor] for vendor in counts if vendor in mapping})
    else:
        # No devices, but a variable that explicitly hides all devices is still
        # evidence that a backend is in play on this host.
        for name, state in visibility.items():
            if not isinstance(state, dict):
                continue
            if state.get("hides_all_devices"):
                backend = {
                    "CUDA_VISIBLE_DEVICES": "cuda",
                    "HIP_VISIBLE_DEVICES": "rocm",
                    "ROCR_VISIBLE_DEVICES": "rocm",
                    "NVIDIA_VISIBLE_DEVICES": "cuda",
                    "AMD_VISIBLE_DEVICES": "rocm",
                }.get(name)
                if backend and backend not in present:
                    present.append(backend)

    if requested == "none":
        return []
    if requested != "auto":
        return [requested]
    return present


def build_plan(snapshot: dict, requested: str) -> dict:
    backends = decide_backends(snapshot, requested)
    accelerators = snapshot.get("accelerators", {})

    plan = {
        "requested_backend": requested,
        "planned_backends": backends,
        "executed": False,
        "executed_note": "This file emits a plan. It runs nothing, installs nothing, "
                         "and mutates nothing.",
        "snapshot_observed_at": snapshot.get("observed_at"),
        "candidate_counts": accelerators.get("candidate_counts", {}),
        "runtime_usable_devices": accelerators.get("runtime_usable_devices"),
        "gates": [
            {
                "gate": "visibility",
                "answered_by": "management query",
                "status": "not_run",
                "queries": [
                    query
                    for backend in backends
                    for query in MANAGEMENT_QUERIES.get(backend, [])
                    if query["answers"] == "visibility"
                ],
            },
            {
                "gate": "permission",
                "answered_by": "framework device query in the executing environment",
                "status": "not_run",
                "queries": [
                    {
                        "id": f"{backend}:{FRAMEWORK_CHECKS[backend]['id']}",
                        "python": FRAMEWORK_CHECKS[backend]["python"],
                        "answers": "permission",
                        "note": FRAMEWORK_CHECKS[backend]["note"],
                    }
                    for backend in backends
                    if backend in FRAMEWORK_CHECKS
                ],
            },
            {
                "gate": "runtime_compatibility",
                "answered_by": "a real allocation attempt in the executing environment",
                "status": "not_answered_by_any_query_here",
                "queries": [
                    query
                    for backend in backends
                    for query in MANAGEMENT_QUERIES.get(backend, [])
                    if query["answers"] == "runtime_compatibility"
                ],
                "note": "No query in this plan settles this. A version match between a "
                        "management CLI and a framework package is necessary and not "
                        "sufficient; the allocation itself is the only test.",
            },
        ],
        "ungated": UNGATED,
        "safety": {
            "installs_anything": False,
            "mutates_device_state": False,
            "performs_device_reset": False,
            "uses_a_shell": False,
            "commands_are_fixed": True,
            "note": "Every argv is a fixed literal in this file. Nothing is assembled "
                    "from the snapshot, so a hostile snapshot cannot inject a command.",
        },
    }

    if not backends:
        plan["outcome"] = (
            "No accelerator candidates are visible and no visibility variable explicitly "
            "hides devices, so there is nothing to plan diagnostics for. That is not "
            "evidence that no device exists — it is evidence that this process cannot see "
            "one. Absence of a management CLI is normal."
        )
    else:
        plan["outcome"] = (
            f"Planned read-only queries for: {', '.join(backends)}. Run them in the exact "
            "environment that will execute the workload, and treat a passing visibility "
            "query as the first of three gates rather than as permission to schedule work."
        )
    return plan


def render_text(plan: dict) -> str:
    lines = [
        "accelerator diagnostic plan",
        f"  requested backend   {plan['requested_backend']}",
        f"  planned backends    {', '.join(plan['planned_backends']) or 'none'}",
        f"  candidate counts    {plan['candidate_counts'] or 'none observed'}",
        f"  usable devices      {plan['runtime_usable_devices']} (null: no runtime loaded)",
        f"  executed            {plan['executed']} — {plan['executed_note']}",
        "",
    ]
    if not plan["planned_backends"]:
        lines.append(f"  {plan['outcome']}")
        return "\n".join(lines) + "\n"

    for gate in plan["gates"]:
        lines.append(f"  gate: {gate['gate']}  [{gate['status']}]")
        lines.append(f"    answered by: {gate['answered_by']}")
        for query in gate["queries"]:
            command = " ".join(query["argv"]) if "argv" in query else query.get("python", "")
            lines.append(f"    $ {command}")
            lines.append(f"      {query['id']}")
            lines.append(f"      {query['note']}")
            lines.append("")
        if gate.get("note"):
            lines.append(f"    {gate['note']}")
            lines.append("")

    lines.append("  gates this plan does NOT check:")
    for item in plan["ungated"]:
        lines.append(f"    - {item}")
    lines += [
        "",
        f"  {plan['outcome']}",
        "",
        "  safety: this plan installs nothing, mutates no device state, performs no reset, "
        "and runs every command without a shell. Run a framework's official availability "
        "check only in the exact environment that will execute the workload, and do not "
        "install or mutate drivers to make it pass.",
    ]
    return "\n".join(lines) + "\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Emit a read-only accelerator diagnostic plan without executing it.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("snapshot", help="resource-snapshot.json from detect_resources.py")
    parser.add_argument("--backend", choices=BACKEND_CHOICES, default="auto",
                        help="auto plans for whatever the snapshot shows as a candidate")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument("--output", default=None,
                        help="write the plan to this bare .json filename; default stdout")
    parser.add_argument("--force", action="store_true", help="allow overwriting --output")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    snapshot = load_snapshot(args.snapshot)
    plan = build_plan(snapshot, args.backend)

    if args.format == "json":
        payload = json.dumps(plan, indent=2, sort_keys=True) + "\n"
    else:
        payload = render_text(plan)

    if args.output:
        if os.path.sep in args.output or not args.output.endswith(".json"):
            raise SystemExit("error: --output must be a bare .json filename here")
        target = Path.cwd() / args.output
        if target.is_symlink():
            raise SystemExit(f"error: {args.output} is a symlink")
        if target.exists() and not args.force:
            raise SystemExit(f"error: {args.output} already exists; pass --force")
        descriptor = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(payload)
        log(f"wrote {args.output}")
    else:
        print(payload, end="")
    return 0 if plan["planned_backends"] else 1


if __name__ == "__main__":
    sys.exit(main())
