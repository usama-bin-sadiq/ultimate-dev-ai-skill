"""Tests for hello_world.

Three tests, covering the three behaviours a caller could depend on: the default,
an explicit name, and the whitespace and empty-input handling. Anything beyond
that belongs in the module's own tests once it has behaviour worth pinning.

PROVENANCE
    Part of assets/hello-world/ in this skill's assets. These tests are this
    file's own.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from hello_world import DEFAULT_NAME, greeting  # noqa: E402

import unittest  # noqa: E402


class GreetingTest(unittest.TestCase):
    def test_default_name(self):
        """No argument greets the documented default."""
        self.assertEqual(greeting(), f"Hello, {DEFAULT_NAME}")

    def test_explicit_name(self):
        """An explicit name is used verbatim."""
        self.assertEqual(greeting("Ada"), "Hello, Ada")

    def test_excited_adds_one_exclamation(self):
        """excited=True adds exactly one mark, and False adds none."""
        self.assertEqual(greeting("Ada", excited=True), "Hello, Ada!")
        self.assertEqual(greeting("Ada", excited=False), "Hello, Ada")

    def test_whitespace_is_stripped(self):
        """A value from a form field behaves like a clean one."""
        self.assertEqual(greeting("  Ada  "), "Hello, Ada")

    def test_empty_falls_back_to_the_default(self):
        """Empty input is a normal case, not an error."""
        self.assertEqual(greeting(""), f"Hello, {DEFAULT_NAME}")
        self.assertEqual(greeting("   "), f"Hello, {DEFAULT_NAME}")
        self.assertEqual(greeting(None), f"Hello, {DEFAULT_NAME}")


if __name__ == "__main__":
    unittest.main()
