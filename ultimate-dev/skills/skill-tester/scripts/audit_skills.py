#!/usr/bin/env python3
"""
Audit Skills - Repo-wide skill quality audit across every skill in a repository

Walks a skills root, applies the write-a-skill checklist to each skill, and
reports what needs attention, worst first. This is the tool to reach for when
the question is "how is the repository doing", rather than the question the
single-skill tools answer ("is this one skill valid").

It is a checklist runner, not a scorer: the per-skill numbers come from
skill_validator.py, script_tester.py, and quality_scorer.py, and this script
consumes their JSON so a score means the same thing everywhere. Reimplementing
their scoring here is how two tools end up disagreeing about the same skill.

Usage:
    python audit_skills.py <skills-root> [--json] [--min-score SCORE]
                           [--fail-under] [--only <glob>] [--quiet]

Examples:
    python audit_skills.py skills
    python audit_skills.py skills --json --min-score 75
    python audit_skills.py skills --only 'cit*' --fail-under

Exit status:
    0  no skill is below --min-score, and no skill is invalid
    1  at least one skill is below the threshold or invalid
    2  the skills root does not exist

Dependencies: Python Standard Library Only
"""

import argparse
import fnmatch
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, NoReturn, Optional

# Sibling tools this script shells out to rather than reimplementing.
SIBLINGS = ("skill_validator.py", "script_tester.py", "quality_scorer.py")

# The write-a-skill checklist, in the order an author should work through it.
# Each item is (id, question, severity) where severity drives the ordering of
# the roadmap: a "must" outranks a "should" at the same score.
CHECKLIST: tuple[tuple[str, str, str], ...] = (
    ("frontmatter-name", "SKILL.md has a name that matches its directory", "must"),
    ("frontmatter-description",
     "description says when to use the skill, not what it does", "must"),
    ("body-length", "SKILL.md body stays under 500 lines", "should"),
    ("no-second-description",
     "'When to use' lives in the description, not repeated in the body", "should"),
    ("directory-shape",
     "skill has scripts/ and references/ only where they carry their weight", "should"),
    ("scripts-runnable", "every bundled script compiles and answers --help", "must"),
    ("scripts-stdlib", "bundled scripts import no third-party package", "should"),
    ("references-linked", "every references/*.md file is linked from SKILL.md", "must"),
    ("referenced-paths-exist", "every path named in backticks resolves", "must"),
    ("no-provenance-claims", "no unresolved filler markers in the prose", "must"),
)

# Frontmatter keys the Agent Skills convention defines. The runtime keys are
# read by other runtimes, not by this checker.
ALLOWED_FRONTMATTER = frozenset({
    "name", "description", "license", "allowed-tools", "metadata", "compatibility",
    "version", "neutralised",
})
RUNTIME_FRONTMATTER = frozenset({
    "triggers", "tools", "model", "context", "domain", "category", "command",
    "tags", "author", "requires", "hooks", "agents", "skills", "services",
    "gbmcp", "gbrain", "user-invocable", "disable-model-invocation",
    "argument-hint", "argument_hint", "preamble-tier", "compatible_tools",
    "color", "emoji", "vibe", "not_for", "tier", "dependencies",
})
KEBAB_CASE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
FRONTMATTER_RE = re.compile(r"\A---\r?\n(.*?)\r?\n---[ \s]*(?:\r?\n|\Z)", re.DOTALL)
HEADING_RE = re.compile(r"^#{1,6}\s+(.*\S)\s*$", re.MULTILINE)
LINK_RE = re.compile(r"`((?:scripts|references|assets|agents)/[A-Za-z0-9_./-]+)`")
REFERENCE_LINK_RE = re.compile(r"`(references/[A-Za-z0-9_./-]+\.md)`")
# The same unfilled-marker rule the repository validator owns. A second
# implementation here is how the check drifts out of step with the real one, so
# this script only reports the finding and leaves the verdict to that validator.
FILLER_RE = re.compile(
    r"\b(TODO|FIXME|TBD|XXX|coming soon|lorem ipsum)\b"
    r"|(?-i:\bPLACEHOLDER\b)"
    r"|<placeholder>"
    r"|\{\{+\s*placeholder\s*\}\}+",
    re.IGNORECASE,
)
STDLIB_HINT = re.compile(r"^\s*(?:import|from)\s+([A-Za-z_][\w.]*)", re.MULTILINE)
PYTHON_SUFFIX = ".py"


