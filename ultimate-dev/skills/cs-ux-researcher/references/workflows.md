<!-- Moved verbatim from cs-ux-researcher/SKILL.md, the
     'workflows' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Workflows

### Workflow 1: Research Plan Creation

**Goal:** Design a rigorous research study that answers specific product questions with appropriate methodology

**Steps:**
1. **Define Research Questions** - Identify what needs to be learned:
   - What are the top 3-5 questions stakeholders need answered?
   - What do we already know from existing data?
   - What assumptions need validation?
   - What decisions will this research inform?

2. **Select Methodology** - Choose the right approach:
   ```bash
   # Review usability testing frameworks for method selection
   cat ../../product-team/skills/ux-researcher-designer/references/usability-testing-frameworks.md
   ```
   - **Exploratory** (interviews, contextual inquiry): When learning about problem space
   - **Evaluative** (usability testing, A/B tests): When validating solutions
   - **Generative** (diary studies, card sorting): When discovering new opportunities
   - **Quantitative** (surveys, analytics): When measuring scale and significance

3. **Define Participants** - Screen for the right users:
   - Target persona(s) to recruit
   - Screening criteria (role, experience, usage patterns)
   - Sample size justification
   - Recruitment channels and incentives

4. **Create Study Materials** - Prepare research instruments:
   ```bash
   # Use the research plan template
   cat ../../product-team/skills/ux-researcher-designer/assets/research_plan_template.md
   ```
   - Interview guide or test script
   - Task scenarios (for usability tests)
   - Consent form and recording permissions
   - Analysis framework and coding scheme

5. **Align with Stakeholders** - Get buy-in:
   - Share research plan with product and engineering leads
   - Invite stakeholders to observe sessions
   - Set expectations for timeline and deliverables
   - Define how findings will be actioned

**Expected Output:** Complete research plan with questions, methodology, participant criteria, study materials, timeline, and stakeholder alignment

**Time Estimate:** 2-3 days for plan creation

**Example:**
```bash
# Create research plan from template
cp ../../product-team/skills/ux-researcher-designer/assets/research_plan_template.md onboarding-research-plan.md

# Review methodology options
cat ../../product-team/skills/ux-researcher-designer/references/usability-testing-frameworks.md

# Review persona methodology for participant criteria
cat ../../product-team/skills/ux-researcher-designer/references/persona-methodology.md
```

### Workflow 2: Persona Generation

**Goal:** Create data-driven user personas from research data that align product teams around real user needs

**Steps:**
1. **Gather Research Data** - Collect inputs from multiple sources:
   - Interview transcripts (analyzed for themes)
   - Survey responses (demographic and behavioral data)
   - Analytics data (usage patterns, feature adoption)
   - Support tickets (common issues, pain points)
   - Sales call notes (buyer motivations, objections)

2. **Analyze Interview Data** - Extract structured insights:
   ```bash
   # Analyze each interview transcript
   python ../../product-team/skills/product-manager-toolkit/scripts/customer_interview_analyzer.py interview-001.txt > insights-001.json
   python ../../product-team/skills/product-manager-toolkit/scripts/customer_interview_analyzer.py interview-002.txt > insights-002.json
   python ../../product-team/skills/product-manager-toolkit/scripts/customer_interview_analyzer.py interview-003.txt > insights-003.json
   ```

3. **Identify Behavioral Segments** - Cluster users by:
   - Goals and motivations (what they are trying to achieve)
   - Behaviors and workflows (how they work today)
   - Pain points and frustrations (what blocks them)
   - Technical sophistication (how they interact with tools)
   - Decision-making factors (what drives their choices)

4. **Generate Personas** - Create data-backed personas:
   ```bash
   # Generate personas from aggregated research
   python ../../product-team/skills/ux-researcher-designer/scripts/persona_generator.py research-data.json
   ```

5. **Validate Personas** - Ensure accuracy:
   - Cross-reference with quantitative data (segment sizes)
   - Review with customer-facing teams (sales, support)
   - Test with stakeholders who interact with users
   - Confirm each persona represents a meaningful segment

6. **Socialize Personas** - Make personas actionable:
   ```bash
   # Review example personas for format guidance
   cat ../../product-team/skills/ux-researcher-designer/references/example-personas.md
   ```
   - Create one-page persona cards for team walls/wikis
   - Present to product, engineering, and design teams
   - Map personas to product areas and features
   - Reference personas in PRDs and design briefs

**Expected Output:** 3-5 validated user personas with demographics, goals, pain points, behaviors, and scenarios

**Time Estimate:** 1-2 weeks (data collection through socialization)

**Example:**
```bash
# Full persona generation workflow
echo "Persona Generation Workflow"
echo "==========================="

# Step 1: Analyze interviews
for f in interviews/*.txt; do
  base=$(basename "$f" .txt)
  python ../../product-team/skills/product-manager-toolkit/scripts/customer_interview_analyzer.py "$f" json > "insights-$base.json"
  echo "Analyzed: $f"
done

# Step 2: Review persona methodology
cat ../../product-team/skills/ux-researcher-designer/references/persona-methodology.md

# Step 3: Generate personas
python ../../product-team/skills/ux-researcher-designer/scripts/persona_generator.py research-data.json

# Step 4: Review example format
cat ../../product-team/skills/ux-researcher-designer/references/example-personas.md
```

### Workflow 3: Journey Mapping

**Goal:** Map the complete user journey to identify pain points, opportunities, and moments that matter

**Steps:**
1. **Define Journey Scope** - Set boundaries:
   - Which persona is this journey for?
   - What is the starting trigger?
   - What is the end state (success)?
   - What timeframe does the journey cover?

