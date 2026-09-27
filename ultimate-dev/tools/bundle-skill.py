#!/usr/bin/env python3
"""Build a runtime-only bundle of the skill.

The repository is deliberately more than the skill. Alongside the runtime it
carries the evaluation corpus, worked examples, architecture documentation,
research notes, and the source specifications — 178 files and roughly 2.1 MB of
material that a reader of the skill never loads.

Standard packaging tools do not know that. They exclude build artefacts and a
directory literally named ``evals``, so a bundle built by one includes
``evaluation/``, ``docs/``, ``examples/``, ``knowledge/``, and ``research/`` in
full. The result is a 2.5 MB artefact of which 76 files are the skill.

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
    new-arch.md, new-arch-updated.md, prd.md, ARCHITECTURE.md   source specs

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
import os
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
SKILL_DIRS = SKILL_ROOT / "skills"

# Bundled: the material a runtime loads.
RUNTIME_DIRS = ("references", "skills", "agents", "tools")
# TREE.json is the generated capability index. The kernel points a reader at
# references/capability-catalogue.md and at `tools/index-tree.py --search`; the
# JSON is the machine-readable form of the same map, so it ships.
RUNTIME_FILES = ("SKILL.md", "TREE.json")

# Excluded: everything a reader of the skill never loads. Listed explicitly so
# a new top-level tree fails the "unclassified" check rather than being silently
# bundled or silently dropped.
EXCLUDED_DIRS = ("knowledge", "evaluation", "examples", "docs", "research",
                 "evals", "catalog")
EXCLUDED_FILES = ("new-arch.md", "new-arch-updated.md", "prd.md",
                   "ARCHITECTURE.md")

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

_DIRS = (r"references|skills|agents|tools|docs|knowledge|evaluation|examples|"
         r"research|evals")
# A path counts as declared in either of the two forms prose actually uses:
# a backticked span, or a markdown link target. Matching only the backticked
# form reported 975 files as unreachable when 275 skills that reference them
# correctly had done so with `[name](references/file.md)`.
PATH_PATTERN = re.compile(
    rf"`((?:{_DIRS})/[A-Za-z0-9_./-]+)`"
    rf"|\]\(\s*((?:{_DIRS})/[A-Za-z0-9_./-]+)(?:#[^)]*)?\s*\)"
)
# `tools/call` and `tools/list` are MCP method names, not paths into this
# repository, and prose about an MCP server mentions them constantly. A
# declared path must carry a file extension or a trailing separator to count.
NOT_A_PATH = re.compile(r"\.(md|py|sh|json|toml|ya?ml|txt|csv|js|ts)$|/$")
# a path that leaves this repository: home-anchored or absolute
OUT_OF_SKILL = re.compile(
    r"(?:~|\$HOME|~/|/home/|/Users/|%[A-Z]+%\\)[A-Za-z0-9_./\\-]*"
)
# A rate or a ratio ("~60/40", "~1.5s/page") is not a path. Requiring the
# character after the prefix to be a path character rather than a digit or a
# unit drops those without dropping a real path.
NOT_A_PATH_TEXT = re.compile(r"^~?\d")
# ...and a line that names the directory as the user's own, rather than
# pointing at repository content that should have been vendored.
WORKSPACE_NAMED = re.compile(
    r"(?i)\b(your|user'?s?|output|save|write|writes?|store|stores?|keep|"
    r"creates?|configures?|set up|working|workspace|vault|reports?|results?|"
    r"artifacts?|cache|logs?|state|sessions?)\b"
)
# ...and looks like a real path rather than a sentence fragment
OUT_OF_SKILL_SHAPE = re.compile(r"[A-Za-z0-9_.-]+[/\\]")


FENCE_LINE = re.compile(r"^(\s*)(`{3,}|~{3,})(.*)$")


def strip_fenced_code(text: str) -> str:
    """Drop fenced code blocks, following CommonMark's closing rule.

    A fenced block is a sample, not a claim. skill-development/SKILL.md shows
    the reader the markdown they should write in their own SKILL.md, and that
    sample legitimately contains `references/advanced.md` even though this
    skill ships no such file. Reading it as a reference produces a dangling
    pointer that can only be fixed by deleting working documentation, which is
    the wrong repair in the wrong direction.

    The closing rule matters. A fence closes on a run of the same character that
    is at least as long as the one that opened it and carries no info string, so
    the ```bash on line 392 of incident-commander does not close the ```markdown
    opened on line 310 -- it is content. A toggle that treats any fence marker as
    a closer reads that file as five balanced blocks instead of six with one
    unclosed, and then blanks or un-blanks the wrong half of the document.
    """
    out: list[str] = []
    fence_char = ""
    fence_len = 0
    for line in text.split("\n"):
        m = FENCE_LINE.match(line)
        if m:
            token, info = m.group(2), m.group(3).strip()
            if not fence_char:
                fence_char, fence_len = token[0], len(token)
            elif token[0] == fence_char and len(token) >= fence_len and not info:
                fence_char, fence_len = "", 0
            out.append("")
            continue
        out.append("" if fence_char else line)
    return "\n".join(out)


def declared_paths(text: str) -> set[str]:
    """Every in-repo path the prose points at, in either form.

    Two capture groups means findall yields tuples, so the non-empty group of
    each match is taken; passing a tuple to a Path operation raises.
    """
    out: set[str] = set()
    for match in PATH_PATTERN.finditer(strip_fenced_code(text)):
        out.update(g for g in match.groups() if g and NOT_A_PATH.search(g))
    return out

# A path the skill tells the agent to *write* is not a reference. "Save as
# `agents/agent-name.md`" names a file that will not exist until the agent
# creates it, and reporting that as a dangling reference tells the author to
# delete an instruction that is working exactly as intended. The two were being
# conflated because declared_paths() throws away the line a path was found on,
# and the verb is the only thing that distinguishes them.
OUTPUT_DECLARATION = re.compile(
    r"(?i)\b(save as|saved as|create|creates|creating|write|writes|writing|"
    r"add|adds|maintain|maintains|update|updates|generate|generates|emit|"
    r"emits|store|stores|place|places|put|puts|output to|new file)\b"
)


def declared_output_paths(text: str) -> set[str]:
    """Paths this document declares as something to produce, not to read."""
    out: set[str] = set()
    for line in strip_fenced_code(text).splitlines():
        if not OUTPUT_DECLARATION.search(line):
            continue
        for match in PATH_PATTERN.finditer(line):
            out.update(g for g in match.groups() if g and NOT_A_PATH.search(g))
    return out

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
    # A sub-skill's own reference file is addressed skill-relative, not relative
    # to whichever file quotes it: a prompt under prompts/ saying
    # `references/x.md` means the skill's references/x.md, which is what the
    # agent reading it will open. Try that before giving up.
    # walk up to the skill that owns this file: skills/<name>/...
    parts = base.relative_to(SKILL_ROOT).parts
    owning = SKILL_DIRS / parts[1] if parts and parts[0] == "skills" and len(parts) > 1 else None
    for candidate in (base / ref, SKILL_ROOT / ref,
                      owning / ref if owning else base / ref):
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
        outputs = declared_output_paths(text)
        for ref in sorted(declared_paths(text) - outputs):
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
    """Every bundled reference file must be reachable from its SKILL.md.

    For a sub-skill, that means its own SKILL.md. For the kernel's own
    references, the chain is two hops -- SKILL.md names `references/README.md`,
    and that index names the files -- because the kernel must stay under a
    500-line ceiling and cannot inline 53 paths without breaching it.

    A one-hop check reported all 53 kernel references as orphaned the moment the
    kernel's index was compressed to group names, which is the check being wrong
    rather than the tree: progressive disclosure is the mechanism, and a reachability
    model that forbids it is measuring the opposite of what it means to measure.
    So a kernel reference reachable through the index counts as reachable.
    """
    problems: list[str] = []
    index = SKILL_ROOT / "references" / "README.md"
    via_index = (index.read_text(encoding="utf-8") if index.is_file() else "")
    for skill_md in [SKILL_ROOT / "SKILL.md", *sorted(SKILL_ROOT.glob("skills/*/SKILL.md"))]:
        if not skill_md.is_file():
            continue
        text = skill_md.read_text(encoding="utf-8")
        declared = declared_paths(text)
        is_kernel = skill_md.parent == SKILL_ROOT
        refs_dir = skill_md.parent / "references"
        if not refs_dir.is_dir():
            continue
        for path in sorted(refs_dir.glob("*.md")):
            if f"references/{path.name}" in declared:
                continue
            if is_kernel and path.name in via_index:
                continue          # reachable via references/README.md
            problems.append(
                f"{path.relative_to(SKILL_ROOT)}: not reachable from "
                f"{skill_md.relative_to(SKILL_ROOT)}"
            )
    return problems


def check_relative_links() -> list[str]:
    """Every parent-relative or dot-relative link must resolve on disk.

    PATH_PATTERN only matches a path that *starts* with a known top-level
    directory, so a link written the way a person actually writes one --
    ``../../agents/cs-chief-of-staff.md``, ``../board-meeting/SKILL.md`` -- was
    invisible to every check here. That is not a theoretical gap: boardroom
    linked three such paths, all of them broken, and the bundler reported zero
    dangling references while they were broken.

    Resolution is relative to the file carrying the link, which is how a reader
    follows it. Three outcomes are reported:

      escapes the repository   the link points outside this skill tree
      does not resolve         the target is not on disk
      points into an omitted   the target exists but the bundle drops that tree

    Fenced code and declared output paths are exempt for the same reasons as in
    check_references: a sample is not a claim, and a path the skill tells the
    agent to write is not a path it expects to find.
    """
    problems: list[str] = []
    link = re.compile(
        r"\]\(\s*(\.{1,2}/[A-Za-z0-9_.\-/]+?)\s*(?:#[^)]*)?\)|"
        r"`(\.{1,2}/[A-Za-z0-9_.\-/]+?)`"
    )
    for path in iter_runtime_files():
        if path.suffix != ".md":
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        outputs = declared_output_paths(text)
        for match in link.finditer(strip_fenced_code(text)):
            target = match.group(1) or match.group(2)
            if target in outputs:
                continue
            resolved = Path(os.path.normpath(path.parent / target))
            rel = path.relative_to(SKILL_ROOT)
            if not resolved.exists():
                problems.append(f"{rel}: {target} does not resolve")
                continue
            try:
                inside = resolved.resolve().relative_to(SKILL_ROOT.resolve())
            except ValueError:
                problems.append(f"{rel}: {target} points outside the skill tree")
                continue
            top = str(inside).split("/")[0]
            if top in EXCLUDED_DIRS or top == "evals":
                problems.append(
                    f"{rel}: {target} points into {top}/, which the bundle omits"
                )
    return problems


def check_escapes() -> list[str]:
    """No skill may point at a path outside itself and outside this repository.

    A reference is a promise to the reader that the named thing is where the
    text says. A path under the user's home directory, an absolute path on one
    machine, or a bare cross-skill file path all break that promise in a way
    that is invisible until someone follows it on a different host.

    Three shapes are rejected:
      - a home- or machine-anchored path that is not a documented placeholder
      - a cross-skill path that does not exist
      - a machine path in an executable script rather than in prose
    """
    problems: list[str] = []
    placeholders = ("<project-root>", "<agent-config-dir>", "<agent-instructions>",
                    "<path", "/Users/", "/home/", "%APPDATA%", "C:/")
    # A path under the home directory that names a tool's own configuration or
    # state is attributable: ~/.gstack/analytics, ~/.config/last30days,
    # ~/vaults/research, ~/.aeo-data. Recognising the shape rather than a list
    # of names is the point - a new tool gets this right without an edit here.
    owned = re.compile(
        r"^~?/?(?:\$\{?HOME\}?/)?(?:\.[A-Za-z0-9_.-]+|Documents|Desktop|"
        r"wt|vaults|scripts|writing|marketing-plans|competitor-ads|papers|"
        r"meetings|code|git|molecule-datasets|Downloads|m5stack|plugins|"
        r"company-vault|dev|src|projects|repos|understand-anything|"
        r"[A-Za-z0-9_]+-plans|[A-Za-z0-9_]+-vault)(?:/|$)"
    )
    # A skill may legitimately name a path that belongs to something other than
    # this repository, provided the thing it names is real and identified:
    #   - the host runtime's own configuration (~/.claude, ~/.codex, ~/.agents)
    #   - a tool's data or state directory (~/.gstack/analytics, ~/.gbrain)
    #   - an installed third-party runtime's own files (<agent-config-dir>/...)
    # What is not legitimate is a path that is neither in this repository nor
    # attributable to one of those, because a reader cannot tell whether it is
    # meant to exist. Those are the ones this check reports.
    attributable = (
        # host-runtime configuration and cross-runtime skill directories
        "~/.claude", "~/.codex", "~/.copilot", "~/.agents", "~/.config/agent",
        "~/.pi/", "~/.gemini", "~/.cursor", "~/.opencode",
        # a tool's own data/state directory
        "~/.gstack", "~/.gbrain", "~/.cache/", "~/.config/last30days",
        "~/.config/research-ops", "~/.research_sessions", "~/.pulse_sessions",
        "~/.syllabus_sessions", "~/.autoresearch", "~/.agent-reach",
        "~/.skillopt-sleep", "~/.p3/", "~/.wt/", "~~/wt",
        # an installed runtime's own files, named by its install prefix
        "<agent-config-dir>/", "$HOME/<agent-config-dir>/",
        # library and platform paths a reader can verify
        "%APPDATA%", "%USERPROFILE%", "/Users/", "/home/", "/Applications/",
        "/Library/", "C:/", "/opt/homebrew", "site-packages",
    )
    for skill_md in sorted(SKILL_ROOT.glob("skills/*/SKILL.md")):
        rel = skill_md.relative_to(SKILL_ROOT)
        text = skill_md.read_text(encoding="utf-8", errors="replace")
        for lineno, line in enumerate(text.splitlines(), 1):
            for m in OUT_OF_SKILL.finditer(line):
                target = m.group(0)
                if any(ph in target for ph in placeholders):
                    continue
                if any(ok in target for ok in attributable):
                    continue
                if owned.match(target):
                    continue
                # A skill may name a working directory it asks the user to keep
                # their own material in -- ~/marketing-plans, ~/vaults/research.
                # That is the design, not a leak, provided the line says so.
                if WORKSPACE_NAMED.search(line):
                    continue
                if not OUT_OF_SKILL_SHAPE.search(target):
                    continue
                if NOT_A_PATH_TEXT.match(target):
                    continue
                # a bare `~/` or `$HOME/` with no component names no file
                if target.rstrip("/").split("/")[-1] in ("~", "$HOME", ""):
                    continue
                problems.append(
                    f"{rel}:{lineno}  points outside the skill and this "
                    f"repository: {target}"
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
                + check_tool_exclusions() + check_escapes()
                + check_relative_links())
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
                + check_tool_exclusions() + check_escapes()
                + check_relative_links())
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
