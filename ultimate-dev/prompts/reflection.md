# Self-Reflection Instructions

Before handing off your work, perform a structured self-reflection. This catches issues before they reach the orchestrator.

## Reflection Checklist

### 1. Requirements Verification

Ask yourself:

- [ ] Did I address the **exact** objective stated in the task?
- [ ] Did I stay within the defined **scope**?
- [ ] Did I meet all **acceptance criteria**?
- [ ] Did I respect all **constraints** (technical, style, scope)?

### 2. Quality Check

- [ ] Does the code follow existing patterns in the codebase?
- [ ] Are there any `TODO`, `FIXME`, or `HACK` comments left behind?
- [ ] Are error cases handled, not just the happy path?
- [ ] Are edge cases considered (empty inputs, null values, boundary conditions)?
- [ ] Is the code readable without comments explaining what it does?

### 3. Impact Assessment

- [ ] Did I change anything outside my assigned scope?
- [ ] Could my changes break existing functionality?
- [ ] Did I introduce any new dependencies?
- [ ] Did I change any public APIs or interfaces?
- [ ] Are there any performance implications?

### 4. Documentation & Communication

- [ ] Did I document non-obvious decisions in comments or commit messages?
- [ ] Did I update relevant documentation (README, API docs, etc.)?
- [ ] Did I clearly state assumptions I made?
- [ ] Did I flag any open questions for the next agent?

## Reflection Output

After completing the checklist, produce this reflection summary:

```yaml
reflection:
  requirements_met: true | false
  scope_stayed: true | false
  quality_checked: true | false
  impact_assessed: true | false
  documentation_updated: true | false

  gaps:
    - "Description of any requirement not fully met"
    - "Any concern about impact on other parts of the system"

  confidence: "high | medium | low"
  confidence_reasoning: >
    Why you have this confidence level.
    "All tests pass, code follows existing patterns, no scope changes."
```

## When to Flag Concerns

Flag concerns immediately if:

- You had to make assumptions that might not align with the orchestrator's intent.
- You couldn't verify something because tests, tools, or data were unavailable.
- Your solution works but feels fragile or has known limitations.
- You discovered related issues while working on the task.

## Reflection vs. Handoff

- **Reflection** is internal — it's your self-assessment before producing the handoff.
- **Handoff** is the output — it's what you deliver to the orchestrator.

Use reflection to ensure your handoff is complete and accurate. If your reflection reveals gaps, address them in the handoff rather than hiding them.
