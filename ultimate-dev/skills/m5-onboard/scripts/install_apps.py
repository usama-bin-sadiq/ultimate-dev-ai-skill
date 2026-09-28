#!/usr/bin/env python3
"""Push a directory of .py files onto the device's /flash/, then reboot it.

What it does
------------
Uploads every ``.py`` in a source directory into the device's flash over the
MicroPython REPL, in paste mode, and reboots with ``machine.reset()``.

Layout mapping:

* ``<src>/*.py``       -> ``/flash/``
* ``<src>/apps/*.py``  -> ``/flash/apps/`` — UIFlow's stock launcher scans that
  directory, so anything there appears in its menu.

The three things this script exists to get right
------------------------------------------------
1. **Paste mode.** Sending ``try:`` / ``except:`` line by line makes the REPL
   accumulate indentation forever and the upload hangs. Blocks are bracketed
   with Ctrl-E and executed with Ctrl-D.
2. **Reboot method.** DTR/RTS is a hard reset on a UART-bridge board and a
   *silent no-op* on a native-USB ESP32-S3, because those pins are not wired to
   EN. Reaching for it on a ``usbmodem`` port leaves the new files on disk and
   the old code running, which looks exactly like a failed upload. This script
   resets through the REPL.
3. **NVS ``boot_option``.** UIFlow's default ``boot_option=1`` starts a
   background Flow-pairing BLE advertise that wedges the NimBLE controller on
   ESP32-S3. User BLE code then fails with ``OSError(-519)`` and the device
   advertises with empty AD fields that iOS and the desktop app filter out. When
   the bundle ships a root ``main.py``, this script sets ``boot_option=2`` so
   UIFlow's launcher does not run and our ``main.py`` takes the boot flow.

   The NVS write must use ``set_str``, never ``set_blob``: UIFlow calls
   ``nvs.get_str()`` and ESP-IDF tags blob and string entries separately, so a
   blob-tagged key returns ``ESP_ERR_NVS_NOT_FOUND`` and the device boot-loops.
   A prior bad write is erased first.

Usage
-----
    python3 scripts/install_apps.py --port /dev/cu.usbmodem1101 --src buddy
    python3 scripts/install_apps.py --port COM3 --src ./my-apps --no-reboot
    python3 scripts/install_apps.py --port /dev/ttyUSB0 --src buddy --dry-run

Exit codes: 0 everything uploaded and the device rebooted, 1 something failed,
2 bad input.

Provenance
----------
Reconstructed to implement stage 5 of the workflow in the SKILL.md, with the
layout mapping, the ``boot_option`` rule, the paste-mode requirement, and the
reboot method it states. The upload loop, the backup handling, and the report are
this file's own.
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from mpy_repl import (  # noqa: E402
    ReplError,
    capture_boot_log,
    enter_raw_repl,
    exit_raw_repl,
    is_native_usb,
    open_port,
    repl_paste,
    repl_reset,
)

DEFAULT_BUDDY_DIRS = (
    "buddy/device",                 # this repo, found relative to this file
    "~/Downloads/m5stack/buddy/device",
    "~/Desktop/m5stack/buddy/device",
)
# UIFlow's launcher, kept aside before anything overwrites it. There is no
# boot_uiflow.py backup to restore in the shipped bundle, so this one is made
# here when a root boot.py is about to be replaced.
BACKUP_NAME = "boot_uiflow.py"
# Root-level entries that make the device boot our code rather than UIFlow's.
TAKEOVER_MAIN = "main.py"
BOOT_OPTION_TAKEOVER = 2
MAX_FILE_BYTES = 128 * 1024
UPLOAD_SETTLE = 0.25


def log(message: str) -> None:
    print(message, file=sys.stderr, flush=True)


def resolve_src(src: str) -> Path:
    """Resolve ``--src``, with ``buddy`` as the shorthand for the shipped bundle.

    Order: an explicit path, then ``$M5_BUDDY_DIR``, then this repo found by
    walking up from this file, then the two historical download locations.
    """
    if src != "buddy":
        path = Path(src).expanduser()
        if not path.is_dir():
            raise SystemExit(f"error: --src {src} is not a directory")
        return path

    override = os.environ.get("M5_BUDDY_DIR")
    if override:
        path = Path(override).expanduser()
        if path.is_dir():
            log(f"--src buddy resolved from $M5_BUDDY_DIR: {path}")
            return path
        raise SystemExit(f"error: $M5_BUDDY_DIR is set to {override}, which is not a directory")

    here = Path(__file__).resolve()
    for parent in list(here.parents)[:6]:
        candidate = parent / "buddy" / "device"
        if candidate.is_dir():
            log(f"--src buddy resolved from the repo: {candidate}")
            return candidate

    for relative in DEFAULT_BUDDY_DIRS[1:]:
        candidate = Path(relative).expanduser()
        if candidate.is_dir():
            log(f"--src buddy resolved from {relative}")
            return candidate

    raise SystemExit(
        "error: could not resolve --src buddy.\n"
        "Tried, in order: $M5_BUDDY_DIR, buddy/device/ next to this script, "
        f"{DEFAULT_BUDDY_DIRS[1]}, {DEFAULT_BUDDY_DIRS[2]}.\n"
        "Set M5_BUDDY_DIR to the bundle directory, or pass --src with an explicit path."
    )


def collect(src: Path) -> list[tuple[Path, str]]:
    """Every .py under the source, paired with its destination on the device."""
    files: list[tuple[Path, str]] = []
    for path in sorted(src.glob("*.py")):
        if path.name.startswith("."):
            continue
        files.append((path, f"/flash/{path.name}"))
    apps = src / "apps"
    if apps.is_dir():
        for path in sorted(apps.glob("*.py")):
            if path.name.startswith("."):
                continue
            files.append((path, f"/flash/apps/{path.name}"))
    return files


def _ensure_dirs(handle) -> None:
    repl_paste(
        handle,
        "import os\n"
        "for d in ('/flash', '/flash/apps'):\n"
        "    try:\n"
        "        os.mkdir(d)\n"
        "    except OSError:\n"
        "        pass\n",
    )


def _exists(handle, remote: str) -> bool:
    output = repl_paste(handle, f"import os; print(os.path.exists({remote!r}))")
    return b"True" in output


def _backup_boot(handle) -> bool:
    """Keep the stock launcher before our main.py takes the boot flow."""
    if not _exists(handle, "/flash/boot.py"):
        return False
    if _exists(handle, f"/flash/{BACKUP_NAME}"):
        log(f"{BACKUP_NAME} already exists; leaving the existing copy alone.")
        return True
    log(f"backing up /flash/boot.py to /flash/{BACKUP_NAME}")
    repl_paste(
        handle,
        "import os\n"
        f"with open('/flash/boot.py','rb') as s, open('/flash/{BACKUP_NAME}','wb') as d:\n"
        "    d.write(s.read())\n",
    )
    return True


def _set_boot_option(handle) -> bool:
    """Write NVS boot_option=2 as a *string*, erasing any prior blob first.

    The erase is not defensive programming; it is the recovery path. A blob
    written by an older version of this script makes the key invisible to
    ``get_str``, the device boot-loops, and ``nvs.erase_key`` is the only way out
    short of reflashing.
    """
    log("setting NVS boot_option=2 (string, not blob) so UIFlow's launcher does not run")
    repl_paste(
        handle,
        "import nvs\n"
        "n = nvs.NVS('uiflow')\n"
        f"try:\n"
        f"    n.erase_key('boot_option')\n"
        f"except Exception:\n"
        f"    pass\n"
        f"n.set_str('boot_option', '{BOOT_OPTION_TAKEOVER}')\n"
        f"print('boot_option ->', n.get_str('boot_option'))\n",
    )
    return True


def upload(handle, path: Path, remote: str, dry_run: bool) -> bool:
    """One file, in paste mode, with the trailing newline that actually executes it."""
    if dry_run:
        log(f"  would write {path} -> {remote} ({path.stat().st_size} bytes)")
        return True

    source = path.read_text(encoding="utf-8", errors="replace")
    # Writing from a Python list of strings avoids any shell or encoding round
    # trip, and keeps CRLF out of a file the device will read back.
    literals = "\n".join(
        f"    {line!r}" for line in source.splitlines()
    )
    program = (
        f"import os\n"
        f"_src = [\n{literals}\n]\n"
        f"with open({remote!r}, 'w') as _f:\n"
        f"    _f.write('\\n'.join(_src) + '\\n')\n"
        f"print('wrote', os.path.getsize({remote!r}), 'to', {remote!r})\n"
    )
    try:
        repl_paste(handle, program, timeout=max(5.0, path.stat().st_size / 4096))
    except ReplError as exc:
        log(f"  FAILED {remote}: {exc}")
        return False
    time.sleep(UPLOAD_SETTLE)
    log(f"  wrote {remote} ({path.stat().st_size} bytes)")
    return True


def dry_run_report(src: Path, files: list[tuple[Path, str]], port: str) -> None:
    log(f"source: {src}")
    log(f"port:   {port}")
    log(f"files:  {len(files)}")
    log("")
    for path, remote in files:
        log(f"  {remote:<34} {path.stat().st_size:>8} bytes  <- {path}")
    log("")
    if any(remote == f"/flash/{TAKEOVER_MAIN}" for _path, remote in files):
        log(f"The bundle ships /flash/{TAKEOVER_MAIN}, so boot_option="
            f"{BOOT_OPTION_TAKEOVER} will be set and /flash/boot.py will be backed up")
        log(f"to /flash/{BACKUP_NAME}. Without this the UIFlow launcher runs first and its")
        log("Flow-pairing BLE advertise wedges the NimBLE controller on ESP32-S3, after")
        log("which every user BLE advertise fails with OSError(-519).")
    else:
        log(f"No /flash/{TAKEOVER_MAIN} in the bundle, so boot_option is left alone and")
        log("UIFlow's own launcher keeps the boot flow.")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Push a directory of .py files onto /flash/, then reboot the device.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--port", required=True, help="serial port from detect.py")
    parser.add_argument("--src", required=True, help="source directory, or 'buddy'")
    parser.add_argument("--no-reboot", action="store_true",
                        help="upload but leave the device running the old code")
    parser.add_argument("--no-boot-option", action="store_true",
                        help="do not set NVS boot_option, even for a root main.py")
    parser.add_argument("--dry-run", action="store_true", help="list the uploads and exit")
    parser.add_argument("--boot-log", type=float, default=0.0, metavar="SECONDS",
                        help="after rebooting, capture this many seconds of boot output")
    args = parser.parse_args(argv)

    src = resolve_src(args.src)
    files = collect(src)
    if not files:
        raise SystemExit(
            f"error: no .py files under {src}. Expected *.py at the top level and "
            "optional apps/*.py."
        )
    for path, _remote in files:
        if path.stat().st_size > MAX_FILE_BYTES:
            log(f"warning: {path} is {path.stat().st_size} bytes, over the "
                f"{MAX_FILE_BYTES}-byte comfortable upload size. It may time out.")

    native = is_native_usb(args.port)
    if args.dry_run:
        dry_run_report(src, files, args.port)
        return 0

    handle = open_port(args.port)
    failures = 0
    try:
        enter_raw_repl(handle)
        _ensure_dirs(handle)

        if args.no_boot_option and any(
            remote == f"/flash/{TAKEOVER_MAIN}" for _path, remote in files
        ):
            log("warning: --no-boot-option given with a root main.py in the bundle. Any BLE")
            log("app will hit OSError(-519) on ESP32-S3 because UIFlow's launcher will")
            log("start its Flow-pairing advertise first.")

        log(f"uploading {len(files)} file(s)")
        for path, remote in files:
            if not upload(handle, path, remote, args.dry_run):
                failures += 1

        if failures == 0 and not args.no_boot_option and any(
            remote == f"/flash/{TAKEOVER_MAIN}" for _path, remote in files
        ):
            _backup_boot(handle)
            _set_boot_option(handle)

        exit_raw_repl(handle)
    except ReplError as exc:
        log(f"error: the REPL failed: {exc}")
        return 1
    finally:
        try:
            handle.close()
        except Exception:
            pass

    if failures:
        log("")
        log(f"{failures} of {len(files)} file(s) failed to upload. Nothing has been")
        log("rebooted, so the device is still running what it was running before.")
        return 1

    log("")
    log(f"all {len(files)} file(s) uploaded")

    if args.no_reboot:
        log("not rebooting (--no-reboot). The files are on disk and the old code is still")
        log("running until the device restarts. That is expected, not a failure.")
        return 0

    if native:
        log("rebooting with machine.reset() through the REPL — DTR/RTS is a no-op on")
        log("native USB, and relying on it leaves the new files on disk with the old code")
        log("still running.")
    else:
        log("rebooting")

    handle = open_port(args.port)
    try:
        repl_reset(handle)
    except SystemExit as exc:
        log(f"error: the reboot failed: {exc}")
        return 1

    if args.boot_log > 0:
        log("")
        log(f"capturing {args.boot_log:.0f}s of boot output")
        log(capture_boot_log(args.port, args.boot_log))

    return 0


if __name__ == "__main__":
    sys.exit(main())
