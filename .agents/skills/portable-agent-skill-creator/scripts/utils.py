"""Shared utilities for the skill-creator scripts.

Design rules that the rest of the bundle depends on:

1. Importable from anywhere. Every entrypoint script bootstraps ``sys.path``
   before importing this module, so ``python scripts/foo.py`` works from any
   working directory as well as ``python -m scripts.foo``.
2. No hard third-party dependencies. PyYAML is used when importable and a
   small built-in parser is used when it is not. A runtime without PyYAML must
   still be able to validate and package a skill.
3. One parser, one schema. Frontmatter parsing lives here only; the duplicate
   parsers that used to live in ``improve_description.py`` and
   ``quick_validate.py`` were removed so the validator, the packager and the
   evaluator cannot disagree about what a skill declares.
"""

from __future__ import annotations

import json
import re
import shlex
from pathlib import Path
from typing import Any

SKILL_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = Path(__file__).resolve().parent

# Frontmatter keys the Agent Skills convention recognises. Anything else in the
# frontmatter block is reported by ``quick_validate.py`` as unexpected, because
# an unknown top-level key is usually a typo that silently disables behaviour.
ALLOWED_FRONTMATTER_KEYS = frozenset(
    {"name", "description", "license", "allowed-tools", "metadata", "compatibility"}
)

# Thresholds from the Agent Skills specification.
NAME_MAX_LENGTH = 64
DESCRIPTION_MAX_LENGTH = 1024
COMPATIBILITY_MAX_LENGTH = 500

_YAML_KEY_RE = re.compile(r"^([A-Za-z0-9_.-]+)\s*:(.*)$")
_BLOCK_INDICATORS = (">", "|", ">-", "|-", ">+", "|+")


def have_yaml() -> bool:
    """True when PyYAML is importable. Never raises."""
    try:
        import yaml  # noqa: F401
    except Exception:
        return False
    return True


# --------------------------------------------------------------------------
# Frontmatter
# --------------------------------------------------------------------------


def _parse_frontmatter_fallback(text: str) -> dict[str, Any]:
    """Minimal YAML-subset frontmatter parser used when PyYAML is absent.

    Supports the constructs that appear in a SKILL.md frontmatter block: ``key:
    value``, quoted values, block scalars (``>`` folds lines, ``|`` keeps
    newlines, each with ``-``/``+`` chomping), nested one-level maps, inline
    ``[a, b]`` lists, and ``- item`` block lists.

    Two deliberate simplifications: scalars are always returned as strings
    (PyYAML would coerce ``2`` to an int), and constructs outside this subset
    are preserved as raw text rather than being silently dropped. Both are
    acceptable because the frontmatter fields the validator acts on --
    ``name`` and ``description`` -- are strings in valid skills.
    """
    result: dict[str, Any] = {}
    lines = text.split("\n")
    i = 0
    current_key: str | None = None

    def coerce(raw: str) -> Any:
        raw = raw.strip()
        if len(raw) > 1 and raw[0] == raw[-1] and raw[0] in "\"'":
            return raw[1:-1]
        return raw

    while i < len(lines):
        line = lines[i].rstrip()
        stripped = line.strip()

        if not stripped or stripped.startswith("#"):
            i += 1
            continue

        indent = len(line) - len(line.lstrip())

        # A nested entry belongs to the most recent top-level key.
        if current_key and indent > 0:
            key = current_key
        else:
            match = _YAML_KEY_RE.match(stripped)
            if not match:
                i += 1
                continue
            key, inline = match.group(1), match.group(2).strip()
            current_key = key

            if inline in _BLOCK_INDICATORS:
                i += 1
                block: list[str] = []
                while i < len(lines):
                    nxt = lines[i]
                    if not nxt.strip():
                        block.append("")
                        i += 1
                        continue
                    if (len(nxt) - len(nxt.lstrip())) == 0:
                        break
                    block.append(nxt.strip())
                    i += 1
                while block and block[-1] == "":
                    block.pop()
                # '|' is a literal block and keeps its newlines; '>' is a folded
                # block and joins with spaces. Getting this wrong changes the
                # description text, so the distinction is preserved.
                literal = inline.startswith("|")
                result[key] = ("\n" if literal else " ").join(block).strip()
                continue

            if inline == "":
                i += 1
                # Look ahead for a nested block list or a nested map. Start as a
                # dict and switch to a list if list items appear.
                container: Any = {}
                saw_list_item = False
                while i < len(lines):
                    nxt = lines[i]
                    if not nxt.strip():
                        i += 1
                        continue
                    if (len(nxt) - len(nxt.lstrip())) == 0:
                        break
                    item = nxt.strip()
                    if item.startswith("- "):
                        saw_list_item = True
                        if not isinstance(container, list):
                            container = [] if container in ({}, None) else [container]
                        container.append(coerce(item[2:]))
                    else:
                        sub = _YAML_KEY_RE.match(item)
                        if sub:
                            if saw_list_item or not isinstance(container, dict):
                                container = {} if not isinstance(container, dict) else container
                            container[sub.group(1)] = coerce(sub.group(2))
                    i += 1
                if container:
                    result[key] = container
                else:
                    result.setdefault(key, None)
                continue

            if inline.startswith("[") and inline.endswith("]"):
                inner = inline[1:-1].strip()
                result[key] = (
                    [coerce(p) for p in inner.split(",") if p.strip()] if inner else []
                )
                i += 1
                continue

            result[key] = coerce(inline)
            i += 1
            continue

        # Continuation of a nested structure.
        if current_key and isinstance(result.get(current_key), list):
            if stripped.startswith("- "):
                result[current_key].append(coerce(stripped[2:]))
        elif current_key and isinstance(result.get(current_key), dict):
            sub = _YAML_KEY_RE.match(stripped)
            if sub:
                result[current_key][sub.group(1)] = coerce(sub.group(2))
        i += 1

    return result


