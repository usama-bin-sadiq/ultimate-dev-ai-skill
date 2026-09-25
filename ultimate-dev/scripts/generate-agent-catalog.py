#!/usr/bin/env python3
"""Generate the derived concrete-agent catalog from agent frontmatter.

This is a maintenance tool, not a runtime dependency. The manifest remains the
portable release registry; this catalog makes the concrete routing surface
machine-readable and lets validation detect drift between them.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError as exc:  # pragma: no cover - environment dependent
    raise SystemExit("generate-agent-catalog: PyYAML is required") from exc

ROOT = Path(__file__).resolve().parent.parent
REPO_ROOT = ROOT.parent
VERSION_FILE = REPO_ROOT / "VERSION"
OUTPUT_FILE = ROOT / "config" / "agent-catalog.yaml"


def frontmatter(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    match = re.match(r"^---\n(.*?)\n---(?:\n|$)", text, re.DOTALL)
    if not match:
        raise ValueError(f"missing frontmatter: {path}")
    value = yaml.safe_load(match.group(1))
    if not isinstance(value, dict):
        raise ValueError(f"frontmatter is not a mapping: {path}")
    return value


def normalize_text(value: Any) -> str:
    if isinstance(value, (list, tuple)):
        return " ".join(str(item) for item in value)
    return " ".join(str(value or "").split())


def build_catalog() -> dict[str, Any]:
    version = VERSION_FILE.read_text(encoding="utf-8").strip()
    agents: list[dict[str, Any]] = []
    for path in sorted((ROOT / "agents").rglob("*.md")):
        if "_shared" in path.parts or path.name.startswith("."):
            continue
        metadata = frontmatter(path)
        name = metadata.get("name")
        domain = metadata.get("domain")
        description = metadata.get("description")
        if not isinstance(name, str) or not name:
            raise ValueError(f"{path}: missing agent name")
        if not isinstance(domain, str) or not domain:
            raise ValueError(f"{path}: missing agent domain")
        if not isinstance(description, str) or not description.strip():
            raise ValueError(f"{path}: missing agent description")
        agents.append(
            {
                "id": name,
                "path": str(path.relative_to(ROOT)),
                "domain": domain,
                "description": normalize_text(description),
                "triggers": list(metadata.get("triggers") or []),
                "anti_triggers": list(metadata.get("anti_triggers") or []),
                "tools": list(metadata.get("tools") or []),
                "model": str(metadata.get("model") or "inherit"),
                "max_turns": metadata.get("max_turns"),
            }
        )
    return {
        "version": version,
        "source": "skill-manifest.yaml",
        "agent_count": len(agents),
        "agents": agents,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="fail if the checked-in catalog is stale")
    args = parser.parse_args()
    catalog = build_catalog()
    rendered = yaml.safe_dump(catalog, sort_keys=False, allow_unicode=True, width=100)
    if args.check:
        if not OUTPUT_FILE.exists():
            print(f"missing: {OUTPUT_FILE.relative_to(REPO_ROOT)}", file=sys.stderr)
            return 1
        if OUTPUT_FILE.read_text(encoding="utf-8") != rendered:
            print(f"stale: {OUTPUT_FILE.relative_to(REPO_ROOT)}; run generate-agent-catalog.py", file=sys.stderr)
            return 1
        print("agent catalog: consistent")
        return 0
    OUTPUT_FILE.write_text(rendered, encoding="utf-8")
    print(f"Generated {OUTPUT_FILE.relative_to(REPO_ROOT)} ({catalog['agent_count']} agents)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
