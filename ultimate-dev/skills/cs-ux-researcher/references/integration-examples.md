<!-- Moved verbatim from cs-ux-researcher/SKILL.md, the 'section' section. Relative links were rebased for the new depth; the prose is otherwise unchanged. -->

# Integration Examples

### Example 1: Discovery Sprint Research

```bash
#!/bin/bash
# discovery-research.sh - 2-week discovery sprint

echo "Discovery Sprint Research"
echo "========================="

# Week 1: Research execution
echo ""
echo "Week 1: Conduct & Analyze Interviews"
echo "-------------------------------------"

# Analyze all interview transcripts
for f in discovery-interviews/*.txt; do
  base=$(basename "$f" .txt)
  echo "Analyzing: $base"
  python ../../product-team/skills/product-manager-toolkit/scripts/customer_interview_analyzer.py "$f" json > "insights/$base.json"
done

# Week 2: Synthesis
echo ""
echo "Week 2: Generate Personas & Journey Map"
echo "----------------------------------------"

# Generate personas from aggregated data
python ../../product-team/skills/ux-researcher-designer/scripts/persona_generator.py aggregated-research.json

# Reference journey mapping guide
echo "Journey mapping guide: ../../product-team/skills/ux-researcher-designer/references/journey-mapping-guide.md"
```

### Example 2: Research Repository Update

```bash
#!/bin/bash
# research-update.sh - Monthly research insights update

echo "Research Repository Update - $(date +%Y-%m-%d)"
echo "================================================"

# Process new interviews
echo ""
echo "New Interview Analysis:"
for f in new-interviews/*.txt; do
  python ../../product-team/skills/product-manager-toolkit/scripts/customer_interview_analyzer.py "$f"
  echo "---"
done

# Review and refresh personas
echo ""
echo "Persona Review:"
echo "Current personas: ../../product-team/skills/ux-researcher-designer/references/example-personas.md"
echo "Methodology: ../../product-team/skills/ux-researcher-designer/references/persona-methodology.md"
```

### Example 3: Design Handoff with Research Context

```bash
#!/bin/bash
# research-handoff.sh - Prepare research context for design team

echo "Research Handoff Package"
echo "========================"

# Persona context
echo ""
echo "1. Active Personas:"
cat ../../product-team/skills/ux-researcher-designer/references/example-personas.md | head -30

# Journey context
echo ""
echo "2. Journey Map Reference:"
echo "See: ../../product-team/skills/ux-researcher-designer/references/journey-mapping-guide.md"

# Design system alignment
echo ""
echo "3. Component Architecture:"
echo "See: ../../product-team/skills/ui-design-system/references/component-architecture.md"

# Developer handoff process
echo ""
echo "4. Handoff Process:"
echo "See: ../../product-team/skills/ui-design-system/references/developer-handoff.md"
```
