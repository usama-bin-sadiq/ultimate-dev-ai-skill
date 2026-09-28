#!/usr/bin/env python3
"""Collect a redacted resource snapshot for the current process.

Emits one JSON object matching schema ``1.1`` (see
``references/snapshot_schema.md``) to stdout, or to one private local file when
``--output`` is given.

What this does and does not measure
-----------------------------------
It measures what is *available to this process*, and it keeps five different
facts apart rather than collapsing them into one number:

* host inventory — what the machine has;
* process affinity — which CPUs this process may run on;
* cgroup v2 limits — what the enclosing control group caps;
* scheduler allocation — what a batch system says this job owns;
* effective limits — the minimum of the finite positive observations above.

Those are not the same quantity. A host with 128 logical CPUs inside a cgroup
with a quota of 1.5 has one and a half cores of CPU *time*, not one and a half
physical cores; affinity constrains placement and quota constrains bandwidth. A
visible GPU is a candidate, never a usable device.

Safety contract
---------------
* No stress test, benchmark, large allocation, write probe, device reset, driver
  install, or clock or power change.
* No environment dump. Only the named Slurm and accelerator variables are read,
  and their *values* are never emitted.
* No hostname, absolute path, cgroup path, job ID, device UUID, or PCI address.
* A missing observation is null, meaning unknown. It is never turned into zero
  and never turned into unlimited.
* Subprocesses use fixed executable and argument tuples, no shell, short
  timeouts, and bounded output.
* A failed probe becomes a warning and a null field. It never erases the
  observations that did succeed.

Usage
-----
    python scripts/detect_resources.py
    python scripts/detect_resources.py --output resource-snapshot.json
    python scripts/detect_resources.py --skip-accelerators
    python scripts/detect_resources.py --output s.json --force

Exit codes: 0 snapshot written, 1 a requested file could not be written, 2 bad
input.

Provenance
----------
Reconstructed to emit the schema 1.1 contract documented in
``references/snapshot_schema.md`` and to keep the separation rules in
``references/resource_semantics.md``. The probes, parsing, redaction, and every
redaction rule are this file's own work.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

SCHEMA_VERSION = "1.1"
SNAPSHOT_KIND = "effective_resource_snapshot"

# Every subprocess in this file is one of these tuples. No shell, ever: a shell
# would mean the arguments come from somewhere that can be edited.
PROBES: dict[str, tuple[tuple[str, ...], ...]] = {
    "nvidia_smi": (("nvidia-smi", "--query-gpu=index,name,memory.total",
                    "--format=csv,noheader,nounits"),),
    "rocm_smi": (("rocm-smi", "--showid", "--showproductname", "--csv"),),
    "mac_displays": (("system_profiler", "SPDisplaysDataType", "-json"),),
}

PROBE_TIMEOUT_SECONDS = 6
MAX_PROBE_OUTPUT_BYTES = 256 * 1024
MAX_WARNINGS = 64
MAX_PROVENANCE = 96

# The only environment variables this file reads. Values are parsed for shape
# and never emitted, because they carry job IDs, node names, and device lists.
SLURM_FIELDS: dict[str, str] = {
    "SLURM_JOB_CPUS_PER_NODE": "cpus_per_node",
    "SLURM_CPUS_PER_TASK": "cpus_per_task",
    "SLURM_CPUS_ON_NODE": "cpus_on_node",
    "SLURM_MEM_PER_NODE": "mem_per_node_mib",
    "SLURM_MEM_PER_CPU": "mem_per_cpu_mib",
    "SLURM_NTASKS": "ntasks",
    "SLURM_CPUS_ON_NODE_ALLOWED": "allowed_cpus",
    "SLURM_JOB_GPUS": "gpus_requested",
    "SLURM_GPUS_ON_NODE": "gpus_on_node",
}
# Only the names of these are reported. Their values can list device indices
# and mask bits that are arguably identifying of the allocation.
ACCELERATOR_VISIBILITY_FIELDS = (
    "CUDA_VISIBLE_DEVICES",
    "HIP_VISIBLE_DEVICES",
    "ROCR_VISIBLE_DEVICES",
    "NVIDIA_VISIBLE_DEVICES",
    "AMD_VISIBLE_DEVICES",
)

# Values that mean "no devices", as opposed to a variable that is simply unset.
# Unset is unknown; this is a source explicitly establishing zero.
ZERO_VISIBILITY = frozenset({"", "-1", "none", "None", "void", "NVIDIA_VISIBLE_DEVICES void"})

WARNINGS: list[dict] = []
PROVENANCE: list[dict] = []


# ---------------------------------------------------------------- recording --


def record(component: str, source: str, status: str) -> None:
    """Note that an observation was attempted, and how it went."""
    if len(PROVENANCE) < MAX_PROVENANCE:
        PROVENANCE.append({"component": component, "source": source, "status": status})


def warn(code: str, component: str, message: str, severity: str = "info") -> None:
    """A sanitized warning. Never carries an exception message or a path."""
    if len(WARNINGS) >= MAX_WARNINGS:
        return
    entry = {"code": code, "component": component, "message": message, "severity": severity}
    if entry not in WARNINGS:
        WARNINGS.append(entry)


def positive(value) -> bool:
    """True for a finite positive number. Zero and negatives are not capacities."""
    return isinstance(value, (int, float)) and value == value and value > 0


def finite(value) -> bool:
    return isinstance(value, (int, float)) and value == value


def run_probe(name: str) -> str | None:
    """Run a fixed probe, returning bounded stdout, or None with a warning."""
    for argv in PROBES.get(name, ()):
        binary = shutil.which(argv[0])
        if binary is None:
            record(name, argv[0], "not_found")
            continue
        try:
            completed = subprocess.run(  # noqa: S603 - fixed argv, no shell
                [binary, *argv[1:]],
                capture_output=True,
                timeout=PROBE_TIMEOUT_SECONDS,
                shell=False,
                check=False,
            )
        except subprocess.TimeoutExpired:
            record(name, argv[0], "timeout")
            warn("PROBE_TIMEOUT", name, f"{name} did not answer within "
                                        f"{PROBE_TIMEOUT_SECONDS}s.")
            continue
        except OSError:
            record(name, argv[0], "error")
            warn("PROBE_ERROR", name, f"{name} could not be started.")
            continue

        if completed.returncode != 0:
            record(name, argv[0], "error")
            warn("PROBE_EXIT", name, f"{name} exited with status {completed.returncode}. "
                                     "Absence of a management CLI is normal.")
            continue

        stdout = completed.stdout or b""
        if len(stdout) > MAX_PROBE_OUTPUT_BYTES:
            stdout = stdout[:MAX_PROBE_OUTPUT_BYTES]
            record(name, argv[0], "truncated")
            warn("PROBE_TRUNCATED", name, f"{name} output exceeded "
                                           f"{MAX_PROBE_OUTPUT_BYTES} bytes and was truncated.")
        else:
            record(name, argv[0], "ok")
        return stdout.decode("utf-8", errors="replace")
    return None


# --------------------------------------------------------------------- cpu --


def detect_cpu() -> dict:
    host: dict = {
        "logical": os.cpu_count(),
        "physical": None,
    }
    record("cpu.host.logical", "os.cpu_count()", "ok" if host["logical"] else "unavailable")

    process: dict = {"affinity_logical": None, "python_available_logical": None}

    getaffinity = getattr(os, "sched_getaffinity", None)
    if getaffinity is not None:
        try:
            process["affinity_logical"] = len(getaffinity(0))
            record("cpu.process.affinity_logical", "os.sched_getaffinity", "ok")
        except OSError:
            record("cpu.process.affinity_logical", "os.sched_getaffinity", "error")
            warn("AFFINITY_UNAVAILABLE", "cpu",
                 "This platform does not expose the process affinity set.")
    else:
        record("cpu.process.affinity_logical", "os.sched_getaffinity", "unavailable")

    process_count = getattr(os, "process_cpu_count", None)
    if process_count is not None:
        try:
            value = process_count()
            process["python_available_logical"] = value if positive(value) else None
            record("cpu.process.python_available_logical", "os.process_cpu_count()", "ok")
        except (OSError, ValueError):
            record("cpu.process.python_available_logical", "os.process_cpu_count()", "error")
    else:
        record("cpu.process.python_available_logical", "os.process_cpu_count()", "unavailable")

    host["physical"] = detect_physical_cores()

    cgroup = detect_cgroup_cpu()

    return {
        "host": host,
        "process": process,
        "cgroup_v2": cgroup,
        "effective": {},  # filled in once the scheduler is known
        "notes": [
            "host.logical is system-visible scheduling units, not cores available here",
            "affinity and cpuset constrain placement; cpu.max quota constrains CPU time",
            "a fractional quota is CPU-time capacity, not fractional physical cores",
        ],
    }


def detect_physical_cores() -> int | None:
    """Physical topology, when the platform exposes it. Never inferred from the
    logical count, because hyperthreading, SMT, and processor groups all make
    the two differ in ways that matter for worker counts."""
    psutil = _try_psutil()
    if psutil is None:
        record("cpu.host.physical", "psutil", "unavailable")
        return None
    try:
        count = psutil.cpu_count(logical=False)
    except Exception:
        record("cpu.host.physical", "psutil.cpu_count(logical=False)", "error")
        return None
    record("cpu.host.physical", "psutil.cpu_count(logical=False)",
           "ok" if positive(count) else "unavailable")
    return count if positive(count) else None


def _try_psutil():
    """Import psutil lazily. Its absence is a warning, not a failure."""
    try:
        import psutil  # noqa: PLC0415
    except ImportError:
        record("psutil", "import psutil", "absent")
        warn("PSUTIL_ABSENT", "cpu",
             "psutil is not installed, so physical-core, available-memory, and swap "
             "observations are unavailable. Run `uv pip install \"psutil==7.2.2\"` for them.",
             "info")
        return None
    record("psutil", "import psutil", "ok")
    return psutil


def _read_bounded(path: str) -> str | None:
    """Read at most one small cgroup file, without following it anywhere."""
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as handle:
            return handle.read(4096)
    except FileNotFoundError:
        return None
    except OSError:
        return None


def _cgroup_roots() -> list[str]:
    """Candidate cgroup v2 mount points, in the order they are consulted.

    The path itself is never emitted; only the observations read from it.
    """
    roots = ["/sys/fs/cgroup"]
    own = _read_bounded("/proc/self/cgroup")
    if own:
        for line in own.splitlines():
            parts = line.split(":", 2)
            if len(parts) == 3 and parts[0] == "0" and parts[2].startswith("/"):
                roots.append("/sys/fs/cgroup" + parts[2].rstrip("/"))
    seen: set[str] = set()
    ordered: list[str] = []
    for root in roots:
        if root not in seen:
            seen.add(root)
            ordered.append(root)
    return ordered


def _parse_cpu_list(spec: str) -> int | None:
    """Count the logical CPUs in a cpuset string like '0-3,8,10-11'."""
    total = 0
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            low, _, high = part.partition("-")
            try:
                total += int(high) - int(low) + 1
            except ValueError:
                return None
        else:
            try:
                total += 1
            except ValueError:
                return None
    return total or None


def detect_cgroup_cpu() -> dict:
    """Cpuset size and the most restrictive ancestor ``cpu.max`` quota."""
    cpuset = None
    quota = None
    scope = "not_applicable"

    for root in _cgroup_roots():
        cpuset_file = _read_bounded(f"{root}/cpuset.cpus.effective")
        if cpuset is None and cpuset_file:
            cpuset = _parse_cpu_list(cpuset_file.strip())
            if cpuset is not None:
                record("cpu.cgroup_v2.cpuset_logical", "cpuset.cpus.effective", "ok")
                scope = "non_root" if root != "/sys/fs/cgroup" else "root"

        # Walk ancestors: the most restrictive finite quota anywhere on the path
        # is the one that binds, not the nearest one.
        current = root
        for _ in range(16):
            cpu_max = _read_bounded(f"{current}/cpu.max")
            if cpu_max:
                first, _, _second = cpu_max.strip().partition(" ")
                if first == "max":
                    break
                try:
                    numerator, _, denominator = first.partition("/")
                    ratio = int(numerator) / (int(denominator) if denominator else 1)
                except (ValueError, ZeroDivisionError):
                    record("cpu.cgroup_v2.quota_cores", "cpu.max", "parse_error")
                    break
                if positive(ratio) and (quota is None or ratio < quota):
                    quota = ratio
                record("cpu.cgroup_v2.quota_cores", "cpu.max", "ok")
                scope = "non_root" if current != "/sys/fs/cgroup" else "root"
                break
            parent = f"{current}/.."  # never resolved or emitted
            if parent == current:
                break
            current = os.path.normpath(parent)
            if current == "/":
                break

    if cpuset is None and quota is None:
        record("cpu.cgroup_v2", "cgroup v2", "absent")
        scope = "not_applicable"
    elif cpuset is None and quota is None:
        scope = "unknown"

    return {
        "cpuset_logical": cpuset,
        "quota_cores": round(quota, 4) if quota is not None else None,
        "scope": scope,
    }


# ------------------------------------------------------------------ memory --


def detect_memory() -> dict:
    psutil = _try_psutil()
    host: dict = {"total_bytes": None, "available_bytes": None, "swap_total_bytes": None,
                  "swap_free_bytes": None}

    if psutil is not None:
        try:
            virtual = psutil.virtual_memory()
            host["total_bytes"] = int(virtual.total)
            host["available_bytes"] = int(virtual.available)
            record("memory.host.total_bytes", "psutil.virtual_memory()", "ok")
            record("memory.host.available_bytes", "psutil.virtual_memory()", "ok")
        except Exception:
            record("memory.host", "psutil.virtual_memory()", "error")
        try:
            swap = psutil.swap_memory()
            host["swap_total_bytes"] = int(swap.total)
            host["swap_free_bytes"] = int(swap.free)
            record("memory.host.swap_total_bytes", "psutil.swap_memory()", "ok")
        except Exception:
            record("memory.host.swap_total_bytes", "psutil.swap_memory()", "unavailable")

    if host["total_bytes"] is None:
        total = _read_bounded("/proc/meminfo")
        if total:
            match = re.search(r"^MemTotal:\s+(\d+) kB", total, re.MULTILINE)
            available = re.search(r"^MemAvailable:\s+(\d+) kB", total, re.MULTILINE)
            if match:
                host["total_bytes"] = int(match.group(1)) * 1024
                record("memory.host.total_bytes", "/proc/meminfo MemTotal", "ok")
            if available:
                host["available_bytes"] = int(available.group(1)) * 1024
                record("memory.host.available_bytes", "/proc/meminfo MemAvailable", "ok")

    cgroup = detect_cgroup_memory()
    model = "unified_cpu_gpu" if _is_apple_silicon() else "system_ram"

    return {
        "host": host,
        "cgroup_v2": cgroup,
        "effective": {},  # filled in once the scheduler is known
        "model": model,
        "notes": [
            "unified CPU/GPU memory is not added again as dedicated VRAM",
            "cgroup memory.high is a pressure and throttle boundary, not a hard cap",
            "swap is not counted as available working memory",
        ],
    }


def _is_apple_silicon() -> bool:
    return platform.system() == "Darwin" and platform.machine() in {"arm64", "aarch64"}


def _parse_byte_value(text: str) -> int | None:
    """Parse a cgroup memory value, which may carry a 'max' sentinel."""
    token = text.strip().split()[0] if text.strip() else ""
    if not token or token == "max":
        return None
    multiplier = 1
    if token.endswith(("K", "k")):
        multiplier, token = 1024, token[:-1]
    elif token.endswith(("M", "m")):
        multiplier, token = 1024 ** 2, token[:-1]
    elif token.endswith(("G", "g")):
        multiplier, token = 1024 ** 3, token[:-1]
    try:
        return int(float(token) * multiplier)
    except ValueError:
        return None


def detect_cgroup_memory() -> dict:
    """Current usage plus the hierarchical effective limits."""
    result = {"current_bytes": None, "available_bytes": None,
              "high_bytes": None, "max_bytes": None, "scope": "not_applicable"}
    found_any = False

    for root in _cgroup_roots():
        current = _read_bounded(f"{root}/memory.current")
        if current is not None:
            result["current_bytes"] = _parse_byte_value(current)
            found_any = True
            record("memory.cgroup_v2.current_bytes", "memory.current", "ok")
            break

    for root in _cgroup_roots():
        node = root
        for _ in range(16):
            high = _read_bounded(f"{node}/memory.high")
            if high:
                value = _parse_byte_value(high)
                if value is not None:
                    result["high_bytes"] = value
                    found_any = True
                record("memory.cgroup_v2.high_bytes", "memory.high", "ok")
            maximum = _read_bounded(f"{node}/memory.max")
            if maximum is not None:
                value = _parse_byte_value(maximum)
                if value is not None and (result["max_bytes"] is None or value < result["max_bytes"]):
                    result["max_bytes"] = value
                    found_any = True
                record("memory.cgroup_v2.max_bytes", "memory.max", "ok")
                result["scope"] = "non_root" if node != "/sys/fs/cgroup" else "root"
                break
            parent = os.path.normpath(f"{node}/..")
            if parent == node or parent == "/":
                break
            node = parent

    if not found_any:
        record("memory.cgroup_v2", "cgroup v2", "absent")
        return result

    # Available is the hard limit (or host total) minus what is already used.
    ceiling = result["max_bytes"]
    if ceiling is not None and result["current_bytes"] is not None:
        result["available_bytes"] = max(0, ceiling - result["current_bytes"])
    return result


# -------------------------------------------------------------------- disk --


def detect_disk() -> dict:
    """Capacity, free blocks, user-available blocks, and a non-writing check.

    No write probe is performed. The permission check is a mode inspection, and
    the report says so, because a filesystem quota or a project quota can still
    refuse a write of any size the free-block count suggests is fine.
    """
    usage = shutil.disk_usage(os.getcwd())
    os.statvfs = getattr(os, "statvfs", None)  # absent on Windows
    user_available = None
    statvfs = getattr(os, "statvfs", None)
    if statvfs is not None:
        try:
            stats = statvfs(os.getcwd())
            user_available = stats.f_bavail * stats.f_frsize
            record("disk.user_available_bytes", "os.statvfs f_bavail", "ok")
        except (OSError, ValueError):
            record("disk.user_available_bytes", "os.statvfs", "error")
    else:
        record("disk.user_available_bytes", "os.statvfs", "unavailable")

    writable = os.access(os.getcwd(), os.W_OK)
    record("disk.writable", "os.access(W_OK)", "ok")

    return {
        "capacity_bytes": int(usage.total),
        "free_bytes": int(usage.free),
        "user_available_bytes": user_available,
        "writable": bool(writable),
        "writability_check": "non-writing os.access inspection; no write probe was performed",
        "scope": "working_filesystem_path_redacted",
        "notes": [
            "free_bytes and user_available_bytes are different quantities; the second "
            "excludes blocks reserved for the filesystem and other users",
            "a filesystem or project quota can be stricter than any of these values",
        ],
    }


# ------------------------------------------------------------- accelerators --


def detect_accelerators(skip: bool) -> dict:
    """Enumerate management-visible accelerator candidates.

    A visible device is a *candidate*. It does not establish scheduler or
    container permission, device-node access, driver compatibility, framework
    package compatibility, or operator and data-type support, so
    ``runtime_usable_devices`` stays null and every device reports
    ``runtime_compatibility: not_tested``.
    """
    devices: list[dict] = []

    if skip:
        record("accelerators", "all probes", "skipped")
    else:
        devices.extend(_nvidia_devices())
        devices.extend(_rocm_devices())
        if platform.system() == "Darwin":
            devices.extend(_apple_devices())

    visibility = {}
    for name in ACCELERATOR_VISIBILITY_FIELDS:
        present = name in os.environ
        visibility[name] = {
            "present": present,
            # Only a variable that explicitly establishes no devices reports zero.
            "hides_all_devices": bool(present and os.environ.get(name, "") in ZERO_VISIBILITY),
        }
    record("accelerators.visibility_environment", "os.environ allowlist", "ok")

    by_vendor: dict[str, int] = {}
    for device in devices:
        by_vendor[device["vendor"]] = by_vendor.get(device["vendor"], 0) + 1

    return {
        "devices": devices,
        "candidate_counts": by_vendor,
        "candidate_upper_bounds": {},
        "runtime_usable_devices": None,
        "visibility_environment": visibility,
        "probes_run": not skip,
        "notes": [
            "a management query establishes visibility, not usability",
            "candidate counts are upper bounds, not guarantees",
            "no framework runtime is loaded here, so runtime compatibility is untested",
        ],
    }


def _nvidia_devices() -> list[dict]:
    output = run_probe("nvidia_smi")
    if not output:
        return []
    devices = []
    for index, line in enumerate(output.splitlines()):
        fields = [field.strip() for field in line.split(",")]
        if len(fields) < 3:
            continue
        memory_bytes = None
        if fields[2].replace(".", "", 1).isdigit():
            memory_bytes = int(float(fields[2]) * 1024 * 1024)
        devices.append({
            "vendor": "nvidia",
            "device_class": "discrete_gpu",
            "backend_candidate": "cuda",
            "management_query": "nvidia-smi --query-gpu",
            "device_permission": "not_tested",
            "runtime_compatibility": "not_tested",
            "memory_model": "dedicated_or_hbm" if memory_bytes else "unknown",
            "memory_total_bytes": memory_bytes,
            "local_index": index,
        })
    return devices


def _rocm_devices() -> list[dict]:
    output = run_probe("rocm_smi")
    if not output:
        return []
    devices = []
    for index, line in enumerate(output.splitlines()):
        if "card" not in line.lower() and "gpu" not in line.lower():
            continue
        devices.append({
            "vendor": "amd",
            "device_class": "discrete_gpu",
            "backend_candidate": "rocm",
            "management_query": "rocm-smi --showid --csv",
            "device_permission": "not_tested",
            "runtime_compatibility": "not_tested",
            "memory_model": "unknown",
            "memory_total_bytes": None,
            "local_index": index,
        })
    return devices


def _apple_devices() -> list[dict]:
    """Apple silicon has an integrated GPU sharing system memory."""
    if not _is_apple_silicon():
        return []
    output = run_probe("mac_displays")
    record("accelerators.devices.apple", "platform inference", "ok")
    warn("APPLE_GPU_INTEGRATED", "accelerators",
         "On Apple silicon the GPU shares system memory; it is reported as a Metal "
         "candidate with no separate VRAM figure.", "info")
    return [{
        "vendor": "apple",
        "device_class": "integrated_gpu",
        "backend_candidate": "metal",
        "management_query": "system_profiler SPDisplaysDataType -json"
                            if output else "platform inference",
        "device_permission": "not_tested",
        "runtime_compatibility": "not_tested",
        "memory_model": "unified",
        "memory_total_bytes": None,
        "local_index": 0,
    }]


# ---------------------------------------------------- scheduler / container --


def detect_scheduler() -> dict:
    """Read the allowlisted Slurm allocation variables, values parsed not emitted."""
    present: list[str] = []
    allocation: dict[str, object] = {}
    scopes: set[str] = set()

    for name, key in SLURM_FIELDS.items():
        if name not in os.environ:
            continue
        present.append(name)
        raw = os.environ[name].strip()
        if key in {"mem_per_node_mib", "mem_per_cpu_mib", "ntasks"}:
            try:
                allocation[key] = int(raw.split(",")[0].split("M")[0].strip("M"))
                continue
            except ValueError:
                warn("SLURM_PARSE", "scheduler",
                     f"{name} was present but its value could not be parsed as an integer.",
                     "info")
                continue
        if key == "allowed_cpus":
            count = _parse_cpu_list(raw)
            if count is not None:
                allocation["allowed_cpus_logical"] = count
                scopes.add("cpu_affinity")
        elif key.startswith("gpus"):
            count = re.search(r"\d+", raw)
            if count:
                allocation[key] = int(count.group(0))

    record("scheduler.allocation", "os.environ Slurm allowlist", "ok" if present else "absent")
    if present:
        warn("SCHEDULER_ALLOCATED", "scheduler",
             "Slurm allocation variables are present. Variables describe an allocation, "
             "not proof of enforcement: site configuration (task affinity, cgroups) "
             "decides whether that allocation is actually enforced. Prefer the affinity "
             "and cgroup observations as enforcement evidence.", "info")

    return {
        "kind": "slurm" if present else "none_detected",
        "fields_read": sorted(present),
        "allocation": allocation,
        "scopes": sorted(scopes),
        "enforcement": "unknown",
        "notes": [
            "no job ID, node list, submit host, or GPU index is emitted",
            "variables alone do not establish confinement",
        ],
    }


def detect_cgroup_scope(cpu_cgroup: dict) -> dict:
    """Whether a cgroup control context is present, and how confident we are."""
    markers = {
        "/.dockerenv": "docker",
        "/run/.containerenv": "podman",
    }
    detected: str | None = None
    for path, kind in markers.items():
        if os.path.exists(path):
            detected = kind
            break
    if detected is None:
        # An empty `container` variable is a real, documented signal; an unset
        # variable is not evidence either way and stays null.
        raw = os.environ.get("container")
        if raw is not None:
            detected = "env_marker_empty" if raw == "" else "env_marker"

    if cpu_cgroup.get("scope") in {"root", "non_root"}:
        limit_evidence = "cgroup_limit" if (
            positive(cpu_cgroup.get("quota_cores")) or cpu_cgroup.get("cpuset_logical")
        ) else None
    else:
        limit_evidence = None

    record("container", "filesystem markers and cgroup scope", "ok" if detected else "absent")
    if cpu_cgroup.get("scope") == "non_root" and not detected:
        warn("NONDETECTABLE_CONTAINER", "container",
             "This process is in a non-root cgroup but no container marker was found. A "
             "non-root cgroup is not automatically a container, and a container with no "
             "finite cgroup value can still see full host inventory.", "info")

    return {
        "detected": detected,
        "cgroup_limit": limit_evidence,
        "notes": [
            "container markers identify context; cgroup controls identify limits",
            "neither is inferred from the other",
        ],
    }


# --------------------------------------------------------------- effective --


def compute_effective(snapshot: dict) -> None:
    """Fill cpu.effective and memory.effective from the observations above.

    The rule throughout is the minimum of the finite positive observations, with
    the names of the tied minima recorded. A null observation never contributes
    and never becomes unlimited: it is simply not known, and the honest result is
    the smallest value that *is* known.
    """
    cpu = snapshot["cpu"]
    scheduler = snapshot["scheduler"]

    candidates: list[tuple[str, float]] = []
    if positive(cpu["host"]["logical"]):
        candidates.append(("cpu.host.logical", float(cpu["host"]["logical"])))
    if positive(cpu["process"]["affinity_logical"]):
        candidates.append(("cpu.process.affinity_logical", float(cpu["process"]["affinity_logical"])))
    if positive(cpu["process"]["python_available_logical"]):
        candidates.append(
            ("cpu.process.python_available_logical", float(cpu["process"]["python_available_logical"]))
        )
    if positive(cpu["cgroup_v2"]["cpuset_logical"]):
        candidates.append(("cpu.cgroup_v2.cpuset_logical", float(cpu["cgroup_v2"]["cpuset_logical"])))
    if positive(cpu["cgroup_v2"]["quota_cores"]):
        candidates.append(("cpu.cgroup_v2.quota_cores", float(cpu["cgroup_v2"]["quota_cores"])))

    scheduler_cpu = scheduler["allocation"].get("cpus_per_task") or scheduler["allocation"].get(
        "cpus_per_node")
    if positive(scheduler_cpu):
        candidates.append(("scheduler.allocation.cpu_per_process", float(scheduler_cpu)))
    if positive(scheduler["allocation"].get("allowed_cpus_logical")):
        candidates.append(
            ("scheduler.allocation.allowed_cpus_logical",
             float(scheduler["allocation"]["allowed_cpus_logical"]))
        )

    if candidates:
        capacity = min(value for _name, value in candidates)
        limiting = sorted(name for name, value in candidates if value == capacity)
    else:
        capacity, limiting = None, []

    # A conservative worker count: never more than the capacity, and never
    # allowed to reach it exactly, because the process itself and the main thread
    # need somewhere to run.
    ceiling = max(1, int(capacity)) if capacity is not None and capacity >= 1 else (
        1 if capacity is not None and capacity > 0 else None
    )
    if ceiling is not None and capacity is not None and capacity < 1:
        ceiling = 1
        warn("CPU_CAPACITY_BELOW_ONE", "cpu",
             "CPU-time capacity is below one core. One process worker is still the floor, "
             "and the workload will run slower than wall-clock time suggests.", "warning")

    cpu["effective"] = {
        "capacity_cores": round(capacity, 4) if capacity is not None else None,
        "worker_ceiling": ceiling,
        "limiting_sources": limiting,
        "note": "capacity_cores is a scheduling-capacity figure, not a physical-core count",
    }
    if not candidates:
        warn("CPU_EFFECTIVE_UNKNOWN", "cpu",
             "No finite positive CPU capacity could be observed, so effective capacity is "
             "null. Null means unknown; it does not mean unlimited.", "warning")

    memory = snapshot["memory"]
    memory_candidates: list[tuple[str, int]] = []
    if positive(memory["host"]["total_bytes"]):
        memory_candidates.append(("memory.host.total_bytes", int(memory["host"]["total_bytes"])))
    if positive(memory["cgroup_v2"]["max_bytes"]):
        memory_candidates.append(("memory.cgroup_v2.max_bytes", int(memory["cgroup_v2"]["max_bytes"])))

    scheduler_mib = scheduler["allocation"].get("mem_per_cpu_mib")
    scheduler_cpus = scheduler["allocation"].get("cpus_per_task")
    if positive(scheduler_mib) and positive(scheduler_cpus):
        memory_candidates.append(
            ("scheduler.allocation.memory_per_task", int(scheduler_mib) * 1024 * 1024)
        )
    elif positive(scheduler["allocation"].get("mem_per_node_mib")):
        memory_candidates.append((
            "scheduler.allocation.memory_per_node",
            int(scheduler["allocation"]["mem_per_node_mib"]) * 1024 * 1024,
        ))

    hard_limit = min((v for _n, v in memory_candidates), default=None)
    hard_sources = sorted(n for n, v in memory_candidates if v == hard_limit) if hard_limit else []

    available_candidates: list[tuple[str, int]] = []
    if positive(memory["host"]["available_bytes"]):
        available_candidates.append(
            ("memory.host.available_bytes", int(memory["host"]["available_bytes"]))
        )
    if positive(memory["cgroup_v2"]["available_bytes"]):
        available_candidates.append(
            ("memory.cgroup_v2.available_bytes", int(memory["cgroup_v2"]["available_bytes"]))
        )
    available = min((v for _n, v in available_candidates), default=None)
    available_sources = (
        sorted(n for n, v in available_candidates if v == available) if available else []
    )

    memory["effective"] = {
        "hard_limit_bytes": hard_limit,
        "available_bytes": available,
        "pressure_threshold_bytes": memory["cgroup_v2"]["high_bytes"],
        "hard_limit_sources": hard_sources,
        "available_limiting_sources": available_sources,
        "note": "pressure_threshold_bytes is cgroup memory.high: a throttle boundary, "
                "not a hard cap, and not relabelled as one",
    }
    if not memory_candidates:
        warn("MEMORY_HARD_LIMIT_UNKNOWN", "memory",
             "No finite memory hard limit could be observed. Null means unknown, and an "
             "unknown limit is not an unlimited one.", "warning")


# ------------------------------------------------------------------ output --


def build_snapshot(skip_accelerators: bool) -> dict:
    snapshot: dict = {
        "schema_version": SCHEMA_VERSION,
        "snapshot_kind": SNAPSHOT_KIND,
        "observed_at": datetime.now(timezone.utc).isoformat(timespec="seconds").replace(
            "+00:00", "Z"
        ),
        "platform": {
            "system": platform.system(),
            "release_major": platform.release().split(".")[0] if platform.release() else None,
            "machine": platform.machine(),
            "python": platform.python_version(),
            "hostname": None,
            "hostname_omitted": "hostnames are not emitted",
        },
        "privacy": {
            "hostname_emitted": False,
            "absolute_paths_emitted": False,
            "cgroup_paths_emitted": False,
            "job_ids_emitted": False,
            "device_uuids_emitted": False,
            "pci_addresses_emitted": False,
            "environment_dumped": False,
            "environment_fields_read": sorted(SLURM_FIELDS) + list(ACCELERATOR_VISIBILITY_FIELDS),
            "stress_test_performed": False,
            "write_probe_performed": False,
        },
    }

    snapshot["cpu"] = detect_cpu()
    snapshot["memory"] = detect_memory()
    snapshot["disk"] = detect_disk()
    snapshot["accelerators"] = detect_accelerators(skip_accelerators)
    snapshot["scheduler"] = detect_scheduler()
    snapshot["cgroup_v2"] = {
        "scope": snapshot["cpu"]["cgroup_v2"]["scope"],
        "path_emitted": False,
    }
    snapshot["container"] = detect_container(snapshot["cpu"]["cgroup_v2"])

    compute_effective(snapshot)

    snapshot["warnings"] = sorted(WARNINGS, key=lambda w: (w["code"], w["component"]))
    snapshot["provenance"] = sorted(PROVENANCE, key=lambda p: (p["component"], p["source"]))

    snapshot["completeness"] = _completeness(snapshot)
    return snapshot


def detect_container(cpu_cgroup: dict) -> dict:
    return detect_cgroup_scope(cpu_cgroup)


def _completeness(snapshot: dict) -> str:
    if snapshot["cpu"]["effective"]["capacity_cores"] is None:
        return "partial"
    if snapshot["memory"]["effective"]["hard_limit_bytes"] is None:
        return "partial"
    if any(w["severity"] == "warning" for w in snapshot["warnings"]):
        return "complete_with_informational_notes"
    return "complete"


def write_private_json(payload: str, filename: str, force: bool) -> str:
    """Write one .json file in the current directory, with private permissions.

    Refuses a path with any directory component, refuses a symlink, and refuses
    to overwrite unless forced. A snapshot is inventory; overwriting one another
    accidentally loses the "before" that a diff needs.
    """
    if os.path.sep in filename or (os.altsep and os.altsep in filename) or filename in {".", ".."}:
        raise SystemExit(
            f"error: --output must be a bare .json filename in the current directory, "
            f"not {filename!r}. The working path is redacted from the snapshot, so a "
            "path outside the current directory would be unauditable."
        )
    if not filename.endswith(".json"):
        raise SystemExit(f"error: --output must end in .json, got {filename!r}")
    target = Path.cwd() / filename
    if target.is_symlink():
        raise SystemExit(f"error: {filename} is a symlink; refusing to write through it")
    if target.exists() and not force:
        raise SystemExit(
            f"error: {filename} already exists. Pass --force to overwrite it, or choose a "
            "different name. Keeping the earlier snapshot is what makes a diff possible."
        )

    descriptor = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_TRUNC, 0o600)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(payload + "\n")
    except FileExistsError:
        raise SystemExit(f"error: {filename} already exists; pass --force to overwrite")
    return str(target)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Collect a redacted resource snapshot for the current process.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--output", default=None,
        help="write to this bare .json filename in the current directory; default stdout",
    )
    parser.add_argument(
        "--force", action="store_true",
        help="allow overwriting an existing --output file",
    )
    parser.add_argument(
        "--skip-accelerators", action="store_true",
        help="skip the accelerator management queries; visibility variables are still summarized",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    snapshot = build_snapshot(args.skip_accelerators)
    payload = json.dumps(snapshot, indent=2, sort_keys=True, default=str)

    if args.output:
        try:
            path = write_private_json(payload, args.output, args.force)
        except SystemExit as exc:
            print(str(exc), file=sys.stderr)
            return 1
        print(f"wrote {args.output} ({snapshot['completeness']})", file=sys.stderr)
    else:
        print(payload)
    return 0


if __name__ == "__main__":
    sys.exit(main())
