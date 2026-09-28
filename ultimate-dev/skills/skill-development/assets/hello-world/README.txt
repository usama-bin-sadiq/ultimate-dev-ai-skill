Hello world template
====================

The smallest thing that is still a real program. Copy it, rename it, and replace
the behaviour — keeping the shape.

Provenance
----------
Authored from the description of ``assets/hello-world/`` in this skill's SKILL.md;
no original copy was recovered. The module's function name, its signature, and the
three tests are a reconstruction chosen to demonstrate the shape — a test file
beside the module — rather than a recovered file. The behaviour is trivial by
design: the point of this template is the layout, not the logic.

Why this exists
---------------
Step 2 of the skill-development process: writing the same few lines of Python for
every new project is exactly what an ``assets/`` template is for. This is the
Python counterpart to ``assets/frontend-template/``, and it is deliberately small
enough to read in one sitting.

Files
-----

``hello_world.py``
    One public function, a named default, and a doctest in the docstring.

``test_hello_world.py``
    Five tests, covering the three things a caller could depend on: the default,
    an explicit name, and how empty and whitespace input is handled.

Using it
--------

.. code-block:: bash

    cp hello_world.py test_hello_world.py /path/to/your/project/
    cd /path/to/your/project
    python -m unittest -v test_hello_world

Renaming: replace ``hello_world`` with your module name everywhere, including
the import in the test file. A copied file still called ``hello_world`` will
confuse the first person who greets by it.

Conventions this template demonstrates
-------------------------------------

* **The default is a named constant.** ``DEFAULT_NAME`` rather than a literal in
  the signature, so changing it is visible and greppable.
* **Empty input is not an error.** "Greet an anonymous user" is a normal thing
  to want, and raising would push that decision onto every caller.
* **A behaviour flag is keyword-only.** ``greeting("Ada", True)`` is unreadable;
  ``greeting("Ada", excited=True)`` is not.
* **The docstring carries examples.** The doctest is executable, so the examples
  cannot go stale without a test failing.
* **Tests cover the edges, not the implementation.** Whitespace and ``None`` are
  pinned because they are documented behaviour, not because they are easy to
  reach.

Before shipping your copy
-------------------------

1. Replace the docstring with the real contract. The one here is a placeholder
   for a real one, and a placeholder contract is worse than none.
2. Delete the tests you do not need, and add the ones you do. Five tests that
   pass is a starting point, not evidence.
3. Delete this file once you have read it. A template that ships alongside the
   finished project is noise.
