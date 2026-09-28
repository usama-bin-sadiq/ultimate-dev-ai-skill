<!-- Moved verbatim from cs-project-manager/SKILL.md, the
     'workflows' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Workflows

### Workflow 1: Sprint Planning and Execution

**Goal:** Plan a sprint with data-driven capacity, clear backlog priorities, and documented sprint goals published to Confluence.

**Steps:**

1. **Analyze Velocity History** - Review past sprint performance to set realistic capacity:
   ```bash
   python ../../project-management/skills/scrum-master/scripts/velocity_analyzer.py sprint_history.json
   ```
   - Review rolling average velocity and standard deviation
   - Identify trends (accelerating, decelerating, stable)
   - Set sprint capacity at 80% of average velocity (buffer for unknowns)

2. **Query Backlog via JQL** - Use jira-expert JQL patterns to pull prioritized candidates:
   - Reference: `../jira-expert/references/jql-examples.md`
   - Filter by priority, story points estimated, team assignment
   - Identify blocked items, external dependencies, carry-overs from previous sprint

3. **Check Resource Availability** - Verify team capacity for the sprint window:
   ```bash
   python ../../project-management/skills/senior-pm/scripts/resource_capacity_planner.py team_data.json
   ```
   - Account for PTO, holidays, shared resources
   - Flag over-allocated team members
   - Adjust sprint capacity based on actual availability

4. **Select Sprint Backlog** - Commit items within capacity:
   - Apply WSJF or priority-based selection (ref: `../senior-pm/references/portfolio-prioritization-models.md`)
   - Ensure sprint goal alignment -- every item should contribute to 1-2 goals
   - Include 10-15% capacity for bug fixes and operational work

5. **Document Sprint Plan** - Create Confluence sprint plan page:
   - Use template from `../confluence-expert/references/templates.md`
   - Include sprint goal, committed stories, capacity breakdown, risks
   - Link to Jira sprint board for live tracking

6. **Set Up Sprint Tracking** - Configure dashboards and automation:
   - Create burndown/burnup dashboard (ref: `../jira-expert/references/AUTOMATION.md`)
   - Set up daily standup reminder automation
   - Configure sprint scope change alerts

**Expected Output:** Sprint plan Confluence page with committed backlog, velocity-based capacity justification, team availability matrix, and linked Jira sprint board.

**Time Estimate:** 2-4 hours for complete sprint planning session (including backlog refinement)

**Example:**
```bash
# Full sprint planning workflow
python ../../project-management/skills/scrum-master/scripts/velocity_analyzer.py sprint_history.json > velocity_report.txt
python ../../project-management/skills/senior-pm/scripts/resource_capacity_planner.py team_data.json > capacity_report.txt
cat velocity_report.txt
cat capacity_report.txt
# Use velocity average and capacity data to commit sprint items
```

### Workflow 2: Portfolio Health Review

**Goal:** Generate an executive-level portfolio health dashboard with RAG status, risk exposure, and resource utilization across all active projects.

**Steps:**

1. **Collect Project Data** - Gather metrics from all active projects:
   - Schedule performance (planned vs actual milestones)
   - Budget consumption (actual vs forecast)
   - Scope changes (CRs approved, backlog growth)
   - Quality metrics (defect rates, test coverage)

2. **Generate Health Dashboard** - Run project health analysis:
   ```bash
   python ../../project-management/skills/senior-pm/scripts/project_health_dashboard.py portfolio_data.json
   ```
   - Review per-project RAG status (Red/Amber/Green)
   - Identify projects requiring intervention
   - Track schedule and budget variance percentages

3. **Analyze Risk Exposure** - Quantify portfolio-level risk:
   ```bash
   python ../../project-management/skills/senior-pm/scripts/risk_matrix_analyzer.py portfolio_risks.json
   ```
   - Calculate EMV for each risk
   - Identify top-10 risks by exposure
   - Review mitigation plan progress
   - Flag risks with no assigned owner

4. **Review Resource Utilization** - Check cross-project allocation:
   ```bash
   python ../../project-management/skills/senior-pm/scripts/resource_capacity_planner.py all_teams.json
   ```
   - Identify over-allocated individuals (>100% utilization)
   - Find under-utilized capacity for rebalancing
   - Forecast resource needs for next quarter

5. **Prepare Executive Report** - Assemble findings into report:
   - Use template: `../senior-pm/assets/executive_report_template.md`
   - Include RAG summary, risk heatmap, resource utilization chart
   - Highlight decisions needed from leadership
   - Provide recommendations with supporting data

6. **Publish to Confluence** - Create executive dashboard page:
   - Reference KPI definitions from `../senior-pm/references/portfolio-kpis.md`
   - Embed Jira macros for live data
   - Set up weekly refresh cadence

**Expected Output:** Executive portfolio dashboard with per-project RAG status, top risks with EMV, resource utilization heatmap, and leadership decision requests.

**Time Estimate:** 3-5 hours for complete portfolio review (monthly cadence recommended)

**Example:**
```bash
# Portfolio health review automation
python ../../project-management/skills/senior-pm/scripts/project_health_dashboard.py portfolio_data.json > health_dashboard.txt
python ../../project-management/skills/senior-pm/scripts/risk_matrix_analyzer.py portfolio_risks.json > risk_report.txt
python ../../project-management/skills/senior-pm/scripts/resource_capacity_planner.py all_teams.json > resource_report.txt
cat health_dashboard.txt
cat risk_report.txt
cat resource_report.txt
```

### Workflow 3: Retrospective and Continuous Improvement

**Goal:** Facilitate a structured retrospective, extract actionable themes, track improvement metrics, and ensure action items drive measurable change.

