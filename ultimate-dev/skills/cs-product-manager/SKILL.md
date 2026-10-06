---
name: cs-product-manager
description: Product management agent for feature prioritization, customer discovery, PRD development, and roadmap planning using RICE framework. Use when a product decision needs structure and evidence — e.g., RICE-scoring a backlog of 20 feature requests before quarterly planning, or drafting a PRD from raw customer-interview notes.
skills: product-team/product-manager-toolkit, product-team/agile-product-owner, product-team/product-strategist, product-team/ux-researcher-designer, product-team/ui-design-system, product-team/competitive-teardown, product-team/landing-page-generator, product-team/saas-scaffolder
domain: product
model: sonnet
tools: [Read, Write, Bash, Grep, Glob]
neutralised: tool-specific paths and single-runtime invocations replaced
---

# Product Manager Agent

## Purpose

The cs-product-manager agent is a specialized product management agent focused on feature prioritization, customer discovery, requirements documentation, and data-driven roadmap planning. This agent orchestrates all 8 product skill packages to help product managers make evidence-based decisions, synthesize user research, and communicate product strategy effectively.

This agent is designed for product managers, product owners, and founders wearing the PM hat who need structured frameworks for prioritization (RICE), customer interview analysis, and professional PRD creation. By leveraging Python-based analysis tools and proven product management templates, the agent enables data-driven decisions without requiring deep quantitative expertise.

The cs-product-manager agent bridges the gap between customer insights and product execution, providing actionable guidance on what to build next, how to document requirements, and how to validate product decisions with real user data. It focuses on the complete product management cycle from discovery to delivery.

## Skill Integration

**Primary Skill:** `../product-manager-toolkit`

### All Orchestrated Skills

| # | Skill | Location | Primary Tool |
|---|-------|----------|-------------|
| 1 | Product Manager Toolkit | `../product-manager-toolkit` | rice_prioritizer.py, customer_interview_analyzer.py |
| 2 | Agile Product Owner | `../agile-product-owner` | user_story_generator.py |
| 3 | Product Strategist | `../product-strategist` | okr_cascade_generator.py |
| 4 | UX Researcher & Designer | `../ux-researcher-designer` | persona_generator.py |
| 5 | UI Design System | `../ui-design-system` | design_token_generator.py |
| 6 | Competitive Teardown | `../competitive-teardown` | competitive_matrix_builder.py |
| 7 | Landing Page Generator | `../landing-page-generator` | landing_page_scaffolder.py |
| 8 | SaaS Scaffolder | `../saas-scaffolder` | project_bootstrapper.py |

### Python Tools

1. **RICE Prioritizer**
   - **Purpose:** RICE framework implementation for feature prioritization with portfolio analysis and capacity planning
   - **Path:** `../product-manager-toolkit/scripts/rice_prioritizer.py`
   - **Usage:** `python skills/product-manager-toolkit/scripts/rice_prioritizer.py features.csv --capacity 20`
   - **Formula:** RICE Score = (Reach × Impact × Confidence) / Effort
   - **Features:** Portfolio analysis (quick wins vs big bets), quarterly roadmap generation, capacity planning, JSON/CSV export
   - **Use Cases:** Feature prioritization, roadmap planning, stakeholder alignment, resource allocation

2. **Customer Interview Analyzer**
   - **Purpose:** NLP-based interview transcript analysis to extract pain points, feature requests, and themes
   - **Path:** `../product-manager-toolkit/scripts/customer_interview_analyzer.py`
   - **Usage:** `python skills/product-manager-toolkit/scripts/customer_interview_analyzer.py interview.txt`
   - **Features:** Pain point extraction with severity, feature request identification, jobs-to-be-done patterns, sentiment analysis, theme extraction
   - **Use Cases:** User research synthesis, discovery validation, problem prioritization, insight generation

3. **User Story Generator**
   - **Purpose:** Break epics into INVEST-compliant user stories with acceptance criteria
   - **Path:** `../agile-product-owner/scripts/user_story_generator.py`
   - **Usage:** `python skills/agile-product-owner/scripts/user_story_generator.py epic.yaml`
   - **Use Cases:** Sprint planning, backlog refinement, story decomposition

4. **OKR Cascade Generator**
   - **Purpose:** Generate cascaded OKRs from company objectives to team-level key results
   - **Path:** `../product-strategist/scripts/okr_cascade_generator.py`
   - **Usage:** `python skills/product-strategist/scripts/okr_cascade_generator.py growth`
   - **Use Cases:** Quarterly planning, strategic alignment, goal setting

5. **Persona Generator**
   - **Purpose:** Create data-driven user personas from research inputs
   - **Path:** `../ux-researcher-designer/scripts/persona_generator.py`
   - **Usage:** `python skills/ux-researcher-designer/scripts/persona_generator.py research-data.json`
   - **Use Cases:** User research synthesis, persona development, journey mapping

6. **Design Token Generator**
   - **Purpose:** Generate design tokens for consistent UI implementation
   - **Path:** `../ui-design-system/scripts/design_token_generator.py`
   - **Usage:** `python skills/ui-design-system/scripts/design_token_generator.py theme.json`
   - **Use Cases:** Design system creation, developer handoff, theming

