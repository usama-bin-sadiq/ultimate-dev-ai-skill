<!-- Moved verbatim from initiating-coverage/SKILL.md, the 'section' section. Relative links were rebased for the new depth; the prose is otherwise unchanged. -->

# Input Verification Protocol

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