def split_frontmatter(content: str) -> tuple[str, str]:
    """Split a document into (frontmatter_text, body).

    Returns an empty frontmatter string when the document has no frontmatter
    block, so callers can report a precise error.
    """
    if not content.startswith("---"):
        return "", content
    match = re.match(r"^---[ \t]*\r?\n(.*?)\r?\n---[ \t]*(?:\r?\n|$)", content, re.DOTALL)
    if not match:
        return "", content
    return match.group(1), content[match.end():]


def parse_frontmatter(content: str) -> dict[str, Any]:
    """Parse a SKILL.md frontmatter block into a dict.

    Uses PyYAML when available. The fallback parser is used otherwise, which
    keeps validation and packaging working on a runtime without PyYAML.
    """
    front_text, _ = split_frontmatter(content)
    if not front_text:
        return {}
    if have_yaml():
        try:
            import yaml

            loaded = yaml.safe_load(front_text)
            if isinstance(loaded, dict):
                return loaded
            return {}
        except Exception:
            # Malformed YAML should surface as a validation error, not as an
            # ImportError from a partially-installed library.
            raise ValueError("frontmatter is not valid YAML")
    return _parse_frontmatter_fallback(front_text)


def parse_skill_md(skill_path: Path) -> tuple[str, str, str]:
    """Parse a skill directory's SKILL.md.

    Returns ``(name, description, full_content)``. The name falls back to the
    directory name when frontmatter omits it, so callers always get a usable
    identifier; ``quick_validate.py`` reports the omission separately.
    """
    skill_path = Path(skill_path)
    content = (skill_path / "SKILL.md").read_text(encoding="utf-8")
    front = parse_frontmatter(content)
    name = front.get("name") or skill_path.name
    description = front.get("description") or ""
    if not isinstance(name, str):
        name = skill_path.name
    if not isinstance(description, str):
        description = str(description)
    return name.strip(), description.strip(), content


def find_skill_md(skill_path: Path) -> Path | None:
    """Return the SKILL.md path for a directory, or None if absent."""
    candidate = Path(skill_path)
    if candidate.is_file() and candidate.name == "SKILL.md":
        return candidate
    nested = candidate / "SKILL.md"
    return nested if nested.is_file() else None


# --------------------------------------------------------------------------
# Eval set normalization
# --------------------------------------------------------------------------

