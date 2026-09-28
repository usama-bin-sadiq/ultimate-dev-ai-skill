<!-- Moved verbatim from cs-project-manager/SKILL.md, the
     'skill-integration' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Skill Integration

### Senior PM

**Skill Location:** `../senior-pm`

**Python Tools:**

1. **Project Health Dashboard**
   - **Purpose:** Generate portfolio-level health dashboard with RAG status across all active projects
   - **Path:** `../senior-pm/scripts/project_health_dashboard.py`
   - **Usage:** `python ../../project-management/skills/senior-pm/scripts/project_health_dashboard.py sample_project_data.json`
   - **Features:** Schedule variance, budget tracking, risk exposure, milestone status, RAG indicators

2. **Risk Matrix Analyzer**
   - **Purpose:** Quantitative risk analysis with probability-impact matrices and Expected Monetary Value (EMV)
   - **Path:** `../senior-pm/scripts/risk_matrix_analyzer.py`
   - **Usage:** `python ../../project-management/skills/senior-pm/scripts/risk_matrix_analyzer.py risks.json`
   - **Features:** Risk scoring, heat map generation, mitigation tracking, EMV calculation

3. **Resource Capacity Planner**
   - **Purpose:** Team resource allocation and capacity forecasting across sprints and projects
   - **Path:** `../senior-pm/scripts/resource_capacity_planner.py`
   - **Usage:** `python ../../project-management/skills/senior-pm/scripts/resource_capacity_planner.py team_data.json`
   - **Features:** Utilization analysis, over-allocation detection, capacity forecasting, cross-project balancing

**Knowledge Bases:**

- `../senior-pm/references/portfolio-prioritization-models.md` -- WSJF, MoSCoW, Cost of Delay, portfolio scoring frameworks
- `../senior-pm/references/risk-management-framework.md` -- Risk identification, qualitative/quantitative analysis, response strategies
- `../senior-pm/references/portfolio-kpis.md` -- KPI definitions, tracking cadences, executive reporting metrics

**Templates:**

- `../senior-pm/assets/executive_report_template.md` -- Executive status report with RAG, risks, decisions needed
- `../senior-pm/assets/project_charter_template.md` -- Project charter with scope, objectives, constraints, stakeholders
- `../senior-pm/assets/raci_matrix_template.md` -- Responsibility assignment matrix for cross-functional teams

### Scrum Master

**Skill Location:** `../scrum-master`

**Python Tools:**

1. **Sprint Health Scorer**
   - **Purpose:** Quantitative sprint health assessment across scope, velocity, quality, and team morale
   - **Path:** `../scrum-master/scripts/sprint_health_scorer.py`
   - **Usage:** `python ../../project-management/skills/scrum-master/scripts/sprint_health_scorer.py sample_sprint_data.json`
   - **Features:** Multi-dimensional scoring (0-100), trend analysis, health indicators, actionable recommendations

2. **Velocity Analyzer**
   - **Purpose:** Historical velocity analysis with forecasting and confidence intervals
   - **Path:** `../scrum-master/scripts/velocity_analyzer.py`
   - **Usage:** `python ../../project-management/skills/scrum-master/scripts/velocity_analyzer.py sprint_history.json`
   - **Features:** Rolling averages, standard deviation, sprint-over-sprint trends, capacity prediction

3. **Retrospective Analyzer**
   - **Purpose:** Structured retrospective analysis with action item tracking and theme extraction
   - **Path:** `../scrum-master/scripts/retrospective_analyzer.py`
   - **Usage:** `python ../../project-management/skills/scrum-master/scripts/retrospective_analyzer.py retro_notes.json`
   - **Features:** Theme clustering, sentiment analysis, action item extraction, trend tracking across sprints

**Knowledge Bases:**

- `../scrum-master/references/retro-formats.md` -- Start/Stop/Continue, 4Ls, Sailboat, Mad/Sad/Glad, Starfish formats
- `../scrum-master/references/team-dynamics-framework.md` -- Tuckman stages, psychological safety, conflict resolution
- `../scrum-master/references/velocity-forecasting-guide.md` -- Monte Carlo simulation, confidence ranges, capacity planning

**Templates:**

- `../scrum-master/assets/sprint_report_template.md` -- Sprint review report with burndown, velocity, demo notes
- `../scrum-master/assets/team_health_check_template.md` -- Spotify-style team health check across 8 dimensions

### Jira Expert

**Skill Location:** `../jira-expert`

**Knowledge Bases:**

- `../jira-expert/references/jql-examples.md` -- JQL query patterns for backlog grooming, sprint reporting, SLA tracking
- `../jira-expert/references/automation-examples.md` -- Jira automation rule templates for common workflows
- `../jira-expert/references/AUTOMATION.md` -- Comprehensive automation guide with triggers, conditions, actions
- `../jira-expert/references/WORKFLOWS.md` -- Workflow design patterns, transition rules, validators, post-functions

### Confluence Expert

**Skill Location:** `../confluence-expert`

**Knowledge Bases:**

- `../confluence-expert/references/templates.md` -- Page templates for sprint plans, meeting notes, decision logs, architecture docs

### Atlassian Admin

**Skill Location:** `../atlassian-admin`

Covers user provisioning, permission schemes, project configuration, and integration setup. No scripts or references yet -- relies on SKILL.md workflows.

### Atlassian Templates

**Skill Location:** `../atlassian-templates`

Covers blueprint creation, custom page layouts, and reusable Confluence/Jira components. No scripts or references yet -- relies on SKILL.md workflows.
