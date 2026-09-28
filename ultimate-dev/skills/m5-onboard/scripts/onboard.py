#!/usr/bin/env python3
"""The orchestrator: detect, identify, flash, install apps, smoke test.

What it does
------------
Runs the whole cold-start sequence for a freshly-plugged-in board, handling the
handoffs between stages that a person stitching the sub-scripts together would
have to get right:

* preflight: check that Python, pyserial, and esptool are present, and offer to
  install what is missing;
* detect the port, asking rather than guessing when there is a real choice;
* coach the user through the physical button press on a native-USB board, and
  wait for the port to come back in download mode;
* flash, tolerating the two esptool failure patterns that are not failures;
* capture the MAC, which UIFlow shows at first boot and which identifies the
  board later;
* install the app bundle, including the NVS ``boot_option`` write;
* optionally smoke test;
* print a DONE banner with the port, the chip, and the MAC.

Why this exists rather than a shell script
------------------------------------------
Every step here is a question with a human in it — which port, which board
variant, is the screen dark yet. A script that cannot ask cannot be the
orchestrator, and a person driving the sub-scripts one at a time will eventually
forget the ordering constraint between the button press and the port rescan.

Run it in the background with a log you can tail
-------------------------------------------------
The full run takes two to three minutes. Under an agent harness whose Bash tool
buffers output until exit, that silence looks exactly like a hang. Run it
backgrounded with ``tee`` and tail the log, rather than calling it in the
foreground:

    python3 scripts/onboard.py --apps buddy 2>&1 | tee /tmp/m5-onboard.log
    tail -f /tmp/m5-onboard.log | grep -E --line-buffered \\
      "^====|Enter download mode|rebooted into UIFlow|DONE|ERROR|Attempt [0-9]"

Usage
-----
    python3 scripts/onboard.py --apps buddy
    python3 scripts/onboard.py --apps buddy --port /dev/cu.usbmodem1101
    python3 scripts/onboard.py --variant core2 --apps buddy --skip-flash
    python3 scripts/onboard.py --apps buddy --stage detect,flash
    python3 scripts/onboard.py --preflight-only

Exit codes: 0 the device is provisioned, 1 a stage failed, 2 bad input.

Provenance
----------
Reconstructed to implement the stage list and the invocation contract in the
SKILL.md, including the variant default, the stage names, the handoffs, and the
DONE banner. The preflight, the stage machine, and the prompts are this file's
own.
"""

from __future__ import annotations

import argparse
import importlib.util
import os
import re
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

STAGES = ("preflight", "detect", "flash", "install", "smoke")
DEFAULT_VARIANT = "cardputer-adv"
# The import name and the pip name differ for pyserial, and only esptool is ever
# installed at run time. pyserial is normally already resolvable from
# scripts/vendor/, so it is checked but not installed unless that copy is gone.
MODULES: tuple[tuple[str, str], ...] = (
    ("esptool", "esptool"),
    ("serial", "pyserial"),
)


def missing_modules() -> list[tuple[str, str]]:
    """Which modules are unresolvable, as (import name, pip name) pairs.

    The import name is what ``find_spec`` needs and what the code uses;
    ``pyserial`` is the distribution and ``serial`` is the module.
    """
    from mpy_repl import ensure_on_syspath  # noqa: E402

    ensure_on_syspath()
    return [
        (import_name, pip_name)
        for import_name, pip_name in MODULES
        if importlib.util.find_spec(import_name) is None
    ]
DOWNLOAD_PORT_TIMEOUT = 180
POST_FLASH_PORT_TIMEOUT = 60
MAC_PATTERN = re.compile(r"(?:[0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}")


def banner(text: str) -> None:
    print("", "=" * 70, text, "=" * 70, sep="\n", flush=True)


def log(message: str) -> None:
    print(message, file=sys.stderr, flush=True)


def in_venv() -> bool:
    return sys.prefix != getattr(sys, "base_prefix", sys.prefix)


def pip_prefix() -> list[str]:
    """pip arguments for this interpreter.

    ``--user`` is dropped inside a venv on purpose: a venv has its own
    site-packages, and ``--user`` there installs somewhere the venv will not
    look, so the import check afterwards fails and the whole preflight looks
    broken.
    """
    return [sys.executable, "-m", "pip", "install"] if in_venv() else [
        sys.executable, "-m", "pip", "install", "--user"
    ]


def ensure_vendor_on_path() -> bool:
    """Prepend scripts/vendor/ so a vendored pyserial resolves."""
    from mpy_repl import ensure_on_syspath, have_vendored_serial  # noqa: E402

    ensure_on_syspath()
    if have_vendored_serial():
        log("pyserial: vendored copy under scripts/vendor/")
        return True
    if importlib.util.find_spec("serial") is not None:
        log("pyserial: system-wide install (the vendored copy is absent)")
        return True
    return False


