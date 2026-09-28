<!-- Moved verbatim from cs-ux-researcher/SKILL.md, the
     'skill-integration' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Skill Integration

**Primary Skill:** `../ux-researcher-designer`

### All Orchestrated Skills

| # | Skill | Location | Primary Tool |
|---|-------|----------|-------------|
| 1 | UX Researcher & Designer | `../ux-researcher-designer` | persona_generator.py |
| 2 | Product Manager Toolkit | `../product-manager-toolkit` | customer_interview_analyzer.py |
| 3 | UI Design System | `../ui-design-system` | design_token_generator.py |

### Python Tools

1. **Persona Generator**
   - **Purpose:** Create data-driven user personas from research inputs including demographics, goals, pain points, and behavioral patterns
   - **Path:** `../ux-researcher-designer/scripts/persona_generator.py`
   - **Usage:** `python ../../product-team/skills/ux-researcher-designer/scripts/persona_generator.py research-data.json`
   - **Features:** Multiple persona generation, behavioral segmentation, needs hierarchy mapping, empathy map creation
   - **Use Cases:** Persona development, user segmentation, design alignment, stakeholder communication

2. **Customer Interview Analyzer**
   - **Purpose:** NLP-based analysis of interview transcripts to extract pain points, feature requests, themes, and sentiment
   - **Path:** `../product-manager-toolkit/scripts/customer_interview_analyzer.py`
   - **Usage:** `python ../../product-team/skills/product-manager-toolkit/scripts/customer_interview_analyzer.py interview.txt`
   - **Features:** Pain point extraction with severity scoring, feature request identification, jobs-to-be-done patterns, theme clustering, key quote extraction
   - **Use Cases:** Interview synthesis, discovery validation, problem prioritization, insight aggregation

3. **Design Token Generator**
   - **Purpose:** Generate design tokens for consistent UI implementation across platforms
   - **Path:** `../ui-design-system/scripts/design_token_generator.py`
   - **Usage:** `python ../../product-team/skills/ui-design-system/scripts/design_token_generator.py theme.json`
   - **Use Cases:** Research-informed design system updates, accessibility token adjustments

### Knowledge Bases

1. **Persona Methodology**
   - **Location:** `../ux-researcher-designer/references/persona-methodology.md`
   - **Content:** Research-backed persona creation methodology, data collection strategies, validation approaches
   - **Use Case:** Methodological guidance for persona projects

2. **Example Personas**
   - **Location:** `../ux-researcher-designer/references/example-personas.md`
   - **Content:** Sample persona documents with demographics, goals, pain points, behaviors, scenarios
   - **Use Case:** Persona format reference, team training

3. **Journey Mapping Guide**
   - **Location:** `../ux-researcher-designer/references/journey-mapping-guide.md`
   - **Content:** Customer journey mapping methodology, touchpoint analysis, emotion mapping, opportunity identification
   - **Use Case:** Journey map creation, experience design, service design

4. **Usability Testing Frameworks**
   - **Location:** `../ux-researcher-designer/references/usability-testing-frameworks.md`
   - **Content:** Test planning, task design, analysis methods, severity ratings, reporting formats
   - **Use Case:** Usability study design, prototype validation, UX evaluation

5. **Component Architecture**
   - **Location:** `../ui-design-system/references/component-architecture.md`
   - **Content:** Component hierarchy, atomic design patterns, composition strategies
   - **Use Case:** Research-to-design translation, component recommendations

6. **Developer Handoff**
   - **Location:** `../ui-design-system/references/developer-handoff.md`
   - **Content:** Design-to-dev handoff process, specification formats, asset delivery
   - **Use Case:** Translating research findings into implementation specs

### Templates

1. **Research Plan Template**
   - **Location:** `../ux-researcher-designer/assets/research_plan_template.md`
   - **Use Case:** Structuring research studies with methodology, participants, and analysis plan

2. **Design System Documentation Template**
   - **Location:** `../ui-design-system/assets/design_system_doc_template.md`
   - **Use Case:** Documenting research-informed design system decisions
