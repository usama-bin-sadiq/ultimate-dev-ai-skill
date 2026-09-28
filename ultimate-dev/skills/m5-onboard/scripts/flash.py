#!/usr/bin/env python3
"""Flash a UIFlow image with esptool, at the baud rate the board actually survives.

What it does
------------
Wraps ``esptool write_flash`` with the two settings that matter and that are
easy to get wrong:

* **Baud rate.** 460800 on a CH9102 UART bridge. 921600 fails on ``erase_flash``
  with that bridge — not intermittently, reliably — because the bridge loses
  sync, so do not raise it.
* **Native USB.** 115200 with ``--no-stub`` on an ESP32-S3. Native USB's
  stub-baud-bump path throws ``Lost connection, retrying`` mid-erase; esptool
  recovers and the flash completes, but it looks like a failure. 115200 with no
  stub is slower per byte and faster end to end because it never fails.

It also handles the two failure modes that are not failures:

* ``Lost connection, retrying`` mid-erase is recoverable; esptool retries.
* The post-flash ``watchdog-reset`` teardown can fail *after* the flash
  succeeded. This script parses esptool's stdout and treats that specific
  pattern as non-fatal once ``Hash of data verified`` has appeared, because the
  hash line is the ground truth and the teardown is not.

On a native-USB board there is no software path into download mode. This script
coaches the user through the button press and waits; it does not try to automate
it, and it does not send a DTR/RTS reset that would do nothing and look like it
worked.

Usage
-----
    python3 scripts/flash.py --port /dev/cu.usbmodem1101 --image firmware.bin
    python3 scripts/flash.py --port /dev/ttyUSB0 --image fw.bin --baud 460800
    python3 scripts/flash.py --native-reset

Exit codes: 0 the image was written and verified, 1 the flash failed, 2 bad input.

Provenance
----------
Reconstructed to implement stage 4 of the workflow in the SKILL.md, with the baud
rates, the ``--no-stub`` rule, the button-dance coaching, and the
``Hash of data verified`` handling it states. The argument assembly, the output
parsing, and the retry logic are this file's own.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from mpy_repl import ensure_on_syspath, is_native_usb, open_port  # noqa: E402

ESPTOOL_TIMEOUT = 900
# The bridge loses sync at 921600 on erase_flash. This is the documented ceiling.
UART_BRIDGE_BAUD = 460800
NATIVE_USB_BAUD = 115200
DOWNLOAD_MODE_PROMPT = (
    "Enter download mode:\n"
    "  1. press and HOLD the G0 button (on the BACK of the Cardputer)\n"
    "  2. while still holding G0, briefly press and release RST\n"
    "  3. keep holding G0 for about one more second, then release it\n"
    "  4. the screen should go fully dark — that is download mode\n"
    "If the device reboots into UIFlow instead of going dark, G0 was released too "
    "early. Hold it longer and try again."
)
DOWNLOAD_WAIT_SECONDS = 180

# The ground truth that the flash succeeded. Nothing else in the output is
# reliable enough to decide on.
HASH_VERIFIED = re.compile(r"hash of data verified", re.IGNORECASE)
LOST_CONNECTION = re.compile(r"lost connection", re.IGNORECASE)
WATCHDOG = re.compile(r"watchdog|hard resetting|failed to connect", re.IGNORECASE)
WROTE_SIZE = re.compile(r"compressed\s+(\d+)\s+bytes", re.IGNORECASE)


class FlashError(RuntimeError):
    """The image was not written and verified."""


def log(message: str) -> None:
    print(message, file=sys.stderr, flush=True)


def find_esptool() -> list[str]:
    """``[sys.executable, "-m", "esptool"]`` when importable, else the binary.

    The module form is preferred because on Windows a ``pip install --user``
    lands outside PATH, and ``esptool not found`` there is a PATH problem, not
    a missing package.
    """
    import importlib.util  # noqa: PLC0415
    import shutil  # noqa: PLC0415

    if importlib.util.find_spec("esptool") is not None:
        return [sys.executable, "-m", "esptool"]
    binary = shutil.which("esptool")
    if binary:
        return [binary]
    raise SystemExit(
        "error: esptool is not installed.\n"
        "Install it with:  python -m pip install --user esptool\n"
        "esptool is GPLv2+, which is why it is not vendored into this tree."
    )


def coaching(native: bool) -> None:
    """Print the physical steps. The only way into download mode on native USB."""
    if native:
        log("")
        log("=" * 70)
        log(DOWNLOAD_MODE_PROMPT)
        log("=" * 70)
        log("")
        log("There is no software path here. The chip has no DTR/RTS bridge, so neither")
        log("esptool's --before default_reset nor pyserial's DTR/RTS will do anything —")
        log("the pins are not wired to EN and GPIO0.")
        log("")
        try:
            input("Press Enter once the screen is fully dark (Ctrl-C to abort): ")
        except (EOFError, KeyboardInterrupt):
            raise SystemExit("aborted before flashing")
    else:
        log("Pulsing DTR/RTS to enter download mode.")


def run_esptool(prefix: list[str], argv: list[str], native: bool, image_size: int) -> dict:
    """Run esptool once, streaming its output, and classify the result.

    Streams rather than capturing: esptool can sit silent through a multi-minute
    erase, and a caller watching a buffer sees nothing and assumes a hang.
    """
    command = [*prefix, *argv]
    log(f"$ {' '.join(command)}")

    recovered = 0
    saw_hash = False
    teardown_failed = False
    lines: list[str] = []

    try:
        process = subprocess.Popen(  # noqa: S603 - fixed argv, no shell
            command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=False
        )
    except OSError as exc:
        raise SystemExit(f"error: could not run esptool: {exc}")

    assert process.stdout is not None
    started = time.monotonic()
    for raw in process.stdout:
        text = raw.decode("utf-8", errors="replace").rstrip()
        lines.append(text)
        if text.strip():
            log(text)

        if HASH_VERIFIED.search(text):
            saw_hash = True
        if LOST_CONNECTION.search(text):
            recovered += 1
            log("")
            log(f"note: 'Lost connection, retrying' ({recovered} so far). This is the")
            log("native-USB stub path talking itself down; esptool retries and the flash")
            log("completes. It looks like a failure and is not.")
        if saw_hash and WATCHDOG.search(text):
            # The flash is verified; this is the teardown. See the module header.
            teardown_failed = True

        if time.monotonic() - started > ESPTOOL_TIMEOUT:
            process.kill()
            raise FlashError(
                f"esptool ran for more than {ESPTOOL_TIMEOUT}s and was stopped. "
                + coaching_text(native)
            )

    returncode = process.wait()

    if saw_hash:
        log("")
        log("Hash of data verified.")
        if teardown_failed:
            log("The post-flash teardown reported an error, but the image was written and")
            log("verified, so this is not a failure. If the device does not come back, run")
            log("native_reset(), then a manual RST press.")
        return {
            "ok": True,
            "verified": True,
            "recovered_connections": recovered,
            "teardown_failed": teardown_failed,
            "returncode": returncode,
            "output": lines,
        }

    tail = "\n".join(lines[-20:])
    raise FlashError(
        "the flash did not complete: no 'Hash of data verified' in esptool's output.\n"
        f"esptool exited with {returncode}.\n"
        f"{coaching_text(native)}\n"
        f"--- last output ---\n{tail}"
    )


def coaching_text(native: bool) -> str:
    if native:
        return (
            "\nIf the board is a native-USB ESP32-S3 it must be in download mode first:\n"
            + DOWNLOAD_MODE_PROMPT
        )
    return (
        "\nCheck: the cable carries data, the port is right, and on Linux you are in the "
        "dialout group (sudo usermod -aG dialout $USER, then log out and back in)."
    )


def native_reset(port: str) -> bool:
    """Reset a native-USB board through the REPL, since DTR/RTS is a no-op there.

    Returns whether the board answered. A board that just came out of the
    bootloader has no running MicroPython to talk to, so a failure here is
    expected and is reported as a prompt to press RST rather than as an error.
    """
    if not is_native_usb(port):
        log("This is a UART-bridge board; a DTR/RTS hard reset is the right tool.")
        try:
            handle = open_port(port)
            handle.dtr = False
            handle.rts = True
            time.sleep(0.1)
            handle.rts = False
            handle.close()
            return True
        except SystemExit as exc:
            log(f"reset failed: {exc}")
            return False

    log("Resetting through the REPL (DTR/RTS is a no-op on native USB).")
    try:
        from mpy_repl import repl_reset  # noqa: PLC0415

        handle = open_port(port)
        return repl_reset(handle)
    except SystemExit as exc:
        log(f"the board did not answer: {exc}")
        return False


def wait_for_port(port: str, timeout: float = 30.0) -> bool:
    """Wait for the port to come back after a flash."""
    ensure_on_syspath()
    try:
        import serial.tools.list_ports as list_ports  # noqa: PLC0415
    except ImportError:
        return False
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if any(entry.device == port for entry in list_ports.comports()):
            return True
        time.sleep(0.5)
    return False


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Flash a UIFlow image with esptool, at the baud the board survives.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--port", default=None, help="serial port of the board")
    parser.add_argument("--image", default=None, help="firmware .bin to write")
    parser.add_argument("--baud", type=int, default=None,
                        help=f"override the baud rate (UART bridge {UART_BRIDGE_BAUD}, "
                             f"native USB {NATIVE_USB_BAUD})")
    parser.add_argument("--offset", default="0x0", help="flash offset (default 0x0)")
    parser.add_argument("--native-reset", action="store_true",
                        help="reset through the REPL instead of DTR/RTS")
    parser.add_argument("--no-coach", action="store_true",
                        help="do not prompt for the button press (you know what to do)")
    parser.add_argument("--skip-verify", action="store_true",
                        help="do not require 'Hash of data verified' in the output")
    args = parser.parse_args(argv)

    if args.native_reset:
        if not args.port:
            raise SystemExit("error: --native-reset needs --port")
        return 0 if native_reset(args.port) else 1

    if not args.port or not args.image:
        raise SystemExit("error: --port and --image are both required")

    image = Path(args.image)
    if not image.is_file():
        raise SystemExit(f"error: firmware image not found: {args.image}")
    if image.stat().st_size == 0:
        raise SystemExit(f"error: {args.image} is empty")

    native = is_native_usb(args.port)
    baud = args.baud or (NATIVE_USB_BAUD if native else UART_BRIDGE_BAUD)

    log(f"port:   {args.port}  ({'native USB' if native else 'UART bridge'})")
    log(f"image:  {image}  ({image.stat().st_size} bytes)")
    log(f"baud:   {baud}" + ("  (--no-stub: the stub baud bump loses the connection)"
                             if native else "  (do not raise this: 921600 fails on the bridge)"))
    log("")

    prefix = find_esptool()
    argv_esptool = ["--port", args.port, "--baud", str(baud)]
    if native:
        argv_esptool.append("--no-stub")
    if not args.no_coach:
        coaching(native)
    argv_esptool += ["write_flash", args.offset, str(image)]

    try:
        result = run_esptool(prefix, argv_esptool, native, image.stat().st_size)
    except FlashError as exc:
        log("")
        log(f"FAILED: {exc}")
        return 1

    if args.skip_verify:
        log("")
        log("note: --skip-verify was given, so the hash line was not required. The flash")
        log("may not have completed.")
        return 0

    log("")
    if wait_for_port(args.port, timeout=20.0):
        log(f"{args.port} came back.")
    else:
        log(f"{args.port} has not reappeared yet. This is normal for a few seconds after a")
        log("reset. If it never comes back, the device needs a manual RST press.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
