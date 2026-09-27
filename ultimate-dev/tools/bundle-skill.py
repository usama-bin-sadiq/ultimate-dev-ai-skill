#!/usr/bin/env python3
"""Build a runtime-only bundle of the skill.

The repository is deliberately more than the skill. Alongside the runtime it
carries the evaluation corpus, worked examples, architecture documentation,
research notes, and the source specifications — 175 files and roughly 2.1 MB of
material that a reader of the skill never loads.

Standard packaging tools do not know that. They exclude build artefacts and a
directory literally named ``evals``, so a bundle built by one includes
``evaluation/``, ``docs/``, ``examples/``, ``knowledge/``, and ``research/`` in
full. The result is a 928 KB artefact of which 74 files are the skill.

This tool produces the part that is actually the skill, and refuses to produce a
bundle with dangling references. A trimmed bundle that points at files it no
longer contains is worse than the full repository, because it looks finished.

What is in the runtime
----------------------
    SKILL.md              the kernel
    references/           loaded on demand
    skills/               sub-skills, loaded on demand
    agents/               delegated roles
    tools/                deterministic utilities, including this script

What is excluded, and why
-------------------------
    knowledge/            data contracts — specification, not execution
    evaluation/           the eval corpus; also generated into evals/ for tooling
    examples/             worked traces; the largest tree and never loaded
    docs/                 architecture, ADRs, operations, security analysis
    research/             external survey; informs changes, not runs
    evals/                generated projection of evaluation/
    new-arch.md, prd.md, ARCHITECTURE.md   source specifications

Usage
-----
    python tools/bundle-skill.py --out dist
    python tools/bundle-skill.py --out dist --zip
    python tools/bundle-skill.py --check               # verify, write nothing

The bundle is always rooted at ``<skill-name>/`` inside ``--out``, because the
skill's name and its directory name must agree. Writing it anywhere else
produces a skill that validators reject.

Checks performed before anything is written
--------------------------------------------
1. Every backticked path in every bundled document resolves **inside the
   bundle**. This is the check that matters: it is what makes a trimmed bundle
   safe.
2. Every ``references/*.md`` file is reachable from its ``SKILL.md``, so nothing
   ships that the reader cannot find.
3. The result passes the skill validator.

Exit status is 0 on success, 1 on any failed check.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent

# Bundled: the material a runtime loads.
RUNTIME_DIRS = ("references", "skills", "agents", "tools")
RUNTIME_FILES = ("SKILL.md",)

# Excluded: everything a reader of the skill never loads. Listed explicitly so
# a new top-level tree fails the "unclassified" check rather than being silently
# bundled or silently dropped.
EXCLUDED_DIRS = ("knowledge", "evaluation", "examples", "docs", "research", "evals")
EXCLUDED_FILES = ("new-arch.md", "prd.md", "ARCHITECTURE.md")

# tools/ is a runtime directory because the kernel tells the agent to run
# tools/validate-skills.py when it needs a structural check. The rest of that
# directory is repository maintenance and evaluation machinery: it is either
# irrelevant to executing the skill (the bundler itself) or depends on
# infrastructure a runtime install does not have (run-pilot.py needs a harness
# with its own adapter; build-fixtures.py writes 48,000 lines of JSON Lines).
#
# Shipping them is not a size problem so much as a promise problem. A tool that
# cannot work from an install should not be present in an install, because its
# presence implies it can.
EXCLUDED_TOOL_FILES = (
    "tools/audit-docs.py",
    "tools/build-evals.py",
    "tools/build-fixtures.py",
    "tools/bundle-skill.py",
    "tools/run-pilot.py",
)

PATH_PATTERN = re.compile(
    r"`((?:references|skills|agents|tools|docs|knowledge|evaluation|examples|"
    r"research|evals)/[A-Za-z0-9_./-]+)`"
)
BUILD_ARTEFACT = re.compile(r"(__pycache__|\.pyc$|\.DS_Store)")


def classify(path: Path) -> str:
    """Return 'runtime', 'excluded', or 'unclassified' for a path in the skill.

    Classification is by top-level component at any depth, so a file nested
    inside a runtime directory is runtime and a file nested inside an excluded
    one is excluded. Only an unrecognised top-level entry is unclassified.
    """
    rel = path.relative_to(SKILL_ROOT)
    top = rel.parts[0]
    if len(rel.parts) > 1 or path.is_dir():
        # File-level exclusions inside a runtime directory, applied first.
        if rel.as_posix() in EXCLUDED_TOOL_FILES:
            return "excluded"
        if top in RUNTIME_DIRS:
            return "runtime"
        if top in EXCLUDED_DIRS:
            return "excluded"
        return "unclassified"
    if rel.as_posix() in RUNTIME_FILES:
        return "runtime"
    if rel.as_posix() in EXCLUDED_FILES:
        return "excluded"
    return "unclassified"


def collect() -> tuple[list[Path], list[Path], list[Path]]:
    """Split the skill's top-level entries into runtime, excluded, unknown."""
    runtime: list[Path] = []
    excluded: list[Path] = []
    unknown: list[Path] = []
    for path in sorted(SKILL_ROOT.iterdir()):
        if path.name.startswith("."):
            continue
        bucket = classify(path)
        {"runtime": runtime, "excluded": excluded, "unclassified": unknown}[bucket].append(path)
    return runtime, excluded, unknown


