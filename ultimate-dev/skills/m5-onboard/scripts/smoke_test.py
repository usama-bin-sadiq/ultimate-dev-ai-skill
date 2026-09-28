#!/usr/bin/env python3
"""Check what the device can actually do: I2C bus, LCD, speaker, buttons.

What it does
------------
Runs four checks over the MicroPython REPL and reports each as pass, fail, or
unknown:

* **I2C scan** — every address that acknowledges. This is the first thing to run
  on a board nobody has touched, because it tells you what is actually wired.
* **LCD** — clear, fill, and a test pattern, then clear. A board with a dead
  panel passes everything else, so a check that only exercises the code path
  proves nothing about the display.
* **Speaker** — a short beep. A board with no buzzer raises, which is a
  pass-with-a-note, not a failure.
* **Buttons** — the GPIO the buttons are on, sampled over a couple of seconds so
  an unpressed board reports idle and a pressed one reports the pin pulled down.

Every check runs in paste mode and each one is isolated, so a failing check does
not stop the others. "What is on the bus and what can the device do" is a
question worth answering completely even when the first answer is no.

Usage
-----
    python3 scripts/smoke_test.py --port /dev/cu.usbmodem1101
    python3 scripts/smoke_test.py --port COM3 --checks i2c,lcd
    python3 scripts/smoke_test.py --port /dev/ttyUSB0 --json

Exit codes: 0 every selected check passed or was skipped, 1 a check failed,
2 bad input or the device did not answer.

Provenance
----------
Reconstructed to implement stage 6 of the workflow in the SKILL.md, which names
the four checks. The check bodies, the I2C address table, and the report format
are this file's own.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from mpy_repl import (  # noqa: E402
    ReplError,
    enter_raw_repl,
    exit_raw_repl,
    is_native_usb,
    open_port,
    repl_paste,
)

CHECKS = ("i2c", "lcd", "speaker", "buttons")

# Known I2C addresses, so a scan can say what it found rather than just listing
# hex. This is a convenience for reading the output, not an exhaustive table.
KNOWN_I2C = {
    0x3C: "SSD1306 / SH1106 OLED, most likely the display",
    0x3D: "SSD1306 OLED, alternate address",
    0x68: "MPU6050 / MPU9250 IMU",
    0x69: "MPU6050 IMU, alternate address",
    0x50: "24Cxx EEPROM",
    0x57: "MAX30102 or MAX30102-class heart-rate sensor",
    0x39: "TSL2561 / TSL2591 light sensor",
    0x76: "BMP280 / BME280 pressure and temperature sensor",
    0x77: "BMP280 / BME280, alternate address",
    0x19: "LSM6DS3 IMU",
    0x6B: "LSM6DS3 IMU, alternate address",
    0x4C: "ADS1115 ADC",
    0x21: "MCP23017 GPIO expander",
    0x23: "MCP23017 GPIO expander, alternate address",
}

# The buttons. On the Cardputer family these are on the back; on the Core
# families the A and B buttons are on the front. The pin numbers here are the
# ESP32 GPIO the firmware conventionally uses; a board that wires them
# differently will simply report idle, which the report says.
BUTTON_PINS = {"G0": 0, "BTN_A": 39, "BTN_B": 38}
LCD_PINS = {"sda": 8, "scl": 9}

PASS = "pass"
FAIL = "fail"
SKIP = "skip"
UNKNOWN = "unknown"


def log(message: str) -> None:
    print(message, file=sys.stderr, flush=True)


def _result(name: str, status: str, detail: str, **extra) -> dict:
    entry = {"check": name, "status": status, "detail": detail}
    entry.update(extra)
    return entry


# ------------------------------------------------------------------- checks --


def check_i2c(handle) -> dict:
    """Scan the bus and name whatever acknowledged."""
    program = """
import sys
_found = []
try:
    from machine import I2C, Pin
except Exception as _e:
    print('NO_MACHINE', _e)
    raise SystemExit
for _sda, _scl in ((8, 9), (8, 9), (18, 8), (21, 22)):
    try:
        _i2c = I2C(0, scl=Pin(_scl), sda=Pin(_sda), freq=400000)
        _addrs = _i2c.scan()
        if _addrs:
            _found.append((_sda, _scl, _addrs))
    except Exception:
        pass
if not _found:
    print('NO_BUS')
else:
    for _sda, _scl, _addrs in _found:
        print('BUS', _sda, _scl, ','.join(hex(a) for a in _addrs))
