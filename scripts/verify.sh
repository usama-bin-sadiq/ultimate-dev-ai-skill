#!/bin/sh
# ultimate-dev verification script
# Checks that all required files exist and are valid

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
# verify.sh lives in the repo's scripts/ directory; the skill itself
# (SKILL.md, router/, modules/, ...) lives in ./ultimate-dev when the
# repo has been cloned. Fall back to the parent dir for flat layouts.
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
if [ -d "$REPO_ROOT/ultimate-dev" ]; then
  SKILL_DIR="$REPO_ROOT/ultimate-dev"
else
  SKILL_DIR="$REPO_ROOT"
fi
ERRORS=0
WARNINGS=0

echo "=== ultimate-dev verification ==="
echo ""

# Check SKILL.md
if [ -f "$SKILL_DIR/SKILL.md" ]; then
  echo "✅ SKILL.md"
else
  echo "❌ SKILL.md missing"
  ERRORS=$((ERRORS + 1))
fi

# Check skill-manifest.yaml
if [ -f "$SKILL_DIR/skill-manifest.yaml" ]; then
  echo "✅ skill-manifest.yaml"
else
  echo "❌ skill-manifest.yaml missing"
  ERRORS=$((ERRORS + 1))
fi

# Check top-level files
echo ""
TOP_LEVEL_FILES="README.md ARCHITECTURE.md CONTRIBUTING.md VERSION CHANGELOG.md"
TOP_LEVEL_COUNT=$(echo "$TOP_LEVEL_FILES" | wc -w | tr -d ' ')
echo "Top-level files ($TOP_LEVEL_COUNT required):"
for f in $TOP_LEVEL_FILES; do
  if [ -f "$REPO_ROOT/$f" ]; then
    echo "  ✅ $f"
  else
    echo "  ❌ $f missing"
    ERRORS=$((ERRORS + 1))
  fi
done

# Check router files
echo ""
ROUTER_FILES="classification-rules.md decomposition.md token-budgets.md grounding-rules.md completion-checklist.md invocation-template.md precedence-rules.md self-check.md gap-promotion-rules.md lite-mode.md"
ROUTER_COUNT=$(echo "$ROUTER_FILES" | wc -w | tr -d ' ')
echo "Router files ($ROUTER_COUNT required):"
for f in $ROUTER_FILES; do
  if [ -f "$SKILL_DIR/router/$f" ]; then
    echo "  ✅ $f"
  else
    echo "  ❌ $f missing"
    ERRORS=$((ERRORS + 1))
  fi
done

# Check engineering modules
echo ""
ENGINEERING_FILES="backend.md frontend.md architecture.md database.md security.md devops.md mobile.md testing-qa.md documentation.md"
ENGINEERING_COUNT=$(echo "$ENGINEERING_FILES" | wc -w | tr -d ' ')
echo "Engineering modules ($ENGINEERING_COUNT required):"
for f in $ENGINEERING_FILES; do
  if [ -f "$SKILL_DIR/modules/engineering/$f" ]; then
    echo "  ✅ $f"
  else
    echo "  ❌ $f missing"
    ERRORS=$((ERRORS + 1))
  fi
done

# Check agency modules
echo ""
AGENCY_FILES="project-management.md product.md design-handoff.md client-communication.md"
AGENCY_COUNT=$(echo "$AGENCY_FILES" | wc -w | tr -d ' ')
echo "Agency modules ($AGENCY_COUNT required):"
for f in $AGENCY_FILES; do
  if [ -f "$SKILL_DIR/modules/agency/$f" ]; then
    echo "  ✅ $f"
  else
    echo "  ❌ $f missing"
    ERRORS=$((ERRORS + 1))
  fi
done

# Check business operations modules
echo ""
BUSINESS_FILES="marketing sales finance support paid-media"
BUSINESS_COUNT=$(echo "$BUSINESS_FILES" | wc -w | tr -d ' ')
echo "Business operations modules ($BUSINESS_COUNT required):"
for f in $BUSINESS_FILES; do
  if [ -f "$SKILL_DIR/modules/$f/$f.md" ]; then
    echo "  ✅ $f.md"
  else
    echo "  ❌ $f.md missing"
    ERRORS=$((ERRORS + 1))
  fi
done

