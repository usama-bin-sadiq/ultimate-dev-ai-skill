#!/usr/bin/env python3
"""Generate logo images with Gemini, Atlas Cloud, or MuAPI.

What it does
------------
Assembles a prompt from the logo catalogue (see ``core.py``), sends it to the
selected provider, and writes the returned image to ``--output``. The output logo
is always requested on a white background, so its contrast can actually be
checked and the file can be reused on any ground.

Providers
---------
``gemini``  default. ``google-genai`` with ``gemini-2.5-flash-image`` (or ``--model pro``
            for ``gemini-3-pro-image-preview``).
``atlas``   Atlas Cloud, openai-compatible image endpoint.
``muapi``   MuAPI, asynchronous model endpoint plus the prediction-result API.
            ``--muapi-model`` selects ``nano-banana`` or ``nano-banana-pro``; Pro
            also accepts ``--resolution``, and leaves it at the provider default
            when not given.

Usage
-----
    python3 scripts/logo/generate.py --brand "TechFlow" --style minimalist --industry tech
    python3 scripts/logo/generate.py --prompt "coffee shop vintage badge" --style vintage
    python3 scripts/logo/generate.py --brand "TechFlow" --provider atlas
    python3 scripts/logo/generate.py --brand "TechFlow" --provider muapi
    python3 scripts/logo/generate.py --brand "TechFlow" --provider muapi \\
        --muapi-model nano-banana-pro
    python3 scripts/logo/generate.py --brand "TechFlow" --dry-run

Exit codes: 0 image written, 1 generation failed, 2 bad input or missing key.

Provenance
----------
Reconstructed to match the invocations in this skill's SKILL.md and the provider
setup in ``references/logo-design.md``. The catalogue and prompt assembly are in
``core.py``; the HTTP call shapes follow the providers' documented request and
response schemas, and the response handling is this file's own.
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from core import build_prompt, resolve, search_domain  # noqa: E402

PROVIDERS = ("gemini", "atlas", "muapi")
MODELS = {"flash": "gemini-2.5-flash-image", "pro": "gemini-3-pro-image-preview"}
MUAPI_MODELS = {
    "nano-banana": "nano-banana",
    "nano-banana-pro": "nano-banana-pro",
}
ATLAS_ENDPOINT = "https://atlascloud.ai/v1/images/generations"
ATLAS_MODEL = "atlas-image"
GEMINI_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models"
MUAPI_ENDPOINT = "https://api.muapi.ai/api/v1"
REQUEST_TIMEOUT = 180
MUAPI_POLL_SECONDS = 4
MUAPI_MAX_POLLS = 60
# Every logo leaves this process on white. A logo on a coloured ground cannot be
# checked for contrast and cannot be dropped onto another ground later.
BACKGROUND_INSTRUCTION = "pure white background, no shadow, no texture, centred with a generous margin"


def log(message: str) -> None:
    print(message, file=sys.stderr, flush=True)


def _post(url: str, payload: dict, headers: dict, timeout: int = REQUEST_TIMEOUT) -> dict:
    """POST JSON and return the parsed body, with the status on any failure."""
    body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(url, data=body, method="POST")
    request.add_header("Content-Type", "application/json")
    for name, value in headers.items():
        request.add_header(name, value)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:400]
        raise SystemExit(f"error: {url} returned {exc.code}: {detail}")
    except urllib.error.URLError as exc:
        raise SystemExit(f"error: cannot reach {url}: {exc.reason}")
    except json.JSONDecodeError as exc:
        raise SystemExit(f"error: {url} did not return JSON: {exc}")


def _write_image(data: bytes, output: Path) -> Path:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(data)
    return output


def _write_from_base64(payload: str, output: Path) -> Path:
    try:
        return _write_image(base64.b64decode(payload), output)
    except (ValueError, TypeError) as exc:
        raise SystemExit(f"error: provider returned base64 data that will not decode: {exc}")


def generate_gemini(prompt: str, output: Path, model: str, api_key: str) -> Path:
    """google-genai, which returns inline bytes for image models."""
    try:
        from google import genai
        from google.genai import types
    except ImportError:
        raise SystemExit(
            "error: google-genai is not installed. Run `pip install google-genai pillow`."
        )
    client = genai.Client(api_key=api_key)
    try:
        response = client.models.generate_content(
            model=model,
            contents=prompt,
            config=types.GenerateContentConfig(response_modalities=["IMAGE"]),
        )
    except Exception as exc:
        raise SystemExit(f"error: Gemini request failed: {exc}")

    for candidate in getattr(response, "candidates", []) or []:
        for part in getattr(candidate.content, "parts", []) or []:
            inline = getattr(part, "inline_data", None)
            if inline is not None and getattr(inline, "data", None):
                return _write_image(inline.data, output)
    raise SystemExit(
        "error: Gemini returned no image data. Check that the model supports image "
        "output and that the prompt did not trip a safety filter."
    )


def generate_atlas(prompt: str, output: Path, api_key: str) -> Path:
    """Atlas Cloud, openai-compatible image generation endpoint."""
    body = _post(
        ATLAS_ENDPOINT,
        {"model": ATLAS_MODEL, "prompt": prompt, "n": 1, "response_format": "b64_json"},
        {"Authorization": f"Bearer {api_key}"},
    )
    items = body.get("data") or []
    if not items:
        raise SystemExit(f"error: Atlas returned no image: {json.dumps(body)[:300]}")
    first = items[0]
    if first.get("b64_json"):
        return _write_from_base64(first["b64_json"], output)
    url = first.get("url")
    if url:
        log(f"downloading the generated image from Atlas: {url}")
        with urllib.request.urlopen(url, timeout=REQUEST_TIMEOUT) as response:
            return _write_image(response.read(), output)
    raise SystemExit("error: Atlas response had neither b64_json nor url")


def generate_muapi(prompt: str, output: Path, api_key: str, model: str, resolution: str | None) -> Path:
    """MuAPI: submit an async prediction, then poll for the result."""
    payload = {"model": model, "prompt": prompt, "aspect_ratio": "1:1"}
    if resolution and model == MUAPI_MODELS["nano-banana-pro"]:
        # Pro accepts resolution; the focused logo workflow leaves it at the
        # provider default unless the caller asks for a specific one.
        payload["resolution"] = resolution

    submitted = _post(
        f"{MUAPI_ENDPOINT}/models/{model}/predictions",
        payload,
        {"Authorization": f"Bearer {api_key}"},
    )
    prediction_id = submitted.get("id") or submitted.get("prediction_id")
    if not prediction_id:
        raise SystemExit(f"error: MuAPI returned no prediction id: {json.dumps(submitted)[:300]}")

    log(f"MuAPI prediction {prediction_id}: polling for the result")
    for _ in range(MUAPI_MAX_POLLS):
        time.sleep(MUAPI_POLL_SECONDS)
        status = _get(
            f"{MUAPI_ENDPOINT}/predictions/{prediction_id}",
            {"Authorization": f"Bearer {api_key}"},
        )
        state = str(status.get("status", "")).lower()
        if state in {"succeeded", "completed", "success"}:
            return _write_muapi_result(status, output)
        if state in {"failed", "error", "canceled", "cancelled"}:
            raise SystemExit(
                f"error: MuAPI prediction failed: {status.get('error') or json.dumps(status)[:300]}"
            )
    raise SystemExit(
        f"error: MuAPI prediction {prediction_id} was still {state!r} after "
        f"{MUAPI_POLL_SECONDS * MUAPI_MAX_POLLS}s"
    )


def _get(url: str, headers: dict) -> dict:
    request = urllib.request.Request(url, method="GET")
    for name, value in headers.items():
        request.add_header(name, value)
    try:
        with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raise SystemExit(f"error: {url} returned {exc.code}: {exc.read().decode('utf-8', 'replace')[:300]}")
    except urllib.error.URLError as exc:
        raise SystemExit(f"error: cannot reach {url}: {exc.reason}")


def _write_muapi_result(status: dict, output: Path) -> Path:
    """Pull the image out of whichever field the prediction result used."""
    for candidate in (status.get("output"), status.get("result"), status):
        if isinstance(candidate, str) and candidate:
            return _write_from_base64(candidate, output)
        if isinstance(candidate, list) and candidate and isinstance(candidate[0], str):
            return _write_from_base64(candidate[0], output)
        if isinstance(candidate, dict):
            url = candidate.get("url")
            if url:
                with urllib.request.urlopen(url, timeout=REQUEST_TIMEOUT) as response:
                    return _write_image(response.read(), output)
            for key in ("b64_json", "image_base64", "image", "base64"):
                if isinstance(candidate.get(key), str):
                    return _write_from_base64(candidate[key], output)
    raise SystemExit(
        "error: MuAPI prediction succeeded but the result held no image. See "
        "https://muapi.ai/docs/api-reference for the current result schema."
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate a logo image with Gemini, Atlas Cloud, or MuAPI.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--brand", default=None, help="brand name")
    parser.add_argument("--prompt", default=None, help="extra visual description, merged into the prompt")
    parser.add_argument("--style", default=None, help=f"style name; omit to infer from the prompt")
    parser.add_argument("--palette", default=None, help="colour palette name; omit to infer")
    parser.add_argument("--industry", default=None, help="industry guide name; omit to infer")
    parser.add_argument("--provider", choices=PROVIDERS, default="gemini", help="generation provider")
    parser.add_argument("--model", choices=tuple(MODELS), default="flash",
                        help="Gemini only: flash, or pro for sharper text")
    parser.add_argument("--muapi-model", choices=tuple(MUAPI_MODELS), default="nano-banana",
                        help="MuAPI only: nano-banana or nano-banana-pro")
    parser.add_argument("--resolution", default=None,
                        help="MuAPI nano-banana-pro only; left at the provider default when unset")
    parser.add_argument("-o", "--output", default=None, help="output PNG path; default <brand>-logo.png")
    parser.add_argument("--dry-run", action="store_true",
                        help="print the assembled prompt and exit without calling any provider")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if not args.brand and not args.prompt:
        raise SystemExit("error: give --brand, --prompt, or both")

    # Infer the style, palette, and industry from the visual description only.
    # A brand name is a proper noun: "TechFlow" contributes the token "tech" to
    # every query, which drags the industry guide towards biotech no matter what
    # the description actually said.
    inference_query = args.prompt or args.brand or ""
    style = args.style
    if style is None:
        style = search_domain("style", inference_query, limit=1)[0]["name"]
    palette = args.palette
    if palette is None:
        palette = search_domain("color", inference_query, limit=1)[0]["name"]
    industry = args.industry
    if industry is None:
        industry = search_domain("industry", inference_query, limit=1)[0]["name"]

    try:
        style = resolve(style, "style")
        palette = resolve(palette, "color")
        industry = resolve(industry, "industry")
    except KeyError as exc:
        raise SystemExit(f"error: {exc.args[0]}")

    prompt = build_prompt(args.brand, style, palette, industry, args.prompt, args.provider)
    prompt = f"{prompt}\n\n{BACKGROUND_INSTRUCTION}"

    if args.dry_run:
        print(prompt)
        print(f"\n# style: {style}\n# palette: {palette}\n# industry: {industry}\n"
              f"# provider: {args.provider}\n# output would be: "
              f"{args.output or (args.brand or 'logo') + '-logo.png'}", file=sys.stderr)
        return 0

    output = Path(args.output or f"{(args.brand or 'logo').lower().replace(' ', '-')}-logo.png")

    if args.provider == "gemini":
        key = os.environ.get("GEMINI_API_KEY")
        if not key:
            raise SystemExit("error: GEMINI_API_KEY is not set. Get one at https://aistudio.google.com/apikey")
        path = generate_gemini(prompt, output, MODELS[args.model], key)
    elif args.provider == "atlas":
        key = os.environ.get("ATLAS_API_KEY") or os.environ.get("OPENAI_API_KEY")
        if not key:
            raise SystemExit("error: ATLAS_API_KEY is not set")
        path = generate_atlas(prompt, output, key)
    else:
        key = os.environ.get("MUAPI_API_KEY")
        if not key:
            raise SystemExit("error: MUAPI_API_KEY is not set")
        path = generate_muapi(prompt, output, key, MUAPI_MODELS[args.muapi_model], args.resolution)

    log(f"wrote {path} ({path.stat().st_size} bytes)")
    log("Open it and check it on white, on black, and at 24px before you use it. "
        "Then ask the user whether they want an HTML preview gallery.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
