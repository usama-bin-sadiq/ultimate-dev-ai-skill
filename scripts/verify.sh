#!/bin/sh
# ultimate-dev verification script
# Checks that all required files exist and are valid

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILL_DIR="$(dirname "$SCRIPT_DIR")"
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
echo "Top-level files:"
for f in README.md ARCHITECTURE.md CONTRIBUTING.md VERSION CHANGELOG.md; do
  if [ -f "$SKILL_DIR/$f" ]; then
    echo "  ✅ $f"
  else
    echo "  ❌ $f missing"
    ERRORS=$((ERRORS + 1))
  fi
done

# Check router files (8 required)
echo ""
echo "Router files (10 required):"
for f in classification-rules.md decomposition.md token-budgets.md grounding-rules.md completion-checklist.md invocation-template.md precedence-rules.md self-check.md gap-promotion-rules.md lite-mode.md; do
  if [ -f "$SKILL_DIR/router/$f" ]; then
    echo "  ✅ $f"
  else
    echo "  ❌ $f missing"
    ERRORS=$((ERRORS + 1))
  fi
done

# Check engineering modules (9 required)
echo ""
echo "Engineering modules (9 required):"
for f in backend.md frontend.md architecture.md database.md security.md devops.md mobile.md testing-qa.md documentation.md; do
  if [ -f "$SKILL_DIR/modules/engineering/$f" ]; then
    echo "  ✅ $f"
  else
    echo "  ❌ $f missing"
    ERRORS=$((ERRORS + 1))
  fi
done

# Check agency modules (4 required)
echo ""
echo "Agency modules (4 required):"
for f in project-management.md product.md design-handoff.md client-communication.md; do
  if [ -f "$SKILL_DIR/modules/agency/$f" ]; then
    echo "  ✅ $f"
  else
    echo "  ❌ $f missing"
    ERRORS=$((ERRORS + 1))
  fi
done

# Check business operations modules (5 required)
echo ""
echo "Business operations modules (5 required):"
for f in marketing sales finance support paid-media; do
  if [ -f "$SKILL_DIR/modules/$f/$f.md" ]; then
    echo "  ✅ $f.md"
  else
    echo "  ❌ $f.md missing"
    ERRORS=$((ERRORS + 1))
  fi
done

# Check research modules (2 required)
echo ""
echo "Research modules (2 required):"
for f in research academic; do
  if [ -f "$SKILL_DIR/modules/$f/$f.md" ]; then
    echo "  ✅ $f.md"
  else
    echo "  ❌ $f.md missing"
    ERRORS=$((ERRORS + 1))
  fi
done

# Check domain-specific modules (5 required)
echo ""
echo "Domain-specific modules (5 required):"
for f in healthcare game-dev gis spatial-computing specialized; do
  if [ -f "$SKILL_DIR/modules/$f/$f.md" ]; then
    echo "  ✅ $f.md"
  else
    echo "  ❌ $f.md missing"
    ERRORS=$((ERRORS + 1))
  fi
done

# Check cross-cutting modules (2 required)
echo ""
echo "Cross-cutting modules (2 required):"
for f in _emerging-tech-handler.md _universal-principles.md; do
  if [ -f "$SKILL_DIR/modules/$f" ]; then
    echo "  ✅ $f"
  else
    echo "  ❌ $f missing"
    ERRORS=$((ERRORS + 1))
  fi
done

# Check personas (dynamically found)
echo ""
echo "Personas (all found):"
PERSONA_COUNT=0
for f in $(find "$SKILL_DIR/personas" -name "*.md" 2>/dev/null | sort); do
  REL=$(echo "$f" | sed "s|$SKILL_DIR/||")
  if [ -f "$f" ]; then
    echo "  ✅ $REL"
    PERSONA_COUNT=$((PERSONA_COUNT + 1))
  fi
done

if [ $PERSONA_COUNT -eq 0 ]; then
  echo "  ❌ No persona files found"
  ERRORS=$((ERRORS + 1))
fi

# Check scripts (4 required)
echo ""
echo "Scripts (4 required):"
for f in install.sh install.ps1 detect-tools.sh verify.sh; do
  if [ -f "$SKILL_DIR/scripts/$f" ]; then
    echo "  ✅ $f"
  else
    echo "  ❌ $f missing"
    ERRORS=$((ERRORS + 1))
  fi
done

# Check adapters (4 required) and staleness
echo ""
echo "Adapters (4 required):"
for f in claude-code.md codex.md cursor.md generic-cli.md; do
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
echo "Personas found: $PERSONA_COUNT"
echo "Router files: 8"
echo "Scripts: 4"
echo "Adapters: 4"
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
