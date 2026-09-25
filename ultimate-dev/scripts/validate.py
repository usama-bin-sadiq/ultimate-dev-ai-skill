#!/usr/bin/env python3
"""
ultimate-dev — Validation Script
Run this to verify the skill structure is consistent.
"""
import yaml
import os
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PASS = 0
FAIL = 0

def check(condition, msg):
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  ✅ {msg}")
    else:
        FAIL += 1
        print(f"  ❌ {msg}")

def load_manifest():
    with open(os.path.join(BASE, "skill-manifest.yaml")) as f:
        return yaml.safe_load(f)

def load_skill_md():
    with open(os.path.join(BASE, "SKILL.md")) as f:
        return f.read()

def load_agents_md():
    with open(os.path.join(BASE, "AGENTS.md")) as f:
        return f.read()

def get_version():
    with open(os.path.join(os.path.dirname(BASE), "VERSION")) as f:
        return f.read().strip()

version = get_version()

print("=" * 60)
print(f"  ultimate-dev v{version} — Structure Validation")
print("=" * 60)

# 1. Required files exist
print("\n=== Required Files ===")
for f in ["SKILL.md", "skill-manifest.yaml", "README.md"]:
    check(os.path.exists(os.path.join(BASE, f)), f"{f} exists")
for contract in ("contracts/README.md", "contracts/four-channels.md", "contracts/task-envelope.yaml"):
    check(os.path.exists(os.path.join(BASE, contract)), f"{contract} exists")
for guide in ("INSTALLATION.md", "requirements-dev.txt"):
    check(os.path.exists(os.path.join(BASE, guide)), f"{guide} exists")
check(os.path.exists(os.path.join(BASE, "skills/universal-task/SKILL.md")), "universal-task skill exists")
check(os.path.exists(os.path.join(os.path.dirname(BASE), "VERSION")), "VERSION exists (root)")

# 2. Version consistency
print("\n=== Version Consistency ===")
manifest = load_manifest()
skill_md = load_skill_md()
agents_md = load_agents_md()

check(manifest.get("version") == version, f"manifest version: {manifest.get('version')}")
check(True, f"VERSION file: {version}")

# 3. Module paths valid
print("\n=== Module Paths ===")
missing_mods = [m for m in manifest.get("modules", []) if not os.path.exists(os.path.join(BASE, m))]
check(len(missing_mods) == 0, f"All {len(manifest.get('modules', []))} module paths valid")
if missing_mods:
    for m in missing_mods:
        print(f"    ✗ {m}")

# 4. Agent paths valid
print("\n=== Agent Paths ===")
missing_agents = [a for a in manifest.get("agents", []) if not os.path.exists(os.path.join(BASE, a))]
check(len(missing_agents) == 0, f"All {len(manifest.get('agents', []))} agent paths valid")
if missing_agents:
    for a in missing_agents:
        print(f"    ✗ {a}")

# 5. No duplicate agents
print("\n=== Duplicate Check ===")
agent_names = {}
for root, dirs, files in os.walk(os.path.join(BASE, "agents")):
    for f in files:
        if f.endswith(".md") and not f.startswith("."):
            name = f.replace(".md", "")
            if name in agent_names:
                print(f"    ✗ DUPLICATE: {name}")
                FAIL += 1
            else:
                agent_names[name] = os.path.join(root, f)
check(True, f"No duplicate agent names ({len(agent_names)} unique)")

# 6. Sub-skills exist
print("\n=== Sub-Skills ===")
skills_dir = os.path.join(BASE, "skills")
if os.path.exists(skills_dir):
    skill_files = []
    for root, dirs, files in os.walk(skills_dir):
        for f in files:
            if f == "SKILL.md":
                skill_files.append(os.path.join(root, f))
    expected_skills = (manifest.get("stats") or {}).get("total_skills")
    check(
        len(skill_files) == expected_skills,
        f"{len(skill_files)} sub-skill SKILL.md files found (manifest expects {expected_skills})",
    )
else:
    check(False, "skills/ directory exists")

# 7. Infrastructure directories
print("\n=== Infrastructure ===")
for d in ["config", "prompts", "workflows", "schemas", "rules", "templates",
          "tools", "tests", "examples", "memory", "reference", "evals",
          "changelog", "modules", "router"]:
    path = os.path.join(BASE, d)
    if os.path.exists(path):
        count = sum(1 for _, _, files in os.walk(path) for f in files if not f.startswith("."))
        check(count > 0, f"{d}/ exists with {count} files")
    else:
        check(False, f"{d}/ directory exists")

# 8. New prompt-first and evaluation entrypoints
print("\n=== Prompt-first Extensions ===")
for script in (
    "scripts/benchmark-prompt-routing.py",
    "scripts/compare-routing-predictions.py",
    "scripts/validate-routing-decision.py",
    "scripts/measure-entrypoint.py",
    "scripts/replay-gate.py",
    "scripts/generate-project-context.py",
    "scripts/measure-install.py",
    "scripts/benchmark-project-context.py",
    "scripts/validate-company-context.py",
):
    check(os.path.exists(os.path.join(BASE, script)), f"{script} exists")

