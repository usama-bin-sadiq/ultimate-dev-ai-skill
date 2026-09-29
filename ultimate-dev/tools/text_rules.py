#!/usr/bin/env python3
"""Shared text rules for the validators, imported by both.

Why this module exists
----------------------
`bundle-skill.py` and `validate-skills.py` both need to know two things about a
line of prose:

  1. whether it declares a path as something to produce rather than to read
     (`OUTPUT_DECLARATION`)
  2. what it says once Markdown emphasis is removed (`without_emphasis`)

Each had its own copy. That is the exact failure this repository keeps
auditing: the unfilled-marker rule had two implementations that disagreed, and a
fence parser that was reimplemented per-file. A rule that exists twice is a rule
whose two copies drift, and the drift is invisible until one of them is wrong.

The marker rule already has a check that fails the build if a second
implementation appears. This module makes the same guarantee structural for these
two: they are defined once, here, and both callers import from it.

Self-contained, deliberately
---------------------------
The first version imported `bundle-skill.py` and re-exported its definitions. That
was DRY and it broke the bundle: `tools/text_rules.py` is classified as a runtime
tool, so it ships, and on load it tried to import `tools/bundle-skill.py` from the
bundle -- where that file is deliberately absent, because a bundler has no reason
to ship itself. The bundle therefore contained a module that could not be
imported, and `python3 tools/validate-skills.py` inside a bundle raised
FileNotFoundError.

Shared code has to live somewhere both consumers can reach, and "somewhere" is
this file. The cost is that `bundle-skill.py` must import this rather than define
the patterns itself; that is the right direction, because the bundler is the
larger consumer and the one whose copy had drifted.

The duplicate-implementation check in validate-skills.py scans for a second
definition of the *marker* rule. It does not need extending here, because a
second definition of these two patterns would have to re-import this module to
be consistent, and the import is the thing that would break.
"""

from __future__ import annotations

import re

# A path that names where something will be written, rather than a file in this
# repository. "output directory", "cache directory", "loader default" and "state
# lives at" all describe a location that will exist because the skill made it.
#
# Kept deliberately tight. A looser set that included "manifest", "config file"
# and "copy" would exempt real references to files that do not exist, which is
# the failure this rule exists to prevent -- and that looseness was measured, not
# assumed: an earlier draft exempted any path in a paragraph containing "create"
# or "write", which is nearly every paragraph, and a planted missing reference
# passed unnoticed while the error count read zero.
OUTPUT_DECLARATION = re.compile(
    r"(?i)\b(save as|saved as|create|creates|creating|write|writes|writing|"
    r"add|adds|maintain|maintains|update|updates|generate|generates|emit|"
    r"emits|store|stores|place|places|put|puts|output to|new file|"
    r"output directory|cache directory|cacheDir|loader default|"
    r"relative to (?:the )?current directory|state lives at|"
    r"lives at|video_folder|path-resolution)\b"
)

# A bolded field label introducing what a command produced. "**Output:** MP4
# videos in `./videos/`" is a declaration in exactly the way "**Default:**
# `./.mcp.json` already was.
#
# Matched against the RAW line, not the de-emphasised one: the asterisks are
# what make it a label. So the two rules are applied to two different views of
# the same line, which is why line_declares_output() exists rather than a single
# combined pattern.
OUTPUT_LABEL = re.compile(r"(?i)\*\*output:?\*\*")

# A dot-relative path in a document describing something other than this
# repository: the reader's own project, a third party's defaults, or an attack
# string.
NOT_THIS_REPOSITORY = re.compile(
    r"(?i)(\be\.g\.|\bfor example\b|\bas an example\b|adversarial|path traversal|"
    r"the user'?s|reader'?s|is relative to|path is relative|from `|"
    r"in your (?:own )?(?:project|repo)|example of|illustrat|"
    r"\*\*default\*\*|\bdefault:|uses `.*` internally|imports? only|"
    r"video_folder|>\s*\./|\bcp \")"
)

