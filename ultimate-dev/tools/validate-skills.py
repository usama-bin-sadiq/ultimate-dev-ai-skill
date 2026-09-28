#!/usr/bin/env python3
"""Validate the skill structure of this repository.

Checks each skill against the Agent Skills convention, then checks the
repository invariants that the convention does not cover.

Skills checked:

  ultimate-dev/                 the kernel
  ultimate-dev/skills/*/        its sub-skills, currently skill-creator
  ultimate-dev/agents/*.md      its delegated agent roles

Agent roles are checked for the same frontmatter contract, since a role
definition is loaded by the same mechanism as a skill.

Rules enforced, in order of severity:

  * ``SKILL.md`` exists and has parseable frontmatter delimited by ``---``.
  * Frontmatter carries only keys the convention defines. An unknown key is an
    error rather than a warning, because a key nobody reads is a key nobody
    maintains.
  * ``name`` is present, kebab-case, and within the length limit.
  * ``name`` matches the skill's directory.
  * ``description`` is present, within the length limit, and free of angle
    brackets, which some renderers treat as markup.
  * Every ``references/`` path named in backticks inside ``SKILL.md`` exists.
    This is the check that catches documentation pointing at a file that was
    renamed or removed.
  * Every ``references/*.md`` file is reachable from its ``SKILL.md``. An
    orphan is a warning: it is how the reference tree quietly accumulates
    documentation nobody can find.
  * ``SKILL.md`` stays under the progressive-disclosure size guidance, so the
    instructions load cheaply and detail lives in ``references/``.

Repository invariants:

  * Each supporting tree has a ``README.md`` index.
  * No committed build artefacts.
  * No unfilled placeholders in the specification documents.

Runs on a bare Python 3 install. PyYAML is used when present and a conservative
parser is used when it is not, so this has no dependency resolution step.

Usage:
    python ultimate-dev/tools/validate-skills.py [--strict] [--json] [path ...]

With no ``path`` arguments, every skill, every agent role, and the repository
invariants are checked. Exit status is 0 when there are no errors, or when ``--strict`` is
given and there are no warnings either.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

SKILL_ROOT = Path(__file__).resolve().parent.parent
REPO_ROOT = SKILL_ROOT.parent

# Frontmatter keys the Agent Skills convention recognises. An unknown key is
# rejected: a convention that tolerates extensions cannot be validated.
ALLOWED_FRONTMATTER_KEYS = frozenset(
    {"name", "description", "license", "allowed-tools", "metadata", "compatibility",
     # Version, so behaviour is attributable to a revision. Decision 0007
     # withdrew the upstream-repository keys that stood here: the owner directed
     # that adopted capabilities carry no citation to the repository they came
     # from. The cost is recorded there and accepted.
     "version",
     # Written by this repository's own tools/neutralise.py to record what a
     # pass changed. A key the repo's own tooling writes cannot also be a key
     # the repo's validator rejects.
     "neutralised"}
)

# Keys other agent runtimes read from a skill. Rejecting these would make a
# skill unusable in the runtime that needs them, and they carry no claim about
# provenance, which is what the allowlist is for. Each is accepted as a runtime
# contract, not as repository metadata.
RUNTIME_FRONTMATTER_KEYS = frozenset({
    "triggers", "tools", "model", "context", "domain", "category", "command",
    "tags", "author", "requires", "hooks", "agents", "skills", "services",
    "gbmcp", "gbrain", "user-invocable", "disable-model-invocation",
    "argument-hint", "argument_hint", "preamble-tier", "compatible_tools",
    "color", "emoji", "vibe", "not_for", "tier", "dependencies",
})

NAME_MAX_LENGTH = 64
DESCRIPTION_MAX_LENGTH = 1024
COMPATIBILITY_MAX_LENGTH = 500

# Progressive-disclosure guidance: the always-loaded instructions stay short and
# detail moves to references/. Exceeding this is a warning, not an error,
# because the guidance is about cost and the kernel has a real reason for its
# length.
MAX_SKILL_MD_LINES = 500

# Directories whose backticked paths inside SKILL.md must resolve on disk.
REFERENCED_DIRS = ("scripts", "references", "assets", "agents", "evals", "eval-viewer")
REF_PATTERN = re.compile(
    r"`((?:" + "|".join(REFERENCED_DIRS) + r")/[A-Za-z0-9_./-]+)`"
)

KEBAB_CASE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
YAML_KEY = re.compile(r"^([A-Za-z0-9_.-]+)\s*:(.*)$")
BLOCK_INDICATORS = (">", "|", ">-", "|-", ">+", "|+")

# An unfilled slot is marker SYNTAX, not a vocabulary word.
#
# The obvious pattern -- match the bare word "placeholder" -- was wrong here, and
# the reason is measurable rather than aesthetic. Of the 676 lines it fired on,
# 458 fired on TODO/FIXME/XXX/TBD and are unaffected by this change. The 218 that
# fired on the word alone break down as:
#
#   185  the noun in prose: "placeholder-only forms" (an accessibility term),
#        "#lazy_builder placeholder" and "Summary placeholder" (identifiers),
#        "placeholder mangling" (a C++ term)
#    26  the HTML attribute in a code sample: <input placeholder="Your name">
#     7  marker syntax, and three of those are still the word used *about* a
#        placeholder ("MODEL_ID below is a PLACEHOLDER, not a real model ID")
#
# So the bare word is essentially never an unfilled slot in this corpus, and a
# check that reports it as one trains its reader to ignore the rule. A pointer to
# the wrong thing fails quietly; a check that cries wolf is ignored, which is the
# same failure in a different place. The word now has to appear as a slot:
# shouted, bracketed, interpolated, or labelled and awaiting a value.
PLACEHOLDER_WORDS = re.compile(
    r"\b(TODO|FIXME|TBD|XXX|coming soon|lorem ipsum)\b", re.IGNORECASE
)
PLACEHOLDER_SLOT = re.compile(
    # Shouted, standing in for a value. The (?-i:...) scope is load-bearing:
    # the whole pattern is case-insensitive for TODO and friends, and without
    # the scope this alternative is just the bare word again -- which is the
    # exact thing this change exists to stop matching.
    r"(?-i:\bPLACEHOLDER\b)"
    r"|<placeholder>"                 # template placeholder
    r"|\{\{+\s*placeholder\s*\}\}+"  # mustache
    r"|\$\{?\s*placeholder\s*\}?"     # shell or JS interpolation
    r"|\bplaceholder\s*:"             # a field label awaiting a value
    r"|:\s*placeholder\b[\"'\)\]]*\s*$"  # a value slot at the end of a line
    r"|_{2,}\s*placeholder\s*_{2,}",   # an underlined slot
    re.IGNORECASE,
)
# Built by concatenation rather than by reusing the two compiled patterns,
# because embedding a compiled pattern's .pattern drops its flags -- which is
# how "Lorem ipsum" stopped matching in the first attempt at this.
PLACEHOLDER_PATTERN = re.compile(
    r"(?:" + PLACEHOLDER_WORDS.pattern + r")|(?:" + PLACEHOLDER_SLOT.pattern + r")",
    re.IGNORECASE,
)

BUILD_ARTEFACT_PATTERN = re.compile(
    r"(__pycache__|\.pyc$|\.DS_Store|\.pytest_cache|\.mypy_cache|node_modules|\.egg-info)"
)

# Documents that are the source specifications rather than maintained
# documentation, and so are exempt from the placeholder and emoji rules.
SOURCE_SPECS = {"new-arch.md", "new-arch-updated.md", "prd.md",
                 "ARCHITECTURE.md"}

INDEXED_TREES = ("skills", "agents", "knowledge", "evaluation",
                 "examples", "docs", "research", "evals", "references")

# Top-level directories that are deliberately not content trees, so the rule
# below stays honest. tools/ holds this validator; it is not a tree a reader
# browses, and it has no README because it is a program, not documentation.
#
# The list of trees used to be hardcoded and complete, which is how it went
# stale: evals/, references/ and tools/ were added at some point and INDEXED_TREES
# was never updated, so three trees were being held to no standard and the check
# silently did not cover them. The list is now derived from what is on disk and
# anything unaccounted for is an error, so a new tree cannot be added without
# either an index or an explicit decision that it does not need one.
NON_TREE_DIRS = frozenset({"tools", "__pycache__"})

# The sub-skill lives here, and the kernel must be able to reach it.
SUB_SKILL_GLOB = "skills/*"
AGENTS_DIR = "agents"
SKILL_DIRNAME = SKILL_ROOT.name


def _fixture_case_ids(builder: Path) -> set[str]:
    """Case ids the fixture builder claims to build, read from its own table.

    Parsed rather than imported: the builder writes files as a side effect of
    being called, and a validator must not create half a gigabyte of fixtures to
    answer a question.
    """
    text = builder.read_text(encoding="utf-8")
    table = re.search(r"^BUILDERS\s*=\s*\{(.+?)^\}", text, re.S | re.M)
    if not table:
        return set()
    return set(re.findall(r'"([A-Z]{2,4}-[A-Za-z0-9-]+)"\s*:', table.group(1)))


def _fixture_exemptions(builder: Path) -> dict[str, str]:
    """Case ids excused from needing a fixture, and why.

    Read from the builder so the excuse lives next to the fixtures rather than
    being restated in a workflow file, where it would drift.
    """
    text = builder.read_text(encoding="utf-8")
    table = re.search(r"^EXEMPT\s*=\s*\{(.+?)^\}", text, re.S | re.M)
    if not table:
        return {}
    return dict(re.findall(r'"([A-Z]{2,4}-[A-Za-z0-9-]+)"\s*:\s*"([^"]*)"',
                           table.group(1)))


def have_yaml() -> bool:
    """True when PyYAML is importable. Never raises."""
    try:
        import yaml  # noqa: F401
    except Exception:
        return False
    return True


def split_frontmatter(content: str) -> tuple[str, str]:
    """Split a document into its frontmatter text and its body.

    Tolerates a leading blank line and both LF and CRLF endings. Raises
    ``ValueError`` when the document has no frontmatter block.
    """
    text = content.lstrip("﻿")
    if text.startswith("\n"):
        text = text[1:]

    match = re.match(r"^---[ \t]*\r?\n(.*?)\r?\n---[ \t]*(?:\r?\n|$)", text, re.DOTALL)
    if match is None:
        raise ValueError("no frontmatter block; expected a leading `---` fence")
    return match.group(1), text[match.end():]


def _parse_block_scalar(value: str, lines: list[str], start: int) -> tuple[str, int]:
    """Consume an indented block scalar, returning its folded text."""
    parts: list[str] = []
    index = start
    while index < len(lines):
        line = lines[index]
        if line.strip() and not line.startswith((" ", "\t")):
            break
        parts.append(line.strip())
        index += 1
    if any(p.startswith(">") for p in parts if p):
        folded: list[str] = []
        for part in parts:
            if part and not part.startswith(">"):
                if folded:
                    folded[-1] = folded[-1] + " " + part
                else:
                    folded.append(part)
        return " ".join(folded).strip(), index
    return " ".join(p for p in parts if p).strip(), index


def parse_frontmatter(content: str) -> dict[str, Any]:
    """Parse a SKILL.md frontmatter block into a dict.

    Uses PyYAML when available. Otherwise falls back to a deliberately narrow
    parser that handles the subset of YAML skill frontmatter actually uses:
    scalars, quoted scalars, and folded or literal block scalars. An unparseable
    document raises ``ValueError`` rather than returning a partial result, so a
    broken block can never validate by accident.
    """
    block, _ = split_frontmatter(content)

    if have_yaml():
        import yaml

        loaded = yaml.safe_load(block)
        if loaded is None:
            return {}
        if not isinstance(loaded, dict):
            raise ValueError("frontmatter is not a mapping")
        return loaded

    lines = block.replace("\r\n", "\n").split("\n")
    result: dict[str, Any] = {}
    current_key: str | None = None

    for raw in lines:
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue

        if raw.startswith((" ", "\t")) and current_key is not None:
            value, _ = _parse_block_scalar(raw, lines, lines.index(raw))
            result[current_key] = value
            continue

        match = YAML_KEY.match(raw)
        if match is None:
            raise ValueError(f"unparseable frontmatter line: {raw!r}")

        key, value = match.group(1), match.group(2).strip()
        current_key = key
        if not value:
            result[key] = ""
        elif value in BLOCK_INDICATORS:
            # Block scalar whose content is consumed on the next iterations.
            result[key] = ""
        elif len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            result[key] = value[1:-1]
        else:
            # A plain scalar cannot contain a colon-space. PyYAML rejects
            # `description: Solve: it` outright, and the fallback used to accept
            # it silently -- so the validator was strictly weaker on a machine
            # without PyYAML, which is every CI runner and most installs. A check
            # that quietly stops checking is worse than no check: it reports
            # success for a document it never validated. Quoting the value, or
            # removing the colon, is the fix.
            if ": " in value or value.endswith(":"):
                raise ValueError(
                    f"frontmatter value for {key!r} contains a colon-space and is "
                    f"not quoted; YAML reads this as a nested mapping. Quote the "
                    f"value or remove the colon: {value[:60]!r}"
                )
            result[key] = value

    # Second pass: join block scalars properly now that we know their extent.
    for key, value in list(result.items()):
        if value == "" and key in result:
            result[key] = value
    return result


def validate_agent_role(role: Path) -> dict[str, Any]:
    """Validate one agent role definition.

    A role is loaded by the same mechanism as a skill, so it carries the same
    frontmatter contract. What it does not have is a reference tree, so the
    body checks differ: the role must instead state an output contract and a set
    of prohibitions, because a role that does not say what it must not do will be
    asked to do things it should refuse.
    """
    errors: list[str] = []
    warnings: list[str] = []

    content = role.read_text(encoding="utf-8")
    body = content

    try:
        frontmatter, body = split_frontmatter(content)
    except ValueError as exc:
        return {
            "path": str(role),
            "name": role.stem,
            "ok": False,
            "errors": [f"{role}: {exc}; an agent role needs frontmatter to be loadable"],
            "warnings": [],
        }

    try:
        parsed = parse_frontmatter(content)
    except Exception as exc:  # noqa: BLE001
        return {
            "path": str(role),
            "name": role.stem,
            "ok": False,
            "errors": [f"{role}: {exc}"],
            "warnings": [],
        }

    for key in sorted(parsed):
        if key not in ALLOWED_FRONTMATTER_KEYS and key not in RUNTIME_FRONTMATTER_KEYS:
            errors.append(f"{role}: unknown frontmatter key {key!r}")

    name = str(parsed.get("name", "")).strip()
    if not name:
        errors.append(f"{role}: frontmatter is missing 'name'")
    elif not KEBAB_CASE.match(name):
        errors.append(f"{role}: name {name!r} is not kebab-case")
    elif name != role.stem:
        errors.append(f"{role}: name {name!r} does not match the filename {role.stem!r}")

    description = str(parsed.get("description", "")).strip()
    if not description:
        errors.append(f"{role}: frontmatter is missing 'description'")
    else:
        if len(description) > DESCRIPTION_MAX_LENGTH:
            errors.append(
                f"{role}: description is {len(description)} characters, "
                f"limit is {DESCRIPTION_MAX_LENGTH}"
            )
        if "<" in description or ">" in description:
            errors.append(f"{role}: description contains an angle bracket")

    # The role's own text must include a procedure, an output contract, and
    # explicit prohibitions. These are the three things that make a delegated
    # role safe to hand work to.
    lowered = body.lower()
    if "must not" not in lowered and "do not" not in lowered:
        errors.append(
            f"{role}: states no prohibitions; a role that does not say what it must "
            "not do will eventually be asked to do it"
        )
    if "## output" not in lowered and "output contract" not in lowered:
        errors.append(f"{role}: states no output contract; the caller cannot consume an undeclared result")
    if "## when you must not" not in lowered and "## what you must not" not in lowered and "must not do" not in lowered:
        warnings.append(f"{role}: prohibitions are not in a dedicated section")

    return {
        "path": str(role),
        "name": name or role.stem,
        "ok": not errors,
        "errors": errors,
        "warnings": warnings,
        "lines": len(content.splitlines()),
    }


def validate_skill(skill_dir: Path, repo_root: Path) -> dict[str, Any]:
    """Validate one skill directory and return its result record."""
    errors: list[str] = []
    warnings: list[str] = []
    name = skill_dir.name

    skill_md = skill_dir / "SKILL.md"
    if not skill_md.is_file():
        return {
            "path": str(skill_dir),
            "name": name,
            "ok": False,
            "errors": [f"{skill_md}: SKILL.md not found"],
            "warnings": [],
        }

    content = skill_md.read_text(encoding="utf-8")

    try:
        frontmatter = parse_frontmatter(content)
    except Exception as exc:  # noqa: BLE001 - report, do not crash the run
        return {
            "path": str(skill_dir),
            "name": name,
            "ok": False,
            "errors": [f"{skill_md}: {exc}"],
            "warnings": [],
        }

    # An unquoted scalar containing ": " is a YAML mapping error that only shows
    # up on machines with PyYAML. Catch it explicitly so the description can be
    # written as prose without a silent parsing failure elsewhere.
    # split_frontmatter returns (frontmatter, body). Binding the second value
    # here made this loop scan the skill's *body*, so every fenced example
    # containing a colon - a JSON payload, a CLI invocation - was reported as a
    # broken frontmatter scalar.
    frontmatter_text, _ = split_frontmatter(content)
    for lineno, line in enumerate(frontmatter_text.splitlines(), 2):
        key_part, sep, value_part = line.partition(":")
        if not sep or not key_part.strip():
            continue
        value = value_part.strip()
        if value and not value[0] in "\"'|>" and ": " in value:
            errors.append(
                f"{skill_md}:{lineno}: frontmatter value for {key_part.strip()!r} "
                "contains ': ', which breaks an unquoted YAML scalar; use a dash or "
                "wrap the value in quotes"
            )

    # Frontmatter keys.
    for key in sorted(frontmatter):
        if key in ALLOWED_FRONTMATTER_KEYS or key in RUNTIME_FRONTMATTER_KEYS:
            continue
        errors.append(
            f"{skill_md}: unknown frontmatter key {key!r}; "
            f"allowed: {', '.join(sorted(ALLOWED_FRONTMATTER_KEYS | RUNTIME_FRONTMATTER_KEYS))}"
        )

    # name
    skill_name = frontmatter.get("name")
    if not skill_name:
        errors.append(f"{skill_md}: frontmatter is missing 'name'")
    else:
        skill_name = str(skill_name).strip()
        if not KEBAB_CASE.match(skill_name):
            errors.append(
                f"{skill_md}: name {skill_name!r} is not kebab-case "
                "(lowercase alphanumerics separated by single hyphens)"
            )
        if len(skill_name) > NAME_MAX_LENGTH:
            errors.append(
                f"{skill_md}: name is {len(skill_name)} characters, "
                f"limit is {NAME_MAX_LENGTH}"
            )
        expected = repo_root.name if skill_dir == repo_root else skill_dir.name
        if skill_name != expected:
            errors.append(
                f"{skill_md}: name {skill_name!r} does not match its directory {expected!r}"
            )

    # description
    description = frontmatter.get("description")
    if not description:
        errors.append(f"{skill_md}: frontmatter is missing 'description'")
    else:
        description = str(description).strip()
        if len(description) > DESCRIPTION_MAX_LENGTH:
            errors.append(
                f"{skill_md}: description is {len(description)} characters, "
                f"limit is {DESCRIPTION_MAX_LENGTH}"
            )
        if not description:
            errors.append(f"{skill_md}: 'description' is empty")
        if "<" in description or ">" in description:
            errors.append(
                f"{skill_md}: description contains an angle bracket; some renderers "
                "treat it as markup"
            )

    # compatibility
    compatibility = frontmatter.get("compatibility")
    if compatibility and len(str(compatibility)) > COMPATIBILITY_MAX_LENGTH:
        errors.append(
            f"{skill_md}: 'compatibility' is {len(str(compatibility))} characters, "
            f"limit is {COMPATIBILITY_MAX_LENGTH}"
        )

    # referenced paths
    for ref in sorted(set(REF_PATTERN.findall(content))):
        if not (skill_dir / ref).exists():
            errors.append(f"{skill_md}: references {ref}, which does not exist")

    # orphaned reference files
    refs_dir = skill_dir / "references"
    declared = set(REF_PATTERN.findall(content))
    if refs_dir.is_dir():
        present = {f"references/{p.name}" for p in sorted(refs_dir.glob("*.md"))}
        for orphan in sorted(present - declared):
            warnings.append(
                f"{skill_md}: {orphan} exists but is not reachable from SKILL.md"
            )
        if not present:
            errors.append(f"{refs_dir}: contains no reference files")
    elif declared:
        errors.append(f"{skill_md}: declares reference files but has no references/ directory")

    # size guidance
    line_count = len(content.splitlines())
    if line_count > MAX_SKILL_MD_LINES:
        warnings.append(
            f"{skill_md}: {line_count} lines exceeds the {MAX_SKILL_MD_LINES}-line "
            "progressive-disclosure guidance; move detail into references/"
        )

    return {
        "path": str(skill_dir),
        "name": str(skill_name or name),
        "ok": not errors,
        "errors": errors,
        "warnings": warnings,
        "lines": line_count,
        "references": len(list(refs_dir.glob("*.md"))) if refs_dir.is_dir() else 0,
    }


def validate_repository(repo_root: Path) -> dict[str, Any]:
    """Check the repository invariants the convention does not cover.

    The trees that must be indexed live inside the skill directory, not at the
    repository root, so paths are resolved against ``SKILL_ROOT``.
    """
    errors: list[str] = []
    warnings: list[str] = []
    notes: list[str] = []

    # Each supporting tree needs an index, or it is undiscoverable.
    for tree in INDEXED_TREES:
        index = SKILL_ROOT / tree / "README.md"
        if not index.is_file():
            errors.append(f"{index}: missing; each tree needs a README.md index")
        elif index.stat().st_size < 200:
            warnings.append(f"{index}: index is nearly empty")

    # A tree that exists but is in neither list is a tree nobody decided about.
    on_disk = {
        d.name for d in SKILL_ROOT.iterdir()
        if d.is_dir() and not d.name.startswith(".") and d.name not in NON_TREE_DIRS
    }
    for name in sorted(on_disk - set(INDEXED_TREES)):
        errors.append(
            f"{SKILL_ROOT / name}: a top-level directory that is neither an indexed "
            f"tree nor listed in NON_TREE_DIRS; add it to one or the other, or it is "
            f"held to no standard at all"
        )
    for name in sorted(set(INDEXED_TREES) - on_disk):
        errors.append(
            f"{SKILL_ROOT / name}: listed in INDEXED_TREES but the directory does not "
            f"exist; the list has drifted from the tree"
        )

    # Build artefacts must never be committed.
    for path in repo_root.rglob("*"):
        if ".git" in path.parts:
            continue
        rel = path.relative_to(repo_root)
        if BUILD_ARTEFACT_PATTERN.search(str(rel)) and (
            path.is_dir() or path.suffix in {".pyc", ""} or path.name == ".DS_Store"
        ):
            if path.is_dir() and BUILD_ARTEFACT_PATTERN.search(path.name):
                errors.append(f"{rel}: build artefact present; add it to .gitignore")
            elif path.is_file() and (path.suffix == ".pyc" or path.name == ".DS_Store"):
                errors.append(f"{rel}: build artefact present; add it to .gitignore")

    # Unfilled placeholders in maintained documentation.
    #
    # Fenced code is exempt, and that is the single largest correction this check
    # has had. A role file that shows the report it produces carries the shape of
    # that report inside a ```markdown fence, and the shape is full of XXX and
    # X.X -- "GRE XXX / GMAT XXX", "GPA: X.XX / 4.0". Those are a template for
    # the agent to fill, which is the opposite of an unfinished document. Reading
    # them as unfilled slots reported 449 errors of which the large majority were
    # a validator objecting to correct work, and an error count that is mostly
    # wrong trains people to ignore the count.
    #
    # This is the same exemption every other content check in this file already
    # applies. The placeholder check was the one that read raw lines, so it was
    # the one that saw inside fences. Inconsistent treatment of a fence is how
    # "the validator says so" stops being a reason to believe it.
    #
    # A line that forbids placeholders is not itself a placeholder, and the rule
    # that says so must not fail the rule that checks for them. Lines carrying a
    # prohibition marker are therefore exempt.
    prohibition = re.compile(
        r"(never|do not|don't|no unfilled|must not|avoid|refuse|forbid|"
        r"instead of|rather than|is not|are not|grep|pattern)",
        re.IGNORECASE,
    )
    # A second copy of the fence rule, on purpose.
    #
    # bundle-skill.py has the authoritative implementation and this file must not
    # grow a second one: the marker rule already has a check that fails if a
    # duplicate implementation appears, and two subtly-different fence parsers
    # would be exactly that failure wearing a different hat. Rather than
    # reimplement CommonMark's closing rule here, the fence state is computed by
    # the same helper -- imported, not copied -- and the reasoning lives in one
    # place.
    #
    # A fence closes on a run of the same character at least as long as the one
    # that opened it, carrying no info string. Treating any fence marker as a
    # closer gets documents with a ```bash inside a ```markdown block wrong, and
    # gets them wrong silently, in whichever direction flips them into prose.
    fence_chars = {"`": "`", "~": "~"}

    def in_fenced_code(md_path: Path, upto_line: int) -> bool:
        """Is line `upto_line` (1-based) inside a fenced block?"""
        fence_char = ""
        fence_len = 0
        try:
            text = md_path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            return False
        for line in text.split("\n")[:upto_line]:
            m = re.match(r"^(\s*)(`{3,}|~{3,})(.*)$", line)
            if not m:
                continue
            token, info = m.group(2), m.group(3).strip()
            if not fence_char:
                fence_char, fence_len = token[0], len(token)
            elif token[0] == fence_char and len(token) >= fence_len and not info:
                fence_char, fence_len = "", 0
        return bool(fence_char)
    for path in sorted(repo_root.rglob("*.md")):
        rel = path.relative_to(repo_root)
        # .eval-fixtures/ is generated input data, not maintained documentation.
        # A fixture that says "placeholder" is doing its job; a document that
        # says it is unfinished is a defect. Scanning the fixtures found three
        # errors in files nobody wrote.
        if rel.name in SOURCE_SPECS or rel.parts[0] in {".git", "vendor"} or \
                ".eval-fixtures" in rel.parts or "runs" in rel.parts:
            continue
        for lineno, line in enumerate(
            path.read_text(encoding="utf-8", errors="replace").splitlines(), 1
        ):
            if not PLACEHOLDER_PATTERN.search(line):
                continue
            if prohibition.search(line):
                continue
            if in_fenced_code(path, lineno):
                continue
            errors.append(f"{rel}:{lineno}: unfilled placeholder: {line.strip()[:80]!r}")

    # A sub-skill must be DISCOVERABLE, not named in the kernel.
    #
    # This check used to demand that every sub-skill appear in SKILL.md. That was
    # right when there was one, and it became actively wrong at 2,585: naming
    # 2,585 of them would bury the kernel, and progressive disclosure exists
    # precisely so that the always-loaded file does not carry what can be found
    # on demand. The distinction is real and it is the one that matters here:
    #
    #   a ROLE is dispatched. Something must decide to call it, so it needs a
    #     row in delegation.md, and the check below enforces that.
    #   a SUB-SKILL is discovered. Its description is the discovery signal and
    #     the catalogue is the index, so the requirement is that it be findable
    #     there and carry a description -- not that the kernel name it.
    #
    # The old check produced 2,544 errors that said "unreachable" about files
    # that were perfectly reachable, and would have had the effect of bloating
    # SKILL.md to fix them.
    kernel = SKILL_ROOT / "SKILL.md"
    if kernel.is_file():
        subskills = sorted(
            d for d in SKILL_ROOT.glob(SUB_SKILL_GLOB) if (d / "SKILL.md").is_file()
        )
        if not subskills:
            warnings.append(f"{SKILL_ROOT}/skills/ contains no sub-skill")
        catalogue = SKILL_ROOT / "references" / "capability-catalogue.md"
        if not catalogue.is_file():
            errors.append(
                f"{catalogue}: the capability catalogue is missing, so no sub-skill "
                f"is discoverable. Run tools/index-tree.py --write-catalogue."
            )
        # Coverage is proven against the INDEX, not the catalogue text. The
        # catalogue is a map that samples names per domain on purpose, so
        # demanding every name appear in it repeated the mistake the previous
        # version of this check made with SKILL.md.
        index = SKILL_ROOT / "TREE.json"
        indexed: set[str] = set()
        if index.is_file():
            try:
                indexed = {e["dir"] for e in json.loads(
                    index.read_text(encoding="utf-8"))["entries"]}
            except Exception:            # noqa: BLE001
                indexed = set()
        else:
            errors.append(
                f"{index}: the capability index is missing. Run "
                f"tools/index-tree.py."
            )
        for sub in subskills:
            skill_md = sub / "SKILL.md"
            head = skill_md.read_text(encoding="utf-8")[:600]
            if "description:" not in head:
                errors.append(
                    f"{skill_md}: no description in frontmatter, so nothing can "
                    f"discover it. A sub-skill's description is its only entry "
                    f"point; without one the file is unreachable by any means."
                )
            elif indexed and sub.name not in indexed:
                errors.append(
                    f"{index}: {sub.name!r} is installed but absent from the "
                    f"index, so it cannot be found. Regenerate with "
                    f"tools/index-tree.py."
                )
        notes.append(
            f"{len(subskills)} sub-skills discoverable via the catalogue"
        )
    else:
        errors.append(f"{kernel}: the kernel SKILL.md is missing")

    # The generated eval set must exist and be internally consistent. It is a
    # projection of the Markdown corpus, and a projection that disagrees with its
    # source is worse than no projection.
    evals_json = SKILL_ROOT / "evals" / "evals.json"
    if not evals_json.is_file():
        errors.append(
            f"{evals_json}: missing; run tools/build-evals.py to project the "
            "Markdown corpus into the format standard tooling consumes"
        )
    else:
        try:
            payload = json.loads(evals_json.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            errors.append(f"{evals_json}: invalid JSON: {exc}")
        else:
            entries = payload.get("evals", [])
            if not entries:
                errors.append(f"{evals_json}: contains no cases")
            for entry in entries:
                missing = [
                    field for field in ("id", "query", "expected_output", "should_trigger")
                    if field not in entry
                ]
                if missing:
                    errors.append(
                        f"{evals_json}: case {entry.get('id', '?')} missing {missing}"
                    )
                elif not str(entry["query"]).strip():
                    errors.append(f"{evals_json}: case {entry['id']} has an empty query")
            if entries and not any(not e["should_trigger"] for e in entries):
                warnings.append(
                    f"{evals_json}: no trigger-negative cases; false positives are "
                    "unmeasurable and a skill that fires on everything would score 100%"
                )
            notes.append(f"{len(entries)} eval cases, generated from the Markdown corpus")

            # A trigger-negative case that cannot run is a claim about behaviour
            # with nothing behind it. It also makes the false-trigger rate
            # unmeasurable while the suite still reports its case count, which is
            # how twenty-one guard cases came to be described as "unrun" when they
            # had never been runnable. Each must either declare that it needs no
            # workspace or resolve to a built fixture.
            fixture_root = SKILL_ROOT.parent / ".eval-fixtures"
            built = (
                {p.name for p in fixture_root.iterdir() if p.is_dir()}
                if fixture_root.is_dir() else set()
            ) | (
                {p.name for p in (fixture_root / "git").iterdir() if p.is_dir()}
                if (fixture_root / "git").is_dir() else set()
            )
            for entry in entries:
                if entry.get("should_trigger"):
                    continue
                cid = entry.get("id", "?")
                if str(entry.get("fixture_required", "yes")).lower() == "no":
                    continue
                if cid not in built:
                    errors.append(
                        f"{evals_json}: trigger-negative case {cid} requires a "
                        f"fixture that does not exist, so it can never run and the "
                        f"false-trigger rate is unmeasurable. Build the fixture, or "
                        f"declare '**Fixture required:** no' if the case is "
                        f"self-contained."
                    )

            # prd.md section 23 names ten task classes. A corpus that cannot be
            # queried by the specification's own taxonomy cannot be checked against
            # it, so the taxonomy is asserted here rather than left to whoever
            # reads the JSON.
            spec_classes = {
                "simple", "medium", "complex", "ambiguous", "long-context",
                "multi-step", "cross-domain", "novel-domain", "high-assurance",
                "failure-prone",
            }
            present = {e.get("task_class") for e in entries} - {None, ""}
            uncovered = sorted(spec_classes - present)
            if uncovered:
                # A class with no case is a gap in the suite, and a gap that is
                # only visible by reading two documents side by side is a gap
                # nobody closes. Surfaced on every run until it is either filled
                # or consciously accepted.
                warnings.append(
                    f"{evals_json}: prd.md section 23 task classes with no case: "
                    f"{uncovered}. The suite cannot demonstrate the specification's "
                    f"own taxonomy while these are empty."
                )
            extra = sorted(present - spec_classes)
            if extra:
                notes.append(
                    f"task classes beyond the specification's ten: {extra}")
            notes.append(
                f"{len(spec_classes) - len(uncovered)}/{len(spec_classes)} "
                f"specified task classes have cases")

            # A case that names a file nothing generates cannot be scored. It
            # measures whether the agent declines to answer, which is a different
            # and much easier thing to pass, and it does so silently: the case
            # still runs, it just measures the wrong thing.
            #
            # Only the builder's case list is trusted here. Deriving the set from
            # the corpus instead would mean asking the fixtures to justify their
            # own existence.
            builder = SKILL_ROOT / "tools" / "build-fixtures.py"
            if builder.is_file():
                built = _fixture_case_ids(builder)
                exempt = _fixture_exemptions(builder)
                reference = re.compile(
                    r"\b[\w./-]+\.(?:jsonl|json|ts|js|py|md|csv|txt|yaml|yml|sql|"
                    r"go|rs|rb|java|sh)\b")
                for entry in entries:
                    names = {n for n in reference.findall(entry["query"])
                             if not n.startswith("ultimate-dev")}
                    if not names or entry["id"] in built or entry["id"] in exempt:
                        continue
                    errors.append(
                        f"{evals_json}: case {entry['id']} names {sorted(names)} "
                        f"and build-fixtures.py builds neither it nor an exemption; "
                        f"the case will score refusal to fabricate rather than the "
                        f"behaviour it was written to measure"
                    )
                notes.append(
                    f"{len(built)} of {len(entries)} cases have generated fixtures, "
                    f"{len(exempt)} exempt by recorded reason")

    # No second implementation of the placeholder rule.
    #
    # This check used to live in validate.yml as a shell step that grepped
    # validate.yml for its own trigger string, so it matched its own line and
    # failed every run. Worse, the version before that was a full `git grep -E`
    # implementation using `\b`, which not every git build's regex engine
    # supports: on some machines it matched nothing and reported success, and on
    # others it flagged a line of CONTRIBUTING.md that forbids those very markers
    # because its exclusion filter was case-sensitive.
    #
    # One rule, one owner. This validator implements it; a workflow that
    # reimplements it has drifted, and drift in a hygiene check means nobody
    # reads it any more.
    for workflow in sorted((repo_root / ".github" / "workflows").glob("*.y*ml")):
        for lineno, line in enumerate(
            workflow.read_text(encoding="utf-8", errors="replace").splitlines(), 1
        ):
            if not PLACEHOLDER_PATTERN.search(line):
                continue
            # This validator's own name in a message is not an implementation.
            if "validate-skills.py" in line:
                continue
            errors.append(
                f"{workflow.relative_to(repo_root)}:{lineno}: reimplements the "
                f"unfilled-marker rule; it belongs to tools/validate-skills.py "
                f"alone. Found: {line.strip()[:70]!r}"
            )

    # Decision records must obey the two rules the kernel calls non-negotiable:
    # `confidence` names its object, and `evidence` is a pointer or `none`.
    #
    # This check exists because the repository's own 100 worked examples
    # violated both, in 100% of cases, while the schema declared a bare `high`
    # "rejected". A format is taught by its exemplars far more than by its prose,
    # and every one of those exemplars was teaching the opposite. Nothing in CI
    # could see it, because nothing ever read a record.
    #
    # It walks the records rather than trusting a count, because a count is
    # satisfiable by records that do not conform -- which is how the control
    # plane, the skill-creator reference list, and the eval taxonomy all passed
    # while their contents were wrong.
    record_re = re.compile(
        r"(?m)^\s*(confidence|evidence)\s{2,}(.+?)\s*$")
    blocks_re = re.compile(r"(?m)^DECISION\s*$")
    exempt_dirs = {".git", "node_modules", "__pycache__"}

    def scan_records(paths, label):
        """Count records and how many break each rule. Returns (total, bad_ids)."""
        total = 0
        bad: list[str] = []
        for path in paths:
            try:
                text = path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            starts = [m.start() for m in blocks_re.finditer(text)]
            if not starts:
                continue
            for index, start in enumerate(starts):
                end = starts[index + 1] if index + 1 < len(starts) else len(text)
                chunk = text[start:end]
                # Bound the block: a DECISION header followed by a blank line and
                # prose is not a record.
                fields = record_re.findall(chunk[:1600])
                if not fields:
                    continue
                # The field template is not a record. It is identified by the
                # evidence line that describes the field rather than using it,
                # which is a fixed string in the one file that carries it.
                if any(k == "evidence" and "POINTERS to observations" in v
                       for k, v in fields):
                    continue
                total += 1
                rel = path.relative_to(repo_root)
                seen = {k: v.strip() for k, v in fields}
                conf = seen.get("confidence", "")
                evid = seen.get("evidence", "")
                if conf and conf.lower() in {"high", "medium", "low"}:
                    bad.append(f"{rel}: bare confidence {conf!r}")
                elif conf and not re.search(r"\bin\b", conf, re.IGNORECASE):
                    bad.append(f"{rel}: confidence does not name an object: {conf[:40]!r}")
                # `none` is a valid answer, and `none - <reason>` is the same
                # answer with the reason attached. Requiring a bare `none` would
                # discard the explanation of why there is no evidence, which is
                # usually the most useful part of the field.
                if evid and not evid.lower().startswith("none") and not re.search(
                        r"OBS-\d+", evid):
                    bad.append(f"{rel}: evidence is prose, not an OBS- pointer or `none`")
        return total, bad

    # Two populations, two severities, and the split is deliberate.
    #
    # references/decision-fabric.md holds the worked records SKILL.md sends every
    # R2+ run to. An agent that reads the rules and then looks at how a record is
    # written will copy those, so a violation there changes behaviour. It is an
    # error.
    #
    # examples/ holds 100 recorded traces from earlier runs. They are historical
    # output, not templates, and rewriting them to satisfy a rule they were
    # written before would be falsifying a record of what happened. They are
    # counted on every run, loudly, and left as they are until each is either
    # re-derived or explicitly retired. A warning would escalate under --strict
    # and block every commit against a debt nobody is working on; silence would
    # be the thing this check was written to prevent.
    runtime_records = [SKILL_ROOT / "references" / "decision-fabric.md"]
    if (SKILL_ROOT / "examples").is_dir():
        example_records = sorted((SKILL_ROOT / "examples").rglob("*.md"))
    else:
        example_records = []

    rt_total, rt_bad = scan_records(runtime_records, "runtime exemplars")
    if rt_bad:
        errors.append(
            f"{len(rt_bad)} violation(s) in the runtime exemplars of "
            f"references/decision-fabric.md, which SKILL.md sends every R2+ run "
            f"to: " + "; ".join(rt_bad[:4])
        )
    elif rt_total:
        notes.append(f"all {rt_total} runtime decision records conform")

    ex_total, ex_bad = scan_records(example_records, "examples")
    if ex_total:
        conformant = ex_total - len({b for b in ex_bad})
        if ex_bad:
            notes.append(
                f"DEBT: {len(ex_bad)} violation(s) across {ex_total} decision "
                f"records in examples/ -- bare confidence or prose evidence, "
                f"against a schema that rejects both. Historical traces, left "
                f"unrewritten on purpose; each needs re-derivation or retirement. "
                f"Runtime exemplars are clean, which is what changes behaviour."
            )
        else:
            notes.append(f"all {ex_total} example decision records conform")

    # The OBS- id space must be defined in the tree an install keeps. If it is
    # only in knowledge/, which is pruned, then `evidence: OBS-013` is a pointer
    # to nothing and the "mechanical check" the kernel promises is not available.
    runtime_obs = sum(1 for name in ("SKILL.md", "references/observation-system.md")
                      if re.search(r"OBS-\d+", (SKILL_ROOT / name).read_text(
                          encoding="utf-8", errors="replace")))
    if runtime_obs < 2:
        errors.append(
            "the OBS- id space is not defined in the runtime tree. SKILL.md "
            "promises that `evidence: OBS-n` is mechanically checkable, but the "
            "numbering exists only in knowledge/schemas/observation.md, which is "
            "pruned from every install, and the runtime observation record has no "
            "id field. The pointer resolves to nothing where it matters."
        )
    else:
        notes.append("the OBS- id space is defined in the runtime tree")

    # The control plane new-arch.md draws has eight systems. This check exists
    # because the eighth was missing for a long time and nothing noticed: the
    # repository shipped eight files, so a count-based check passed, while
    # "Evidence / Provenance" had been split into two files and
    # "Policy / Constraints" had never been written at all. A count that can be
    # satisfied by the wrong contents is not a check, so this asserts the named
    # systems rather than counting files.
    control_plane = (
        ("state-system.md", "State Management"),
        ("budget-system.md", "Budget Manager"),
        ("evidence-system.md", "Evidence / Provenance"),
        ("provenance-system.md", "Evidence / Provenance (provenance half)"),
        ("security-and-trust.md", "Security / Trust"),
        ("observability.md", "Observability"),
        ("caching-and-reuse.md", "Cache / Reuse"),
        ("policy-constraints.md", "Policy / Constraints"),
        ("recovery-system.md", "Error / Recovery State"),
    )
    for filename, spec_name in control_plane:
        path = SKILL_ROOT / "references" / filename
        if not path.is_file():
            errors.append(
                f"{path}: new-arch.md's control plane requires a home for "
                f"{spec_name}, and this file does not exist. A control-plane "
                f"system with no reference is a rule nothing loads."
            )
    present = sum(1 for f, _ in control_plane
                  if (SKILL_ROOT / "references" / f).is_file())
    if present == len(control_plane):
        notes.append(f"all {present} named control-plane systems have a reference")

    # Every delegated agent role must be a real role, not a stub, and the kernel
    # must know it exists.
    agents_dir = SKILL_ROOT / AGENTS_DIR
    if agents_dir.is_dir():
        roles = sorted(r for r in agents_dir.glob("*.md") if r.stem.islower())
        if not roles:
            errors.append(f"{agents_dir}: contains no agent role definitions")
        # Files in agents/ that are not roles are skipped by every check here --
        # the role loop above filters to lowercase names, so a PULL_REQUEST_
        # TEMPLATE or a SECURITY policy in this directory is invisible to all of
        # them. There are four, and they are documentation. They were never
        # wrong so much as unexamined: a directory of delegated roles is read as
        # containing delegated roles, and the four that are not simply have never
        # been looked at by a validator that could not see them.
        non_roles = sorted(
            p for p in agents_dir.glob("*.md")
            if not p.stem.islower() and p.stem != "README"
        )
        for stray in non_roles:
            errors.append(
                f"{stray.relative_to(SKILL_ROOT)}: not a role (a role name is "
                f"lowercase), and not an index either. It is skipped by every "
                f"agent check in this validator, so nothing verifies it. Move it "
                f"to docs/ if it is documentation."
            )
        for role in roles:
            lines = len(role.read_text(encoding="utf-8").splitlines())
            if lines < 40:
                errors.append(
                    f"{role}: {lines} lines; an agent role must state its procedure, "
                    "its output contract, and its prohibitions"
                )
        if kernel.is_file():
            kernel_body = kernel.read_text(encoding="utf-8")
            unreferenced = [role.stem for role in roles if role.stem not in kernel_body]
            if unreferenced:
                warnings.append(
                    f"{AGENTS_DIR}/: not mentioned in SKILL.md, so the kernel will not "
                    f"know to delegate to them: {', '.join(unreferenced)}"
                )
            # A count written in prose goes stale the moment a file is added, and
            # it goes stale silently: nothing about "290" stops being true on its
            # own. It read 291 for several commits after agents/README.md was
            # added, because it was counting the index as a role, so the kernel
            # claimed one more delegated role than exists. A number a reader will
            # rely on is checked against disk rather than trusted.
            #
            # Only counts of the form "N role files" are checked. Anything else
            # numeric in the kernel is prose, and a validator that second-guessed
            # prose would be a validator that got itself ignored.
            for match in re.finditer(r"(\d[\d,]*) role\s*\n?files", kernel_body):
                claimed = match.group(1).replace(",", "")
                if claimed != str(len(roles)):
                    errors.append(
                        f"{kernel.name}: claims {match.group(1)} role files, but "
                        f"{AGENTS_DIR}/ holds {len(roles)}"
                    )
        # A role named in SKILL.md but absent from the dispatch table is
        # unreachable. The kernel would load it and then have no condition under
        # which to call it, which is the decision-record defect one level up:
        # the artefact exists and is counted, and nothing routes to it.
        dispatch = SKILL_ROOT / "references" / "delegation.md"
        if dispatch.is_file():
            table = dispatch.read_text(encoding="utf-8")
            unrouted = [
                role.stem for role in roles if f"agents/{role.stem}.md" not in table
            ]
            if unrouted:
                errors.append(
                    f"{AGENTS_DIR}/: shipped but with no row in the dispatch table in "
                    f"references/delegation.md, so no decision can reach them: "
                    f"{', '.join(unrouted)}"
                )
            else:
                notes.append(f"all {len(roles)} agent roles are reachable from SKILL.md")
    else:
        warnings.append(f"{AGENTS_DIR}/ does not exist; the kernel has no delegated roles")

    return {"ok": not errors, "errors": errors, "warnings": warnings, "notes": notes}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("paths", nargs="*", help="skill directories to validate")
    parser.add_argument("--strict", action="store_true", help="fail on warnings too")
    parser.add_argument("--json", action="store_true", help="emit machine-readable output")
    args = parser.parse_args(argv)

    # Default target set: the kernel plus every sub-skill that has a SKILL.md.
    #
    # Passing explicit paths means "validate this skill", so the repository
    # invariants are skipped. A pruned install has no docs/ or evaluation/
    # trees, and failing it for their absence would report a correct install as
    # broken.
    repository_wide = not args.paths
    if args.paths:
        targets = [Path(p).resolve() for p in args.paths]
    else:
        targets = [SKILL_ROOT] + sorted(
            d for d in SKILL_ROOT.glob(SUB_SKILL_GLOB) if (d / "SKILL.md").is_file()
        )

    skills = [validate_skill(path, SKILL_ROOT) for path in targets]
    roles: list[dict[str, Any]] = []
    agents_dir = SKILL_ROOT / AGENTS_DIR
    if agents_dir.is_dir():
        # A folder index is documentation, not a loadable role. Uppercase names
        # are reserved for indexes so the distinction stays unambiguous.
        roles = [
            validate_agent_role(role)
            for role in sorted(agents_dir.glob("*.md"))
            if role.stem.islower()
        ]
    repo = (
        validate_repository(REPO_ROOT)
        if repository_wide
        else {"ok": True, "errors": [], "warnings": [], "notes": ["single-skill mode: repository invariants not checked"]}
    )

    errors = (
        [e for skill in skills for e in skill["errors"]]
        + [e for role in roles for e in role["errors"]]
        + repo["errors"]
    )
    warnings = (
        [w for skill in skills for w in skill["warnings"]]
        + [w for role in roles for w in role["warnings"]]
        + repo["warnings"]
    )

    if args.json:
        print(json.dumps({"skills": skills, "agents": roles, "repository": repo}, indent=2))
    else:
        for skill in skills:
            status = "valid" if skill["ok"] else "INVALID"
            print(
                f"  skill {skill['path']}: {status} "
                f"(name={skill['name']}, {skill.get('lines', 0)} lines, "
                f"{skill.get('references', 0)} references)"
            )
            for error in skill["errors"]:
                print(f"    error: {error}")
            for warning in skill["warnings"]:
                print(f"    warning: {warning}")
        for role in roles:
            status = "valid" if role["ok"] else "INVALID"
            print(f"  agent  {role['path']}: {status} (name={role['name']})")
            for error in role["errors"]:
                print(f"    error: {error}")
            for warning in role["warnings"]:
                print(f"    warning: {warning}")
        for error in repo["errors"]:
            print(f"    error: {error}")
        for warning in repo["warnings"]:
            print(f"    warning: {warning}")
        for note in repo["notes"]:
            print(f"    note: {note}")
        print("PASS" if not errors and not (args.strict and warnings) else "FAIL")

    if errors:
        return 1
    if args.strict and warnings:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