# Check research modules
echo ""
RESEARCH_FILES="research academic"
RESEARCH_COUNT=$(echo "$RESEARCH_FILES" | wc -w | tr -d ' ')
echo "Research modules ($RESEARCH_COUNT required):"
for f in $RESEARCH_FILES; do
  if [ -f "$SKILL_DIR/modules/$f/$f.md" ]; then
    echo "  ✅ $f.md"
  else
    echo "  ❌ $f.md missing"
    ERRORS=$((ERRORS + 1))
  fi
done

# Check domain-specific modules
echo ""
DOMAIN_FILES="healthcare game-dev gis spatial-computing specialized"
DOMAIN_COUNT=$(echo "$DOMAIN_FILES" | wc -w | tr -d ' ')
echo "Domain-specific modules ($DOMAIN_COUNT required):"
for f in $DOMAIN_FILES; do
  if [ -f "$SKILL_DIR/modules/$f/$f.md" ]; then
    echo "  ✅ $f.md"
  else
    echo "  ❌ $f.md missing"
    ERRORS=$((ERRORS + 1))
  fi
done

# Check cross-cutting modules
echo ""
CROSS_FILES="_emerging-tech-handler.md _universal-principles.md"
CROSS_COUNT=$(echo "$CROSS_FILES" | wc -w | tr -d ' ')
echo "Cross-cutting modules ($CROSS_COUNT required):"
for f in $CROSS_FILES; do
  if [ -f "$SKILL_DIR/modules/$f" ]; then
    echo "  ✅ $f"
  else
    echo "  ❌ $f missing"
    ERRORS=$((ERRORS + 1))
  fi
done

# Check agents (dynamically found)
echo ""
echo "Agents:"
AGENT_COUNT=$(find "$SKILL_DIR/agents" -name "*.md" -not -path "*/_shared/*" 2>/dev/null | wc -l | tr -d ' ')

if [ "$AGENT_COUNT" -gt 0 ]; then
  echo "  ✅ $AGENT_COUNT agent files"
else
  echo "  ❌ No agent files found"
  ERRORS=$((ERRORS + 1))
fi

# Check scripts
echo ""
SCRIPTS_FILES="install.sh install.ps1 detect-tools.sh verify.sh"
SCRIPTS_COUNT=$(echo "$SCRIPTS_FILES" | wc -w | tr -d ' ')
echo "Scripts ($SCRIPTS_COUNT required):"
for f in $SCRIPTS_FILES; do
  if [ -f "$REPO_ROOT/scripts/$f" ]; then
    echo "  ✅ $f"
  else
    echo "  ❌ $f missing"
    ERRORS=$((ERRORS + 1))
  fi
done

# Check adapters and staleness
echo ""
ADAPTERS_FILES="claude-code.md codex.md cursor.md generic-cli.md"
ADAPTERS_COUNT=$(echo "$ADAPTERS_FILES" | wc -w | tr -d ' ')
echo "Adapters ($ADAPTERS_COUNT required):"
for f in $ADAPTERS_FILES; do
  if [ -f "$SKILL_DIR/adapters/$f" ]; then
    # Check for doc_source and last_verified fields
    if grep -q "doc_source:" "$SKILL_DIR/adapters/$f" && grep -q "last_verified:" "$SKILL_DIR/adapters/$f"; then
      echo "  ✅ $f (with metadata)"
    else
      echo "  ⚠️  $f (missing doc_source or last_verified)"
      WARNINGS=$((WARNINGS + 1))
    fi
  else
    echo "  ❌ $f missing"
    ERRORS=$((ERRORS + 1))
  fi
done

# Check evals
echo ""
echo "Evaluations:"
if [ -f "$SKILL_DIR/evals/golden-cases.yaml" ]; then
  echo "  ✅ golden-cases.yaml"
else
  echo "  ⚠️  golden-cases.yaml missing"
  WARNINGS=$((WARNINGS + 1))
fi

# Summary
echo ""
echo "=== Results ==="
echo "Agents found: $AGENT_COUNT"
echo "Router files: $ROUTER_COUNT"
echo "Scripts: $SCRIPTS_COUNT"
echo "Adapters: $ADAPTERS_COUNT"
echo ""

if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
  echo "🎉 All checks passed!"
  exit 0
elif [ $ERRORS -eq 0 ]; then
  echo "⚠️  $WARNINGS warnings (non-blocking)"
  exit 0
else
  echo "❌ $ERRORS errors, $WARNINGS warnings"
  exit 1
fi
