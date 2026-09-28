#!/usr/bin/env python3
"""Shared serial and MicroPython REPL helpers.

Every script in this skill that needs a serial port goes through here, so the
three things that are easy to get wrong on a board are right in one place:

* **the vendor path** — ``scripts/vendor/`` is prepended to ``sys.path`` before
  the first third-party import, so the pinned pyserial resolves regardless of
  what the user has system-wide;
* **paste mode** — a multi-line block is bracketed with Ctrl-E and executed with
  Ctrl-D. Sending ``try:``/``except:`` line by line makes the REPL accumulate
  indentation forever and hang the upload;
* **reset** — DTR/RTS is the hard reset on a UART-bridge board and a silent
  no-op on a native-USB ESP32-S3, so ``repl_reset()`` goes through the REPL
  with ``machine.reset()`` instead and is the only correct call on ``usbmodem``
  ports.

Usage as a library:

    from mpy_repl import ensure_on_syspath, open_port, repl_paste, repl_reset

    ensure_on_syspath()
    port = open_port("/dev/cu.usbmodem1101")
    repl_paste(port, "print(1)")
    repl_reset(port)

Provenance
----------
Authored from this skill's `SKILL.md` and from the pyserial 3.5 API; no original
copy of this module was recovered. The board-specific constants below
(``CTRL_E``/``CTRL_D`` paste mode, ``DEFAULT_BAUD``, the DTR/RTS caveat) are the
MicroPython REPL protocol and the CH9102/ESP32-S3 behaviour, and are stated in
the skill; the function names and signatures are a reconstruction chosen to match
how the sibling scripts call it. Expect to adjust names, not behaviour.
"""

from __future__ import annotations

import os
import sys
import time

# Ctrl-E enters paste mode; Ctrl-D executes the buffered block.
CTRL_E = b"\x05"
CTRL_D = b"\x04"
# Ctrl-C interrupts a running block; Ctrl-A enters raw REPL.
CTRL_C = b"\x03"
CTRL_A = b"\x01"
CTRL_B = b"\x02"   # exit raw REPL
PROMPT = b">>> "

DEFAULT_BAUD = 115200
DEFAULT_TIMEOUT = 10.0
REPL_READY_TIMEOUT = 20.0
REPL_SETTLE = 0.35
# How long to wait for a port to reappear after a reset or a mode change.
PORT_RESCAN_TIMEOUT = 20.0


class ReplError(RuntimeError):
    """The REPL did not reach a usable state within the timeout."""


def vendor_path():
    """The absolute path of ``scripts/vendor/``."""
    here = os.path.dirname(os.path.realpath(__file__))
    return os.path.join(here, "vendor")


def ensure_on_syspath() -> str | None:
    """Prepend ``scripts/vendor/`` to ``sys.path``.

    Returns the directory that was added, or ``None`` when it is absent — which
    happens when someone downloaded a source-only zip or trimmed the repo. The
    caller can then fall back to a pip-installed pyserial, which is exactly the
    fallback path the skill documents.

    This must run *before* the first ``import serial``, because a module that is
    already imported is not re-resolved.
    """
    vendor = vendor_path()
    if not os.path.isdir(vendor):
        return None
    if vendor not in sys.path:
        sys.path.insert(0, vendor)
    return vendor


def have_vendored_serial() -> bool:
    """Whether the vendored pyserial is actually there and importable."""
    if ensure_on_syspath() is None:
        return False
    try:
        import serial  # noqa: F401,PLC0415
    except ImportError:
        return False
    return os.path.realpath(getattr(serial, "__file__", "")).startswith(
        os.path.realpath(vendor_path())
    )


def import_serial():
    """Import pyserial after the vendor path is set up, with a clear error.

    The two submodule imports are not optional and not cosmetic. ``import serial``
    does not bind ``serial.tools`` as an attribute, and ``serial.tools`` does not
    re-export ``list_ports``; without these two lines a caller reaching for
    ``serial.tools.list_ports()`` gets an AttributeError instead of a port list.
    """
    ensure_on_syspath()
    try:
        import serial  # noqa: PLC0415
        import serial.tools  # noqa: PLC0415,F401  binds the attribute
        import serial.tools.list_ports  # noqa: PLC0415,F401  defines the function
    except ImportError as exc:
        raise SystemExit(
            "error: pyserial is not importable, and the vendored copy under "
            f"{vendor_path()} is missing.\n"
            "Install it with:  python -m pip install --user pyserial\n"
            "The vendored copy keeps the tree Apache-2.0 clean; pyserial is BSD-3-Clause "
            "and is vendored for exactly that reason."
        ) from exc
    return serial