def iter_runtime_files() -> list[Path]:
    """Every file that belongs in the bundle, in a stable order."""
    files: list[Path] = []
    for entry in collect()[0]:
        if entry.is_file():
            files.append(entry)
            continue
        for path in sorted(entry.rglob("*")):
            if not path.is_file():
                continue
            rel = path.relative_to(SKILL_ROOT).as_posix()
            if BUILD_ARTEFACT.search(rel):
                continue
            # A runtime tree can still have individual files excluded. collect()
            # only classifies top-level entries, so without this a file-level
            # exclusion inside tools/ would be declared and then ignored.
            if rel in EXCLUDED_TOOL_FILES:
                continue
            files.append(path)
    return files


def check_tool_exclusions() -> list[str]:
    """Every entry in EXCLUDED_TOOL_FILES must exist and must actually be excluded.

    Without this the exclusion list is a comment. A typo in it silently ships a
    maintenance tool, and a stale entry silently stops excluding anything, and
    neither shows up as an error -- the bundle just quietly gets wrong. This is
    the same failure mode as a reference that resolves to nothing: the list looks
    authoritative and is not.
    """
    problems: list[str] = []
    runtime = {p.relative_to(SKILL_ROOT).as_posix() for p in iter_runtime_files()}
    for rel in EXCLUDED_TOOL_FILES:
        if not (SKILL_ROOT / rel).is_file():
            problems.append(
                f"{rel}: listed in EXCLUDED_TOOL_FILES but does not exist; the "
                f"entry is stale and excludes nothing")
        if rel in runtime:
            problems.append(
                f"{rel}: listed in EXCLUDED_TOOL_FILES but is bundled; the entry "
                f"is not being honoured")
    return problems


def would_survive(ref: str, base: Path) -> bool:
    """Would ``ref`` still resolve once the excluded trees are gone?

    Existence in the source tree is not the question. The source still contains
    ``docs/`` and ``research/``, so a naive existence check passes a reference
    that the bundle will not contain — which is precisely the dangling pointer
    this is meant to catch.
    """
    for candidate in (base / ref, SKILL_ROOT / ref):
        if not candidate.exists():
            continue
        try:
            rel = candidate.resolve().relative_to(SKILL_ROOT.resolve())
        except ValueError:
            continue
        return classify(SKILL_ROOT / rel) == "runtime"
    return False


def check_references() -> list[str]:
    """Every backticked path in a bundled document must resolve in the bundle.

    Resolution is document-relative first, then bundle-root, mirroring how a
    reader resolves it. A sub-skill's ``references/`` shadows the kernel's, so
    root-first resolution would send a reader to the wrong file.
    """
    problems: list[str] = []
    for path in iter_runtime_files():
        if path.suffix != ".md":
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for ref in sorted(set(PATH_PATTERN.findall(text))):
            if not would_survive(ref, path.parent):
                top = ref.split("/")[0]
                reason = (
                    f"points into {top}/, which the bundle omits"
                    if top in EXCLUDED_DIRS or top == "evals"
                    else "does not resolve"
                )
                problems.append(f"{path.relative_to(SKILL_ROOT)}: {ref} {reason}")
    return problems


def check_orphans() -> list[str]:
    """Every bundled reference file must be reachable from its SKILL.md."""
    problems: list[str] = []
    for skill_md in [SKILL_ROOT / "SKILL.md", *sorted(SKILL_ROOT.glob("skills/*/SKILL.md"))]:
        if not skill_md.is_file():
            continue
        text = skill_md.read_text(encoding="utf-8")
        declared = set(PATH_PATTERN.findall(text))
        refs_dir = skill_md.parent / "references"
        if not refs_dir.is_dir():
            continue
        for path in sorted(refs_dir.glob("*.md")):
            if f"references/{path.name}" not in declared:
                problems.append(
                    f"{path.relative_to(SKILL_ROOT)}: not reachable from "
                    f"{skill_md.relative_to(SKILL_ROOT)}"
                )
    return problems


