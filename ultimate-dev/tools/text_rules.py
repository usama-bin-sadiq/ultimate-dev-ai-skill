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
        or OUTPUT_DECLARATION.search(without_emphasis(line))
        or NOT_THIS_REPOSITORY.search(line)
    )


__all__ = [
    "OUTPUT_DECLARATION",
    "OUTPUT_LABEL",
    "NOT_THIS_REPOSITORY",
    "without_emphasis",
    "line_declares_output",
]