# ------------------------------------------------------------------ the port --


def open_port(port: str, baud: int = DEFAULT_BAUD, timeout: float = DEFAULT_TIMEOUT):
    """Open a serial port for the REPL, with a read timeout that cannot hang.

    The timeout matters more than usual here: a native-USB board that is waiting
    for the button dance will accept bytes and never answer, and a blocking read
    turns that into a hang rather than a prompt.
    """
    serial = import_serial()
    try:
        handle = serial.Serial(port=port, baudrate=baud, timeout=timeout, write_timeout=timeout)
    except Exception as exc:
        raise SystemExit(
            f"error: could not open {port}: {exc}\n"
            "On Linux, a permission error here means the user is not in the dialout group:\n"
            "  sudo usermod -aG dialout $USER   # then log out and back in\n"
            "That is a long-term fix. `sudo python3 scripts/onboard.py ...` works as a "
            "one-off but leaves the group problem in place."
        ) from exc
    return handle


def is_native_usb(port: str) -> bool:
    """Whether this port name is a native-USB ESP32-S3, by the names each OS uses.

    Naming is the only signal available before the chip has been flashed, and it
    is a good one: a USB-serial bridge gets a ``usbserial``/``ttyUSB``/``COM``
    name, while a native-USB device gets ``usbmodem``/``ttyACM``.
    """
    name = (port or "").lower()
    return any(marker in name for marker in ("usbmodem", "ttyacm", "usb jtag", "usb_jtag"))


def hard_reset(port: str) -> bool:
    """DTR/RTS hard reset. Correct on a UART bridge, a no-op on native USB.

    Returns whether the pulse was worth sending. On a native-USB board the pins
    are not wired to EN and GPIO0, so sending it looks like it worked and does
    nothing at all — which is worse than not sending it, because the caller
    then believes the board rebooted.
    """
    if is_native_usb(port):
        return False
    serial = import_serial()
    handle = open_port(port)
    try:
        handle.dtr = False
        handle.rts = True
        time.sleep(0.1)
        handle.rts = False
    finally:
        handle.close()
    return True


# ------------------------------------------------------------------ the repl --


def read_until_quiet(handle, quiet: float = 0.4, total: float = DEFAULT_TIMEOUT) -> bytes:
    """Read until the port goes quiet for ``quiet`` seconds, or ``total`` elapses."""
    deadline = time.monotonic() + total
    buffer = bytearray()
    last = time.monotonic()
    while time.monotonic() < deadline:
        waiting = handle.in_waiting if hasattr(handle, "in_waiting") else 0
        if waiting:
            buffer += handle.read(waiting)
            last = time.monotonic()
        elif time.monotonic() - last >= quiet:
            break
        else:
            time.sleep(0.02)
    return bytes(buffer)


