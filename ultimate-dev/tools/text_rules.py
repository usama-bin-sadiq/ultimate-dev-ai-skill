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
two: they cannot be copied, because there is only one place to copy from.

`validate-skills.py` is executed as a script by CI from an arbitrary working
directory, so this is imported by path rather than by package name. Importing by
name would require `tools/` on `sys.path`, and the workflows call the validators
as `python ultimate-dev/tools/validate-skills.py` from the repository root.
"""

from __future__ import annotations

import importlib.util
import pathlib
import re
import sys

# Importing bundle-skill.py by path writes a .pyc beside it. The validator that
# loads this module fails the build for a committed build artefact, so its own
# helper import made it fail.
sys.dont_write_bytecode = True

HERE = pathlib.Path(__file__).resolve().parent


def _load_bundle_skill():
    """Import bundle-skill.py, which is a script rather than a module."""
    spec = importlib.util.spec_from_file_location(
        "_bundle_skill", HERE / "bundle-skill.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_b = _load_bundle_skill()
# Re-exported so callers can `from text_rules import OUTPUT_DECLARATION`.
OUTPUT_DECLARATION = _b.OUTPUT_DECLARATION
NOT_THIS_REPOSITORY = _b.NOT_THIS_REPOSITORY
OUTPUT_LABEL = getattr(_b, "OUTPUT_LABEL", None)
without_emphasis = _b.without_emphasis
line_declares_output = _b.line_declares_output

__all__ = [
    "OUTPUT_DECLARATION",
    "NOT_THIS_REPOSITORY",
    "OUTPUT_LABEL",
    "without_emphasis",
    "line_declares_output",
]
