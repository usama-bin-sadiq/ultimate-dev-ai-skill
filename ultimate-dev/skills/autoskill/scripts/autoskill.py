#!/usr/bin/env python3
"""Unified CLI for the autoskill skill: doctor, run, promote.

What it does
------------
    python scripts/autoskill.py doctor  --config config.yaml --skills-dir ../
    python scripts/autoskill.py run     --start ... --end ... --config config.yaml
    python scripts/autoskill.py promote --proposed ~/.autoskill/proposed/<ts> \\
                                        --skills-dir ../ --name <skill>

``doctor``  checks config, skills dir, screenpipe reachability, and the LLM backend
            in one shot; non-zero exit on any failure with the offending line
            marked ``error``.
``run``     fetches the screenpipe window, redacts it, clusters it, matches each
            cluster against the skills in ``--skills-dir``, asks the LLM to judge
            each cluster as reuse / compose / novel, and writes a proposal tree
            plus ``report.md``. ``--dry-run`` (alias ``--plan``) stops after
            clustering, skips the LLM and the embedding model, and writes only
            ``plan.md``.
``promote`` moves an approved proposal directory into ``<skills-dir>/<name>/``,
            refusing to overwrite an existing skill.

Expected input
--------------
A ``config.yaml`` (see the shape in the SKILL.md and ``references/screenpipe-config.yaml``
for the capture side), an existing skills directory, and -- for ``run`` only -- a
running screenpipe daemon plus ``SCREENPIPE_TOKEN``.

Provenance
----------
Reconstructed to match the three-subcommand CLI and the pipeline stages the SKILL.md
documents. The orchestration here is this file's own; the fetch, redaction, and
clustering stages live in ``fetch_window.py``, ``redact.py``, and ``cluster.py`` in
this directory, and the matching and synthesis stages live in ``match_skills.py``
and ``synthesize.py``.
"""

from __future__ import annotations

import argparse
import os
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

BACKENDS = ("local", "claude", "foundry")
DEFAULT_CONFIG = {
    "backend": "local",
    "local": {"endpoint": "http://localhost:1234/v1", "model": "Gemma-4-31B-it"},
    "screenpipe": {"url": "http://localhost:3030"},
    "cluster": {
        "min_session_minutes": 5,
        "idle_gap_minutes": 10,
        "min_cluster_size": 2,
    },
}
DEFAULT_PROPOSAL_ROOT = Path.home() / ".autoskill" / "proposed"


def log(message: str) -> None:
    print(message, file=sys.stderr, flush=True)


def load_config(path: str | None) -> dict:
    """Read config.yaml and layer it over the documented defaults."""
    config = {key: dict(value) if isinstance(value, dict) else value
              for key, value in DEFAULT_CONFIG.items()}
    if path is None:
        return config
    try:
        import yaml
    except ImportError:
        raise SystemExit("error: pyyaml is not installed; `pipenv install httpx pyyaml sentence-transformers`")
    file_path = Path(path)
    if not file_path.is_file():
        raise SystemExit(f"error: config file not found: {path}")
    with file_path.open(encoding="utf-8") as handle:
        loaded = yaml.safe_load(handle) or {}
    if not isinstance(loaded, dict):
        raise SystemExit(f"error: {path} must be a YAML mapping at the top level")
    for key, value in loaded.items():
        if isinstance(value, dict) and isinstance(config.get(key), dict):
            config[key].update(value)
        else:
            config[key] = value
    return config


# ---------------------------------------------------------------- doctor ----

def cmd_doctor(args) -> int:
    """Check every dependency in one shot; return 0 only if all four pass."""
    config = load_config(args.config)
    checks: list[tuple[str, bool, str]] = []

    backend = config.get("backend")
    checks.append((
        "config",
        backend in BACKENDS,
        f"backend={backend}" + ("" if backend in BACKENDS else f" (expected one of {', '.join(BACKENDS)})"),
    ))

    skills_dir = Path(args.skills_dir)
    has_skills = skills_dir.is_dir() and any(skills_dir.glob("*/SKILL.md"))
    checks.append((
        "skills_dir",
        has_skills,
        f"{skills_dir} holds {len(list(skills_dir.glob('*/SKILL.md')))} skill(s)"
        if has_skills else f"{skills_dir} is not a directory of skills",
    ))

    token = os.environ.get("SCREENPIPE_TOKEN")
    screenpipe_ok, screenpipe_note = _check_screenpipe(config, token)
    checks.append(("screenpipe", screenpipe_ok, screenpipe_note))

    llm_ok, llm_note = _check_llm(config)
    checks.append(("llm", llm_ok, llm_note))

    print("component    status  detail")
    failed = 0
    for name, ok, note in checks:
        print(f"{name:<12} {'ok' if ok else 'error':<6}  {note}")
        if not ok:
            failed += 1
    return 1 if failed else 0