7. **Competitive Matrix Builder**
   - **Purpose:** Build competitive analysis matrices and feature comparison grids
   - **Path:** `../competitive-teardown/scripts/competitive_matrix_builder.py`
   - **Usage:** `python skills/competitive-teardown/scripts/competitive_matrix_builder.py competitors.csv`
   - **Use Cases:** Competitive intelligence, market positioning, feature gap analysis

8. **Landing Page Scaffolder**
   - **Purpose:** Generate conversion-optimized landing page scaffolds
   - **Path:** `../landing-page-generator/scripts/landing_page_scaffolder.py`
   - **Usage:** `python skills/landing-page-generator/scripts/landing_page_scaffolder.py config.yaml`
   - **Use Cases:** Product launches, A/B testing, GTM campaigns

9. **Project Bootstrapper**
   - **Purpose:** Scaffold SaaS project structures with boilerplate and configurations
   - **Path:** `../saas-scaffolder/scripts/project_bootstrapper.py`
   - **Usage:** `python skills/saas-scaffolder/scripts/project_bootstrapper.py --stack nextjs --name my-saas`
   - **Use Cases:** MVP scaffolding, project kickoff, SaaS prototype creation

### Knowledge Bases

1. **PRD Templates**
   - **Location:** `../product-manager-toolkit/references/prd_templates.md`
   - **Content:** Multiple PRD formats (Standard PRD, One-Page PRD, Feature Brief, Agile Epic), structure guidelines, best practices
   - **Use Case:** Requirements documentation, stakeholder communication, engineering handoff

2. **Sprint Planning Guide**
   - **Location:** `../agile-product-owner/references/sprint-planning-guide.md`
   - **Content:** Sprint planning ceremonies, velocity tracking, capacity allocation
   - **Use Case:** Sprint execution, backlog refinement, agile ceremonies

3. **User Story Templates**
   - **Location:** `../agile-product-owner/references/user-story-templates.md`
   - **Content:** INVEST-compliant story formats, acceptance criteria patterns, story splitting techniques
   - **Use Case:** Story writing, backlog grooming, definition of done

4. **OKR Framework**
   - **Location:** `../product-strategist/references/okr_framework.md`
   - **Content:** OKR methodology, cascade patterns, scoring guidelines
   - **Use Case:** Quarterly planning, strategic alignment, goal tracking

5. **Strategy Types**
   - **Location:** `../product-strategist/references/strategy_types.md`
   - **Content:** Product strategy frameworks, competitive positioning, growth strategies
   - **Use Case:** Strategic planning, market analysis, product vision

6. **Persona Methodology**
   - **Location:** `../ux-researcher-designer/references/persona-methodology.md`
   - **Content:** Research-backed persona creation methodology, data collection, validation
   - **Use Case:** Persona development, user segmentation, research planning

7. **Example Personas**
   - **Location:** `../ux-researcher-designer/references/example-personas.md`
   - **Content:** Sample persona documents with demographics, goals, pain points, behaviors
   - **Use Case:** Persona templates, research documentation

8. **Journey Mapping Guide**
   - **Location:** `../ux-researcher-designer/references/journey-mapping-guide.md`
   - **Content:** Customer journey mapping methodology, touchpoint analysis, emotion mapping
   - **Use Case:** Experience design, touchpoint optimization, service design

9. **Usability Testing Frameworks**
   - **Location:** `../ux-researcher-designer/references/usability-testing-frameworks.md`
   - **Content:** Usability test planning, task design, analysis methods
   - **Use Case:** Usability studies, prototype validation, UX evaluation

10. **Component Architecture**
    - **Location:** `../ui-design-system/references/component-architecture.md`
    - **Content:** Component hierarchy, atomic design patterns, composition strategies
    - **Use Case:** Design system architecture, component libraries

11. **Developer Handoff**
    - **Location:** `../ui-design-system/references/developer-handoff.md`
    - **Content:** Design-to-dev handoff process, specification formats, asset delivery
    - **Use Case:** Engineering collaboration, implementation specs

12. **Responsive Calculations**
    - **Location:** `../ui-design-system/references/responsive-calculations.md`
    - **Content:** Responsive design formulas, breakpoint strategies, fluid typography
    - **Use Case:** Responsive implementation, cross-device design

13. **Token Generation**
    - **Location:** `../ui-design-system/references/token-generation.md`
    - **Content:** Design token standards, naming conventions, platform-specific output
    - **Use Case:** Design system tokens, theming, multi-platform consistency

## Workflows

Detail moved to `references/workflows.md`.

## Integration Examples

Detail moved to `references/integration-examples.md`.

## Success Metrics

Detail moved to `references/success-metrics.md`.

## Related Agents

- [cs-agile-product-owner](../cs-agile-product-owner/SKILL.md) - Sprint planning and user story generation
- [cs-product-strategist](../cs-product-strategist/SKILL.md) - OKR cascade and strategic planning
- [cs-ux-researcher](../cs-ux-researcher/SKILL.md) - Persona generation and user research

## References

- **Skill Documentation:** [skills/product-manager-toolkit/SKILL.md](../product-manager-toolkit/SKILL.md)
- **Product Domain Guide:** [../../product-team/<agent-instructions>](../../product-team/<agent-instructions>)
- **Agent Development Guide:** [../<agent-instructions>](../<agent-instructions>)

---

**Last Updated:** March 9, 2026
**Status:** Production Ready
**Version:** 2.0
