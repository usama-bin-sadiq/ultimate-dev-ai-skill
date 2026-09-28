#!/usr/bin/env python3
"""Plan workers and memory for a workload from a validated resource snapshot.

What it does
------------
Reads a snapshot produced by ``detect_resources.py``, applies one documented
heuristic for the requested workload class, and prints a plan. It performs no
work: it does not allocate, benchmark, spawn, or measure anything.

The one thing this file is careful about
----------------------------------------
Process workers and native threads multiply. Eight Python worker processes each
starting eight BLAS or OpenMP threads is 64 threads on an 8-core allocation, and
the result is contention that looks like slow code. So the plan reports
``suggested_workers`` and ``threads_per_worker`` *together*, and the
``threads_per_worker`` value is derived from the worker count so the product
stays inside the observed capacity.

Accelerators are reported as candidates only. ``--accelerator cuda`` means "plan
for a CUDA candidate backend if one is visible", never "a CUDA device is
available and usable": visibility does not establish permission, device-node
access, driver compatibility, framework compatibility, or operator support.

Usage
-----
    python scripts/plan_workload.py resource-snapshot.json \\
        --workload cpu --tasks 100 --memory-per-worker-mib 2048
    python scripts/plan_workload.py snap.json --workload mixed --workers 4
    python scripts/plan_workload.py snap.json --workload io --accelerator any --outdir .
    python scripts/plan_workload.py snap.json --workload cpu --output plan.json

Exit codes: 0 plan written, 1 unusable snapshot, 2 bad input.

Provenance
----------
Reconstructed to match the invocations and the flags the SKILL.md documents, and
to consume the schema 1.1 snapshot from ``references/snapshot_schema.md``. The
worker heuristics, the memory arithmetic, and the accelerator-candidate decision
logic are this file's own.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

WORKLOADS = ("cpu", "mixed", "io")
ACCELERATOR_CHOICES = ("none", "any", "cuda", "rocm", "metal")
MAX_SNAPSHOT_BYTES = 1024 * 1024
MIB = 1024 * 1024

# I/O-bound work can usefully oversubscribe, because the workers spend their
# time blocked rather than running. This is a bound, not a licence, and the
# output labels it as a heuristic.
MAX_IO_OVERSUBSCRIPTION = 32


def log(message: str) -> None:
    print(message, file=sys.stderr, flush=True)


def load_snapshot(path: str) -> dict:
    """Read one regular, non-symlink JSON file, bounded in size."""
    if path.startswith(("http://", "https://")):
        raise SystemExit(f"error: {path} is a URL; this planner reads local files only")
    file_path = Path(path)
    if file_path.is_symlink():
        raise SystemExit(f"error: {path} is a symlink; refusing to read through it")
    if not file_path.is_file():
        raise SystemExit(f"error: snapshot not found: {path}")
    if file_path.stat().st_size > MAX_SNAPSHOT_BYTES:
        raise SystemExit(
            f"error: {path} is larger than {MAX_SNAPSHOT_BYTES} bytes; it is not a snapshot"
        )
    try:
        with file_path.open(encoding="utf-8") as handle:
            snapshot = json.load(handle)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"error: {path} is not valid JSON: {exc}")
    if not isinstance(snapshot, dict):
        raise SystemExit(f"error: {path} must contain a JSON object")

    for field in ("schema_version", "cpu", "memory"):
        if field not in snapshot:
            raise SystemExit(
                f"error: {path} has no {field!r}. Validate it first with "
                f"`python scripts/snapshot_tools.py validate {path}`."
            )
    if snapshot["schema_version"] != "1.1":
        raise SystemExit(
            f"error: snapshot schema is {snapshot['schema_version']!r}, this planner reads 1.1"
        )
    return snapshot


def capacity_cores(snapshot: dict) -> float | None:
    return snapshot.get("cpu", {}).get("effective", {}).get("capacity_cores")


def worker_ceiling(snapshot: dict) -> int | None:
    return snapshot.get("cpu", {}).get("effective", {}).get("worker_ceiling")


def hard_limit_bytes(snapshot: dict) -> int | None:
    return snapshot.get("memory", {}).get("effective", {}).get("hard_limit_bytes")


def available_bytes(snapshot: dict) -> int | None:
    return snapshot.get("memory", {}).get("effective", {}).get("available_bytes")


def choose_workers(
    snapshot: dict,
    workload: str,
    tasks: int,
    explicit: int | None,
) -> tuple[int, list[str]]:
    """Workers for this workload, and the reasons that led to the number.

    Every constraint that bound the answer is reported, because a worker count
    with no derivation is a number nobody can argue with and therefore nobody
    can check.
    """
    reasons: list[str] = []
    ceiling = worker_ceiling(snapshot)
    capacity = capacity_cores(snapshot)

    if ceiling is None and capacity is None:
        # No CPU observation at all. Refusing is the honest answer: "as many as
        # you like" is what unlimited means, and we do not know it.
        return 1, [
            "no finite CPU capacity was observed, so the plan falls back to a single "
            "worker. Null means unknown, not unlimited. Collect a snapshot where the "
            "affinity set or a cgroup limit is visible before planning a parallel run."
        ]

    limit = ceiling if ceiling is not None else max(1, int(capacity or 1))
    if ceiling is not None:
        reasons.append(
            f"cpu.effective.worker_ceiling = {ceiling} "
            f"(capacity {capacity} cores, limited by "
            f"{', '.join(snapshot['cpu']['effective'].get('limiting_sources', [])) or 'unknown'})"
        )
    else:
        reasons.append(f"cpu.effective.capacity_cores = {capacity}, rounded down to {limit}")

    if workload == "io":
        limit = min(limit * 4, MAX_IO_OVERSUBSCRIPTION)
        reasons.append(
            f"io workload: bounded oversubscription by 4, capped at "
            f"{MAX_IO_OVERSUBSCRIPTION}. This is a heuristic: it assumes the workers "
            "spend most of their time blocked, which the snapshot cannot verify."
        )

    if explicit is not None:
        if explicit < 1:
            raise SystemExit("error: --workers must be at least 1")
        if explicit > limit:
            log(
                f"warning: --workers {explicit} exceeds the observed limit of {limit}. "
                "Using the observed limit instead. Oversubscribing does not go faster, "
                "and it makes the run harder to reason about when it goes wrong."
            )
        else:
            reasons.append(f"--workers {explicit} requested explicitly, within the limit")
        limit = min(explicit, limit)

    if tasks > 0:
        if limit > tasks:
            limit = max(1, tasks)
            reasons.append(f"capped at --tasks {tasks}: more workers than tasks is idle overhead")

    return max(1, limit), reasons


def choose_threads(workers: int, capacity: float | None, workload: str) -> tuple[int, list[str]]:
    """Native threads per worker, chosen so workers x threads stays inside capacity.

    BLAS and OpenMP default to one thread per core in most builds, so a process
    pool alone will already oversubscribe. Deriving the thread count from the
    worker count is the only way to avoid needing an environment variable the
    user has to remember.
    """
    reasons: list[str] = []
    budget = max(1, int(capacity or workers))

    if workload == "io":
        threads = 1
        reasons.append("io workload: 1 thread per worker; the worker is blocked, not computing")
        return threads, reasons

    threads = max(1, budget // max(1, workers))
    if threads == 1:
        reasons.append(
            f"1 thread per worker: {workers} workers against {budget} cores of capacity "
            "leaves no room for native threading"
        )
    else:
        reasons.append(
            f"{threads} threads per worker: {workers} x {threads} = "
            f"{workers * threads}, inside the observed capacity of {budget}"
        )
    reasons.append(
        "Set OMP_NUM_THREADS, OPENBLAS_NUM_THREADS, MKL_NUM_THREADS, and "
        "NUMEXPR_NUM_THREADS to this value if the library ignores the default"
    )
    return threads, reasons


def memory_plan(
    snapshot: dict,
    workers: int,
    per_worker_mib: int | None,
    reserve_mib: int,
) -> dict:
    """Worker memory budget against the effective hard limit and availability."""
    if per_worker_mib is not None and per_worker_mib < 1:
        raise SystemExit("error: --memory-per-worker-mib must be at least 1")

    hard = hard_limit_bytes(snapshot)
    available = available_bytes(snapshot)
    ceiling = available if available is not None else hard

    plan: dict = {
        "hard_limit_bytes": hard,
        "available_bytes": available,
        "reserve_memory_mib": reserve_mib,
        "unknown_ceiling": ceiling is None,
    }

    if ceiling is None:
        plan["fits"] = None
        plan["note"] = (
            "No finite memory ceiling was observed, so this plan cannot say whether the "
            "workload fits. Null means unknown, not unlimited. Collect a snapshot with "
            "host or cgroup memory visible before committing a large run."
        )
        if per_worker_mib:
            plan["requested_total_mib"] = workers * per_worker_mib
        return plan

    ceiling_mib = ceiling // MIB
    reserve = max(0, reserve_mib)
    budget_mib = max(0, ceiling_mib - reserve)

    plan["ceiling_mib"] = ceiling_mib
    plan["budget_mib"] = budget_mib
    plan["ceiling_sources"] = snapshot["memory"]["effective"].get("available_limiting_sources") or \
        snapshot["memory"]["effective"].get("hard_limit_sources") or []

    if per_worker_mib is None:
        plan["fits"] = None
        plan["note"] = (
            f"{budget_mib} MiB of the {ceiling_mib} MiB ceiling is available for workers "
            "after the reserve. Pass --memory-per-worker-mib to get a fit check."
        )
        return plan

    requested = workers * per_worker_mib
    plan["requested_total_mib"] = requested
    plan["memory_per_worker_mib"] = per_worker_mib
    plan["fits"] = requested <= budget_mib

    if plan["fits"]:
        headroom = budget_mib - requested
        plan["headroom_mib"] = headroom
        plan["note"] = (
            f"{workers} workers x {per_worker_mib} MiB = {requested} MiB, inside "
            f"{budget_mib} MiB of budget with {headroom} MiB of headroom."
        )
    else:
        affordable = max(1, budget_mib // per_worker_mib)
        plan["affordable_workers"] = affordable
        plan["note"] = (
            f"{workers} workers x {per_worker_mib} MiB = {requested} MiB exceeds the "
            f"{budget_mib} MiB budget. At this per-worker figure the budget supports "
            f"{affordable} worker(s). Lower --memory-per-worker-mib, lower "
            f"--reserve-memory-mib, or run in batches. Note also that "
            f"memory.high is a throttle boundary, not a hard cap: "
            f"{snapshot['memory']['effective'].get('pressure_threshold_bytes') is not None and 'set' or 'not set'}"
        )
    return plan


def accelerator_plan(snapshot: dict, choice: str) -> dict:
    """A candidate-backend decision, never a usability claim."""
    accelerators = snapshot.get("accelerators", {})
    devices = accelerators.get("devices", []) or []
    counts = accelerators.get("candidate_counts", {}) or {}

    plan: dict = {
        "requested": choice,
        "runtime_usable_devices": accelerators.get("runtime_usable_devices"),
        "candidate_counts": counts,
        "decision": "none",
        "rationale": "",
        "gates_not_checked": [
            "scheduler or container permission for the device",
            "device-node access",
            "driver and runtime version compatibility",
            "framework package compatibility in this interpreter",
            "operator and data-type support",
        ],
    }

    if choice == "none":
        plan["rationale"] = "no accelerator backend requested"
        return plan

    if not devices:
        plan["rationale"] = (
            "No accelerator candidates were visible in the snapshot. Absence of a "
            "management CLI is normal and is not evidence that no device exists; it is "
            "evidence that this process cannot see one."
        )
        return plan

    wanted = None if choice == "any" else choice
    matching = [
        device for device in devices
        if wanted is None or device.get("backend_candidate") == wanted
    ]

    if not matching:
        plan["rationale"] = (
            f"Accelerator candidates are visible ({', '.join(sorted(counts))}) but none "
            f"maps to the {wanted!r} backend. Visible backends: "
            + ", ".join(sorted({d.get('backend_candidate', '?') for d in devices}))
        )
        return plan

    plan["decision"] = wanted or "any_visible_backend"
    plan["candidate_count"] = len(matching)
    plan["rationale"] = (
        f"{len(matching)} {plan['decision']} candidate(s) are visible to the management "
        "query. That is visibility, not usability. Every gate above is unchecked: run the "
        "framework's official availability check in the exact environment that will "
        "execute the workload, and do not install or mutate drivers to make it pass."
    )
    plan["hint"] = (
        "Accelerator_diagnostics.py emits the exact read-only management queries and the "
        "separate gates, without running them."
    )
    return plan


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Plan workers and memory for a workload from a resource snapshot.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("snapshot", help="resource-snapshot.json from detect_resources.py")
    parser.add_argument("--workload", choices=WORKLOADS, required=True,
                        help="cpu for compute, mixed for a blend, io for blocked work")
    parser.add_argument("--tasks", type=int, default=0,
                        help="number of tasks, used to cap the worker count; 0 for unknown")
    parser.add_argument("--workers", type=int, default=None,
                        help="explicit upper bound on workers; the observed limit still applies")
    parser.add_argument("--memory-per-worker-mib", type=int, default=None,
                        help="expected resident memory per worker, for a fit check")
    parser.add_argument("--reserve-memory-mib", type=int, default=0,
                        help="memory kept outside the worker budget for the OS and the parent")
    parser.add_argument("--accelerator", choices=ACCELERATOR_CHOICES, default="none",
                        help="request a candidate backend decision; never asserts usability")
    parser.add_argument("--output", default=None,
                        help="write the plan to this bare .json filename; default stdout")
    parser.add_argument("--force", action="store_true", help="allow overwriting --output")
    return parser


def write_plan(payload: str, filename: str, force: bool) -> None:
    if os.path.sep in filename or (os.altsep and os.altsep in filename) or not filename.endswith(".json"):
        raise SystemExit(f"error: --output must be a bare .json filename in the current directory")
    target = Path.cwd() / filename
    if target.is_symlink():
        raise SystemExit(f"error: {filename} is a symlink; refusing to write through it")
    if target.exists() and not force:
        raise SystemExit(f"error: {filename} already exists; pass --force to overwrite it")
    descriptor = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
        handle.write(payload + "\n")


def render_text(plan: dict) -> str:
    lines = [
        "workload plan",
        f"  observed at         {plan['snapshot_observed_at']}",
        f"  snapshot complete   {plan['snapshot_completeness']}",
        f"  CPU capacity        {plan['cpu']['capacity_cores']} scheduling cores",
        f"  worker ceiling      {plan['cpu']['worker_ceiling']}",
        f"  limiting sources    {', '.join(plan['cpu']['limiting_sources']) or 'unknown'}",
        "",
        f"  suggested workers   {plan['workers']['suggested_workers']}",
        f"  threads per worker  {plan['workers']['threads_per_worker']}",
        f"  total native threads {plan['workers']['workers_x_threads']}",
        "",
        f"  memory ceiling      {plan['memory'].get('ceiling_mib', 'unknown')} MiB",
        f"  worker budget       {plan['memory'].get('budget_mib', 'unknown')} MiB",
    ]
    memory = plan["memory"]
    if memory.get("requested_total_mib") is not None:
        verdict = {True: "fits", False: "DOES NOT FIT", None: "not checked"}[memory["fits"]]
        lines.append(f"  requested           {memory['requested_total_mib']} MiB  ({verdict})")
    lines += ["", f"  {memory.get('note', '')}", ""]
    for reason in plan["workers"]["reasons"]:
        lines.append(f"  - {reason}")
    lines += ["", f"  {plan['workers']['thread_note']}", ""]

    accelerator = plan["accelerator"]
    lines += [
        f"  accelerator         {accelerator['decision']}",
        f"  usable devices      {accelerator['runtime_usable_devices']} (null: no runtime was loaded)",
        f"  {accelerator['rationale']}",
    ]
    if accelerator["decision"] != "none":
        lines += ["", "  gates this plan did NOT check:"]
        for gate in accelerator["gates_not_checked"]:
            lines.append(f"    - {gate}")

    lines += [
        "",
        "  This plan performs no work. Benchmark the real representative workload before "
        "trusting the worker count, and stay inside the scheduler and container limits you "
        "actually have rather than the ones you hope for.",
    ]
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.tasks < 0:
        raise SystemExit("error: --tasks must not be negative")

    snapshot = load_snapshot(args.snapshot)
    capacity = capacity_cores(snapshot)
    workers, reasons = choose_workers(snapshot, args.workload, args.tasks, args.workers)
    threads, thread_reasons = choose_threads(workers, capacity, args.workload)

    plan = {
        "snapshot_observed_at": snapshot.get("observed_at"),
        "snapshot_completeness": snapshot.get("completeness"),
        "workload": args.workload,
        "cpu": {
            "capacity_cores": capacity,
            "worker_ceiling": worker_ceiling(snapshot),
            "limiting_sources": snapshot.get("cpu", {}).get("effective", {}).get(
                "limiting_sources", []),
        },
        "workers": {
            "suggested_workers": workers,
            "threads_per_worker": threads,
            "workers_x_threads": workers * threads,
            "tasks": args.tasks or None,
            "reasons": reasons,
            "thread_note": " ".join(thread_reasons),
        },
        "memory": memory_plan(snapshot, workers, args.memory_per_worker_mib,
                              args.reserve_memory_mib),
        "accelerator": accelerator_plan(snapshot, args.accelerator),
    }

    payload = json.dumps(plan, indent=2, sort_keys=True, default=str)
    if args.output:
        try:
            write_plan(payload, args.output, args.force)
        except SystemExit as exc:
            print(str(exc), file=sys.stderr)
            return 1
        log(f"wrote {args.output}")
    else:
        print(render_text(plan))
    return 0


if __name__ == "__main__":
    sys.exit(main())