def _check_screenpipe(config: dict, token: str | None) -> tuple[bool, str]:
    try:
        import httpx
    except ImportError:
        return False, "httpx not installed"
    url = config.get("screenpipe", {}).get("url", "http://localhost:3030")
    try:
        response = httpx.get(f"{url.rstrip('/')}/health", timeout=5.0)
    except Exception as exc:
        return False, f"{url} unreachable: {exc}"
    if response.status_code in (401, 403):
        return False, f"{url} rejected the request; set SCREENPIPE_TOKEN"
    return response.status_code < 400, f"{url} responded {response.status_code}"


def _check_llm(config: dict) -> tuple[bool, str]:
    backend = config.get("backend")
    if backend == "claude":
        return (bool(os.environ.get("ANTHROPIC_API_KEY")),
                "ANTHROPIC_API_KEY set" if os.environ.get("ANTHROPIC_API_KEY")
                else "ANTHROPIC_API_KEY not set")
    if backend == "foundry":
        endpoint = config.get("foundry", {}).get("endpoint", "")
        return (bool(os.environ.get("FOUNDRY_API_KEY") and endpoint),
                f"FOUNDRY_API_KEY and foundry.endpoint ({endpoint or 'unset'})")
    local = config.get("local", {})
    endpoint = local.get("endpoint", "http://localhost:1234/v1")
    model = local.get("model", "unknown")
    try:
        import httpx
    except ImportError:
        return False, "httpx not installed"
    try:
        response = httpx.get(f"{endpoint.rstrip('/')}/models", timeout=5.0)
    except Exception as exc:
        return False, f"local backend {endpoint} unreachable: {exc}"
    return response.status_code < 400, f"local backend {endpoint} serving {model}"


# ------------------------------------------------------------------- run ----

def cmd_run(args) -> int:
    """Run the full pipeline over a time window and write a proposal tree."""
    config = load_config(args.config)
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from cluster import cluster_sessions, segment_sessions, summarize  # noqa: E402
    from fetch_window import ScreenpipeUnreachable, fetch_window  # noqa: E402
    from redact import redact  # noqa: E402

    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%S")
    out_dir = Path(args.out) / stamp if args.out else DEFAULT_PROPOSAL_ROOT / stamp

    screenpipe_cfg = config.get("screenpipe", {})
    token = os.environ.get("SCREENPIPE_TOKEN")
    try:
        events = fetch_window(
            start=args.start, end=args.end,
            url=screenpipe_cfg.get("url", "http://localhost:3030"),
            token=token,
        )
    except ScreenpipeUnreachable as exc:
        log(f"error: {exc}")
        return 2

    events = redact(events)
    log(f"fetched and redacted {len(events)} event(s)")

    cluster_cfg = config.get("cluster", {})
    sessions = segment_sessions(
        events,
        idle_gap_minutes=cluster_cfg.get("idle_gap_minutes", 10),
        min_session_minutes=cluster_cfg.get("min_session_minutes", 5),
    )
    for session in sessions:
        from cluster import app_signature  # noqa: E402
        session["signature"] = app_signature(session)
    clusters = cluster_sessions(sessions, cluster_cfg.get("min_cluster_size", 2))
    summaries = summarize(clusters)
    log(f"{len(sessions)} session(s), {len(clusters)} cluster(s)")

    out_dir.mkdir(parents=True, exist_ok=True)

    if args.dry_run:
        plan = ["# autoskill plan (dry run)", "",
                f"Window: {args.start} to {args.end}",
                f"Clusters: {len(summaries)}", ""]
        for cluster in summaries:
            plan.append(f"## {cluster['signature']}")
            plan.append(f"- apps: {', '.join(cluster['apps'])}")
            plan.append(f"- sessions: {cluster['session_count']}, "
                        f"total {cluster['total_minutes']} min")
            plan.append("")
        plan_path = out_dir / "plan.md"
        plan_path.write_text("\n".join(plan) + "\n", encoding="utf-8")
        log(f"dry run: wrote {plan_path}; no LLM call was made")
        return 0

    try:
        from match_skills import load_skill_descriptions, top_k_matches  # noqa: E402
        from synthesize import synthesize  # noqa: E402
    except ImportError as exc:
        log(f"error: {exc}. Match and synthesize stages are required for a full run; "
            "use --dry-run to inspect the clustering without them.")
        return 2

    skills = load_skill_descriptions(args.skills_dir)
    proposals = []
    for cluster in summaries:
        matches = top_k_matches(cluster, skills, k=3)
        verdict = synthesize(cluster, matches, config)
        proposals.append(verdict)

    report = _write_report(out_dir, args, summaries, proposals)
    log(f"wrote {report} and {len(proposals)} proposal(s) under {out_dir}")
    return 0


