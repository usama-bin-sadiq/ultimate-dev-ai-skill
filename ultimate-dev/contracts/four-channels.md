# Four-Channel Contract

Ultimate-Dev separates four information channels so a prompt can work across
subjects, formats, and hosts without copying the entire agent registry.

```text
Intent → Knowledge → Action → Evidence
```

## 1. Intent channel

Normalize the user's request into the task envelope before selecting a method.
Capture language, goal, constraints, acceptance criteria, inputs, assumptions,
unknowns, risk, and requested output. Do not execute or imply authorization here.

## 2. Knowledge channel

Choose the smallest useful capability:

1. universal core rule;
2. common skill;
3. exact specialist;
4. domain fallback;
5. universal fallback;
6. human review.

Load only the selected skill and references. Record which knowledge was used and
which sources or assumptions support it. A missing capability is a reportable
state, not a reason to invent a provider or specialist.

## 3. Action channel

Represent requested capabilities separately from capabilities the host actually
exposes. Mark each action as read-only, reversible, or side-effecting. Include
approval state when the host provides it. In prompt-only mode, use this channel
to describe a proposed action or produce a plan; do not claim that an action ran.

## 4. Evidence channel

Return the result with the smallest honest proof set:

- checks actually run and their `pass`, `fail`, or `not_run` state;
- sources, assumptions, and provenance;
- artifacts or changed paths;
- limitations, residual risk, and confidence;
- next actions or human decisions still required.

An answer without evidence may be valid advice, but it must not be presented
as a verified implementation or an executed external action.

## JEV profiles

### Prompt-only profile

Use JEV concepts as a lightweight reasoning rubric:

- normalize NOUL facts (urgency, safety, sensitivity, evidence needs);
- normalize CHOICE facts (deliverable, pattern, route, context);
- normalize SCORE facts (risk, complexity, confidence, context pressure);
- report missing host facts and ask for human review when material.

No decision packet, provider, runtime, or authorization is required.

### Host/runtime profile

When the host supplies capability facts, policy, and approvals, it may use the
optional JEV kernel to produce a deterministic decision packet. The host remains
responsible for confirmation, execution, evidence, and recovery. JEV never calls
tools or grants authority.

## Universal fallback

For an unknown or unclassified task:

1. classify the deliverable and risk;
2. ask one focused question only if the missing fact changes the result;
3. use available research/reference capabilities, preferring authoritative
   sources;
4. decompose the task into bounded, independently verifiable steps;
5. complete the safe bounded portion;
6. report `capability_gap`, unknowns, assumptions, and confidence;
7. propose a specialist, reference pack, or future evaluation case.

Never create a permanent skill from one isolated task. Promotion requires
repeated evidence and review through the self-evolution workflow.
