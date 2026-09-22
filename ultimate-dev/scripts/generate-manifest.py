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
    """Scan agents/ directory and return organized agent list."""
    agents_dir = os.path.join(BASE, "agents")
    agents = []
    
    for root, dirs, files in os.walk(agents_dir):
        for f in sorted(files):
            if not f.endswith('.md') or f.startswith('.'):
                continue
            
            filepath = os.path.join(root, f)
            rel_path = os.path.relpath(filepath, BASE)
            
            # Skip _shared (they're fragments, not agents)
            if '_shared' in rel_path:
                continue
            
            fm = parse_frontmatter(filepath)
            if fm:
                agents.append({
                    "path": rel_path,
                    "name": fm.get("name", f.replace(".md", "")),
                    "domain": fm.get("domain", "unknown"),
                    "triggers": fm.get("triggers", []),
                })
            else:
                # No frontmatter — still register
                agents.append({
                    "path": rel_path,
                    "name": f.replace(".md", ""),
                    "domain": "unknown",
                    "triggers": [],
                })
    
    return agents

def scan_skills():
    """Scan skills/ directory and return skill list."""
    skills_dir = os.path.join(BASE, "skills")
    skills = []
    
    if not os.path.exists(skills_dir):
        return skills
    
    for root, dirs, files in os.walk(skills_dir):
        for f in sorted(files):
            if f == "SKILL.md":
                filepath = os.path.join(root, f)
                rel_path = os.path.relpath(filepath, BASE)
                skills.append(rel_path)
    
    return skills

def scan_modules():
    """Scan modules/ directory and return module list."""
    modules_dir = os.path.join(BASE, "modules")
    modules = []
    
    for root, dirs, files in os.walk(modules_dir):
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
    version_path = os.path.join(BASE, "VERSION")
    if os.path.exists(version_path):
        with open(version_path) as f:
            return f.read().strip()
    return "2.1.0"

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
        "description": "Master software-engineering orchestrator. Adapts to model size: tiny→inline, small→1 module, large→parallel agents, huge→full system. Includes universal specialists that learn ANY technology from the web and auto-generate new agents for future use.",
        "author": existing.get("author", "ultimate-dev team"),
        "license": existing.get("license", "MIT"),
        "repository": existing.get("repository", ""),
        "keywords": existing.get("keywords", [
            "multi-agent", "orchestrator", "software-engineering",
            "code-generation", "code-review", "architecture",
            "self-evolving", "langchain-patterns"
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
        "modules": modules,
        "shared": shared,
        "scripts": [
            "scripts/validate.py",
            "scripts/generate-manifest.py",
            "scripts/install.sh",
            "scripts/install.ps1",
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
                "router/completion-checklist.md",
                "router/decomposition.md",
                "router/gap-promotion-rules.md",
                "router/grounding-rules.md",
                "router/invocation-template.md",
                "router/lite-mode.md",
                "router/precedence-rules.md",
                "router/self-check.md",
                "router/token-budgets.md",
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