def preflight(auto_install: bool, non_interactive: bool) -> bool:
    """Check the dependencies, and offer to install what is missing."""
    banner("STAGE 1/5  preflight")

    log(f"python:   {sys.version.split()[0]}  ({sys.executable})")
    log(f"venv:     {'yes' if in_venv() else 'no'}")
    ensure_vendor_on_path()

    missing = missing_modules()
    if not missing:
        log("esptool:  importable")
        log("pyserial: importable")
        return True

    # A missing pyserial with no vendored copy is the prune-vendor case the
    # skill documents: reinstall it rather than refusing to run.
    names = [import_name for import_name, _pip in missing]
    for import_name, pip_name in missing:
        log(f"{import_name}: MISSING (pip name: {pip_name})")

    commands = "\n".join(
        f"  {' '.join(pip_prefix())} {pip_name}" for _import_name, pip_name in missing
    )
    if non_interactive:
        log("")
        log("This is not an interactive session, so nothing will be installed. Run:")
        log(commands)
        return False

    if not auto_install:
        answer = input(
            f"\nInstall {' and '.join(pip_names(missing))} now? [Y/n]: "
        ).strip().lower()
        if answer not in ("", "y", "yes"):
            log("skipped. Install manually with:")
            log(commands)
            return False

    for import_name, pip_name in missing:
        log("")
        log(f"installing {pip_name}")
        completed = subprocess.run(  # noqa: S603 - fixed argv, no shell
            [*pip_prefix(), pip_name], check=False
        )
        if completed.returncode != 0:
            log(f"pip failed for {pip_name} (exit {completed.returncode})")
            return False

    still_missing = [name for name, _pip in missing_modules()]
    if still_missing:
        log("")
        log(f"still missing after installing: {', '.join(still_missing)}")
        return False
    log("")
    log("all dependencies present")
    return True


def pip_names(missing: list[tuple[str, str]]) -> list[str]:
    return [pip_name for _import_name, pip_name in missing]


# ------------------------------------------------------------------- stages --


def stage_detect(port: str | None, non_interactive: bool) -> str | None:
    banner("STAGE 2/5  detect")
    argv = [sys.executable, str(HERE / "detect.py"), "--yes" if non_interactive else "--probe"]
    if port:
        argv += ["--port", port]

    # Capture stdout while still streaming it, so the user sees the port list and
    # the next stage can read the selection out of it. Re-running detect to get
    # that one fact would be slower and would re-prompt.
    process = subprocess.Popen(  # noqa: S603 - fixed argv, no shell
        argv, stdout=subprocess.PIPE, stderr=None, shell=False
    )
    assert process.stdout is not None
    selected = None
    for raw in process.stdout:
        line = raw.decode("utf-8", errors="replace")
        print(line, end="", flush=True)
        if line.startswith("selected:"):
            selected = line.split(":", 1)[1].strip()
    if process.wait() != 0:
        return None
    return selected


def stage_flash(port: str, image: Path, variant: str, no_coach: bool) -> bool:
    banner("STAGE 3/5  flash")
    if not image.is_file():
        log(f"no firmware image at {image}; fetching one")
        completed = subprocess.run(  # noqa: S603
            [sys.executable, str(HERE / "fetch_firmware.py"), "--variant", variant],
            check=False,
        )
        if completed.returncode != 0:
            return False

    from mpy_repl import is_native_usb  # noqa: E402

    native = is_native_usb(port)
    argv = [sys.executable, str(HERE / "flash.py"), "--port", port, "--image", str(image)]
    if no_coach:
        argv.append("--no-coach")
    if native:
        log("native-USB board: the button press below is required, not optional")
    completed = subprocess.run(argv, check=False)  # noqa: S603
    if completed.returncode != 0:
        return False

    log("")
    log("waiting for the board to come back after the flash")
    from mpy_repl import wait_for_port  # noqa: E402

    back = wait_for_port(port, timeout=POST_FLASH_PORT_TIMEOUT)
    if back:
        log(f"{port} is back")
        return True
    log(f"{port} has not reappeared. This is normal for a few seconds; if it never does,")
    log("press RST on the board and re-run. The flash is idempotent.")
    return False


def stage_install(port: str, apps: str) -> bool:
    banner("STAGE 4/5  install apps")
    completed = subprocess.run(  # noqa: S603
        [sys.executable, str(HERE / "install_apps.py"), "--port", port, "--src", apps],
        check=False,
    )
    return completed.returncode == 0


def stage_smoke(port: str) -> bool:
    banner("STAGE 5/5  smoke test")
    completed = subprocess.run(  # noqa: S603
        [sys.executable, str(HERE / "smoke_test.py"), "--port", port],
        check=False,
    )
    return completed.returncode == 0