# Emphasis can be stripped before a prose rule matches. "imports **only**
# `../index`" says what "imports only `../index`" says, and only the second
# matched. That is a bug in the matcher, not a property of the document -- an
# author bolding a word should not decide whether their sentence counts as a
# declaration.
def without_emphasis(line: str) -> str:
    """Strip markdown emphasis, leaving the text a reader actually reads.

    Bold and italic markers go; the words between them stay. Note this is the
    opposite of what a label rule needs: "**Output:**" is *only* recognisable as
    a field label while the asterisks are still there. One line, two views,
    because the two are looking for different things.
    """
    return re.sub(
        r"\*\*(.+?)\*\*",
        r"\1",
        re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"\1", line),
    )


def line_declares_output(line: str) -> bool:
    """Does this line say the paths in it are produced rather than read?

    Three views, because the rules were written against three shapes of prose:
    the raw line for a bolded field label, the de-emphasised line for the prose
    rules, and the raw line again because NOT_THIS_REPOSITORY contains a
    shell-continuation pattern that de-emphasis would leave intact but that a
    stripped `**default**` would have destroyed.
    """
    return bool(
        OUTPUT_LABEL.search(line)
        or OUTPUT_DECLARATION.search(without_adjunct_gerund(without_emphasis(line)))
        or NOT_THIS_REPOSITORY.search(line)
    )


# A gerund with no object is an adjunct, not a declaration. "Before writing,
# read `references/09-risk-and-macro.md`" is a temporal frame wrapped around a
# different instruction, and its "writing" was matching OUTPUT_DECLARATION and
# clearing the reference standing right beside it.
#
# A gerund declares only when something follows it that it can take as an
# object, and the comma is the test: "writing the report to `docs/report.md`"
# declares, "writing," does not.
#
# Only the two -ing forms in OUTPUT_DECLARATION's vocabulary need this -- it has
# "creating" and "writing" and no other participle, so the other five verbs
# there ("add", "store", "place", ...) are untouched. Bare imperatives were
# never at risk: a comma after "Add" is not English.
_ADJUNCT_GERUND = re.compile(r"(?i)\b(?:writing|creating)\s*(?=,)")


def without_adjunct_gerund(text: str) -> str:
    """Drop participles that carry no object, leaving everything else.

    Removing rather than negating: the alternative is to teach the pattern a
    negative lookahead, which puts the exception inside the vocabulary where
    the next person adding a participle will not see it.
    """
    return _ADJUNCT_GERUND.sub(" ", text)


# Where one instruction can end and the next begin.
#
# A Markdown line routinely packs several instructions, and a declaration that
# governs one of them must not exempt the others. The line that exposed this
# held a read, a write, and two more reads:
#
#   Score using `references/11-scoring-rubric.md` (run `scripts/score.py` for
#   the arithmetic), then write the report using the template in
#   `references/12-report-template.md`. Before writing, read the worked
#   exemplars in `examples/` to calibrate the target quality:
#   `examples/forensic-analysis-example.md` (a Forensic-mode review ...).
#
# Judged per line, the "write" cleared all five paths, so a referenced file that
# did not exist went unreported and the error count read zero. Scoping the
# judgement to the clause removes it: the write exempts the template, the reads
# stay reads, and the missing exemplar is reported.
#
# The split is deliberately narrow, because a missed split and a false split are
# not symmetric. Merging two clauses only re-applies a declaration the author
# actually wrote -- the old behaviour, and a false negative. Splitting a clause
# that never ended exempts a reference on the strength of a verb belonging to a
# neighbouring instruction, and reports a file that exists as missing: a false
# positive that stops a commit. So this cuts only where an instruction can
# genuinely end, and leaves a decimal point, a file extension, an initial and
# an abbreviation intact, because none of those end one.
_CLAUSE_BOUNDARY = re.compile(
    # A sentence end. What may precede the full stop: a lowercase letter, digit
    # or closing mark, or a two-letter-capital token. That last alternative is
    # what lets "per the AR. The next step" split -- sentences here end in
    # acronyms constantly -- while still refusing "J. Smith", where the token
    # before the stop is a single capital. Requiring a full stop to be followed
    # by whitespace and an opening character is what keeps "18.4%" and the full
    # stop in "`report.md`." from being read as sentence ends.
    r"(?:(?<=[a-z0-9`)\]\"'])|(?<=[A-Za-z][A-Z]))\.(?=\s+[A-Z`*])"
    r"|(?<=[a-z0-9`)\]\"']);(?=\s)"   # a semicolon
    r"|(?:,|;)\s+then\b"             # a sequencing join
    r"|\s+—\s+"                     # the em-dash separator
)

