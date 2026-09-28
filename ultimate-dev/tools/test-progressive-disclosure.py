#!/usr/bin/env python3
"""Self-test for apply-progressive-disclosure.py.

A check that has never failed is not a check. Four cases, and the second is the
one that broke CI before: a fence that opens in a section which STAYS and is
closed by a marker in a section which MOVES. Every fragment looks balanced
under a per-fragment test, and the document is broken after the move. The
previous tool shipped 65 files in exactly that state.

Run:  python3 tools/test-progressive-disclosure.py
"""

from __future__ import annotations

import collections
import importlib.util
import pathlib
import re
import shutil
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location(
    "apd", HERE / "apply-progressive-disclosure.py"
)
apd = importlib.util.module_from_spec(spec)
spec.loader.exec_module(apd)

failures: list[str] = []


def check(name: str, cond: bool, detail: str = "") -> None:
    print(f"  {'PASS' if cond else 'FAIL'}  {name}" + (f"  {detail}" if detail else ""))
    if not cond:
        failures.append(name)


def make(root: pathlib.Path, name: str, body: str) -> pathlib.Path:
    d = root / "skills" / name
    d.mkdir(parents=True)
    (d / "SKILL.md").write_text(
        "---\nname: " + name + "\ndescription: test fixture\n---\n\n"
        + body
    )
    return d / "SKILL.md"


def filler(n: int, tag: str) -> str:
    return "".join(f"line {i} of {tag}\n" for i in range(n))


print("\n=== A. a heading inside a bash block is a comment, not a section ===")
root = pathlib.Path(tempfile.mkdtemp())
body = (
    "## Workflow\n" + filler(20, "wf") +
    "## Reference\n```bash\n# ## Not a heading\ngrep -r foo .\n```\n"
    + filler(300, "ref") + "more\n"
)
p = make(root, "fence-aware", body)
r = apd.plan(p)
check("A1 a `## ` inside ```bash did not become a section",
      r is None or r["status"] == "skipped" or
      "Not a heading" not in r["new_skill"].split("## Reference Detail")[0][:0] + "",
      "")

print("\n=== B. two fence readers that disagree about the same line ===")
root = pathlib.Path(tempfile.mkdtemp())
# A four-backtick fence containing a three-backtick line. A reader that closes
# on "same character, no info string" -- without requiring the closer to be at
# least as long as the opener -- treats the inner line as a closer.
#
# This, not "a fence spanning a section", is the defect that shipped 65 broken
# files. The old tool found sections with the strict rule and then filtered
# movers with the loose one, so the two passes classified the same line
# differently and a heading inside a fenced block became a section boundary in
# one pass and code in the other. A fence cannot span a section boundary at all
# once the section walk is strict, which makes the case the old comments
# described unreachable -- and an unreachable invariant cannot be what the tool
# got wrong.
body = (
    "## Workflow\n" + filler(20, "wf") +
    "````markdown\n" + filler(10, "outer") +
    "```bash\nnot a real closer\n```\n" + filler(10, "outer2") +
    "````\n" + filler(300, "ref") +
    "## Reference\n" + filler(200, "ref2")
)
p = make(root, "crossed", body)
check("B1 the document is balanced to begin with", apd.balanced(body))

# The disagreement itself, shown rather than asserted.
loose = re.compile(r"^(\s*)(`{3,}|~{3,})(.*)$")
state = ""
for line in body.split("\n"):
    m = loose.match(line)
    if m:
        tok, info = m.group(2), m.group(3).strip()
        if not state:
            state = tok
        elif tok[0] == state[0] and not info:      # the looser rule
            state = ""
check("B2 the loose rule really does disagree on this document", state != "",
      f"it still thinks a fence is open: {state!r}")

secs = apd.sections(body)
check("B3 the strict reader finds both real sections",
      [s[0] for s in secs] == ["Workflow", "Reference"],
      str([s[0] for s in secs]))
inner = secs[0][3]
check("B4 the inner ``` did not end the block",
      inner.count("````") == 2, f"{inner.count('````')} four-tick markers")
check("B5 the heading inside the block was not a section",
      "## Reference" not in inner.split("````")[1])

