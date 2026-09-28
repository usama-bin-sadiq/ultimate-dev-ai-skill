#!/usr/bin/env python3
"""Enumerate serial ports and confirm which ones are ESP32 boards.

What it does
------------
Lists every serial port, classifies it, and probes the likely ones with esptool
to read the chip description. Prints the port to pass to every other script in
this skill.

The classification is by USB vendor and by port name:

* **CH9102** (WCH, vendor ``0x1A86``) — a USB-UART bridge. The M5Stack Basic,
  Fire, Core2, and StickC.
* **CP210x** (Silicon Labs, ``0x10C4``) — also a bridge, on some clones.
* **FTDI** (``0x0403``) — also a bridge.
* **ESP32-S3 native USB-JTAG** (``0x303A``) — not a bridge at all. The device
  enumerates as a composite USB-CDC device and has no DTR/RTS lines, which is
  why it needs the physical button dance to enter download mode. Cardputer,
  Cardputer-Adv, and CoreS3.

Bluetooth-serial ports are filtered out: they are not wired to the chip and
probing them is slow and pointless.

When more than one candidate survives, this asks rather than guessing. A wrong
guess here means flashing the wrong board, and the only recovery is a physical
button press.

Usage
-----
    python3 scripts/detect.py
    python3 scripts/detect.py --json
    python3 scripts/detect.py --port /dev/cu.usbmodem1101 --probe
    python3 scripts/detect.py --no-probe

Exit codes: 0 one port was selected, 1 none found, 2 bad input.

Provenance
----------
Reconstructed to implement stage 1 of the workflow in the SKILL.md, with the
vendor IDs, the port-name forms, and the "do not guess" rule it states. The
classification, the esptool probe, and the selection prompt are this file's own.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from mpy_repl import ensure_on_syspath, is_native_usb, vendor_path  # noqa: E402

# USB vendor IDs that mean "this is a serial device on an M5Stack or an ESP32".
BRIDGE_VENDORS = {
    0x1A86: ("CH9102", "WCH USB-UART bridge"),
    0x10C4: ("CP210x", "Silicon Labs USB-UART bridge"),
    0x0403: ("FTDI", "FTDI USB-UART bridge"),
    0x10C4 & 0xFFFF: ("CP210x", "Silicon Labs USB-UART bridge"),
}
NATIVE_USB_VENDORS = {
    0x303A: ("ESP32-S3", "Espressif native USB-JTAG"),
}

# Port-name fragments that mean native USB, per OS.
NATIVE_NAME_MARKERS = ("usbmodem", "ttyacm", "usb jtag", "usb_jtag")
# Fragments that mean the port is not wired to the chip.
EXCLUDE_NAME_MARKERS = ("bluetooth", "bt-", "debug ", "wlan", "irda")

ESPTOOL_TIMEOUT = 25
# esptool is GPLv2+ and deliberately not vendored, so it may or may not be
# present. Its absence is not an error: the port names and vendor IDs already
# answer the question this script is usually asked.
ESPTOOL_MODULE = "esptool"


class Candidate:
    """One port that could be a board."""

    def __init__(self, device: str, description: str, hwid: str, vid: int | None,
                 pid: int | None) -> None:
        self.device = device
        self.description = description
        self.hwid = hwid
        self.vid = vid
        self.pid = pid
        self.kind = "unknown"
        self.chip = None
        self.flash_bytes = None
        self.probe_error = None

    @property
    def native_usb(self) -> bool:
        return self.kind == "native_usb"

    def to_dict(self) -> dict:
        return {
            "port": self.device,
            "description": self.description,
            "hwid": self.hwid,
            "kind": self.kind,
            "native_usb": self.native_usb,
            "chip": self.chip,
            "flash_bytes": self.flash_bytes,
            "probe_error": self.probe_error,
            "requires_button_dance": self.native_usb,
        }


def _parse_vid_pid(hwid: str) -> tuple[int | None, int | None]:
    """Pull VID and PID out of a pyserial hwid string, on any OS."""
    lowered = (hwid or "").lower()
    vid = pid = None
    for key, name in (("vid", "vid"), ("pid", "pid")):
        marker = f"{name}=0x"
        index = lowered.find(marker)
        if index != -1:
            digits = lowered[index + len(marker):]
            end = 0
            while end < len(digits) and digits[end] in "0123456789abcdef":
                end += 1
            try:
                value = int(digits[:end], 16)
            except ValueError:
                continue
            if key == "vid":
                vid = value
            else:
                pid = value
    return vid, pid


def classify(candidate: Candidate) -> Candidate:
    """Decide whether a port is a native-USB ESP32-S3 or a USB-UART bridge."""
    name = candidate.device.lower()
    description = (candidate.description or "").lower()
    hwid = (candidate.hwid or "").lower()

    if any(marker in name for marker in EXCLUDE_NAME_MARKERS):
        candidate.kind = "excluded"
        return candidate
    if any(marker in description for marker in EXCLUDE_NAME_MARKERS):
        candidate.kind = "excluded"
        return candidate
    if "bluetooth" in hwid or "pnp" in hwid and "bluetooth" in hwid:
        candidate.kind = "excluded"
        return candidate

    if candidate.vid in NATIVE_USB_VENDORS:
        candidate.kind = "native_usb"
        return candidate
    if candidate.vid in BRIDGE_VENDORS:
        candidate.kind = "uart_bridge"
        return candidate

    if any(marker in name for marker in NATIVE_NAME_MARKERS):
        candidate.kind = "native_usb"
        return candidate

    # No vendor ID we recognise. If it looks like a serial port at all, keep it
    # as a weak candidate and let the probe decide.
    if name.startswith("/dev/tty") or name.upper().startswith("COM"):
        candidate.kind = "unclassified"
        return candidate

    candidate.kind = "excluded"
    return candidate


def list_ports() -> list[Candidate]:
    """Every port the OS reports, classified."""
    ensure_on_syspath()
    try:
        import serial.tools.list_ports as list_ports_module  # noqa: PLC0415
    except ImportError as exc:
        raise SystemExit(
            "error: pyserial is not importable, and the vendored copy is missing.\n"
            "Install it with:  python -m pip install --user pyserial"
        ) from exc

    candidates: list[Candidate] = []
    for entry in list_ports_module.comports():
        vid, pid = _parse_vid_pid(getattr(entry, "hwid", "") or "")
        candidate = Candidate(entry.device, entry.description or "", entry.hwid or "", vid, pid)
        candidates.append(classify(candidate))
    return candidates


def find_esptool() -> tuple[list[str] | None, str]:
    """The argv prefix for esptool, and where it was found.

    The module form is preferred: ``[sys.executable, "-m", "esptool"]`` always
    works regardless of PATH, which on Windows is frequently wrong after a
    ``pip install --user``.
    """
    import importlib.util  # noqa: PLC0415

    if importlib.util.find_spec(ESPTOOL_MODULE) is not None:
        return [sys.executable, "-m", ESPTOOL_MODULE], "importable module"
    binary = _which(ESPTOOL_MODULE)
    if binary:
        return [binary], binary
    return None, "not found"


def _which(name: str) -> str | None:
    import shutil  # noqa: PLC0415

    found = shutil.which(name)
    if found:
        return found
    # Windows: pip --user lands here, and it is often not on PATH.
    home = os.path.expanduser("~")
    candidates = [os.path.join(home, ".local", "bin", name)]
    appdata = os.environ.get("APPDATA")
    if appdata:
        for version in range(8, 16):
            candidates.append(
                os.path.join(appdata, "Python", f"Python3{version}", "Scripts", name + ".exe")
            )
    library = os.path.join(home, "Library", "Python")
    if os.path.isdir(library):
        for version in sorted(os.listdir(library)):
            candidates.append(
                os.path.join(library, version, "bin", name)
            )
    for candidate in candidates:
        if os.path.isfile(candidate):
            return candidate
    return None


def probe(candidate: Candidate, prefix: list[str]) -> Candidate:
    """Ask esptool what chip is on the other end.

    This is a read, not a write: ``chip_id`` puts the chip in reset and reads
    back its identification, and nothing is erased. On a board that needs the
    button dance to reach its ROM bootloader it will simply time out, which is
    why the probe is optional and why the answer is allowed to be unknown.
    """
    try:
        completed = subprocess.run(  # noqa: S603 - fixed argv prefix, no shell
            [*prefix, "--port", candidate.device, "chip_id"],
            capture_output=True,
            timeout=ESPTOOL_TIMEOUT,
            shell=False,
            check=False,
        )
    except subprocess.TimeoutExpired:
        candidate.probe_error = (
            "timed out. On a native-USB board that usually means it needs the "
            "BtnG0 + BtnRST press to enter download mode."
        )
        return candidate
    except OSError as exc:
        candidate.probe_error = f"could not run esptool: {exc}"
        return candidate

    output = (completed.stdout or b"").decode("utf-8", errors="replace")
    output += (completed.stderr or b"").decode("utf-8", errors="replace")
    lowered = output.lower()

    for label in ("esp32-s3", "esp32-c3", "esp32-c6", "esp32-h2", "esp32", "esp8266"):
        if label in lowered:
            candidate.chip = label.upper()
            break
    if "detecting chip type" in lowered and candidate.chip is None:
        candidate.chip = "ESP32 (specific variant unreported)"

    if "flash size" in lowered or "flash_id" in lowered:
        import re  # noqa: PLC0415

        match = re.search(r"flash size:\s*([0-9a-fx]+)", lowered)
        if match:
            candidate.flash_bytes = match.group(1)

    if completed.returncode != 0 and candidate.chip is None:
        candidate.probe_error = (
            "esptool could not identify the chip. A board that has never been "
            "flashed, or that needs the button dance, reports nothing here."
        )
    return candidate


def choose(candidates: list[Candidate], interactive: bool) -> Candidate:
    """Pick the board. Ask when there is a real choice; never guess."""
    viable = [
        c for c in candidates
        if c.kind in {"native_usb", "uart_bridge", "unclassified"}
    ]
    if not viable:
        raise SystemExit(
            "No USB serial port found.\n\n"
            "Check, in order:\n"
            "  1. the device is plugged in and powered\n"
            "  2. the cable carries data — many USB-C cables are charge-only, and this is\n"
            "     the single most common reason nothing appears\n"
            "  3. on Windows, the CH9102 driver is installed (WCH publishes no winget\n"
            "     manifest, so it is a manual install; native-USB boards need no driver)\n"
            "  4. on Linux, you are in the dialout group:\n"
            "       sudo usermod -aG dialout $USER   # then log out and back in"
        )

    if len(viable) == 1:
        return viable[0]

    if not interactive or not sys.stdin.isatty():
        listing = "\n".join(
            f"  [{index}] {c.device}  ({c.kind}{', ' + c.chip if c.chip else ''})"
            for index, c in enumerate(viable, start=1)
        )
        raise SystemExit(
            f"Multiple candidate ports found and this is not an interactive session:\n"
            f"{listing}\n\n"
            "Pass the one you want with --port. Guessing here means flashing the wrong "
            "board, and the only recovery is a physical button press."
        )

    print("\nMultiple candidate ports found:")
    for index, candidate in enumerate(viable, start=1):
        detail = candidate.chip or candidate.kind
        note = ""
        if candidate.native_usb:
            note = "  (native USB: needs the BtnG0 + BtnRST press to flash)"
        print(f"  [{index}] {candidate.device}  —  {detail}{note}")

    while True:
        answer = input("\nWhich one is the device? (number, or r to rescan): ").strip()
        if answer.lower() == "r":
            return choose(list_ports(), interactive)
        if answer.isdigit() and 1 <= int(answer) <= len(viable):
            return viable[int(answer) - 1]
        print("Enter a number from the list, or 'r' to rescan.")


def render(candidates: list[Candidate], chosen: Candidate | None) -> str:
    lines = ["serial ports", ""]
    if not candidates:
        lines.append("  none found")
        return "\n".join(lines) + "\n"

    for candidate in candidates:
        marker = ""
        if chosen is not None and candidate.device == chosen.device:
            marker = "  <- selected"
        label = {
            "native_usb": "native USB-JTAG (ESP32-S3)",
            "uart_bridge": "USB-UART bridge",
            "unclassified": "unclassified serial port",
            "excluded": "excluded (not the chip)",
        }.get(candidate.kind, candidate.kind)
        lines.append(f"  {candidate.device:<34} {label}{marker}")
        if candidate.description and candidate.description != "n/a":
            lines.append(f"      {candidate.description}")
        if candidate.chip:
            lines.append(f"      chip: {candidate.chip}")
        if candidate.probe_error:
            lines.append(f"      probe: {candidate.probe_error}")

    if chosen is not None:
        lines += [
            "",
            f"selected: {chosen.device}",
            f"pass this to every other script:  --port {chosen.device}",
        ]
        if chosen.native_usb:
            lines += [
                "",
                "This is a native-USB board. It has no DTR/RTS bridge, so there is NO software",
                "way into download mode. Before flashing you will need to:",
                "  1. press and HOLD BtnG0 (on the BACK of the Cardputer)",
                "  2. while still holding it, briefly press and release BtnRST",
                "  3. keep holding BtnG0 for about a second more, then release it",
                "  4. the screen should go fully dark — that is download mode",
                "If it reboots into UIFlow instead, BtnG0 was released too early.",
            ]
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Enumerate serial ports and confirm which ones are ESP32 boards.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--port", default=None, help="use this port instead of choosing one")
    parser.add_argument("--probe", action="store_true", help="ask esptool to identify the chip")
    parser.add_argument("--no-probe", action="store_true", help="never run esptool")
    parser.add_argument("--json", action="store_true", help="emit JSON")
    parser.add_argument("--yes", action="store_true", help="never prompt; fail if ambiguous")
    args = parser.parse_args(argv)

    candidates = list_ports()

    prefix = None
    if args.probe or not args.no_probe:
        prefix, location = find_esptool()
        if prefix is None:
            if args.probe:
                raise SystemExit(
                    f"error: {ESPTOOL_MODULE} is not installed.\n"
                    "Install it with:  python -m pip install --user esptool\n"
                    "esptool is GPLv2+, which is why it is not vendored into this tree."
                )
            print(
                f"note: {ESPTOOL_MODULE} is not installed, so the chip will not be identified. "
                "Install it with:  python -m pip install --user esptool",
                file=sys.stderr,
            )

    if prefix is not None and not args.no_probe:
        wanted = args.port
        for candidate in candidates:
            if wanted and candidate.device != wanted:
                continue
            if candidate.kind == "excluded":
                continue
            probe(candidate, prefix)
    else:
        # Without a probe, only probe-looking candidates were classified above.
        pass

    if args.port:
        chosen = next(
            (c for c in candidates if c.device == args.port), None
        )
        if chosen is None:
            raise SystemExit(
                f"error: {args.port} was not found among the serial ports. "
                f"Ran with esptool at: {prefix[0] if prefix else 'n/a'}"
            )
        if chosen.kind == "excluded":
            raise SystemExit(
                f"error: {args.port} looks like a non-serial port ({chosen.description}). "
                "Pass the port the board is on."
            )
    else:
        chosen = choose(candidates, interactive=not args.yes)

    if args.json:
        print(json.dumps(
            {
                "esptool": location if prefix else None,
                "ports": [c.to_dict() for c in candidates],
                "selected": chosen.to_dict(),
            },
            indent=2,
        ))
    else:
        print(render(candidates, chosen), end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