# Canonical eval field -> accepted legacy aliases. The documented schema uses
# ``query``; earlier drafts used ``prompt``. Both load, and the result is always
# canonical, so downstream code has exactly one shape to handle.
_EVAL_ALIASES = {
    "query": ("query", "prompt", "task", "input"),
    "expected_output": ("expected_output", "expectation", "expected"),
    "should_trigger": ("should_trigger", "shouldTrigger", "triggers"),
    "assertions": ("assertions", "expectations", "checks"),
    "id": ("id", "eval_id"),
}

VALID_ASSERTION_TYPES = frozenset(
    {
        "file_exists",
        "file_contains",
        "file_absent",
        "json_valid",
        "frontmatter_valid",
        "command_succeeds",
        "output_contains",
        "output_matches",
        "no_placeholder",
        "manual",
    }
)


def normalize_eval(raw: dict[str, Any], index: int) -> dict[str, Any]:
    """Normalize one eval entry to the canonical shape.

    Legacy ``prompt``/``expectations`` inputs are accepted. A missing
    ``should_trigger`` defaults to True: the eval set is about the skill
    handling the task, and a trigger-specific set states its own negatives.
    """
    if not isinstance(raw, dict):
        raise ValueError(f"eval[{index}] must be an object, got {type(raw).__name__}")

    out: dict[str, Any] = dict(raw)
    for canonical, aliases in _EVAL_ALIASES.items():
        for alias in aliases:
            if alias in raw and raw[alias] not in (None, ""):
                out[canonical] = raw[alias]
                break

    query = out.get("query")
    if not isinstance(query, str) or not query.strip():
        raise ValueError(
            f"eval[{index}] is missing a non-empty 'query' "
            f"(accepted aliases: {', '.join(_EVAL_ALIASES['query'])})"
        )
    out["query"] = query.strip()
    out["id"] = out.get("id", index + 1)

    should_trigger = out.get("should_trigger", True)
    out["should_trigger"] = bool(should_trigger)

    files = out.get("files") or []
    if isinstance(files, str):
        files = [files]
    if not isinstance(files, list):
        raise ValueError(f"eval[{out['id']}].files must be a list of paths")
    out["files"] = files

    assertions = out.get("assertions") or []
    if not isinstance(assertions, list):
        raise ValueError(f"eval[{out['id']}].assertions must be a list")
    out["assertions"] = assertions

    expected = out.get("expected_output", "")
    out["expected_output"] = expected if isinstance(expected, str) else str(expected)
    return out


def load_evals(path: Path) -> tuple[str | None, list[dict[str, Any]]]:
    """Load and validate an eval set file.

    Accepts either a bare list of evals or an object with ``evals`` and an
    optional ``skill_name``. Returns ``(skill_name, evals)``.
    """
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(data, list):
        raw_evals, skill_name = data, None
    elif isinstance(data, dict):
        raw_evals = data.get("evals") or data.get("queries") or data.get("cases")
        skill_name = data.get("skill_name")
    else:
        raise ValueError(f"eval set must be a list or object, got {type(data).__name__}")

    if not isinstance(raw_evals, list) or not raw_evals:
        raise ValueError(f"eval set {path} contains no evals")

    evals = [normalize_eval(raw, i) for i, raw in enumerate(raw_evals)]
    ids = [e["id"] for e in evals]
    duplicates = {i for i in ids if ids.count(i) > 1}
    if duplicates:
        raise ValueError(
            f"eval set {path} has duplicate ids: {sorted(map(str, duplicates))}"
        )
    return skill_name, evals


# --------------------------------------------------------------------------
# JSON helpers
# --------------------------------------------------------------------------


def read_json(path: Path, default: Any = None) -> Any:
    """Read JSON, returning ``default`` when the file is absent."""
    p = Path(path)
    if not p.exists():
        return default
    return json.loads(p.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> Path:
    """Write JSON with a trailing newline, creating parent directories."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return p


def split_command(command: str) -> list[str]:
    """Split a shell-ish command string into argv tokens."""
    return shlex.split(command)


def format_duration(ms: int | None) -> str:
    """Human-readable duration that never invents a measurement."""
    if ms is None:
        return "n/a"
    return f"{ms / 1000:.1f}s"