def enter_raw_repl(handle, timeout: float = REPL_READY_TIMEOUT) -> None:
    """Interrupt anything running and get to a raw ``>>>`` prompt."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        handle.write(CTRL_C)
        handle.flush()
        handle.write(CTRL_A)
        handle.flush()
        time.sleep(0.2)
        if CTRL_B in read_until_quiet(handle, quiet=0.3, total=1.5):
            handle.write(CTRL_B)
            handle.flush()
        banner = read_until_quiet(handle, quiet=0.4, total=2.0)
        if PROMPT in banner or b">>" in banner:
            return
    raise ReplError(
        "the REPL did not reach a prompt. UIFlow 2.0 prints asyncio heap diagnostics while "
        "it waits at the pairing screen, and that output is normal — it is not a hang. If "
        "the device is stuck in a loop, power-cycle it and try again."
    )


def exit_raw_repl(handle) -> None:
    handle.write(CTRL_D)
    handle.flush()
    time.sleep(REPL_SETTLE)
    read_until_quiet(handle, quiet=0.3, total=1.0)


def repl_paste(handle, code: str, timeout: float = DEFAULT_TIMEOUT) -> bytes:
    """Send a block of code in paste mode and return whatever the REPL printed.

    Ctrl-E then the code then Ctrl-D. The trailing newline matters: without it
    the buffer is never handed to the interpreter and the call appears to
    succeed while doing nothing.
    """
    handle.write(CTRL_E)
    handle.flush()
    time.sleep(0.1)
    payload = code if code.endswith("\n") else code + "\n"
    handle.write(payload.encode("utf-8"))
    handle.flush()
    time.sleep(0.1)
    handle.write(CTRL_D)
    handle.flush()
    time.sleep(REPL_SETTLE)
    output = read_until_quiet(handle, quiet=0.5, total=timeout)
    if b"Traceback" in output:
        raise ReplError(
            "the REPL raised while executing the block.\n"
            + output.decode("utf-8", errors="replace")
        )
    return output


def repl_reset(handle) -> bool:
    """Reboot the board with ``machine.reset()`` through the REPL.

    This is the only reset that works on a native-USB ESP32-S3. DTR/RTS is not
    wired to EN on those boards, so the pulse is a silent no-op: the files you
    just uploaded are on disk and the old code keeps running, which looks
    exactly like a failed upload.
    """
    enter_raw_repl(handle)
    try:
        repl_paste(handle, "import machine; machine.reset()", timeout=3.0)
    except ReplError:
        # A reset tears the port down mid-response; a broken pipe here is the
        # expected outcome, not a failure.
        pass
    finally:
        exit_raw_repl(handle)
        try:
            handle.close()
        except Exception:
            pass
    return True


def capture_boot_log(port: str, seconds: float = 12.0, baud: int = DEFAULT_BAUD) -> str:
    """Reset the board and collect what it prints, as text.

    Useful after an install to confirm which ``main.py`` the launcher picked, and
    after a flash to see whether the firmware came up. A board that prints
    nothing has booted; a board that prints a heap loop has booted into UIFlow.
    """
    serial = import_serial()
    handle = serial.Serial(port=port, baudrate=baud, timeout=0.5)
    collected = bytearray()
    try:
        if not is_native_usb(port):
            handle.dtr = False
            handle.rts = True
            time.sleep(0.1)
            handle.rts = False
        deadline = time.monotonic() + seconds
        while time.monotonic() < deadline:
            waiting = handle.in_waiting if hasattr(handle, "in_waiting") else 0
            if waiting:
                collected += handle.read(waiting)
            else:
                time.sleep(0.05)
    finally:
        handle.close()
    return collected.decode("utf-8", errors="replace")


def list_serial_ports() -> list:
    """Every serial port pyserial can see, as ``ListPortInfo`` objects.

    Wrapped rather than called inline because the pyserial path is a trap:
    ``import serial`` does not bind ``serial.tools``, ``serial.tools`` does not
    re-export ``list_ports``, and ``serial.tools.list_ports`` is a *module*, not a
    function. The callable is ``serial.tools.list_ports.comports()``. Getting
    that wrong raises three different exceptions depending on which link of the
    chain you skip, so the chain lives here once.
    """
    serial = import_serial()
    return list(serial.tools.list_ports.comports())


def wait_for_port(port: str, timeout: float = PORT_RESCAN_TIMEOUT) -> str | None:
    """Poll until ``port`` exists again, for after a reset or a mode change.

    A native-USB board that entered download mode keeps the same port name; a
    board that just rebooted re-enumerates and macOS can hand back the same name
    a beat later. Returning ``None`` means the caller should tell the user to
    unplug and replug rather than spin.
    """
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        ports = [entry.device for entry in list_serial_ports()]
        if port in ports:
            return port
        time.sleep(0.5)
    return None


def main(argv: list[str] | None = None) -> int:
    """Small self-test: report what this module can see."""
    ensure_on_syspath()
    serial = import_serial()
    print(f"vendored pyserial: {have_vendored_serial()}")
    print(f"pyserial version: {getattr(serial, '__version__', 'unknown')}")
    print(f"vendor path: {vendor_path()}")
    print()
    print("ports:")
    found = False
    for entry in list_serial_ports():
        found = True
        kind = "native USB" if is_native_usb(entry.device) else "UART bridge"
        print(f"  {entry.device:<32} {kind:<12} {entry.description}")
    if not found:
        print("  none")
    return 0


if __name__ == "__main__":
    sys.exit(main())