# An abbreviation's full stop ends no instruction, so it is not a boundary.
# "e.g. `path`" must stay with the sentence it sits in, or the "e.g." that
# marks a path as belonging to some other repository is cut away from it and
# the path starts looking like a dangling reference in this one.
#
# Case-sensitive on purpose, and matched against the text that ends immediately
# before the boundary, so there is no trailing full stop to match here. The
# capitalised entries would fire on ordinary words if this were case-
# insensitive: "No." would swallow the end of any sentence ending "there is no",
# and "St." every "st.". Both are misses in the safe direction -- a clause left
# joined, so a declaration is re-applied -- but there is no reason to take them.
_ABBREVIATION_TAIL = re.compile(
    r"(?:\be\.g|\bi\.e|\betc|\bvs|\bpp|\bcf|\bNo|\bFig|\bDr|\bMr|\bMs|\bSt)$"
)


def clauses(line: str) -> list[str]:
    """Split one line into the spans a single instruction can govern.

    Splitting on the full stop alone would cut a decimal, a file extension, an
    initial and an abbreviation, so the boundary pattern requires a lowercase
    letter, digit or closing mark before the full stop and whitespace plus an
    opening character after it, and the abbreviation guard rejects the rest.

    Returns a single-element list for a line with no boundary, which is the
    common case and leaves the line-level behaviour unchanged.
    """
    out: list[str] = []
    start = 0
    for match in _CLAUSE_BOUNDARY.finditer(line):
        if _ABBREVIATION_TAIL.search(line[start:match.start()]):
            continue
        out.append(line[start:match.start()])
        start = match.end()
    out.append(line[start:])
    return [c for c in out if c.strip()]


def output_spans(line: str) -> list[str]:
    """The spans of one line whose paths are declared as outputs, not reads.

    The two rules that match are scoped differently, and deliberately so.

    OUTPUT_DECLARATION names an instruction, and an instruction governs the
    paths in its own clause only. That is the fix this function exists for: a
    single "write" in one clause used to clear every other path on the line,
    including references to files that did not exist.

    NOT_THIS_REPOSITORY makes a claim about where the paths on the line come
    from -- "a folder in the reader's own repository", "e.g.", "for example" --
    and a disclaimer is routinely written after the thing it disclaims, in the
    next clause: "`docs/decisions/` -- a folder in the reader's own repository,
    not a directory this skill ships." Scoping that to clauses cut the path away
    from its own justification and reported a file the document had explicitly
    said was not its to carry.

    So a line matching NOT_THIS_REPOSITORY is exempt whole, which is also the
    behaviour it had before either scoping existed.
    """
    if NOT_THIS_REPOSITORY.search(line):
        return [line]
    return [
        clause
        for clause in clauses(line)
        if OUTPUT_LABEL.search(clause)
        or OUTPUT_DECLARATION.search(
            without_adjunct_gerund(without_emphasis(clause))
        )
    ]


__all__ = [
    "OUTPUT_DECLARATION",
    "OUTPUT_LABEL",
    "NOT_THIS_REPOSITORY",
    "without_emphasis",
    "without_adjunct_gerund",
    "line_declares_output",
    "clauses",
    "output_spans",
]
