<!-- Moved verbatim from cs-project-manager/SKILL.md, the
     'integration-examples' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Integration Examples

### Example 1: Weekly Project Status Report

```bash
#!/bin/bash
# weekly-status.sh - Automated weekly project status generation

echo "Weekly Project Status - $(date +%Y-%m-%d)"
echo "============================================"

# Sprint health assessment
echo ""
echo "Sprint Health:"
python ../../project-management/skills/scrum-master/scripts/sprint_health_scorer.py current_sprint.json

# Velocity trend
echo ""
echo "Velocity Trend:"
python ../../project-management/skills/scrum-master/scripts/velocity_analyzer.py sprint_history.json

# Risk exposure
echo ""
echo "Active Risks:"
python ../../project-management/skills/senior-pm/scripts/risk_matrix_analyzer.py active_risks.json

# Resource utilization
echo ""
echo "Team Capacity:"
python ../../project-management/skills/senior-pm/scripts/resource_capacity_planner.py team_data.json
```

### Example 2: Sprint Retrospective Pipeline

```bash
#!/bin/bash
# retro-pipeline.sh - End-of-sprint analysis pipeline

SPRINT_NUM=$1
echo "Sprint $SPRINT_NUM Retrospective Pipeline"
echo "=========================================="

# Step 1: Score sprint health
echo ""
echo "1. Sprint Health Score:"
python ../../project-management/skills/scrum-master/scripts/sprint_health_scorer.py sprint_${SPRINT_NUM}.json > sprint_health.txt
cat sprint_health.txt

# Step 2: Analyze velocity trend
echo ""
echo "2. Velocity Analysis:"
python ../../project-management/skills/scrum-master/scripts/velocity_analyzer.py velocity_history.json > velocity.txt
cat velocity.txt

# Step 3: Process retro notes
echo ""
echo "3. Retrospective Themes:"
python ../../project-management/skills/scrum-master/scripts/retrospective_analyzer.py retro_sprint_${SPRINT_NUM}.json > retro_analysis.txt
cat retro_analysis.txt

echo ""
echo "Pipeline complete. Review outputs above for retro facilitation."
```

### Example 3: Portfolio Dashboard Generation

```bash
#!/bin/bash
# portfolio-dashboard.sh - Monthly executive portfolio review

MONTH=$(date +%Y-%m)
echo "Portfolio Dashboard - $MONTH"
echo "================================"

# Project health across portfolio
echo ""
echo "Project Health (All Active):"
python ../../project-management/skills/senior-pm/scripts/project_health_dashboard.py portfolio_$MONTH.json > dashboard.txt
cat dashboard.txt

# Risk heatmap
echo ""
echo "Risk Exposure Summary:"
python ../../project-management/skills/senior-pm/scripts/risk_matrix_analyzer.py risks_$MONTH.json > risks.txt
cat risks.txt

# Resource forecast
echo ""
echo "Resource Utilization:"
python ../../project-management/skills/senior-pm/scripts/resource_capacity_planner.py resources_$MONTH.json > capacity.txt
cat capacity.txt

echo ""
echo "Dashboard generated. Use executive_report_template.md to assemble final report."
echo "Template: ../../project-management/skills/senior-pm/assets/executive_report_template.md"
```