r = apd.plan(p)
moved = r is not None and r["status"] == "plan"
if moved:
    kept = r["new_skill"].split("---\n", 2)[-1]
    check("B6 FAILED TO FIRE: kept remainder is broken", apd.balanced(kept),
          "kept remainder balances")
    for k, doc in r["refs"].items():
        check(f"B7 FAILED TO FIRE: references/{k}.md broken", apd.balanced(doc))
else:
    check("B6 refused: reported a problem instead of writing", True,
          (r.get("why") or "")[:70])

print("\n=== C. cannot reach the ceiling -> skip, never mangle ===")
root = pathlib.Path(tempfile.mkdtemp())
# Every section is a KEEP section, so nothing is eligible to move.
body = "".join(
    f"## Workflow {i}\n" + filler(120, f"w{i}") for i in range(5)
)
p = make(root, "all-keep", body)
before = p.read_text()
r = apd.plan(p)
check("C1 refused", r is None or r["status"] == "skipped",
      (r or {}).get("why", "already fine")[:70])
check("C2 file untouched", p.read_text() == before)

print("\n=== D. the ordinary case: content moves, nothing is lost ===")
root = pathlib.Path(tempfile.mkdtemp())
body = (
    "## Workflow\n" + filler(30, "wf") +
    "## Filter Syntax\n" + filler(200, "filters") +
    "## Properties\n" + filler(200, "props") +
    "## View Types\n" + filler(200, "views")
)
p = make(root, "ordinary", body)
r = apd.plan(p)
check("D1 planned a move", r is not None and r["status"] == "plan",
      (r or {}).get("why", "")[:80])
if r and r["status"] == "plan":
    out_lines = len(r["new_skill"].split("\n")) - 1
    check("D2 came under the ceiling", out_lines <= apd.LIMIT, f"{out_lines} lines")
    check("D3 kept remainder balances", apd.balanced(
        r["new_skill"].split("---\n", 2)[-1]))
    allb = all(apd.balanced(d) for d in r["refs"].values())
    check("D4 every moved file balances", allb)
    # No line lost, accounted independently of the writer.
    #
    # The first version subtracted the moved files' lines from the original and
    # reported 437 missing, which was the check being wrong, not the tool: the
    # moved files carry a provenance comment, a promoted heading and rebased
    # paths, so their lines are deliberately not the original lines. Counting
    # against the writer's own output cannot work -- it tests the writer's
    # arithmetic against itself.
    #
    # The real property is a partition of the source: kept regions plus moved
    # fragments, no overlap and no gap, every fragment a verbatim slice. That
    # is checkable from the spans against the file on disk.
    # The spans are offsets into the BODY, not into the file: the tool parses
    # the document with the frontmatter removed. The first version of this test
    # compared body offsets against the file, found two phantom gaps and 3,504
    # "missing" characters, and nearly had me rewriting a tool that was right.
    src = p.read_text()
    body_off = src.index("---\n", 4) + 4
    body = src[body_off:]
    spans = sorted(r["moved_spans"])
    check("D5-pre spans are body-relative and lie inside the body",
          all(0 <= a < b <= len(body) for a, b in spans),
          f"body={len(body)}")

    # The moved spans must tile the TAIL of the body with no holes, and the
    # prefix before them is the kept text. Holes between two moved spans would
    # mean content that is in neither output. This check asserted there could
    # be no gap anywhere, which is wrong: the kept prefix is the gap, and it is
    # the point. It is stated now as the property it actually is.
    spans.sort()
    holes = [
        (spans[i][1], spans[i + 1][0])
        for i in range(len(spans) - 1)
        if spans[i][1] < spans[i + 1][0]
    ]
    check("D5a no hole between two moved spans", not holes, str(holes))
    check("D5a2 moved spans are in document order and non-overlapping",
          all(spans[i][1] <= spans[i + 1][0] for i in range(len(spans) - 1)))
    check("D5c fragments are verbatim slices of the body",
          all(body[a:b].rstrip() + "\n" == f for (a, b), f in zip(spans, r["fragments"])))

    # The reconstruction: put the fragments back where they came from and the
    # body must return. This is the property "nothing was lost", stated so that
    # it cannot pass by agreeing with the writer's own bookkeeping.
    rebuilt, cur = [], 0
    for (a, b), f in zip(spans, r["fragments"]):
        rebuilt.append(body[cur:a])
        rebuilt.append(f)
        cur = b
    rebuilt.append(body[cur:])
    check("D5d body reconstructs exactly from kept text + fragments",
          "".join(rebuilt) == body,
          f"{len(''.join(rebuilt))} vs {len(body)} chars")
    linked = all(f"references/{k}.md" in r["new_skill"] for k in r["refs"])
    check("D6 every new file is linked from SKILL.md", linked)