"""
    try:
        output = repl_paste(handle, program, timeout=25.0)
    except ReplError as exc:
        return _result("i2c", UNKNOWN, f"the scan did not complete: {exc}")

    text = output.decode("utf-8", errors="replace")
    if "NO_MACHINE" in text:
        return _result("i2c", UNKNOWN, "machine.I2C is not available; this is not a board")
    if "NO_BUS" in text:
        return _result(
            "i2c", FAIL,
            "no I2C bus answered on any of the common pin pairs. On a Cardputer the bus "
            "is SDA=8 SCL=9; if this board wires it differently, the scan will not find it "
            "and that is a wiring fact, not a fault.",
        )

    found: list[int] = []
    for line in text.splitlines():
        if line.startswith("BUS "):
            parts = line.split()
            found.extend(int(token, 16) for token in parts[3].split(","))
    found = sorted(set(found))
    named = [f"0x{a:02X} ({KNOWN_I2C[a]})" for a in found if a in KNOWN_I2C]
    unknown = [f"0x{a:02X}" for a in found if a not in KNOWN_I2C]
    detail = ", ".join(named + unknown) if (named or unknown) else "nothing"
    if not found:
        return _result("i2c", FAIL, "the bus came up but no address acknowledged")
    return _result(
        "i2c", PASS, detail, addresses=[f"0x{a:02X}" for a in found],
        recognised=len(named), unrecognised=unknown,
    )


def check_lcd(handle) -> dict:
    """Clear, fill, draw a pattern, clear again.

    The pattern matters: a board with a dead panel runs all of this without
    error, so a check that only clears the screen proves the code path and
    nothing about the display.
    """
    program = """
try:
    import lcd
except Exception as _e:
    print('NO_LCD_MODULE', _e)
    raise SystemExit
lcd.init()
lcd.clear()
lcd.fill(lcd.COLOR_WHITE)
lcd.circle(60, 30, 20, lcd.COLOR_RED)
lcd.rect(10, 10, 40, 40, lcd.COLOR_BLUE)
lcd.text('SMOKE TEST', 20, 70, lcd.COLOR_BLACK)
print('LCD_OK')
import time
time.sleep(0.3)
lcd.clear()
print('LCD_CLEARED')
"""
    try:
        output = repl_paste(handle, program, timeout=15.0)
    except ReplError as exc:
        return _result("lcd", FAIL, f"the display test raised: {exc}")

    text = output.decode("utf-8", errors="replace")
    if "NO_LCD_MODULE" in text:
        return _result(
            "lcd", SKIP,
            "the lcd module is not on the device. UIFlow 2.0 exposes the panel under its "
            "own module name, so this is expected on a stock firmware image rather than a "
            "fault.",
        )
    if "LCD_CLEARED" in text:
        return _result(
            "lcd", PASS,
            "cleared, filled, drew, and cleared again. You should have seen a white screen "
            "with a red circle, a blue square, and the words SMOKE TEST for about a third "
            "of a second.",
        )
    if "LCD_OK" in text:
        return _result(
            "lcd", UNKNOWN,
            "the panel was written but the final clear did not confirm. Check the screen: "
            "if it is blank, the panel is fine.",
        )
    return _result("lcd", FAIL, "the display test produced no confirmation")


def check_speaker(handle) -> dict:
    """A short beep. A board with no buzzer raises, which is not a failure."""
    program = """
try:
    from machine import Pin
    _p = None
    for _pin in (25, 26, 2, 15):
        try:
            _p = Pin(_pin, Pin.OUT)
            break
        except Exception:
            _p = None
    if _p is None:
        print('NO_SPEAKER_PIN')
    else:
        import time
        for _ in range(2):
            _p.value(1)
            time.sleep(0.08)
            _p.value(0)
            time.sleep(0.08)
        print('BEEPED', _pin)
except Exception as _e:
    print('SPEAKER_ERROR', _e)
"""
    try:
        output = repl_paste(handle, program, timeout=10.0)
    except ReplError as exc:
        return _result("speaker", UNKNOWN, f"the beep did not complete: {exc}")

    text = output.decode("utf-8", errors="replace")
    if "BEEPED" in text:
        pin = text.split("BEEPED", 1)[1].strip().split()[0]
        return _result(
            "speaker", PASS,
            f"drove GPIO {pin} twice. If you heard two clicks, the buzzer works.",
        )
    if "NO_SPEAKER_PIN" in text:
        return _result(
            "speaker", SKIP,
            "no candidate speaker pin accepted an output. The Cardputer has no buzzer, so "
            "this is expected on that family and is not a fault.",
        )
    if "SPEAKER_ERROR" in text:
        return _result("speaker", UNKNOWN, f"the device raised: {text.strip()[:200]}")
    return _result("speaker", UNKNOWN, "no confirmation either way")


def check_buttons(handle) -> dict:
    """Sample the button pins for a few seconds and report what they read.

    Sampled over time rather than once, because a single read tells you the idle
    level and nothing else. Press and hold a button while this runs and the
    report will say which pin moved.
    """
    program = """
