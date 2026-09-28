<!-- Moved verbatim from plan-devex-review/SKILL.md, the
     'step-0-dx-investigation-before-scoring' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Step 0: DX Investigation (before scoring)

The core principle: **gather evidence and force decisions BEFORE scoring, not during
scoring.** Steps 0A through 0G build the evidence base. Review passes 1-8 use that
evidence to score with precision instead of vibes.

**Decision cadence, including Step 0:** One unresolved DX issue per AskUserQuestion
call. Never batch issues into a call's `questions` array. Wait for each answer.
Keep persona, empathy, and mode confirmations in separate calls from issue approvals.
Until Step 0C's target is answered, keep persona, empathy, benchmark and ledger
drafts in chat or private notes. Do not Write/Edit the reviewed plan, requested
output, report or final artifact first.

### 0A. Developer Persona Interrogation

Before anything else, identify WHO the target developer is. Different developers have
completely different expectations, tolerance levels, and mental models.

**Gather evidence first:** Read README.md for "who is this for" language. Check
package.json description/keywords. Check design doc for user mentions. Check docs/
for audience signals.

Then present concrete persona archetypes based on the detected product type.

AskUserQuestion:

> "Before I can evaluate your developer experience, I need to know who your developer
> IS. Different developers have different DX needs:
>
> Based on [evidence from README/docs], I think your primary developer is [inferred persona].
>
> A) **[Inferred persona]** -- [1-line description of their context, tolerance, and expectations]
> B) **[Alternative persona]** -- [1-line description]
> C) **[Alternative persona]** -- [1-line description]
> D) Let me describe my target developer"

Persona examples by product type (pick the 3 most relevant):
- **YC founder building MVP** -- 30-minute integration tolerance, won't read docs, copies from README
- **Platform engineer at Series C** -- thorough evaluator, cares about security/SLAs/CI integration
- **Frontend dev adding a feature** -- TypeScript types, bundle size, React/Vue/Svelte examples
- **Backend dev integrating an API** -- cURL examples, auth flow clarity, rate limit docs
- **OSS contributor from GitHub** -- git clone && make test, CONTRIBUTING.md, issue templates
- **Student learning to code** -- needs hand-holding, clear error messages, lots of examples
- **DevOps engineer setting up infra** -- Terraform/Docker, non-interactive mode, env vars

After reply, keep this in working notes; write it above the plan's decision ledger
only after 0C's target is answered:

```
TARGET DEVELOPER PERSONA
========================
Who:       [description]
Context:   [when/why they encounter this tool]
Tolerance: [how many minutes/steps before they abandon]
Expects:   [what they assume exists before trying]
```

**STOP.** Do NOT proceed until user responds. This persona shapes the entire review.
