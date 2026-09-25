#!/usr/bin/env bash
# Lightweight workflow security regression check.
#
# GitHub expressions are data when supplied through env/with/if, but expanding
# them into a shell run block is command injection.  This check intentionally
# has no third-party dependencies so it can run before package installation.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd -P)"
WORKFLOW_DIR="$REPO_ROOT/.github/workflows"

python3 - "$WORKFLOW_DIR" <<'PY'
import re
import sys
from pathlib import Path

workflow_dir = Path(sys.argv[1])
files = sorted(workflow_dir.glob("*.yml")) + sorted(workflow_dir.glob("*.yaml"))
if not files:
    raise SystemExit("no workflow files found")

block_re = re.compile(r"^(?P<indent>\s*)run:\s*(?:[|>][-+]?\d*)?\s*$")
inline_re = re.compile(r"^\s*run:.*\$\{\{")

for path in files:
    text = path.read_text(encoding="utf-8")
    if "pull_request_target" in text:
        raise SystemExit(f"{path}: pull_request_target is forbidden")
    if not re.search(r"(?m)^\s*permissions:\s*$", text):
        raise SystemExit(f"{path}: missing explicit permissions")
    if not re.search(r"(?m)^\s*concurrency:\s*$", text):
        raise SystemExit(f"{path}: missing concurrency gate")

    lines = text.splitlines()
    for index, line in enumerate(lines):
        if inline_re.search(line):
            raise SystemExit(f"{path}:{index + 1}: expression in inline run command")
        match = block_re.match(line)
        if not match:
            continue
        base_indent = len(match.group("indent"))
        body = []
        for following in lines[index + 1 :]:
            if following.strip() and len(following) - len(following.lstrip()) <= base_indent:
                break
            body.append(following)
        if any("${{" in following for following in body):
            raise SystemExit(
                f"{path}:{index + 1}: GitHub expression expanded inside run block"
            )

# The write-enabled paths must remain explicitly separated from PR validation.
auto_fix = (workflow_dir / "auto-fix.yml").read_text(encoding="utf-8")
for required in (
    "validate-generated:",
    "auto-fix:",
    "generate-agent-catalog.py",
    "github.ref == 'refs/heads/main'",
    "contents: write",
    "environment: auto-fix",
    "cancel-in-progress: false",
):
    if required not in auto_fix:
        raise SystemExit(f"auto-fix.yml: missing separation marker {required!r}")

release = (workflow_dir / "release.yml").read_text(encoding="utf-8")
for required in (
    'release:major',
    'release:minor',
    'release:patch',
    'head.repo.full_name',
    'push:\n    branches: [main]',
    "github.event_name == 'push'",
    'chore: release v',
    'chore: auto-sync manifest and docs',
    '[skip release]',
    'pull-requests: read',
    'secrets.ULTIMATE_DEV_TOKEN',
    'github.api_url',
    'github.token',
    'environment: release',
    'environment: CICD',
    'sync-version.py',
    'generate-agent-catalog.py',
    'validate-consistency.py',
    'cancel-in-progress: false',
):
    if required not in release:
        raise SystemExit(f"release.yml: missing release safety marker {required!r}")

pr_check = (workflow_dir / "pr-check.yml").read_text(encoding="utf-8")
for required in ("pr-template-check:", "permissions:"):
    if required not in pr_check:
        raise SystemExit(f"pr-check.yml: missing read-only PR validation marker {required!r}")
for forbidden in ("pull-requests: write", "issues: write", "gh pr edit", "github-script"):
    if forbidden in pr_check:
        raise SystemExit(f"pr-check.yml: untrusted PR write path remains: {forbidden}")

print(f"Workflow security checks passed: {len(files)} files")
PY
