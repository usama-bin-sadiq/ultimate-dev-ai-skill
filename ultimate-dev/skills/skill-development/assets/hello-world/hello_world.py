"""Hello world — the smallest thing that is still a real program.

WHAT THIS IS
    A deliberately boring module. One public function, one docstring that
    explains what it returns and when, and three tests that pin the behaviour
    people actually depend on.

WHY IT EXISTS
    Step 2 of this skill's process names ``assets/hello-world/`` as the
    "boilerplate HTML/React project files" template: the thing you would otherwise
    rewrite for every new project. The HTML/CSS variant lives in
    ``assets/frontend-template/``; this is the Python equivalent, and it is
    deliberately small enough to read in one sitting.

WHAT IT IS NOT
    Not a framework, not a package layout, not a starting point for a
    distribution. A template with structure you have to unpick is a template you
    will not use.

PROVENANCE
    Reconstructed to serve the ``assets/hello-world/`` example in this skill's
    SKILL.md. The function, the tests, and the notes are this file's own.
"""

from __future__ import annotations

__all__ = ["greeting", "DEFAULT_NAME"]

# The one decision this module makes, named rather than inlined: what a caller
# gets when it does not say. Changing it is a breaking change, which is why it
# is a constant rather than a default buried in a signature.
DEFAULT_NAME = "world"


def greeting(name: str = DEFAULT_NAME, *, excited: bool = False) -> str:
    """Return a greeting for ``name``.

    Args:
        name: Who to greet. Leading and trailing whitespace is stripped, so a
            value that arrived from a form field behaves the same as one that
            did not.
        excited: Append an exclamation mark. The default is a plain greeting,
            because punctuation is a style decision and a function should not
            make it silently.

    Returns:
        A string. Empty input is not an error: it falls back to ``DEFAULT_NAME``,
        because "greet an anonymous user" is a normal thing to want and raising
        would push that decision onto every caller.

    Example:
        >>> greeting()
        'Hello, world'
        >>> greeting("Ada", excited=True)
        'Hello, Ada!'
        >>> greeting("  Ada  ")
        'Hello, Ada'
    """
    who = (name or "").strip() or DEFAULT_NAME
    return f"Hello, {who}{'!' if excited else ''}"


if __name__ == "__main__":
    # Running the file prints both forms, which is the fastest way to confirm an
    # edit did what you thought.
    print(greeting())
    print(greeting("Ada", excited=True))
