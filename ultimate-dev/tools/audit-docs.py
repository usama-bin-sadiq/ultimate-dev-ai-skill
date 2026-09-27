#!/usr/bin/env python3
"""Audit the documentation set: does the prose still agree with the tree?

Companion to ``validate-skills.py``, which checks structure, placeholders, and
sub-skill reachability. This one checks the four things that rot silently in a
repository of this size:

  links     a markdown link that points at a file that is not there
  paths     a backticked path that resolves from no plausible root
  index     a file sitting beside a README that the README does not list
  inventory a stated count that no longer matches the filesystem

Why the scope is narrow
-----------------------
A documentation linter that reports everything reports nothing. The first draft
of this script produced 230 findings, and most were correct-but-useless:
``evaluation/`` and ``examples/`` describe *hypothetical* repositories
(``src/report.ts``, ``ops/rota-policy.md``) that are not meant to exist here, and
``research/`` cites other projects' trees (``skills.sh``, ``.claude-plugin/``).
Those three directories are excluded from path resolution, and fenced code is
exempt because a path shown as an example is not a claim about this repository.

What survives is short and worth failing a build over. If you widen a check and
the output stops being actionable, the check was wrong, not the documents.

Usage
-----
    python3 ultimate-dev/tools/audit-docs.py             # human report
    python3 ultimate-dev/tools/audit-docs.py --check     # exit 1 on any defect
    python3 ultimate-dev/tools/audit-docs.py --only index
"""

from __future__ import annotations

import argparse
import re
import sys
from collections import defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SKILL_ROOT = REPO_ROOT / "ultimate-dev"

# Directories whose Markdown is *about* something other than this tree.
#   evaluation/  benchmark cases describing fictional repositories
#   examples/    worked traces that quote scenario fixtures
#   research/    a survey citing external projects' file layouts
EXTERNAL_SUBJECT_DIRS = {"evaluation", "examples", "research"}

# Historical inputs, not maintained prose.
SOURCE_SPECS = {"new-arch.md", "new-arch-updated.md", "prd.md"}

DOC_EXTS = {".md", ".py", ".sh", ".json", ".yml", ".yaml", ".txt", ".toml"}
INDEX_NAME = "README.md"

MD_LINK = re.compile(r"(?<!!)\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
CODE_SPAN = re.compile(r"`([^`\n]+)`")
FENCE = re.compile(r"^\s*(```|~~~)")
ATX = re.compile(r"^(#{1,6})\s+(.*?)\s*$")

WORDS = {w: i for i, w in enumerate(
    ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight",
     "nine", "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen",
     "sixteen", "seventeen", "eighteen", "nineteen", "twenty"], start=0)}


def to_int(tok: str) -> int | None:
    tok = tok.strip().lower()
    if tok in WORDS:
        return WORDS[tok]
    return int(tok) if tok.isdigit() else None


def _refs() -> int:
    return len([p for p in (SKILL_ROOT / "references").glob("*.md")
                if p.name != INDEX_NAME])


def _roles() -> int:
    return len([p for p in (SKILL_ROOT / "agents").glob("*.md")
                if p.name != INDEX_NAME])


def _traces() -> int:
    return len([p for p in (SKILL_ROOT / "examples").rglob("*.md")
                if p.name != INDEX_NAME])


def _domains() -> int:
    return len([p for p in (SKILL_ROOT / "examples").iterdir() if p.is_dir()])


def count_layers() -> int:
    """The layer count is self-declared in the architecture index."""
    readme = SKILL_ROOT / "docs" / "architecture" / "README.md"
    if not readme.is_file():
        return -1
    m = re.search(r"##\s+The\s+(\w+)\s+layers", readme.read_text(encoding="utf-8"))
    return to_int(m.group(1)) if m else -1


BOUNDARY_ROW = re.compile(r"^\|\s*(\d{1,2})\s*\|", re.MULTILINE)


def count_boundaries() -> int:
    """Highest-numbered row in the kernel's boundary table.

    The table is the authority; the word "seventeen" in prose is a claim about
    it, and this is what makes that claim checkable.
    """
    kernel = SKILL_ROOT / "docs" / "architecture" / "kernel.md"
    if not kernel.is_file():
        return -1
    numbers = [int(n) for n in BOUNDARY_ROW.findall(kernel.read_text(encoding="utf-8"))]
    return max(numbers) if numbers else -1


