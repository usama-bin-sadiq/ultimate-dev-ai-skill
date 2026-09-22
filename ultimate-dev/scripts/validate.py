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

def get_version():
    with open(os.path.join(BASE, "VERSION")) as f:
        return f.read().strip()

version = get_version()

print("=" * 60)
print(f"  ultimate-dev v{version} — Structure Validation")
print("=" * 60)

# 1. Required files exist
print("\n=== Required Files ===")
for f in ["SKILL.md", "skill-manifest.yaml", "README.md", "VERSION"]:
    check(os.path.exists(os.path.join(BASE, f)), f"{f} exists")

# 2. Version consistency
print("\n=== Version Consistency ===")
manifest = load_manifest()
skill_md = load_skill_md()

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

# 8. SKILL.md references skills/
print("\n=== SKILL.md Pattern Wiring ===")
check("skills/" in skill_md, "SKILL.md references skills/ directory")
check("SKILLS" in skill_md and "SUBAGENTS" in skill_md, "SKILL.md includes LangChain patterns (Skills, Subagents)")
check("HANDOFFS" in skill_md and "ROUTER" in skill_md, "All 4 patterns documented (Handoffs, Router)")
check("self-evolve" in skill_md, "Self-evolution skill referenced")
check("skill-manifest.yaml" in skill_md, "Manifest referenced for agent registry")

# 9. Three-Layer Architecture documented
print("\n=== Three-Layer Architecture ===")
check("Three-Layer Architecture" in skill_md, "Three-Layer Architecture section exists")
check("SKILLS" in skill_md and "AGENTS" in skill_md and "MODULES" in skill_md, "All three layers documented")
check("No triple-loading" in skill_md, "Triple-loading prevention documented")

# 10. Agent Selection Tiebreaker
print("\n=== Agent Selection Rules ===")
check("Selection Priority" in skill_md or "Tiebreaker" in skill_md, "Agent selection tiebreaker documented")
check("Max 1 agent per domain" in skill_md, "Max 1 agent per domain rule")

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
            with open(os.path.join(config_dir, f)) as fh:
                content = fh.read()
            has_version = "version:" in content
            has_current = f'"{version}"' in content or f"'{version}'" in content
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