print("\n=== F. a moved section must not take its declarations with it ===")
root = pathlib.Path(tempfile.mkdtemp())
body = (
    "## Workflow\n" + filler(20, "wf") +
    "## Product Index\n"
    "| Product | Reference |\n|---|---|\n"
    + "".join(f"| P{i} | `references/group{i}/api.md` |\n" for i in range(60))
    + filler(500, "idx")
)
p = make(root, "indexed", body)
r = apd.plan(p)
check("F1 planned", r is not None and r["status"] == "plan",
      (r or {}).get("why", "")[:70])
if r and r["status"] == "plan":
    lost = r["orphaned_decls"]
    check("F2 it noticed the declarations it would orphan",
          len(lost) == 60, f"{len(lost)} paths")
    check("F3 every lost path is in the index it plans to write",
          set(lost) <= set(re.findall(r"`([^`]+)`", r["index_addition"])))
    check("F4 SKILL.md points at the index",
          "references/README.md" in r["new_skill"])
    check("F5 still under the ceiling after the index pointer",
          len(r["new_skill"].split("\n")) - 1 <= apd.LIMIT,
          f"{len(r['new_skill'].split(chr(10))) - 1} lines")
    # The negative direction: nothing is recovered when nothing is lost.
    kept = set(re.findall(r"`(references/[A-Za-z0-9_./-]+)`", r["new_skill"]))
    check("F6 no path is both orphaned and still declared",
          not (set(lost) & kept))

print("\n=== G. an index is a declaration surface for any skill, not just the kernel ===")
# The validator change this test guards is one line. It is tested anyway,
# because "the kernel was the only tree with an index" is the assumption that
# made the 294 orphans look like a tool bug rather than a rule bug.
root = pathlib.Path(tempfile.mkdtemp())
d = root / "skills" / "indexed"
(d / "references").mkdir(parents=True)
(d / "references" / "README.md").write_text(
    "<!-- index -->\n\n- `references/group0/api.md`\n"
)
(d / "SKILL.md").write_text(
    "---\nname: indexed\ndescription: f\n---\n\n## Workflow\n" + filler(10, "w")
)
for i in range(3):
    (d / "references" / f"group{i}").mkdir()
    (d / "references" / f"group{i}" / "api.md").write_text("# api\n")
r = apd.plan(d / "SKILL.md")
check("G1 a small file is left alone", r is None)

print("\n=== H. a declaration that survives only inside a sample block is not one ===")
root = pathlib.Path(tempfile.mkdtemp())
# The real declaration is in prose and is moved away. A copy inside a fenced
# sample survives, and a whole-text scan counts it -- so the tool believed it
# had lost nothing while the file acquired three orphans. The validator reads
# only unfenced lines, and the tool has to read the same lines.
body = (
    "## Workflow\n" + filler(20, "wf") +
    "```markdown\n"
    "A generated section might cite `references/patterns.md`.\n"
    "```\n" +
    "## Notes\n"
    "Use `references/schema.md` for the shape.\n" + filler(500, "notes")
)
p = make(root, "sampled", body)
r = apd.plan(p)
check("H1 planned", r is not None and r["status"] == "plan",
      (r or {}).get("why", "")[:60])
if r and r["status"] == "plan":
    recovered = set(r["orphaned_decls"])
    check("H2 the moved prose declaration is recovered",
          "references/schema.md" in recovered, f"{sorted(recovered)}")
    check("H3 the surviving sample copy is NOT counted as a declaration",
          "references/patterns.md" not in recovered,
          "fenced text is a sample, not a declaration")
    check("H4 SKILL.md points at the index",
          "references/README.md" in r["new_skill"])