# Counts the prose states as fact. Each entry is
#   (documents that state it, singular noun, the filesystem answer).
#
# The documents are listed explicitly because "any document that mentions a
# number" is how this check becomes useless: prose is full of incidental
# numbers, and only the reader-facing inventories make a checkable claim.
INVENTORY = [
    (["README.md", "INSTALL.md", "ultimate-dev/references/README.md"],
     "reference", _refs),
    (["README.md", "INSTALL.md", "ultimate-dev/references/README.md",
      "ultimate-dev/SKILL.md"], "role", _roles),
    (["README.md", "INSTALL.md", "ultimate-dev/references/README.md"],
     "trace", _traces),
    (["README.md", "ultimate-dev/references/README.md"], "domain", _domains),
    (["ultimate-dev/docs/architecture/README.md", "ultimate-dev/docs/README.md"],
     "layer", count_layers),
    (["ultimate-dev/docs/architecture/kernel.md",
      "ultimate-dev/references/decision-fabric.md",
      "ultimate-dev/docs/decisions/0001-jev-as-decision-fabric.md"],
     "decision boundar", count_boundaries),
]


SKIP_DIRS = {".git", ".idea", ".eval-fixtures", "__pycache__", "node_modules",
             ".venv", "venv", "dist", "build", "runs", "vendor"}


def rel_to_repo(path: Path) -> Path:
    """Path relative to the repository root, whatever form it arrived in."""
    try:
        return path.resolve().relative_to(REPO_ROOT)
    except ValueError:
        return Path(path)


def is_external_subject(rel: Path) -> bool:
    """True for prose that describes some tree other than this one."""
    parts = rel_to_repo(rel).parts
    if not parts:
        return False
    # A repo-root file has no directory part; a skill file has one.
    scope = parts[:-1] if len(parts) > 1 else ()
    return bool(EXTERNAL_SUBJECT_DIRS & set(scope))


def strip_fences(lines: list[str]) -> list[str]:
    """Blank fenced code blocks while preserving line numbers."""
    out, fence = [], None
    for line in lines:
        m = FENCE.match(line)
        if m:
            token = m.group(1)
            fence = None if fence == token else token
            out.append("")
            continue
        out.append("" if fence else line)
    return out


def prose_docs() -> list[Path]:
    """Maintained prose a reader navigates by reference."""
    out = []
    for path in REPO_ROOT.rglob("*.md"):
        rel = rel_to_repo(path)
        if rel.name in SOURCE_SPECS or is_external_subject(rel):
            continue
        if SKIP_DIRS & set(rel.parts[:-1]):
            continue
        out.append(REPO_ROOT / rel)
    return sorted(out)


def roots_for(doc: Path) -> list[Path]:
    """Every directory a relative path in `doc` could legitimately mean.

    Markdown readers resolve relative to the file, and this repository's prose
    also writes paths from the skill root and from the repository root. All
    three are accepted; anything else is a genuine ambiguity.
    """
    roots, cur = [], doc.parent
    while True:
        roots.append(cur)
        if cur == REPO_ROOT or cur == cur.parent:
            break
        cur = cur.parent
    for extra in (SKILL_ROOT, REPO_ROOT):
        if extra not in roots:
            roots.append(extra)
    return roots


def looks_like_path(token: str) -> bool:
    t = token.strip().rstrip(".,;:")
    if not t or " " in t or t.startswith(("#", ">", "|", "*", "=", "-")):
        return False
    if t.startswith(("http://", "https://", "mailto:")):
        return False
    if any(c in t for c in "*{}<>"):
        return False           # glob, placeholder, or ellipsis
    if Path(t).suffix not in DOC_EXTS:
        return False
    # A bare filename carries no directory, so "does this exist" has no single
    # answer: `references/README.md` names its siblings as `triage.md`, and
    # `CONTRIBUTING.md` cites names as naming examples. Only assert on paths
    # that say which directory they are in.
    return "/" in t


def is_historical(rel: Path) -> bool:
    """Documents that record the past rather than navigate the present.

    A changelog quotes paths as they were named when the entry was written, and
    those files may since have moved. That is history, not a broken link.
    """
    return rel.name in {"CHANGELOG.md"}


def is_placeholder_target(target: str) -> bool:
    """True when a markdown target is an example rather than a real path.

    Four shapes occur in this repository, all of them documentation *about*
    links rather than links:
      - the bare word `url` or `link`, used as a citation or anchor example
      - a `<slug>` or `<topic>` angle-bracket slot: `chapters/ch01-<slug>.md`
      - a `NNN`-prefixed name that is a section number, not a directory:
        `skills/01-estrategia/...`
    """
    t = target.strip()
    if t.lower() in {"url", "link", "path", "href", "example.com"}:
        return True
    if re.search(r"<[^>]+>", t):
        return True
    return bool(re.search(r"(^|/)\d{2}-[a-z]", t))


