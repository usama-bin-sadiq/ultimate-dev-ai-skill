<!-- Moved verbatim from cs-product-manager/SKILL.md, the 'section' section. Relative links were rebased for the new depth; the prose is otherwise unchanged. -->

# Integration Examples

### Example 1: Weekly Product Review Dashboard

```bash
#!/bin/bash
# product-weekly-review.sh - Automated product metrics summary

echo "📊 Weekly Product Review - $(date +%Y-%m-%d)"
echo "=========================================="

# Current roadmap status
echo ""
echo "🎯 Roadmap Priorities (RICE Sorted):"
python ../../product-team/skills/product-manager-toolkit/scripts/rice_prioritizer.py current-roadmap.csv --capacity 20

# Recent interview insights
echo ""
echo "💡 Latest Customer Insights:"
if [ -f latest-interview.txt ]; then
  python ../../product-team/skills/product-manager-toolkit/scripts/customer_interview_analyzer.py latest-interview.txt
else
  echo "No new interviews this week"
fi

# PRD templates available
echo ""
echo "📝 PRD Templates:"
echo "Standard PRD, One-Page PRD, Feature Brief, Agile Epic"
echo "Location: ../../product-team/skills/product-manager-toolkit/references/prd_templates.md"
```

### Example 2: Discovery Sprint Workflow

```bash
# Complete discovery sprint (2 weeks)

echo "🔍 Discovery Sprint - Week 1"
echo "=============================="

# Day 1-2: Conduct interviews
echo "Conducting 5 customer interviews..."

# Day 3-5: Analyze insights
python ../../product-team/skills/product-manager-toolkit/scripts/customer_interview_analyzer.py interview-001.txt > insights-001.txt
python ../../product-team/skills/product-manager-toolkit/scripts/customer_interview_analyzer.py interview-002.txt > insights-002.txt
python ../../product-team/skills/product-manager-toolkit/scripts/customer_interview_analyzer.py interview-003.txt > insights-003.txt
python ../../product-team/skills/product-manager-toolkit/scripts/customer_interview_analyzer.py interview-004.txt > insights-004.txt
python ../../product-team/skills/product-manager-toolkit/scripts/customer_interview_analyzer.py interview-005.txt > insights-005.txt

echo ""
echo "🔍 Discovery Sprint - Week 2"
echo "=============================="

# Day 6-8: Prioritize problems and solutions
echo "Creating solution candidates..."

# Day 9-10: RICE prioritization
python ../../product-team/skills/product-manager-toolkit/scripts/rice_prioritizer.py solution-candidates.csv

echo ""
echo "✅ Discovery Complete - Ready for PRD creation"
```

### Example 3: Quarterly Planning Automation

```bash
# Quarterly planning automation script

QUARTER="Q4-2025"
CAPACITY=18  # person-months

echo "📅 $QUARTER Planning"
echo "===================="

# Step 1: Prioritize backlog
echo ""
echo "1. Feature Prioritization:"
python ../../product-team/skills/product-manager-toolkit/scripts/rice_prioritizer.py backlog.csv --capacity $CAPACITY > $QUARTER-roadmap.txt

# Step 2: Extract quick wins
echo ""
echo "2. Quick Wins (Ship First):"
grep "Quick Win" $QUARTER-roadmap.txt

# Step 3: Identify big bets
echo ""
echo "3. Big Bets (Strategic Investments):"
grep "Big Bet" $QUARTER-roadmap.txt

# Step 4: Generate summary
echo ""
echo "4. Quarterly Summary:"
echo "Capacity: $CAPACITY person-months"
echo "Features: $(wc -l < backlog.csv)"
echo "Report: $QUARTER-roadmap.txt"
```
