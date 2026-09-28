Vendored third-party dependencies
=================================

Provenance
----------
This README is authored, not recovered. The pyserial 3.5 tree it describes is
**not** in this repository: writing out a third-party package from memory would
produce something that looks vendored and is not, which is worse than an empty
directory with a README that says what goes in it. To populate the directory the
way the description below says, run::

    pip download pyserial==3.5 --no-deps --no-binary :all: -d /tmp/pys
    tar -xzf /tmp/pys/pyserial-3.5.tar.gz
    cp -R pyserial-3.5/serial ./serial
    cp pyserial-3.5/LICENSE ./LICENSE.pyserial

Until then every script in this skill falls back to an installed pyserial and
says so, rather than pretending a vendored copy resolved.

This directory is where third-party packages are vendored so a fresh clone
works with no pip step. It is on ``sys.path``: every script in this skill calls
``mpy_repl.ensure_on_syspath()``, which prepends this directory before the first
third-party import, and the import machinery then prefers it over whatever the
user has installed system-wide.

What belongs here
-----------------

``serial/``
    **pyserial 3.5** (BSD-3-Clause, Apache-compatible), the upstream package
    directory, vendored verbatim. About 500 KB of pure Python, identical on
    macOS, Linux, and Windows. This is what makes port enumeration and REPL I/O
    work on a fresh clone with no install step.

``serial.pyi``
    Optional type stubs, if you vendor them alongside.

What does *not* belong here, and why
------------------------------------

``esptool``
    GPLv2+. Vendoring it would put GPL code in a tree that is otherwise
    Apache-2.0, so it is deliberately absent. It is a pip dependency instead:
    ``onboard.py``'s preflight finds it missing, asks, and runs
    ``python -m pip install --user esptool`` — dropping ``--user`` inside a venv
    so it lands in the venv's site-packages. Subprocesses invoke it as
    ``[sys.executable, "-m", "esptool", ...]``, which works regardless of PATH,
    which matters on Windows where a ``--user`` install frequently lands outside
    it.

    A non-interactive caller (piped stdin, CI) skips the prompt and gets the
    install command as a hint instead.

    If esptool is missing, ``flash.py`` refuses with the install command rather
    than failing somewhere less obvious.

If this directory is empty
--------------------------
That is expected on a source-only download or after someone trimmed the repo.
The same preflight path reinstalls pyserial from pip, so the skill still works.
Nothing here is required for a functioning checkout; it exists so that the
common case needs no install at all.

Version pinning
---------------
pyserial is pinned at 3.5 because that is what this skill was developed and
tested against. If you re-vendor, keep the pin and update the note in
SKILL.md's Dependencies section, because the REPL helpers in ``mpy_repl.py``
depend on ``serial.tools.list_ports.comports()`` and on the ``in_waiting`` /
``dtr`` / ``rts`` attributes being present.
