---
name: initiating-coverage
description: Create institutional-quality equity research initiation reports through a 5-task workflow. Tasks must be executed individually with verified prerequisites - (1) company research, (2) financial modeling, (3) valuation analysis, (4) chart generation, (5) final report assembly. Each task produces specific deliverables (markdown docs, Excel models, charts, or DOCX reports). Tasks 3-5 have dependencies on earlier tasks.
---

# Initiating Coverage

Create institutional-quality equity research initiation reports through a structured 5-task workflow. Each task must be executed separately with verified inputs.

## Overview

This skill produces comprehensive first-time coverage reports following institutional standards (JPMorgan, Goldman Sachs, Morgan Stanley format). Tasks are executed individually, each verifying prerequisites before proceeding.

**Default Font**: Times New Roman throughout all documents (unless user specifies otherwise).

---

## ⚠️ CRITICAL: One Task at a Time

Detail moved verbatim to `references/critical-one-task-at-a-time.md`. Load it when this section matters and the pointer is not enough.

## Task Selection

Select which task to execute:

| Task | Name | Prerequisites | Output |
|------|------|--------------|--------|
| **1** | Company Research | Company name/ticker | 6-8K word document |
| **2** | Financial Modeling | 10-K or financials access | Excel model (6 tabs) |
| **3** | Valuation Analysis | Financial model (Task 2) | Valuation + price target |
| **4** | Chart Generation | Tasks 1, 2, 3 + external data | 25-35 PNG/JPG charts |
| **5** | Report Assembly | ALL previous tasks (1-4) | 30-50 page DOCX report |

---

## How to Use This Skill

Detail moved verbatim to `references/how-to-use-this-skill.md`. Load it when this section matters and the pointer is not enough.

## Task 1: Company Research

**Purpose**: Research company's business, management, competitive position, industry, and risks.

**Prerequisites**: ✅ None (fully independent)
- Company name or ticker symbol

**Process**:
1. Verify company name/ticker provided
2. Load detailed instructions from references/task1-company-research.md
3. Execute qualitative research workflow
4. Deliver research document

**Output**: Company Research Document (6,000-8,000 words)
- Company overview & history
- Management bios (300-400 words × 3-4 execs)
- Products & services analysis
- Industry overview
- Competitive analysis (5-10 competitors)
- TAM sizing
- Risk assessment (8-12 risks)

**File name**: `[Company]_Research_Document_[Date].md`

**⚠️ DELIVER ONLY THIS 1 FILE. NO completion summaries, no extra documents.**

**⚠️ DO NOT TAKE SHORTCUTS:**
- ✅ Write full 6,000-8,000 words (not summaries)
- ✅ Complete 300-400 word bios for ALL 3-4 executives
- ✅ Analyze ALL 5-10 competitors thoroughly
- ✅ Cover all 8-12 risks across 4 categories
- ❌ Do not abbreviate sections to save time
- ❌ Do not skip any required sections

**Verification before proceeding**: None required for this task.

---

## Task 2: Financial Modeling

Detail moved verbatim to `references/task-2-financial-modeling.md`. Load it when this section matters and the pointer is not enough.

## Task 3: Valuation Analysis

Detail moved verbatim to `references/task-3-valuation-analysis.md`. Load it when this section matters and the pointer is not enough.

## Task 4: Chart Generation

Detail moved verbatim to `references/task-4-chart-generation.md`. Load it when this section matters and the pointer is not enough.

## Task 5: Report Assembly

Detail moved verbatim to `references/task-5-report-assembly.md`. Load it when this section matters and the pointer is not enough.

## Input Verification Protocol

### Why Input Verification Matters

Each task has strict prerequisites. Running a task without required inputs will:
- Waste time with incomplete work
- Produce low-quality outputs
- Require rework

**Always verify inputs before starting a task.**

### Verification Checklist by Task

**Task 1**: ✅ No verification needed (independent)

**Task 2**: Check historical financials available

**Task 3**: Check financial model exists and is accessible

**Task 4**: Check both model (Task 2) AND valuation (Task 3) exist

**Task 5**: Check ALL previous tasks complete (1, 2, 3, 4)

### What to Do if Verification Fails

```
IF prerequisites are missing:
1. Stop the current task
2. Identify which prerequisite task(s) need to be completed
3. Execute the missing task(s) first
4. Return to current task once prerequisites are met
```

### Example Verification Dialogue

```
User: "Use initiating-coverage, Task 5 for Tesla"

Claude: "Starting Task 5: Report Assembly for Tesla

VERIFICATION - Checking prerequisites:
- Task 1 (Company research)... ❌ NOT FOUND
- Task 2 (Financial model)... ❌ NOT FOUND
- Task 3 (Valuation)... ❌ NOT FOUND
- Task 4 (Charts)... ❌ NOT FOUND

⚠️ VERIFICATION FAILED

Task 5 requires ALL previous tasks to be complete.

To proceed:
1. Complete Task 1: Company Research
2. Complete Task 2: Financial Modeling
3. Complete Task 3: Valuation Analysis
4. Complete Task 4: Chart Generation
5. Then return to Task 5

Would you like to start with Task 1 first?"
```