def capture_mac(port: str, seconds: float = 8.0) -> str | None:
    """Read the MAC the board prints at first boot.

    It identifies the board afterwards — in the Claude app, in M5Burner, and in
    a bug report — and it is the only hardware identifier worth having here.
    """
    from mpy_repl import capture_boot_log  # noqa: E402

    try:
        text = capture_boot_log(port, seconds)
    except SystemExit:
        return None
    match = MAC_PATTERN.search(text)
    return match.group(0).upper() if match else None


# --------------------------------------------------------------------- main --


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="End-to-end M5Stack onboarding: detect, flash, install apps, smoke test.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--apps", default=None,
                        help="app bundle to install, e.g. 'buddy' or a path; omit to skip")
    parser.add_argument("--variant", default=DEFAULT_VARIANT,
                        help=f"board variant (default {DEFAULT_VARIANT})")
    parser.add_argument("--port", default=None, help="serial port; omit to detect")
    parser.add_argument("--image", default=None, help="firmware image; omit to fetch")
    parser.add_argument("--stage", default=",".join(STAGES),
                        help="comma-separated subset of: " + ", ".join(STAGES))
    parser.add_argument("--skip-flash", action="store_true", help="do not flash")
    parser.add_argument("--no-coach", action="store_true",
                        help="do not prompt for the button press")
    parser.add_argument("--no-smoke", action="store_true", help="do not smoke test")
    parser.add_argument("--preflight-only", action="store_true",
                        help="check the dependencies and exit")
    parser.add_argument("--yes", action="store_true", help="never prompt")
    args = parser.parse_args(argv)

    selected = [name.strip().lower() for name in args.stage.split(",") if name.strip()]
    unknown = [name for name in selected if name not in STAGES]
    if unknown:
        raise SystemExit(f"error: unknown stage(s): {', '.join(unknown)}. "
                         f"Available: {', '.join(STAGES)}")

    if "flash" in selected and args.skip_flash:
        selected.remove("flash")
    if "smoke" in selected and args.no_smoke:
        selected.remove("smoke")

    banner("M5Stack onboarding")
    log(f"stages:  {', '.join(selected)}")
    log(f"variant: {args.variant}")
    non_interactive = args.yes or not sys.stdin.isatty()

    if args.preflight_only:
        return 0 if preflight(args.yes, non_interactive) else 1

    if "preflight" in selected and not preflight(args.yes, non_interactive):
        log("")
        log("FAILED at preflight. Nothing has touched the device.")
        return 1

    port = args.port
    if "detect" in selected and not port:
        log("")
        log("detecting the port")
        port = stage_detect(None, non_interactive)
        if not port:
            log("")
            log("FAILED at detect. Nothing has been written to the device.")
            return 1
    if not port:
        raise SystemExit("error: no --port and detect was not in the stage list")
    log("")
    log(f"port: {port}")

    if "flash" in selected:
        image = Path(args.image) if args.image else Path(
            os.environ.get("M5_CACHE_DIR")
            or os.path.join(
                os.environ.get("XDG_CACHE_HOME")
                or os.path.join(os.path.expanduser("~"), ".cache"),
                "m5-onboard",
            )
        ) / "M5Stack_Cardputer_Adv_Factory_2025-03-11.bin"
        if not stage_flash(port, image, args.variant, args.no_coach):
            log("")
            log("FAILED at flash. Re-running is safe: the mask ROM is in silicon and")
            log("survives a corrupted flash, so `m5-onboard go` again will recover.")
            return 1

    if "install" in selected and args.apps:
        if not stage_install(port, args.apps):
            log("")
            log(f"FAILED at install. The firmware is on the device; the apps are not. "
                f"Re-run with --stage install --port {port} --apps {args.apps}")
            return 1

    mac = capture_mac(port)
    if mac:
        log(f"MAC: {mac}")

    if "smoke" in selected and port:
        log("")
        stage_smoke(port)

    banner("DONE")
    log(f"port:    {port}")
    log(f"variant: {args.variant}")
    if mac:
        log(f"MAC:     {mac}")
    log("")
    log("The board is provisioned. Slide the power switch on the right edge to start it;")
    log("it boots into the launcher, which lists everything in /flash/apps/.")
    if args.apps:
        log("")
        log("Claude Buddy over BLE: in Claude Desktop, Help -> Troubleshooting -> Enable")
        log("Developer Tools once, then Developer menu -> Hardware Buddy -> Connect. The")
        log("link is local and works regardless of the WiFi state.")
        log("")
        log("To go back to UIFlow: from the REPL, os.remove('/flash/main.py') then")
        log("machine.reset(). The stock launcher takes over on the next boot.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