**Steps:**

1. **Gather Sprint Metrics** - Collect quantitative data before the retro:
   ```bash
   python ../../project-management/skills/scrum-master/scripts/sprint_health_scorer.py sprint_data.json
   ```
   - Review sprint health score (0-100)
   - Identify scoring dimensions that dropped (scope, velocity, quality, morale)
   - Compare against previous sprint scores for trend analysis

2. **Select Retro Format** - Choose format based on team needs:
   - Reference: `../scrum-master/references/retro-formats.md`
   - **Start/Stop/Continue**: General-purpose, good for new teams
   - **4Ls (Liked/Learned/Lacked/Longed For)**: Focuses on learning and growth
   - **Sailboat**: Visual metaphor for anchors (blockers) and wind (accelerators)
   - **Mad/Sad/Glad**: Emotion-focused, good for addressing team morale
   - **Starfish**: Five categories for nuanced feedback

3. **Facilitate Retrospective** - Run the session:
   - Present sprint metrics as context (not judgment)
   - Time-box each section (5 min brainstorm, 10 min discuss, 5 min vote)
   - Use dot voting to prioritize discussion topics
   - Reference team dynamics from `../scrum-master/references/team-dynamics-framework.md`

4. **Analyze Retro Output** - Extract structured insights:
   ```bash
   python ../../project-management/skills/scrum-master/scripts/retrospective_analyzer.py retro_notes.json
   ```
   - Identify recurring themes across sprints
   - Cluster related items into improvement areas
   - Track action item completion from previous retros

5. **Create Action Items** - Convert insights to trackable work:
   - Limit to 2-3 action items per sprint (avoid overcommitment)
   - Assign clear owners and due dates
   - Create Jira tickets for process improvements
   - Add action items to next sprint backlog

6. **Document in Confluence** - Publish retro summary:
   - Use sprint report template: `../scrum-master/assets/sprint_report_template.md`
   - Include sprint health score, retro themes, action items, metrics trends
   - Link to previous retro pages for longitudinal tracking

7. **Track Improvement Over Time** - Measure continuous improvement:
   - Compare sprint health scores quarter-over-quarter
   - Track action item completion rate (target: >80%)
   - Monitor velocity stability as proxy for process maturity

**Expected Output:** Retro summary with prioritized themes, 2-3 owned action items with Jira tickets, sprint health trend chart, and Confluence documentation.

**Time Estimate:** 1.5-2 hours (30 min prep + 60 min retro + 30 min documentation)

**Example:**
```bash
# Pre-retro data collection
python ../../project-management/skills/scrum-master/scripts/sprint_health_scorer.py sprint_data.json > health_score.txt
python ../../project-management/skills/scrum-master/scripts/velocity_analyzer.py sprint_history.json > velocity_trend.txt
cat health_score.txt
# Use health score insights to guide retro discussion
python ../../project-management/skills/scrum-master/scripts/retrospective_analyzer.py retro_notes.json > retro_analysis.txt
cat retro_analysis.txt
```

### Workflow 4: Jira/Confluence Setup for New Teams

**Goal:** Stand up a complete Atlassian environment for a new team including Jira project, workflows, automation, Confluence space, and templates.

**Steps:**

1. **Define Team Process** - Map the team's delivery methodology:
   - Scrum vs Kanban vs Scrumban
   - Issue types needed (Epic, Story, Task, Bug, Spike)
   - Custom fields required (team, component, environment)
   - Workflow states matching actual process

2. **Create Jira Project** - Set up project structure:
   - Select project template (Scrum board, Kanban board, Company-managed)
   - Configure issue type scheme with required types
   - Set up components and versions
   - Define priority scheme and SLA targets

3. **Design Workflows** - Build workflows matching team process:
   - Reference: `../jira-expert/references/WORKFLOWS.md`
   - Map states: Backlog > Ready > In Progress > Review > QA > Done
   - Add transitions with conditions (e.g., assignee required for In Progress)
   - Configure validators (e.g., story points required before Done)
   - Set up post-functions (e.g., auto-assign reviewer, notify channel)

4. **Configure Automation** - Set up time-saving automation rules:
   - Reference: `../jira-expert/references/AUTOMATION.md`
   - Examples from: `../jira-expert/references/automation-examples.md`
   - Auto-transition: Move to In Progress when branch created
   - Auto-assign: Rotate assignments based on workload
   - Notifications: Slack alerts for blocked items, SLA breaches
   - Cleanup: Auto-close stale items after 30 days

5. **Set Up Confluence Space** - Create team knowledge base:
   - Reference: `../confluence-expert/references/templates.md`
   - Create space with standard page hierarchy:
     - Home (team overview, quick links)
     - Sprint Plans (per-sprint documentation)
     - Meeting Notes (standup, planning, retro)
     - Decision Log (ADRs, trade-off decisions)
     - Runbooks (operational procedures)
   - Link Confluence space to Jira project

6. **Create Dashboards** - Build visibility for team and stakeholders:
   - Sprint board with swimlanes by assignee
   - Burndown/burnup chart gadget
   - Velocity chart for historical tracking
   - SLA compliance tracker
   - Use JQL patterns from `../jira-expert/references/jql-examples.md`

7. **Onboard Team** - Walk team through the setup:
   - Document workflow rules and why they exist
   - Create quick-reference guide for common Jira operations
   - Run a pilot sprint to validate configuration
   - Iterate on feedback within first 2 sprints

**Expected Output:** Fully configured Jira project with custom workflows and automation, Confluence space with page hierarchy and templates, team dashboards, and onboarding documentation.

**Time Estimate:** 1-2 days for complete environment setup (excluding pilot sprint)
