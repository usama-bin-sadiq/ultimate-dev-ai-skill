#!/usr/bin/env python3
"""
ultimate-dev — Manifest Auto-Generator
Scans agents/ and skills/ directories and generates skill-manifest.yaml.
Run after adding/removing agents or skills.
"""
import yaml
import os
import re
import sys
from datetime import datetime

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MANIFEST_PATH = os.path.join(BASE, "skill-manifest.yaml")

def parse_frontmatter(filepath):
    """Extract YAML frontmatter from a markdown file."""
    try:
        with open(filepath) as f:
            content = f.read()
        match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
        if match:
            return yaml.safe_load(match.group(1))
    except:
        pass
    return None

def scan_agents():
    """Scan agents/ directory and return organized agent list - deterministic order."""
    agents_dir = os.path.join(BASE, "agents")
    agents = []
    
    # Get all .md files first, then sort by full relative path for deterministic order
    all_files = []
    for root, dirs, files in os.walk(agents_dir):
        # Sort dirs for consistent traversal
        dirs.sort()
        for f in sorted(files):
            if not f.endswith('.md') or f.startswith('.'):
                continue
            filepath = os.path.join(root, f)
            rel_path = os.path.relpath(filepath, BASE)
            if '_shared' in rel_path:
                continue
            all_files.append(rel_path)
    
    # Sort all paths for deterministic order
    all_files.sort()
    
    for rel_path in all_files:
        filepath = os.path.join(BASE, rel_path)
        fm = parse_frontmatter(filepath)
        if fm:
            agents.append({
                "path": rel_path,
                "name": fm.get("name", os.path.basename(rel_path).replace(".md", "")),
                "domain": fm.get("domain", "unknown"),
                "triggers": fm.get("triggers", []),
            })
        else:
            agents.append({
                "path": rel_path,
                "name": os.path.basename(rel_path).replace(".md", ""),
                "domain": "unknown",
                "triggers": [],
            })
    
    return agents

def scan_skills():
    """Scan skills/ directory and return skill list - deterministic order."""
    skills_dir = os.path.join(BASE, "skills")
    skills = []
    
    if not os.path.exists(skills_dir):
        return skills
    
    all_skills = []
    for root, dirs, files in os.walk(skills_dir):
        dirs.sort()
        for f in sorted(files):
            if f == "SKILL.md":
                filepath = os.path.join(root, f)
                rel_path = os.path.relpath(filepath, BASE)
                all_skills.append(rel_path)
    
    all_skills.sort()
    return all_skills

def scan_modules():
    """Scan modules/ directory and return module list - deterministic order."""
    modules_dir = os.path.join(BASE, "modules")
    modules = []
    
    for root, dirs, files in os.walk(modules_dir):
        dirs.sort()
        for f in sorted(files):
            if f.endswith('.md') and not f.startswith('.'):
                filepath = os.path.join(root, f)
                rel_path = os.path.relpath(filepath, BASE)
                modules.append(rel_path)
    
    return sorted(modules)

def scan_shared():
    """Scan agents/_shared/ for shared fragments."""
    shared_dir = os.path.join(BASE, "agents", "_shared")
    shared = []
    
    if os.path.exists(shared_dir):
        for f in sorted(os.listdir(shared_dir)):
            if f.endswith('.md') and not f.startswith('.'):
                shared.append(f"agents/_shared/{f}")
    
    return shared

def get_version():
    """Read version from VERSION file."""
    version_path = os.path.join(os.path.dirname(BASE), "VERSION")
    if os.path.exists(version_path):
        with open(version_path) as f:
            return f.read().strip()
    return "3.0.0"