from machine import Pin
_samples = {}
for _name, _num in (('G0', 0), ('BTN_A', 39), ('BTN_B', 38)):
    try:
        _samples[_name] = Pin(_num, Pin.IN, Pin.PULL_UP)
    except Exception:
        pass
if not _samples:
    print('NO_BUTTON_PINS')
else:
    import time
    _low = set()
    _end = time.time() + 3.0
    while time.time() < _end:
        for _name, _pin in _samples.items():
            if _pin.value() == 0:
                _low.add(_name)
        time.sleep(0.05)
    print('PINS', ','.join(sorted(_samples)))
    print('PRESSED', ','.join(sorted(_low)) if _low else '')
"""
    try:
        output = repl_paste(handle, program, timeout=12.0)
    except ReplError as exc:
        return _result("buttons", UNKNOWN, f"the button read did not complete: {exc}")

    text = output.decode("utf-8", errors="replace")
    if "NO_BUTTON_PINS" in text:
        return _result(
            "buttons", UNKNOWN,
            "none of the conventional button GPIOs could be configured. The pins are "
            "board-specific and a miss here says nothing about the buttons themselves.",
        )
    if "PRESSED" not in text:
        return _result("buttons", UNKNOWN, "the device did not report a reading")

    pins = ""
    pressed = ""
    for line in text.splitlines():
        if line.startswith("PINS "):
            pins = line[5:].strip()
        elif line.startswith("PRESSED "):
            pressed = line[9:].strip()
    return _result(
        "buttons", PASS,
        f"sampled {pins} for 3s. Buttons held down during the sample: "
        f"{pressed or 'none — all idle, which is correct with nothing pressed'}",
        pins=[pin for pin in pins.split(",") if pin],
        pressed=[pin for pin in pressed.split(",") if pin],
    )


CHECK_FUNCTIONS = {
    "i2c": check_i2c,
    "lcd": check_lcd,
    "speaker": check_speaker,
    "buttons": check_buttons,
}


# ------------------------------------------------------------------- report --


def render_text(port: str, native: bool, results: list[dict]) -> str:
    lines = [f"port: {port}  ({'native USB' if native else 'UART bridge'})", ""]
    for result in results:
        marker = {PASS: "pass", FAIL: "FAIL", SKIP: "skip", UNKNOWN: "?"}[result["status"]]
        lines.append(f"[{marker}] {result['check']}")
        for chunk in wrap(result["detail"], 74):
            lines.append(f"        {chunk}")
    lines += [
        "",
        "These checks say what the device responds to, not what it should do. A passing",
        "I2C scan does not tell you which device is at an address; a passing display test",
        "does not tell you the colours are right. Both need eyes on the hardware.",
    ]
    return "\n".join(lines) + "\n"


def wrap(text: str, width: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        if current and len(current) + 1 + len(word) > width:
            lines.append(current)
            current = word
        else:
            current = f"{current} {word}".strip()
    if current:
        lines.append(current)
    return lines or [""]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Check the I2C bus, LCD, speaker, and buttons on an M5Stack board.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--port", required=True, help="serial port from detect.py")
    parser.add_argument("--checks", default=",".join(CHECKS),
                        help=f"comma-separated subset of: {', '.join(CHECKS)}")
    parser.add_argument("--json", action="store_true", help="emit JSON")
    args = parser.parse_args(argv)

    selected = [name.strip().lower() for name in args.checks.split(",") if name.strip()]
    unknown = [name for name in selected if name not in CHECK_FUNCTIONS]
    if unknown:
        raise SystemExit(
            f"error: unknown check(s): {', '.join(unknown)}. "
            f"Available: {', '.join(CHECKS)}"
        )
    if not selected:
        raise SystemExit(f"error: --checks was empty. Available: {', '.join(CHECKS)}")

    native = is_native_usb(args.port)
    handle = open_port(args.port)
    results: list[dict] = []
    try:
        enter_raw_repl(handle)
        for name in selected:
            log(f"--- {name}")
            try:
                results.append(CHECK_FUNCTIONS[name](handle))
            except ReplError as exc:
                results.append(_result(name, UNKNOWN, str(exc)))
        exit_raw_repl(handle)
    except ReplError as exc:
        log("")
        log(f"error: the device did not reach a usable REPL: {exc}")
        return 2
    finally:
        try:
            handle.close()
        except Exception:
            pass

    if args.json:
        print(json.dumps({
            "port": args.port,
            "native_usb": native,
            "results": results,
        }, indent=2))
    else:
        print(render_text(args.port, native, results), end="")

    return 1 if any(r["status"] == FAIL for r in results) else 0


if __name__ == "__main__":
    sys.exit(main())