def anchor_exists(path: Path, fragment: str) -> bool:
    """True when `path` has a heading that would produce this anchor.

    GitHub's rule: lowercase the heading, drop punctuation, spaces to hyphens.
    """
    if not path.exists() or path.suffix.lower() != ".md":
        return False
    want = re.sub(r"[^\w\s-]", "", fragment.lower()).replace(" ", "-")
    heads = re.findall(r"^#{1,6}\s+(.*)$",
                       path.read_text(encoding="utf-8", errors="replace"),
                       re.M)
    for h in heads:
        if re.sub(r"[^\w\s-]", "", h.lower()).replace(" ", "-") == want:
            return True
    return False


def check_links_paths(docs: list[Path], out: dict[str, list[str]]) -> None:
    for doc in docs:
        rel = rel_to_repo(doc)
        rels = rel.as_posix()
        historical = is_historical(rel)
        lines = doc.read_text(encoding="utf-8", errors="replace").splitlines()
        prose = strip_fences(lines)
        roots = roots_for(doc)

        for lineno, clean in enumerate(prose, 1):
            for target in MD_LINK.findall(clean):
                if target.startswith(("http://", "https://", "#", "mailto:")):
                    continue
                # A placeholder is not a path. Documentation about how to write
                # markdown contains `[label](url)` and `[x](references/<topic>.md)`
                # as illustrative text, and a vendored skill contains `[name](url)`
                # as a citation template. None of those is a link a reader can
                # follow, so reporting them as dead would bury the real defects.
                if is_placeholder_target(target):
                    continue
                # resolve the file part, then the anchor against its headings
                path, _, frag = target.partition("#")
                hit = next((r for r in roots if (r / path).exists()), None)
                if hit is None:
                    out["links"].append(f"{rels}:{lineno}  dead link [{target}]")
                elif frag and not anchor_exists(hit / path, frag):
                    out["links"].append(
                        f"{rels}:{lineno}  dead anchor [{target}]")

        if historical:
            continue
        for lineno, clean in enumerate(prose, 1):
            for token in CODE_SPAN.findall(clean):
                if not looks_like_path(token):
                    continue
                if any((r / token).exists() for r in roots):
                    continue
                out["paths"].append(f"{rels}:{lineno}  `{token}` resolves from no root")

        # Fenced blocks are scanned too, for paths only. In maintained prose a
        # fenced path is nearly always a claim about *this* repository — the
        # install tree diagrams are the case that matters, and they are exactly
        # where the stale file counts live. The false positives that made this
        # noisy lived in evaluation/ and examples/, which are already excluded.
        for lineno, raw in enumerate(lines, 1):
            if not raw.strip() or raw == prose[lineno - 1]:
                continue                      # already scanned as prose
            for token in CODE_SPAN.findall(raw):
                if not looks_like_path(token):
                    continue
                if any((r / token).exists() for r in roots):
                    continue
                out["paths"].append(
                    f"{rels}:{lineno}  `{token}` (in a code block) resolves from no root"
                )


def check_index(docs: list[Path], out: dict[str, list[str]]) -> None:
    by_dir: dict[Path, list[Path]] = defaultdict(list)
    for doc in docs:
        by_dir[doc.parent].append(doc)

    for directory, members in sorted(by_dir.items()):
        index = directory / INDEX_NAME
        if not index.is_file() or len(members) < 2:
            continue
        body = index.read_text(encoding="utf-8", errors="replace")
        for member in sorted(members):
            if member == index:
                continue
            if member.stem in body or member.name in body:
                continue
            out["index"].append(
                f"{member.relative_to(REPO_ROOT)}  absent from "
                f"{index.relative_to(REPO_ROOT)}"
            )


SPELLED = (r"\d{1,4}|one|two|three|four|five|six|seven|eight|nine|ten|eleven|"
           r"twelve|thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|"
           r"nineteen|twenty")