def _write_report(out_dir: Path, args, summaries: list[dict], proposals: list[dict]) -> Path:
    lines = ["# autoskill proposal", "",
             f"- Window: {args.start} to {args.end}",
             f"- Clusters analyzed: {len(summaries)}",
             f"- Proposals: {len(proposals)}", ""]
    for cluster, proposal in zip(summaries, proposals):
        lines.append(f"## {cluster['signature']}")
        lines.append(f"- Apps: {', '.join(cluster['apps'])}")
        lines.append(f"- Sessions: {cluster['session_count']} over {cluster['total_minutes']} min")
        lines.append(f"- Verdict: {proposal.get('verdict')}")
        matched = proposal.get("matched_skills") or []
        if matched:
            lines.append("- Matched skills: " + ", ".join(matched))
        if proposal.get("path"):
            lines.append(f"- Draft: {proposal['path']}")
        lines.append("")
    report = out_dir / "report.md"
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report


# --------------------------------------------------------------- promote ----

def cmd_promote(args) -> int:
    """Move an approved proposal directory into the skills tree."""
    proposed = Path(args.proposed)
    if not proposed.is_dir():
        log(f"error: proposal directory not found: {proposed}")
        return 1

    target = Path(args.skills_dir) / args.name
    if target.exists():
        log(f"error: {target} already exists; refusing to overwrite. "
            "Choose another --name or move the existing skill first.")
        return 1

    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(proposed), str(target))
    log(f"promoted {proposed} to {target}")
    return 0


# ------------------------------------------------------------------ cli -----

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Propose new skills from your own screenpipe workflow history.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    sub = parser.add_subparsers(dest="command", required=True)

    doctor = sub.add_parser("doctor", help="check every dependency in one shot")
    doctor.add_argument("--config", default=None, help="path to config.yaml")
    doctor.add_argument("--skills-dir", required=True, help="directory holding */SKILL.md")
    doctor.set_defaults(func=cmd_doctor)

    run = sub.add_parser("run", help="run the pipeline over a time window")
    run.add_argument("--start", required=True, help="window start, ISO-8601")
    run.add_argument("--end", required=True, help="window end, ISO-8601")
    run.add_argument("--config", default=None, help="path to config.yaml")
    run.add_argument("--skills-dir", required=True, help="directory holding */SKILL.md")
    run.add_argument("--out", default=None, help="proposal root; default ~/.autoskill/proposed")
    run.add_argument(
        "--dry-run", "--plan", dest="dry_run", action="store_true",
        help="stop after clustering; write plan.md and make no LLM call",
    )
    run.set_defaults(func=cmd_run)

    promote = sub.add_parser("promote", help="move an approved proposal into skills/")
    promote.add_argument("--proposed", required=True, help="the proposal directory to promote")
    promote.add_argument("--skills-dir", required=True, help="directory holding */SKILL.md")
    promote.add_argument("--name", required=True, help="name for the promoted skill")
    promote.set_defaults(func=cmd_promote)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