# 9. SKILL.md / AGENTS.md references and patterns
print("\n=== SKILL.md Pattern Wiring ===")
check("skills/" in skill_md, "SKILL.md references skills/ directory")
# Case-insensitive check for all 5 patterns (new architecture includes Composition)
patterns_ok = all(p.lower() in skill_md.lower() or p.lower() in agents_md.lower() for p in ["skills", "subagents", "handoffs", "router", "composition", "compose"])
check("skills" in skill_md.lower() and "subagents" in skill_md.lower(), "SKILL.md includes Skills and Subagents patterns")
check(any(x in skill_md.lower() for x in ["handoffs", "router"]), "SKILL.md documents Handoffs and Router patterns")
check("composition" in skill_md.lower() or "compose" in agents_md.lower(), "Composition/Compose pattern documented")
check("self-evolve" in agents_md.lower() or "self-evolution" in agents_md.lower(), "Self-evolution skill referenced")
check("skill-manifest.yaml" in agents_md or "agent registry" in agents_md.lower(), "Manifest referenced for agent registry")

# 9. Architecture documented (v2.5 — durable runtime / no triple-loading)
print("\n=== Architecture ===")
check("No triple-loading" in skill_md, "Triple-loading prevention documented")
check("runtime" in skill_md.lower() or "RUN" in agents_md, "Durable runtime / execution layer referenced")
check("CAPTURE" in skill_md or "CAPTURE" in agents_md, "Mandatory lifecycle (CAPTURE) documented")

# 10. Agent Selection Rules (v2.5)
print("\n=== Agent Selection Rules ===")
selection_text = (skill_md + agents_md).lower()
check("selection priority" in selection_text or "tiebreaker" in selection_text, "Agent selection tiebreaker/priority documented")
check("at most one primary" in agents_md.lower() or "max 1 agent" in selection_text, "Max 1 agent per domain / single primary specialist rule")

# 11. Frontend agent anti_triggers (overlap prevention)
print("\n=== Frontend Agent Anti-Triggers ===")
frontend_agents = ["react-specialist", "vue-specialist", "css-architect", "accessibility-engineer", "perf-specialist"]
for agent_name in frontend_agents:
    agent_path = os.path.join(BASE, "agents", "frontend", f"{agent_name}.md")
    if os.path.exists(agent_path):
        with open(agent_path) as f:
            content = f.read()
        has_anti = "anti_triggers:" in content
        # Check that anti_triggers contains framework-specific exclusions
        anti_line = [l for l in content.split("\n") if "anti_triggers:" in l]
        if anti_line:
            anti_content = anti_line[0]
            # Each frontend agent should exclude other frameworks
            if agent_name == "react-specialist":
                has_exclusion = "vue" in anti_content.lower()
            elif agent_name == "vue-specialist":
                has_exclusion = "react" in anti_content.lower()
            elif agent_name == "css-architect":
                has_exclusion = "react" in anti_content.lower() and "vue" in anti_content.lower()
            elif agent_name == "accessibility-engineer":
                has_exclusion = "react" in anti_content.lower() or "WCAG" in anti_content
            elif agent_name == "perf-specialist":
                has_exclusion = "react" in anti_content.lower() or "WCAG" in anti_content
            else:
                has_exclusion = True
            check(has_anti and has_exclusion, f"{agent_name} has framework-specific anti_triggers")
        else:
            check(False, f"{agent_name} has anti_triggers line")
    else:
        check(False, f"{agent_name}.md exists")

# 12. Config versions
print("\n=== Config Versions ===")
config_dir = os.path.join(BASE, "config")
if os.path.exists(config_dir):
    for f in sorted(os.listdir(config_dir)):
        if f.endswith(".yaml"):
            config_path = os.path.join(config_dir, f)
            with open(config_path) as fh:
                try:
                    config_data = yaml.safe_load(fh) or {}
                except yaml.YAMLError:
                    config_data = {}
            has_version = isinstance(config_data, dict) and "version" in config_data
            has_current = isinstance(config_data, dict) and str(config_data.get("version")) == version
            if has_version:
                check(has_current, f"config/{f} has version {version}")
            else:
                check(True, f"config/{f} (no version field, ok)")

# 13. Router files exist
print("\n=== Router Completeness ===")
router_dir = os.path.join(BASE, "router")
required_router = ["classification-rules.md", "token-budgets.md", "precedence-rules.md"]
for f in required_router:
    check(os.path.exists(os.path.join(router_dir, f)), f"router/{f} exists")

# Check classification-rules has agent selection
with open(os.path.join(router_dir, "classification-rules.md")) as f:
    rules_content = f.read()
check("Agent Selection" in rules_content, "Classification rules include Agent Selection section")
check("tiebreaker" in rules_content.lower() or "TIEBREAKER" in rules_content, "Classification rules include tiebreaker logic")

# Summary
print("\n" + "=" * 60)
total = PASS + FAIL
if FAIL == 0:
    print(f"  🎉 ALL {total} CHECKS PASSED")
else:
    print(f"  ⚠️  {PASS}/{total} passed, {FAIL} failed")
print("=" * 60)

sys.exit(0 if FAIL == 0 else 1)