def die(message: str) -> NoReturn:
    print(f"audit_skills.py: {message}", file=sys.stderr)
    raise SystemExit(2)


def parse_frontmatter(text: str) -> Dict[str, str]:
    """Parse the leading frontmatter block as flat scalars.

    Not a YAML parser on purpose: the repository validator is the authority, and
    a second parser here would only be able to disagree with it.
    """
    match = FRONTMATTER_RE.match(text)
    if match is None:
        return {}
    fields: Dict[str, str] = {}
    for line in match.group(1).replace("\r\n", "\n").split("\n"):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if line[:1] in (" ", "\t"):
            continue
        head = re.match(r"^([A-Za-z0-9_.-]+)\s*:\s*(.*)$", line)
        if head:
            value = head.group(2).strip()
            if value[:1] in "\"'":
                value = value.strip("\"'")
            fields[head.group(1)] = value
    return fields


def run_sibling(script: Path, args: List[str]) -> Optional[Dict[str, Any]]:
    """Run a sibling tool and return its JSON, or None if it cannot be run.

    A missing or failing sibling degrades the audit rather than aborting it: a
    repo-wide run over hundreds of skills should still report what it could
    check.
    """
    if not script.is_file():
        return None
    try:
        completed = subprocess.run(
            [sys.executable, str(script), *args, "--json"],
            capture_output=True, text=True, timeout=600, check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if not completed.stdout.strip():
        return None
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError:
        return None
    return payload if isinstance(payload, dict) else None


def stdlib_modules(path: Path) -> List[str]:
    """Top-level modules a Python file imports, for the stdlib-only check."""
    try:
        source = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []
    return [match.group(1).split(".")[0] for match in STDLIB_HINT.finditer(source)]


class SkillAudit:
    """The write-a-skill checklist applied to one skill directory."""

    def __init__(self, skill_dir: Path) -> None:
        self.dir = skill_dir
        self.name = skill_dir.name
        self.skill_md = skill_dir / "SKILL.md"
        self.findings: List[Dict[str, str]] = []
        self.text = ""
        self.frontmatter: Dict[str, str] = {}
        self.scripts: List[Path] = []
        self.references: List[Path] = []

    def record(self, item_id: str, severity: str, detail: str) -> None:
        self.findings.append({
            "check": item_id,
            "severity": severity,
            "detail": detail,
        })

    def load(self) -> None:
        if not self.skill_md.is_file():
            self.record("frontmatter-name", "must", "SKILL.md is missing")
            return
        try:
            self.text = self.skill_md.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            self.record("frontmatter-name", "must", f"SKILL.md unreadable: {exc}")
            return
        self.frontmatter = parse_frontmatter(self.text)
        scripts_dir = self.dir / "scripts"
        if scripts_dir.is_dir():
            self.scripts = sorted(scripts_dir.rglob(f"*{PYTHON_SUFFIX}"))
        references_dir = self.dir / "references"
        if references_dir.is_dir():
            self.references = sorted(references_dir.glob("*.md"))

    # -- individual checks ---------------------------------------------------

    def check_frontmatter(self) -> None:
        if not self.text:
            return
        name = str(self.frontmatter.get("name", "")).strip()
        if not name:
            self.record("frontmatter-name", "must", "frontmatter has no 'name'")
        elif not KEBAB_CASE.match(name):
            self.record("frontmatter-name", "must",
                        f"name {name!r} is not kebab-case")
        elif name != self.name:
            self.record("frontmatter-name", "must",
                        f"name {name!r} does not match the directory")

        description = str(self.frontmatter.get("description", "")).strip()
        if not description:
            self.record("frontmatter-description", "must", "frontmatter has no 'description'")
        elif len(description) > 1024:
            self.record("frontmatter-description", "must",
                        f"description is {len(description)} characters, limit is 1024")
        elif not description.lower().startswith("use when"):
            self.record("frontmatter-description", "should",
                        "description does not open with 'Use when'")

        unknown = sorted(
            set(self.frontmatter) - ALLOWED_FRONTMATTER - RUNTIME_FRONTMATTER
        )
        if unknown:
            self.record("frontmatter-name", "must",
                        f"unknown frontmatter keys: {', '.join(unknown)}")

    def check_body(self) -> None:
        if not self.text:
            return
        lines = len(self.text.splitlines())
        if lines > 500:
            self.record("body-length", "should",
                        f"SKILL.md is {lines} lines; move detail into references/")
        if re.search(r"^#{1,6}\s+when to use\b", self.text, re.MULTILINE | re.IGNORECASE):
            self.record("no-second-description", "should",
                        "a 'When to use' heading in the body duplicates the description")

    def check_directory_shape(self) -> None:
        for name in ("README.md", "INSTALLATION_GUIDE.md", "CHANGELOG.md"):
            if (self.dir / name).is_file():
                self.record("directory-shape", "should",
                            f"{name} is auxiliary documentation, not skill content")
        for directory in ("references", "assets"):
            path = self.dir / directory
            if path.is_dir() and not any(path.iterdir()):
                self.record("directory-shape", "should", f"{directory}/ is empty")

    def check_scripts(self, script_report: Optional[Dict[str, Any]]) -> None:
        if not self.scripts and not script_report:
            return
        for script in self.scripts:
            for module in stdlib_modules(script):
                if module in ("__future__",) or module.startswith("_"):
                    continue
                # Local modules and sibling skill files are not packages.
                if (self.dir / "scripts" / f"{module}.py").is_file():
                    continue
                if (self.dir / f"{module}.py").is_file():
                    continue
                if module in _STDLIB:
                    continue
                self.record("scripts-stdlib", "should",
                            f"{script.name} imports {module}, which is not stdlib")
                break
        if script_report is None:
            self.record("scripts-runnable", "should",
                        "script_tester.py could not be run, so script health is unmeasured")
        else:
            for entry in script_report.get("scripts", []) or []:
                if not entry.get("passed", True):
                    detail = "; ".join(
                        str(f) for f in (entry.get("errors") or entry.get("issues") or [])
                    ) or entry.get("status", "failed")
                    self.record("scripts-runnable", "must",
                                f"{entry.get('name', '?')}: {detail}")

    def check_references(self) -> None:
        linked = set(REFERENCE_LINK_RE.findall(self.text))
        for reference in self.references:
            rel = f"references/{reference.name}"
            if rel not in linked:
                self.record("references-linked", "must",
                            f"{rel} exists but SKILL.md never links it")
        for target in sorted(set(LINK_RE.findall(self.text))):
            if not (self.dir / target).exists():
                self.record("referenced-paths-exist", "must",
                            f"SKILL.md names {target}, which does not exist")

    def check_prose(self) -> None:
        for number, line in enumerate(self.text.splitlines(), 1):
            match = FILLER_RE.search(line)
            if match and not re.search(
                r"(never|do not|must not|avoid|refuse|forbid)", line, re.IGNORECASE
            ):
                self.record("no-provenance-claims", "must",
                            f"line {number}: unfilled marker {match.group(0)!r}")

    # -- report --------------------------------------------------------------

    def report(self) -> Dict[str, Any]:
        """Run every check that needs only the skill directory.

        The script-health check is not run here: it needs the sibling tool, and
        calling it twice would record its "could not be run" finding alongside
        the real one.
        """
        self.load()
        self.check_frontmatter()
        self.check_body()
        self.check_directory_shape()
        self.check_references()
        self.check_prose()
        musts = sum(1 for f in self.findings if f["severity"] == "must")
        shoulds = len(self.findings) - musts
        return {
            "skill": self.name,
            "path": str(self.dir),
            "ok": musts == 0,
            "must_fix": musts,
            "should_fix": shoulds,
            "lines": len(self.text.splitlines()),
            "scripts": len(self.scripts),
            "references": len(self.references),
            "findings": self.findings,
        }


def _load_stdlib_names() -> frozenset:
    """Top-level module names in the running interpreter's standard library."""
    import sys as _sys

    names = set(_sys.stdlib_module_names)
    names.update(getattr(_sys, "builtin_module_names", ()))
    return frozenset(names)


_STDLIB = _load_stdlib_names()


def discover(root: Path) -> List[Path]:
    """Every skill directory under root, in name order."""
    return sorted(
        entry for entry in root.iterdir()
        if entry.is_dir() and (entry / "SKILL.md").is_file()
        and not entry.name.startswith((".", "_"))
    )


def render_text(summary: Dict[str, Any]) -> str:
    lines: List[str] = []
    lines.append("SKILL AUDIT")
    lines.append(f"  skills scanned:  {summary['skills_scanned']}")
    lines.append(f"  passing:         {summary['skills_passing']}")
    lines.append(f"  with must-fix:   {summary['skills_with_must_fix']}")
    lines.append(f"  total findings:  {summary['total_findings']}")
    lines.append("")

    if summary["worst"]:
        lines.append(f"{'skill':<40} must  should  score  grade")
        lines.append("-" * 72)
        for entry in summary["worst"]:
            lines.append(
                f"{entry['skill'][:40]:<40} {entry['must_fix']:>4}  "
                f"{entry['should_fix']:>6}  {entry.get('score', '-'):>5}  "
                f"{entry.get('grade') or '-':<5}"
            )
        lines.append("")

    for entry in summary["worst"]:
        if not entry["findings"]:
            continue
        lines.append(f"{entry['skill']}")
        for finding in entry["findings"][:8]:
            lines.append(f"  [{finding['severity']}] {finding['check']}: {finding['detail']}")
        remaining = len(entry["findings"]) - 8
        if remaining > 0:
            lines.append(f"  ... {remaining} more")
        lines.append("")

    return "\n".join(lines)


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="audit_skills.py",
        description="Audit every skill under a root against the write-a-skill checklist.",
        epilog=(
            "Per-skill scores come from the sibling tools, so a score means the "
            "same thing here as it does when a single skill is checked."
        ),
    )
    parser.add_argument("root", help="directory holding one subdirectory per skill")
    parser.add_argument("--json", action="store_true", help="emit machine-readable output")
    parser.add_argument("--min-score", type=float, default=0.0,
                        help="flag any skill scoring below this")
    parser.add_argument("--only", help="audit only skills matching this glob")
    parser.add_argument("--quiet", action="store_true", help="print only the summary")
    parser.add_argument("--limit", type=int, default=25,
                        help="how many failing skills to list in full (default 25)")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    if not root.is_dir():
        die(f"{root} is not a directory")

    here = Path(__file__).resolve().parent
    validator = here / "skill_validator.py"
    tester = here / "script_tester.py"
    scorer = here / "quality_scorer.py"
    for sibling in SIBLINGS:
        if not (here / sibling).is_file():
            print(f"audit_skills.py: {sibling} not found beside this script; "
                  "its checks will be reported as unmeasured", file=sys.stderr)

    skills = [d for d in discover(root) if not args.only or fnmatch.fnmatch(d.name, args.only)]
    if not skills:
        die(f"no skill directories with a SKILL.md under {root}")

    results: List[Dict[str, Any]] = []
    for skill_dir in skills:
        audit = SkillAudit(skill_dir)
        entry = audit.report()

        # Feed the audit's own findings into the script checks, then take the
        # numbers from the sibling tools rather than scoring here.
        audit.check_scripts(run_sibling(tester, [str(skill_dir)]))
        entry["findings"] = audit.findings
        musts = sum(1 for f in entry["findings"] if f["severity"] == "must")
        entry["must_fix"] = musts
        entry["should_fix"] = len(entry["findings"]) - musts
        entry["ok"] = musts == 0

        structure = run_sibling(validator, [str(skill_dir)])
        if structure:
            entry["structure_score"] = structure.get("overall_score")
            entry["compliance_level"] = structure.get("compliance_level")

        quality = run_sibling(scorer, [str(skill_dir)])
        if quality:
            entry["score"] = quality.get("overall_score")
            entry["grade"] = quality.get("letter_grade")
            entry["tier_recommendation"] = quality.get("tier_recommendation")

        results.append(entry)

    def sort_key(entry: Dict[str, Any]) -> tuple:
        return (
            -entry["must_fix"],
            -(entry.get("score") or 0.0),
            entry["skill"],
        )

    ranked = sorted(results, key=sort_key)
    below = [
        entry for entry in ranked
        if entry["must_fix"] > 0
        or (args.min_score and (entry.get("score") or 0.0) < args.min_score)
    ]

    summary = {
        "root": str(root),
        "skills_scanned": len(results),
        "skills_passing": sum(1 for entry in results if entry["ok"]),
        "skills_with_must_fix": sum(1 for entry in results if entry["must_fix"]),
        "total_findings": sum(len(entry["findings"]) for entry in results),
        "min_score": args.min_score,
        "worst": below[: args.limit] if below else [],
        "skills": results,
    }

    if args.json:
        print(json.dumps(summary, indent=2, default=str))
    elif not args.quiet:
        print(render_text(summary))
    else:
        print(
            f"{summary['skills_scanned']} skills, {summary['skills_passing']} passing, "
            f"{summary['skills_with_must_fix']} with must-fix findings, "
            f"{summary['total_findings']} findings"
        )

    return 1 if below else 0


if __name__ == "__main__":
    raise SystemExit(main())