def check_inventory(_: list[Path], out: dict[str, list[str]]) -> None:
    """Counts stated in reader-facing inventories, against the filesystem.

    Two shapes of prose are exempt, because both are correct and both are
    common in this repository:

      "fourteen layers"            a claim, checked
      "four layers, not fourteen"  a contrast, where the number is the point
      "seventeen decision boundaries"  a claim, checked
    """
    for doc_rels, subject, counter in INVENTORY:
        actual = counter()
        if actual < 0:
            continue
        for doc_rel in doc_rels:
            path = REPO_ROOT / doc_rel
            if not path.is_file():
                continue
            # Match the noun, then read the number that governs it, allowing
            # "the kernel's seventeen decision boundaries" and "17 boundaries".
            number = re.compile(
                r"\b(" + SPELLED + r")\b\s+"
                r"(?:\w+[\s'’-]+){0,3}?" + re.escape(subject) + r"s?\b",
                re.IGNORECASE,
            )
            for lineno, line in enumerate(
                path.read_text(encoding="utf-8", errors="replace").splitlines(), 1
            ):
                for m in number.finditer(line):
                    claimed = to_int(m.group(1))
                    if claimed is None or claimed == actual:
                        continue
                    # "four layers, not fourteen" — a contrast, not a claim.
                    tail = line[m.end():].lstrip()
                    if tail.lower().startswith((", not", " not")):
                        continue
                    # A true number elsewhere on the line means this one is a
                    # component of a compound claim, not the inventory figure.
                    if any(to_int(g) == actual for g in number.findall(line)):
                        continue
                    out["inventory"].append(
                        f"{doc_rel}:{lineno}  says {claimed}, tree has {actual}"
                        f"  |  \"{m.group(0).strip()}\""
                    )


def runtime_payload() -> tuple[int, int] | None:
    """(file count, bytes) of the installable payload, per the bundler.

    Imported rather than reimplemented: a second copy of the runtime-file
    rules is a second thing to keep correct, and this check exists precisely
    because the documented numbers drifted from the real ones.
    """
    import importlib.util
    import sys

    # Importing the bundler must not leave a __pycache__ inside the skill tree:
    # validate-skills.py --strict fails the build on a build artefact, so an
    # auditor that creates one makes the two tools contradict each other.
    previous = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        bundler = SKILL_ROOT / "tools" / "bundle-skill.py"
        if not bundler.is_file():
            return None
        try:
            spec = importlib.util.spec_from_file_location("bundle_skill", bundler)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            files = list(module.iter_runtime_files())
        except Exception:
            return None
        return len(files), sum(f.stat().st_size for f in files)
    finally:
        sys.dont_write_bytecode = previous


def skill_dir_size() -> int:
    return sum(
        p.stat().st_size
        for p in SKILL_ROOT.rglob("*")
        if p.is_file() and not any(x in p.parts for x in (".git", "__pycache__"))
    )


# Every install-facing number that is currently wrong, pinned explicitly.
#
# This is a table and not a pattern over the prose because the quantities are
# genuinely different things: the runtime payload, the pruned tree beside it,
# the whole skill directory, and the zipped bundle. A generic "find a number
# near a unit" rule cannot tell them apart, and a check that compares the wrong
# pair is worse than none — it produces findings that are wrong, which is how a
# linter gets switched off.
#
# Each entry: (file, regex capturing one number, what it must equal, label).
# ``None`` as the expected value disables the check without deleting the row.
def _payload_claims() -> list[tuple[str, str, int, str, str]]:
    payload = runtime_payload()
    if payload is None:
        return []
    count, nbytes = payload
    kib = nbytes / 1024
    pct_smaller = round((1 - nbytes / skill_dir_size()) * 100) if skill_dir_size() else -1
    return [
        ("README.md", r"install to run it:\s*(\d+)\s+files", count,
         "runtime files in the pruned install"),
        ("README.md", r"(\d+)%\s+smaller", pct_smaller,
         "percent the bundle is smaller than the skill directory"),
        ("INSTALL.md", r"the\s+(\d+)\s+runtime files", count,
         "runtime files in the pruned install"),
        ("INSTALL.md", r"Pruned in place:\s*(\d+)\s+files", count,
         "runtime files in the pruned install"),
        ("INSTALL.md", r"references/\s+(\d+)\s+files", _refs(),
         "reference files"),
        ("INSTALL.md", r"it is\s+(\d+)%\s+smaller", pct_smaller,
         "percent the bundle is smaller than the skill directory"),
        ("ultimate-dev/tools/bundle-skill.py", r"of which\s+(\d+)\s+files are the skill",
         count, "runtime files in the pruned install"),
    ]