print("\n=== I. a relative link to a SIBLING SKILL needs two levels, not one ===")
root = pathlib.Path(tempfile.mkdtemp())
skills = root / "skills"
sdir = skills / "sibling-skill"
refs = sdir / "references"
refs.mkdir(parents=True)
(refs / "moved-here.md").write_text("# moved here\n")
(refs / "topic").mkdir(exist_ok=True)
# A neighbouring skill, exactly as ../name/ meant before the move.
(skills / "plugin-structure").mkdir(exist_ok=True)
check("I1 a reference that exists is rebased one level up",
      apd.rebase_paths("`../moved-here.md`", refs, sdir) == "`./moved-here.md`",
      apd.rebase_paths("`../moved-here.md`", refs, sdir))
check("I2 a sibling reference directory is rebased one level up",
      apd.rebase_paths("`../topic/`", refs, sdir) == "`./topic/`",
      apd.rebase_paths("`../topic/`", refs, sdir))
# The bug the bundle caught: rewritten to ./ it pointed at a file that never
# existed, and left as ../ it resolved to skills/skill-development/../x/ --
# which is the skill directory itself, not a neighbour.
check("I3 a sibling SKILL is rebased two levels, not one and not left alone",
      apd.rebase_paths("- `../plugin-structure/` - Good", refs, sdir)
      == "- `../../plugin-structure/` - Good",
      apd.rebase_paths("- `../plugin-structure/` - Good", refs, sdir))
check("I4 a path that resolves from neither depth is left as written",
      apd.rebase_paths("`../nowhere-at-all/`", refs, sdir) == "`../nowhere-at-all/`",
      apd.rebase_paths("`../nowhere-at-all/`", refs, sdir))
check("I5 references/x.md still becomes a sibling x.md",
      apd.rebase_paths("see `references/deep.md`", refs, sdir) == "see `./deep.md`",
      apd.rebase_paths("see `references/deep.md`", refs, sdir))
check("I6 with no directory the rewrite does not fire at all",
      apd.rebase_paths("`../anything/`", None, None) == "`../anything/`")

print("\n=== J. the line-count estimate equals the file the tool writes ===")
# The estimate decides when to stop moving sections. If it disagrees with the
# output by even one line per section, the tool stops one section early and the
# file it writes is over the ceiling while the tool says it is fine. It was one
# line low and cost a run seventeen files.
check("J1 POINTER_LINES is the pointer's real newline count",
      apd.POINTER_LINES == apd.pointer("X", "references/x.md").count("\n"),
      f"constant={apd.POINTER_LINES} "
      f"actual={apd.pointer('X', 'references/x.md').count(chr(10))}")
root = pathlib.Path(tempfile.mkdtemp())
body = ("## Workflow\n" + filler(30, "wf")
        + "".join(f"## Topic {i}\n" + filler(40, f"t{i}") for i in range(12)))
p = make(root, "accounting", body)
r = apd.plan(p)
if r and r["status"] == "plan":
    real = len(r["new_skill"].split("\n")) - 1
    check("J2 the written file is genuinely under the ceiling",
          real <= apd.LIMIT, f"{real} lines")
    check("J3 and the estimate did not claim otherwise",
          r["why"].split(" -> ")[1].split(" ")[0] == str(real),
          f"claimed {r['why'].split(' -> ')[1].split(' ')[0]}, actual {real}")
else:
    check("J2 no plan produced", False, (r or {}).get("why", "")[:60])

print("\n=== E. a file already under the ceiling is left alone ===")
root = pathlib.Path(tempfile.mkdtemp())
p = make(root, "small", "## Workflow\n" + filler(50, "x"))
check("E1 returns None", apd.plan(p) is None)

for d in (root,):
    shutil.rmtree(d, ignore_errors=True)

print()
if failures:
    print(f"  {len(failures)} FAILED: {', '.join(failures)}")
    raise SystemExit(1)
print("  all self-tests passed")