def generate_manifest():
    """Generate the complete skill-manifest.yaml."""
    agents = scan_agents()
    skills = scan_skills()
    modules = scan_modules()
    shared = scan_shared()
    version = get_version()
    
    # Read existing manifest to preserve non-scanned fields
    existing = {}
    if os.path.exists(MANIFEST_PATH):
        with open(MANIFEST_PATH) as f:
            existing = yaml.safe_load(f) or {}
    
    manifest = {
        "name": "ultimate-dev",
        "version": version,
        "description": "Prompt-first, model-agnostic agentic skill suite for software agencies and companies. Detects context, classifies tasks, selects the smallest useful method or specialist, executes, verifies, and learns. Durable runtime and JEV are optional extensions. Uses bounded universal fallback and evidence-gated capability proposals.",
        "author": existing.get("author", "ultimate-dev team"),
        "license": existing.get("license", "MIT"),
        "repository": existing.get("repository", "https://github.com/usama-bin-sadiq/ultimate-dev-ai-skill/ultimate-dev"),
        "keywords": existing.get("keywords", [
            "multi-agent", "orchestrator", "software-engineering",
            "code-generation", "code-review", "architecture",
            "self-evolving", "capability-learning"
        ]),
        "entry": "SKILL.md",
        "compatible_tools": existing.get("compatible_tools", [
            "opencode", "claude-code", "gemini-cli", "cursor",
            "windsurf", "continue", "aider", "cline", "roo-code"
        ]),
        "min_tool_version": existing.get("min_tool_version", "1.0.0"),
        "stats": {
            "total_agents": len(agents),
            "total_skills": len([s for s in skills if s != "skills/_learned"]),
            "total_modules": len(modules),
            "total_shared": len(shared),
            "departments_covered": len(set(
                a.get("domain", "unknown") for a in agents
            )),
            "last_generated": datetime.now().strftime("%Y-%m-%d"),
        },
        "agents": [a["path"] for a in agents],
        "skills": skills,
        "adapters": sorted(
            os.path.relpath(entry.path, BASE).replace(os.sep, "/")
            for entry in os.scandir(os.path.join(BASE, "adapters"))
            if entry.is_file() and entry.name.endswith(".md")
        ),
        "modules": modules,
        "shared": shared,
        "development": {
            "python": ">=3.11",
            "requirements": "requirements-dev.txt",
            "optional_node": ">=20",
            "optional_powershell": ">=7",
            "prompt_only_dependencies": [],
        },
        "contracts": [
            "contracts/README.md",
            "contracts/capability-manifest.yaml",
            "contracts/four-channels.md",
            "contracts/handoff-contract.yaml",
            "contracts/hitl-interrupt.yaml",
            "contracts/memory-provenance.yaml",
            "contracts/middleware-hooks.yaml",
            "contracts/subagent-contract.yaml",
            "contracts/task-envelope.yaml",
            "contracts/task-state-machine.yaml",
        ],
        "scripts": [
            "scripts/validate.py",
            "scripts/generate-manifest.py",
            "scripts/install.sh",
            "scripts/install.ps1",
            "scripts/validate-consistency.py",
            "scripts/benchmark-prompt-routing.py",
            "scripts/compare-routing-predictions.py",
            "scripts/validate-routing-decision.py",
            "scripts/measure-entrypoint.py",
            "scripts/replay-gate.py",
            "scripts/generate-project-context.py",
            "scripts/measure-install.py",
            "scripts/validate-company-context.py",
            "scripts/benchmark-project-context.py",
        ],
        "templates": [
            "templates/task.md",
            "templates/adr.md",
            "templates/code-review.md",
            "templates/git/commit-conventions.md",
        ],
        "router": {
            "description": "Classification and routing logic",
            "files": [
                "router/classification-rules.md",
                "router/behavioral-calibration.md",
                "router/progressive-disclosure.md",
                "router/completion-checklist.md",
                "router/decomposition.md",
                "router/gap-promotion-rules.md",
                "router/grounding-rules.md",
                "router/invocation-template.md",
                "router/lite-mode.md",
                "router/precedence-rules.md",
                "router/self-check.md",
                "router/token-budgets.md",
                "router/trigger-collision-policy.md",
            ],
        },
    }
    
    return manifest

def main():
    print("Generating skill-manifest.yaml...")
    manifest = generate_manifest()
    
    # Write with nice formatting
    with open(MANIFEST_PATH, 'w') as f:
        yaml.dump(manifest, f, default_flow_style=False, sort_keys=False, width=120)
    
    # Print summary
    print(f"✅ Generated manifest with:")
    print(f"   Agents:  {manifest['stats']['total_agents']}")
    print(f"   Skills:  {manifest['stats']['total_skills']}")
    print(f"   Modules: {manifest['stats']['total_modules']}")
    print(f"   Shared:  {manifest['stats']['total_shared']}")
    print(f"   Departments: {manifest['stats']['departments_covered']}")
    print(f"   Written to: {MANIFEST_PATH}")

if __name__ == "__main__":
    main()