def check_payload(_: list[Path], out: dict[str, list[str]]) -> None:
    """Install-facing counts, each against the quantity it actually names."""
    payload = runtime_payload()
    if payload is None:
        return
    kib = payload[1] / 1024
    for rel, pattern, expected, label in _payload_claims():
        path = REPO_ROOT / rel
        if not path.is_file() or expected < 0:
            continue
        unit = "%" if "percent" in label else ""
        for lineno, line in enumerate(
            path.read_text(encoding="utf-8", errors="replace").splitlines(), 1
        ):
            for m in re.finditer(pattern, line):
                claimed = int(m.group(1))
                if claimed == expected:
                    continue
                out["payload"].append(
                    f"{rel}:{lineno}  says {claimed}{unit}, actual "
                    f"{expected}{unit}  |  {label}"
                )

    # Sizes are compared per named quantity, never across quantities.
    for rel, pattern, expected_kib, label in (
        ("README.md", r"install to run it:\s*\d+\s+files,\s*(\d+)\s*KB",
         payload[1] / 1024, "runtime payload size"),
        ("INSTALL.md", r"Pruned in place:\s*\d+\s+files,\s*(\d+)\s*KB",
         payload[1] / 1024, "runtime payload size"),
        ("INSTALL.md", r"about\s+(\d+(?:\.\d+)?)\s*MB against a\s*(\d+)\s*KB",
         payload[1] / 1024, "runtime payload size"),
    ):
        path = REPO_ROOT / rel
        if not path.is_file():
            continue
        for lineno, line in enumerate(
            path.read_text(encoding="utf-8", errors="replace").splitlines(), 1
        ):
            for m in re.finditer(pattern, line):
                claimed = float(m.group(2)) if m.lastindex and m.lastindex > 1 \
                    else float(m.group(1))
                if abs(claimed - expected_kib) / expected_kib <= 0.02:
                    continue
                out["payload"].append(
                    f"{rel}:{lineno}  says {claimed:.0f} KB, actual "
                    f"{expected_kib:.0f} KB  |  {label}"
                )


def check_headings(docs: list[Path], out: dict[str, list[str]]) -> None:
    for doc in docs:
        rel = doc.relative_to(REPO_ROOT).as_posix()
        prev = 0
        for lineno, line in enumerate(
            strip_fences(doc.read_text(encoding="utf-8", errors="replace").splitlines()),
            1,
        ):
            m = ATX.match(line)
            if not m:
                continue
            level = len(m.group(1))
            if prev and level > prev + 1:
                out["headings"].append(
                    f"{rel}:{lineno}  H{prev} -> H{level}: {m.group(2)[:56]}"
                )
            prev = level


CHECKS = {
    "links": check_links_paths,
    "paths": check_links_paths,
    "index": check_index,
    "inventory": check_inventory,
    "payload": check_payload,
    "headings": check_headings,
}

BLURB = {
    "links": "dead markdown links",
    "paths": "backticked paths that resolve from no root",
    "index": "files missing from their directory index",
    "inventory": "stated counts that disagree with the tree",
    "payload": "install-payload size and file counts that disagree with the bundler",
    "headings": "skipped heading levels",
}
ORDER = ["links", "paths", "index", "inventory", "payload", "headings"]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="audit documentation cross-references")
    ap.add_argument("--check", action="store_true", help="exit 1 if any defect")
    ap.add_argument("--only", help="comma-separated: " + ",".join(ORDER))
    ap.add_argument("--max", type=int, default=20)
    args = ap.parse_args(argv)

    wanted = set(args.only.split(",")) if args.only else set(ORDER)
    docs = prose_docs()
    out: dict[str, list[str]] = defaultdict(list)

    # links and paths share one pass; run it once if either is wanted.
    if wanted & {"links", "paths"}:
        check_links_paths(docs, out)
    for name in ("index", "inventory", "payload", "headings"):
        if name in wanted:
            CHECKS[name](docs, out)

    print(f"audited {len(docs)} maintained documents under {REPO_ROOT}")
    print(f"(excluded as describing other trees: "
          f"{', '.join(sorted(EXTERNAL_SUBJECT_DIRS))}/)\n")

    total = 0
    for kind in ORDER:
        rows = out.get(kind) or []
        if not rows:
            continue
        total += len(rows)
        print(f"{BLURB[kind]}: {len(rows)}")
        for r in rows[: args.max]:
            print(f"    {r}")
        if len(rows) > args.max:
            print(f"    ... and {len(rows) - args.max} more")
        print()

    print("clean: prose agrees with the tree" if not total else f"TOTAL: {total}")
    return 1 if (args.check and total) else 0


if __name__ == "__main__":
    sys.exit(main())