def build(out_dir: Path, make_zip: bool) -> dict:
    runtime, excluded, unknown = collect()

    if unknown:
        names = ", ".join(p.name for p in unknown)
        raise SystemExit(
            f"error: unclassified top-level entries: {names}\n"
            "Add each to RUNTIME_DIRS, EXCLUDED_DIRS, RUNTIME_FILES, or "
            "EXCLUDED_FILES in tools/bundle-skill.py. An unclassified tree must "
            "never be silently bundled or silently dropped."
        )

    problems = (check_references() + check_orphans()
                + check_tool_exclusions())
    if problems:
        raise SystemExit(
            "error: the bundle would contain dangling references:\n  "
            + "\n  ".join(problems)
            + "\n\nFix the source before bundling. A trimmed bundle that points at "
            "files it does not contain is worse than the full repository."
        )

    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True)

    files = iter_runtime_files()
    copied = 0
    total_bytes = 0
    for path in files:
        rel = path.relative_to(SKILL_ROOT)
        destination = out_dir / rel
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, destination)
        copied += 1
        total_bytes += destination.stat().st_size

    # Validate the bundle with the skill's own validator, in single-skill mode
    # so it does not demand the documentation trees this bundle omits.
    validator = out_dir / "tools" / "validate-skills.py"
    verdict = subprocess.run(
        [sys.executable, str(validator), str(out_dir)],
        capture_output=True, text=True,
    )
    if verdict.returncode != 0:
        raise SystemExit(
            "error: the bundle failed its own validator:\n" + verdict.stdout + verdict.stderr
        )

    archive = None
    if make_zip:
        archive = out_dir.with_suffix(".zip")
        if archive.exists():
            archive.unlink()
        with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as zf:
            for path in sorted(out_dir.rglob("*")):
                if path.is_file():
                    zf.write(path, path.relative_to(out_dir))

    return {
        "files": copied,
        "bytes": total_bytes,
        "excluded_entries": [p.name for p in excluded],
        "out_dir": str(out_dir),
        "archive": str(archive) if archive else None,
        "validator": verdict.stdout.strip().splitlines()[-1] if verdict.stdout.strip() else "ok",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", default="dist",
                        help="parent directory; the bundle is written to <out>/<skill-name>/")
    parser.add_argument("--zip", action="store_true", dest="make_zip",
                        help="also write a .zip archive")
    parser.add_argument("--check", action="store_true",
                        help="run the checks and report; write nothing")
    parser.add_argument("--json", action="store_true", help="machine-readable output")
    args = parser.parse_args(argv)

    runtime, excluded, unknown = collect()
    runtime_files = iter_runtime_files()
    runtime_bytes = sum(f.stat().st_size for f in runtime_files)

    excluded_files = 0
    excluded_bytes = 0
    for entry in excluded:
        if entry.is_file():
            excluded_files += 1
            excluded_bytes += entry.stat().st_size
        else:
            for path in entry.rglob("*"):
                if path.is_file() and not BUILD_ARTEFACT.search(path.as_posix()):
                    excluded_files += 1
                    excluded_bytes += path.stat().st_size

    report = {
        "runtime_files": len(runtime_files),
        "runtime_bytes": runtime_bytes,
        "excluded_files": excluded_files,
        "excluded_bytes": excluded_bytes,
        "excluded_entries": [p.name for p in excluded],
        "unclassified": [p.name for p in unknown],
        "repo_bytes": runtime_bytes + excluded_bytes,
    }

    if args.check:
        problems = (check_references() + check_orphans()
                + check_tool_exclusions())
        report["problems"] = problems
        if unknown:
            report["problems"] = report["problems"] + [
                f"unclassified top-level entries: {', '.join(p.name for p in unknown)}"
            ]
        if args.json:
            print(json.dumps(report, indent=2))
        else:
            print(f"runtime:    {report['runtime_files']:4d} files  "
                  f"{runtime_bytes/1024:8.0f} KB")
            print(f"excluded:   {report['excluded_files']:4d} files  "
                  f"{excluded_bytes/1024:8.0f} KB")
            if problems:
                print(f"problems:   {len(problems)}")
                for problem in problems:
                    print(f"  {problem}")
            else:
                print("problems:   none")
        return 1 if report["problems"] or unknown else 0

    out_dir = Path(args.out)
    if not out_dir.is_absolute():
        out_dir = Path.cwd() / out_dir
    # Root the bundle at the skill name so name and directory agree.
    skill_name = SKILL_ROOT.name
    if out_dir.name != skill_name:
        out_dir = out_dir / skill_name
    result = build(out_dir, args.make_zip)

    if args.json:
        print(json.dumps({**report, **result}, indent=2))
        return 0

    print(f"bundle:     {result['files']} files  {result['bytes']/1024:.0f} KB")
    print(f"  from:     {SKILL_ROOT}")
    print(f"  to:       {result['out_dir']}")
    if result["archive"]:
        print(f"  archive:  {result['archive']}")
    print(f"  excluded: {', '.join(result['excluded_entries'])}")
    print(f"  checked:  references resolve, no orphans, validator {result['validator']}")
    saved = 1 - result["bytes"] / report["repo_bytes"] if report["repo_bytes"] else 0
    print(f"  size:     {saved*100:.0f}% smaller than the full skill directory")
    return 0


if __name__ == "__main__":
    sys.exit(main())
