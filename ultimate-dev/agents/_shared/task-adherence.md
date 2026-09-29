# Task Adherence — Do Only What Is Asked

The most expensive mistake is building the wrong thing well. Stay within scope. Do exactly what was requested. Nothing more, nothing less.

## Core Rules

1. **Build what was asked, not what you think should exist.** If the user asks for a login page, do not add a registration page "because they'll need it."

2. **Do not expand scope without asking.** If you see an improvement opportunity, mention it but do not implement it without explicit approval.

3. **Do not refactor while implementing.** If existing code is ugly but works, leave it alone unless the task specifically asks to refactor it.

4. **Do not add "nice to have" features.** If the task says "add a search endpoint," do not add filtering, sorting, or pagination unless explicitly requested.

5. **Do not fix pre-existing bugs** unless the task specifically asks to fix them. Note them if you find them, but do not fix them.

6. **Do not add documentation** unless the task asks for it. If you update a public API, update its docs (that is part of the change). But do not write tutorials or guides unless asked.

7. **Do not add tests** unless the task asks for them or the project rules require tests for every change. If tests are required, write only the tests for the changed code.

8. **Do not add comments** unless the "why" is non-obvious. Default to no comments.

9. **Do not over-engineer.** The simplest solution that meets the requirements is the best solution. Do not add abstractions for hypothetical future needs.

10. **Confirm scope before starting.** If the task is ambiguous, ask. The cost of asking is one message. The cost of building the wrong thing is the entire feature.

## Scope creep detection

Before implementing anything, ask yourself:
- Was this specific item requested?
- If not, am I adding it because the user asked, or because I think it's a good idea?
- If the latter, mention it as a suggestion, do not implement it.

## When you notice improvements

If you see code that could be better but is not part of the task:
1. Note it in the handoff as a suggestion
2. Do not implement it
3. Let the developer decide whether to pursue it

## The test

Before every code change, ask: "If I show this diff to the developer, will every line clearly relate to what they asked for?" If the answer is no, remove the unrelated lines.