2. **Review Journey Mapping Methodology** - Understand the framework:
   ```bash
   cat ../../product-team/skills/ux-researcher-designer/references/journey-mapping-guide.md
   ```

3. **Map Journey Stages** - Identify key phases:
   - **Awareness:** How users discover the product
   - **Consideration:** How users evaluate and compare
   - **Onboarding:** First-time setup and activation
   - **Regular Use:** Core workflow and daily interactions
   - **Growth:** Expanding usage, inviting team, upgrading
   - **Advocacy:** Referring others, providing feedback

4. **Document Touchpoints** - For each stage:
   - User actions (what they do)
   - Channels (where they interact)
   - Emotions (how they feel)
   - Pain points (what frustrates them)
   - Opportunities (how we can improve)

5. **Identify Moments of Truth** - Critical experience points:
   - First-time use (aha moment)
   - First success (value realization)
   - First problem (support experience)
   - Upgrade decision (value justification)
   - Referral moment (advocacy trigger)

6. **Prioritize Opportunities** - Focus on highest-impact improvements:
   ```bash
   # Prioritize journey improvement opportunities
   cat > journey-opportunities.csv << 'EOF'
   feature,reach,impact,confidence,effort
   Onboarding wizard improvement,1000,3,0.9,3
   First-success celebration,800,2,0.7,1
   Self-service help in context,600,2,0.8,2
   Upgrade prompt optimization,400,3,0.6,2
   EOF
   python ../../product-team/skills/product-manager-toolkit/scripts/rice_prioritizer.py journey-opportunities.csv
   ```

**Expected Output:** Visual journey map with stages, touchpoints, emotions, pain points, and prioritized improvement opportunities

**Time Estimate:** 1-2 weeks for research-backed journey map

**Example:**
```bash
# Journey mapping workflow
echo "Journey Mapping - Onboarding Flow"
echo "=================================="

# Review journey mapping methodology
cat ../../product-team/skills/ux-researcher-designer/references/journey-mapping-guide.md

# Analyze relevant interview transcripts for journey insights
python ../../product-team/skills/product-manager-toolkit/scripts/customer_interview_analyzer.py onboarding-interview-01.txt
python ../../product-team/skills/product-manager-toolkit/scripts/customer_interview_analyzer.py onboarding-interview-02.txt

# Prioritize improvement opportunities
python ../../product-team/skills/product-manager-toolkit/scripts/rice_prioritizer.py journey-opportunities.csv
```

### Workflow 4: Usability Test Analysis

**Goal:** Conduct and analyze usability tests to evaluate design solutions and identify critical UX issues

**Steps:**
1. **Plan the Test** - Design the study:
   ```bash
   # Review usability testing frameworks
   cat ../../product-team/skills/ux-researcher-designer/references/usability-testing-frameworks.md
   ```
   - Define test objectives (what decisions will this inform)
   - Select test type (moderated/unmoderated, remote/in-person)
   - Write task scenarios (realistic, goal-oriented)
   - Set success criteria per task (completion, time, errors)

2. **Prepare Materials** - Set up the test:
   - Prototype or staging environment ready
   - Test script with introduction, tasks, and debrief questions
   - Recording tools configured
   - Note-taking template for observers
   - Use research plan template for documentation:
   ```bash
   cat ../../product-team/skills/ux-researcher-designer/assets/research_plan_template.md
   ```

3. **Conduct Sessions** - Run 5-8 sessions:
   - Follow consistent script for each participant
   - Use think-aloud protocol
   - Note task completion, errors, and verbal feedback
   - Capture quotes and emotional reactions
   - Debrief after each session

4. **Analyze Results** - Synthesize findings:
   - Calculate task success rates
   - Measure time-on-task per scenario
   - Categorize usability issues by severity:
     - **Critical:** Prevents task completion
     - **Major:** Causes significant difficulty or errors
     - **Minor:** Creates confusion but user recovers
     - **Cosmetic:** Aesthetic or minor friction
   - Identify patterns across participants

5. **Analyze Verbal Feedback** - Extract qualitative insights:
   ```bash
   # Analyze session transcripts for themes
   python ../../product-team/skills/product-manager-toolkit/scripts/customer_interview_analyzer.py usability-session-01.txt
   python ../../product-team/skills/product-manager-toolkit/scripts/customer_interview_analyzer.py usability-session-02.txt
   ```

6. **Create Report and Recommendations** - Deliver findings:
   - Executive summary (key findings in 3-5 bullets)
   - Task-by-task results with evidence
   - Prioritized issue list with severity
   - Recommended design changes
   - Highlight reel of key moments (video clips)

7. **Inform Design Iteration** - Close the loop:
   - Review findings with design team
   - Map issues to components in design system:
   ```bash
   cat ../../product-team/skills/ui-design-system/references/component-architecture.md
   ```
   - Create Jira tickets for each issue
   - Plan re-test for critical issues after fixes

**Expected Output:** Usability test report with task metrics, severity-rated issues, recommendations, and design iteration plan

**Time Estimate:** 2-3 weeks (planning through report delivery)

**Example:**
```bash
# Usability test analysis workflow
echo "Usability Test Analysis"
echo "======================="

# Review frameworks
cat ../../product-team/skills/ux-researcher-designer/references/usability-testing-frameworks.md

# Analyze each session transcript
for i in 1 2 3 4 5; do
  echo "Session $i Analysis:"
  python ../../product-team/skills/product-manager-toolkit/scripts/customer_interview_analyzer.py "usability-session-0$i.txt"
  echo ""
done

# Review component architecture for design recommendations
cat ../../product-team/skills/ui-design-system/references/component-architecture.md
```
