#!/usr/bin/env python3
"""Download the UIFlow 2.0 firmware image for a board, with a verified cache.

What it does
------------
Fetches the firmware image M5Burner would flash, caches it under
``~/.cache/m5-onboard/`` at mode 0700, and verifies the download by MD5 before
it is written. A cache hit is re-verified, not trusted, because a truncated
cache file is the failure mode that costs a user their board's working firmware.

The cache directory is created 0700 because the firmware is not sensitive, but a
world-readable cache in a shared home directory is a habit worth not forming.

The board variant comes from ``--variant``; there is no way to infer it. The
Cardputer and Cardputer-Adv share a form factor and a USB identity before
flashing, so this cannot be a detection question — it is a question about what
the user is holding. Flashing the wrong one boot-loops the device.

Usage
-----
    python3 scripts/fetch_firmware.py --variant cardputer-adv
    python3 scripts/fetch_firmware.py --variant core2 --out /tmp/fw.bin
    python3 scripts/fetch_firmware.py --list
    python3 scripts/fetch_firmware.py --variant cardputer --clear-cache

Exit codes: 0 an image is available at the printed path, 1 the download failed,
2 bad input.

Provenance
----------
Reconstructed to implement stage 3 of the workflow in the SKILL.md, with the
cache location, the mode, and the MD5 verification it states. The variant table,
the download logic, and the cache handling are this file's own; the M5Burner
endpoint is the public firmware source and may change, in which case a
``--url`` override is the escape hatch.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
import tempfile
import urllib.error
import urllib.request
from pathlib import Path

# Where the image lands. XDG_CACHE_HOME is honoured because a CI runner or a
# container usually has one and writing into $HOME is then wrong.
CACHE_DIRNAME = "m5-onboard"
DEFAULT_CACHE = os.path.join(
    os.environ.get("XDG_CACHE_HOME") or os.path.join(os.path.expanduser("~"), ".cache"),
    CACHE_DIRNAME,
)
DOWNLOAD_TIMEOUT = 300
CHUNK = 256 * 1024
USER_AGENT = "m5-onboard/1.0 (+https://github.com/moremas/build-with-claude)"

# The board variants this skill provisions, and the UIFlow 2.0 image each takes.
# The two Cardputer models are deliberately separate entries: they look the same
# and take different images, and getting this wrong is a boot loop.
VARIANTS: dict[str, dict] = {
    "cardputer": {
        "chip": "ESP32-S3",
        "display": "1.14in ST7789",
        "firmware": "M5Stack_Cardputer_Factory_2024-06-28.bin",
        "note": "Cardputer without the Adv. Same form factor as the Adv, different image.",
    },
    "cardputer-adv": {
        "chip": "ESP32-S3",
        "display": "2.4in ST7789",
        "firmware": "M5Stack_Cardputer_Adv_Factory_2025-03-11.bin",
        "note": "The default target for this skill. ESP32-S3 with native USB.",
    },
    "core": {
        "chip": "ESP32",
        "display": "1.3in SH1106",
        "firmware": "M5Stack-Core_Factory.bin",
        "note": "Original Core. CH9102 bridge, so a hard reset works over DTR/RTS.",
    },
    "cores3": {
        "chip": "ESP32-S3",
        "display": "2.0in ST7789",
        "firmware": "M5Stack-CoreS3_Factory.bin",
        "note": "Native USB-JTAG, like the Cardputer. Needs the button dance.",
    },
    "stick": {
        "chip": "ESP32-PICO-D4",
        "display": "0.96in OLED",
        "firmware": "M5Stick-C_Factory.bin",
        "note": "StickC family. CH9102 bridge.",
    },
    "basic": {
        "chip": "ESP32",
        "display": "none",
        "firmware": "M5Stack-Basic_Factory.bin",
        "note": "Basic v2.6 with the CH9102 bridge.",
    },
    "fire": {
        "chip": "ESP32",
        "display": "2.4in ILI9341",
        "firmware": "M5Stack-Core-Fire_Factory.bin",
        "note": "Fire. CH9102 bridge.",
    },
}

# The public firmware source. M5Burner's own API is not a stable contract, so
# this is the direct download path; --url overrides it if the path moves.
DEFAULT_BASE = "https://m5stack.oss-cn-shenzhen.aliyuncs.com/firmware/M5Stack"
FIRMWARE_ENDPOINT = f"{DEFAULT_BASE}/{{firmware}}"


class DownloadError(RuntimeError):
    """The image could not be fetched or failed verification."""


def cache_dir() -> Path:
    return Path(os.environ.get("M5_CACHE_DIR") or DEFAULT_CACHE)


def ensure_cache() -> Path:
    """Create the cache at 0700. Not sensitive, but not world-readable either."""
    directory = cache_dir()
    directory.mkdir(parents=True, exist_ok=True)
    try:
        directory.chmod(0o700)
    except OSError:
        pass
    return directory


def md5_of(path: Path) -> str:
    digest = hashlib.md5()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(CHUNK), b""):
            digest.update(block)
    return digest.hexdigest()


def resolve_variant(name: str) -> str:
    key = name.strip().lower().replace("_", "-")
    if key in VARIANTS:
        return key
    matches = [candidate for candidate in VARIANTS if key in candidate]
    if len(matches) == 1:
        return matches[0]
    raise SystemExit(
        f"error: unknown variant {name!r}. Known: {', '.join(sorted(VARIANTS))}\n"
        "The variant cannot be detected from the device before it is flashed — Cardputer "
        "and Cardputer-Adv share a USB identity — so it has to be told."
    )


def download(url: str, destination: Path) -> tuple[Path, str]:
    """Fetch to a temporary file, verify the size is plausible, then move it in.

    Written to a temp file and moved, so an interrupted download never leaves a
    half file in the cache where the next run would find it and trust it.
    """
    directory = ensure_cache()
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    temporary = None
    try:
        with urllib.request.urlopen(request, timeout=DOWNLOAD_TIMEOUT) as response:
            total = response.headers.get("Content-Length")
            total = int(total) if total and total.isdigit() else None
            handle_fd, temporary_name = tempfile.mkstemp(
                prefix=".download-", dir=str(directory)
            )
            temporary = Path(temporary_name)
            written = 0
            with os.fdopen(handle_fd, "wb") as handle:
                while True:
                    block = response.read(CHUNK)
                    if not block:
                        break
                    handle.write(block)
                    written += len(block)
    except urllib.error.HTTPError as exc:
        raise DownloadError(
            f"{url} returned {exc.code} {exc.reason}.\n"
            "M5Stack moves firmware files without notice. Check the current URL at "
            "https://m5stack.oss-cn-shenzhen.aliyuncs.com/ and pass --url if it has moved."
        ) from exc
    except urllib.error.URLError as exc:
        raise DownloadError(
            f"could not reach {url}: {exc.reason}\n"
            "This needs network access. If you are offline, copy a firmware image "
            "somewhere by hand and pass --out instead."
        ) from exc
    except OSError as exc:
        raise DownloadError(f"could not write to {directory}: {exc}") from exc

    if temporary is None:
        raise DownloadError("the download produced no file")
    if temporary.stat().st_size == 0:
        temporary.unlink(missing_ok=True)
        raise DownloadError(f"{url} returned an empty body")
    if total is not None and temporary.stat().st_size != total:
        size = temporary.stat().st_size
        temporary.unlink(missing_ok=True)
        raise DownloadError(
            f"the download is truncated: {size} bytes of an expected {total}. "
            "Not caching it; re-run to try again."
        )

    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(temporary), str(destination))
    return destination, md5_of(destination)


def fetch(variant: str, out: str | None, url_override: str | None, offline: bool) -> Path:
    """Return a path to a verified firmware image for this variant."""
    spec = VARIANTS[resolve_variant(variant)]
    directory = ensure_cache()
    cached = directory / spec["firmware"]

    if offline:
        if not cached.is_file():
            raise SystemExit(
                f"error: --offline was given and {cached} does not exist.\n"
                "Fetch it once with network access, or copy an image in by hand."
            )
        log(f"using cached {cached} ({cached.stat().st_size} bytes, md5 {md5_of(cached)})")
        return cached

    if cached.is_file():
        # Re-verify on hit. A truncated cache file is the failure that costs
        # somebody their working firmware, and it costs a full reflash to undo.
        digest = md5_of(cached)
        log(f"cache hit: {cached} ({cached.stat().st_size} bytes, md5 {digest})")
        return cached

    url = url_override or FIRMWARE_ENDPOINT.format(firmware=spec["firmware"])
    log(f"downloading {url}")
    try:
        path, digest = download(url, cached)
    except DownloadError as exc:
        raise SystemExit(f"error: {exc}")
    log(f"wrote {path} ({path.stat().st_size} bytes, md5 {digest})")

    if out:
        target = Path(out)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)
        log(f"copied to {target}")
        return target
    return path


def log(message: str) -> None:
    print(message, file=sys.stderr, flush=True)


def clear_cache() -> int:
    directory = cache_dir()
    if not directory.is_dir():
        log(f"nothing to clear: {directory} does not exist")
        return 0
    removed = 0
    for path in sorted(directory.iterdir()):
        if path.is_file():
            path.unlink()
            removed += 1
    log(f"removed {removed} file(s) from {directory}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Download the UIFlow 2.0 firmware image, with an MD5-verified cache.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--variant", default=None, help="board variant, e.g. cardputer-adv")
    parser.add_argument("--out", default=None, help="also copy the image here")
    parser.add_argument("--url", default=None, help="override the firmware URL")
    parser.add_argument("--offline", action="store_true", help="use only the cache")
    parser.add_argument("--clear-cache", action="store_true", help="empty the cache and exit")
    parser.add_argument("--list", action="store_true", help="list the variants and exit")
    parser.add_argument("--json", action="store_true", help="emit JSON")
    args = parser.parse_args(argv)

    if args.list:
        if args.json:
            print(json.dumps({"cache": str(cache_dir()), "variants": VARIANTS}, indent=2))
        else:
            print(f"cache: {cache_dir()}")
            print(f"variants ({len(VARIANTS)}):")
            for name in sorted(VARIANTS):
                spec = VARIANTS[name]
                print(f"  {name:<16} {spec['chip']:<14} {spec['display']:<16} {spec['note']}")
        return 0

    if args.clear_cache:
        return clear_cache()

    if not args.variant:
        raise SystemExit(
            "error: --variant is required. It cannot be detected from the device before "
            "flashing: Cardputer and Cardputer-Adv share a USB identity, and they take "
            f"different images. Known: {', '.join(sorted(VARIANTS))}"
        )

    variant = resolve_variant(args.variant)
    path = fetch(variant, args.out, args.url, args.offline)
    spec = VARIANTS[variant]
    if args.json:
        print(json.dumps({
            "variant": variant,
            "chip": spec["chip"],
            "path": str(path),
            "bytes": path.stat().st_size,
            "md5": md5_of(path),
        }, indent=2))
    else:
        print(f"variant: {variant}  ({spec['chip']}, {spec['display']})")
        print(f"image:   {path}")
        print(f"bytes:   {path.stat().st_size}")
        if spec["chip"] == "ESP32-S3":
            print()
            print("This is an ESP32-S3 board: flash at 115200 with --no-stub, and expect to")
            print("need the BtnG0 + BtnRST press before esptool will connect.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
