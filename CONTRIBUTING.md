# Contributing to ultimate-dev

## Adding a Domain Module

Every domain module must conform to this skeleton exactly:

```markdown
---
name: <domain-name>
description: >
  <one or two sentences: exactly what this covers, in imperative/factual terms>
  Does NOT cover <related-but-different domain> — see <that module> instead.
triggers: [keyword or phrase, keyword or phrase, ...]
anti_triggers: [keyword or phrase that looks similar but must NOT route here, ...]
last_verified: YYYY-MM-DD
---

# <Domain Name>

<Identity and persona — who you are>

## Identity & Memory
- **Role**: <specialist role>
- **Personality**: <3-4 traits>
- **Memory**: <what you remember>
- **Experience**: <what you've seen succeed/fail>

## Core Mission
<3-5 subsections with specific responsibilities>

## Critical Rules
<10-15 imperative, checkable rules>

## Technical Deliverables
<Code examples, templates, specifications>

## Communication Style
<How this module communicates>

## Anti-Patterns
<Paired negative/positive examples>

## Success Metrics
<Measurable success criteria>

## Current Tooling Notes
<Dated, isolated from principles — expected to go stale>

## Output Contract
<Exact shape of deliverables>

## Escalation Triggers
<When this module's guidance is insufficient>
```

## Rules for Module Authors

1. **Imperative, not descriptive** — "Validate all input" not "It's good practice to validate input"
2. **Trigger and anti-trigger together** — say what it's for AND what it's not for
3. **Pair every positive with a negative** — "do this" + "don't do this"
4. **Fixed structural template** — same section order, same headers
5. **Every rule must be checkable** — "Write clean code" is unfalsifiable
6. **Most important rules first** — adherence degrades over document length
7. **No vague qualifiers** — ban "usually", "try to", "when appropriate" unless followed by explicit conditions

## Adding a Persona

Personas are Tier 2 specialists. They are NOT registered in the Capability Index.

```markdown
---
name: <specialist-name>
domain: <parent-domain>
description: >
  <one sentence: what this specialist does>
triggers: [keywords]
anti_triggers: [keywords]
last_verified: YYYY-MM-DD
---

# <Specialist Name>

<Identity and core expertise>

## Core Expertise
<Specific skills>

## Deliverables
<What this specialist produces>

## Principles
<5-10 domain-specific rules>
```

## Adding a Tool Adapter

```markdown
---
tool: <tool-name>
doc_source: <official documentation URL>
last_verified: YYYY-MM-DD
---

# <Tool Name> Adapter

## Package Placement
| Scope | Path |
|-------|------|
| User | <path> |
| Project | <path> |

## Sub-Agent Spawning
<How to map to Owner Decision table>

## Instruction Hierarchy
<How Tier 0 rules survive the tool's context handling>

## File Placement
<Directory tree>

## Activation
<How the skill is activated in this tool>
```

## Versioning

- **Patch**: Bug fixes, tooling-notes refreshes, typo corrections
- **Minor**: New domain module, new persona, new adapter, Capability Index additions
- **Major**: Classification algorithm changes, breaking structural changes

## Testing

1. Run `./scripts/verify.sh` — all files must pass
2. Test classification on `evals/golden-cases.yaml` — correct tier and modules
3. Test near-miss triggers — anti-triggers must NOT match
4. Test escalation — modules must escalate correctly when guidance is insufficient