---

## Task Reference Files

Detailed instructions for each task are in separate reference files to keep this skill lean:

- **references/task1-company-research.md** - Company research workflow
- **references/task2-financial-modeling.md** - Financial modeling workflow
- **references/task3-valuation.md** - Valuation methodology
  - Also see: references/valuation-methodologies.md for DCF/comps deep dive
- **references/task4-chart-generation.md** - Chart generation workflow
- **references/task5-report-assembly.md** - Report writing workflow
  - Also see: assets/report-template.md for report structure
  - Also see: assets/quality-checklist.md for quality checks

**When to load reference files**: Load ONLY the reference file associated with the specific task being performed. These files are very large - do not load multiple reference files at once. Read the appropriate task reference file at the start of the task for detailed step-by-step instructions.

---

## Reference files

These ship with the skill and are read on demand; none is needed to
use it. Each answers one question the sections above do not.

- [`references/task1-company-research.md`](references/task1-company-research.md)
- [`references/task2-financial-modeling.md`](references/task2-financial-modeling.md)
- [`references/task3-valuation.md`](references/task3-valuation.md)
- [`references/task4-chart-generation.md`](references/task4-chart-generation.md)
- [`references/task5-report-assembly.md`](references/task5-report-assembly.md)
- [
Each file below is loaded on demand, not at triage. 9 file(s):

- `references/important-notes.md` — Important Notes. <!-- Moved verbatim from initiating-coverage/SKILL.md, the
- `references/input-verification-protocol.md` — Input Verification Protocol. <!-- Moved verbatim from initiating-coverage/SKILL.md, the
- `references/overview.md` — Overview. <!-- Moved verbatim from initiating-coverage/SKILL.md, the
- `references/quality-standards.md` — Quality Standards. <!-- Moved verbatim from initiating-coverage/SKILL.md, the
- `references/reference-files.md` — Reference files. <!-- Moved verbatim from initiating-coverage/SKILL.md, the
- `references/success-criteria.md` — Success Criteria. <!-- Moved verbatim from initiating-coverage/SKILL.md, the
- `references/task-1-company-research.md` — Task 1: Company Research. <!-- Moved verbatim from initiating-coverage/SKILL.md, the
- `references/task-reference-files.md` — Task Reference Files. <!-- Moved verbatim from initiating-coverage/SKILL.md, the
- `references/task-selection.md` — Task Selection. <!-- Moved verbatim from initiating-coverage/SKILL.md, the

`references/valuation-methodologies.md`](references/valuation-methodologies.md)

## Quality Standards

All outputs meet institutional standards from leading investment banks (JPMorgan, Goldman Sachs, Morgan Stanley):

- **Comprehensive**: Meet all minimum requirements
- **Detailed**: Specific data and examples, not generic statements
- **Quantified**: Lead with numbers and metrics
- **Cited**: Proper sources with clickable hyperlinks
- **Professional**: Institutional-quality formatting
- **Accurate**: All numbers verified and cross-checked

---

## Important Notes

### Task Independence

- **Task 1** can run anytime (no dependencies)
- **Task 2** can run anytime (just needs historical data)
- **Tasks 1 & 2** can run in parallel
- **Task 3** requires Task 2
- **Task 4** requires Tasks 2 & 3
- **Task 5** requires Tasks 1, 2, 3, & 4

### Session Management

**Same session**: Outputs automatically available to subsequent tasks

**Different sessions**: Reference previous task outputs explicitly
```
"Use Task 3 with the model from yesterday at [path]"
"Use Task 5 with the research document at [path]"
```

### File Organization

Recommended structure during workflow:
```
ProjectFolder/
├── Task1_Research/
│   └── [Company]_Research_Document.md
├── Task2_Model/
│   └── [Company]_Financial_Model.xlsx
├── Task3_Valuation/
│   └── [Company]_Valuation_Analysis.pdf
├── Task4_Charts/
│   ├── chart_01.png
│   └── ... (25-35 files)
└── Task5_Report/
    └── [Company]_Initiation_Report.docx
```

### No End-to-End Execution

This skill does **NOT** support running all tasks automatically in sequence. Each task must be explicitly requested and verified.

**Why**: This ensures:
- Quality control at each stage
- Ability to review outputs before proceeding
- Flexibility to pause/resume workflow
- Clear verification of prerequisites

---

## Success Criteria

A successful initiation report workflow should:
1. Complete all 5 tasks in order
2. Pass all input verifications
3. Meet all quality standards
4. Produce all required deliverables
5. Numbers cross-check between outputs
6. Final report is publication-ready

**Output quality**: Institutional (JPMorgan/Goldman/Morgan Stanley level)
**Use case**: First-time comprehensive coverage of a company
