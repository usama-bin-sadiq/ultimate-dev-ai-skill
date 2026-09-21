# Invocation Template (compact)

## Template
```
<role>{domain} specialist</role>
<task_contract>
  <goal>1-2 lines: definition of done</goal>
  <inputs>exact files/data</inputs>
  <constraints>conventions, risk flags, precedence rules</constraints>
  <definition_of_done>checkable criteria</definition_of_done>
  <out_of_scope>what NOT to do</out_of_scope>
</task_contract>
<context>minimum files/outputs only</context>
<applicable_principles>principle numbers only (e.g., "1, 3, 7")</applicable_principles>
<output_format>
{
  "decisions_made": ["..."],
  "files_touched": ["..."],
  "open_risks": ["..."]
}
</output_format>
<escalation_rule>stop if high-risk or outside contract</escalation_rule>
```

## Rules
1. Master fills template before dispatching
2. Sub-agent has no ambiguity about scope/constraints/output
3. Escalation rule is non-negotiable
4. out_of_scope prevents scope creep
5. List principle numbers, not full text

## Minimal Version (tiny models)
```
<role>{domain}</role>
<goal>1 line</goal>
<inputs>files</inputs>
<constraints>rules</constraints>
<done>criteria</done>
<output>structured result</output>
```