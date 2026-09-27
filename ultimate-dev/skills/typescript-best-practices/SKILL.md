---
name: typescript-best-practices
description: TypeScript type-system, trust-boundary, and module-contract practices. Use when designing, writing, refactoring, or reviewing TypeScript or TSX. When the code uses Effect, also use the effect skill.
---

# TypeScript best practices

Use TypeScript to carry facts that callers would otherwise need to remember.
Keep the model only as strong as the operations require. Repository instructions
own architecture, and library skills own library APIs and programming models.

## 1. Establish the local contract

Before changing code, read the applicable repository and directory instructions,
the owning package manifest, TypeScript and lint configuration, neighboring code,
and tests. Trace the changed operation from its input boundary through the point
that handles its result or failure.

Project instructions decide ownership, imports, exports, naming, testing, and
architecture. This skill fills gaps in those instructions. Use existing domain
types, validators, error types, and module seams when they express the same
meaning.

If the repository uses Effect as its application programming model, or the
changed path imports from `effect`, returns an Effect, or introduces an Effect
schema, service, layer, error, Result, stream, or test, read the `effect` skill
before editing. Let that skill decide Effect APIs and patterns. Follow the same
rule for another library with a dedicated skill.

**Complete when:** the owning module, callers, boundary, current error path,
applicable instructions, and required library skills are known.

## 2. Model the legal values

- Start with the simplest type that keeps every operation total. Strengthen it when the looser type forces a non-null assertion, cast, repeated guard, or impossible-state branch.
- Model meaningful variants with a discriminated union. Use the codebase's established discriminant for that family instead of imposing one repository-wide spelling.
- Use a brand with a validated constructor when it prevents a realistic mix-up or invalid construction. Keep ordinary primitives when the distinction adds no safety.
- Push optionality to the caller that knows what absence means. Use an optional result only when absence is an ordinary outcome, not a hidden failure.
- Derive from an authoritative runtime validator or exported contract when the meanings match. Define a named projection when transport, persistence, or application meanings differ.
- Use `satisfies` to check an object contract without replacing its useful inferred literal types.
- Prefer readonly values. Local mutation is fine when it stays behind a precise interface and makes an algorithm or boundary clearer.
- Let local implementation types infer. Add explicit types to exported contracts and places where the annotation states an invariant or prevents widening.

Read [patterns.md](references/patterns.md) when a type admits contradictory
states, an operation is partial, a cast seems necessary, or a local failure
shape is unclear.

## 3. Parse at boundaries

Treat values whose runtime shape is outside the type checker's guarantee as `unknown` until decoded. This includes network input, persisted JSON, environment values, browser storage, untyped SDK output, and caught exceptions. Parse once per trust or representation boundary, then pass the parsed type inward. Storage reads, serialization, process or worker transport, mutable SDKs, and authority changes can create a new boundary inside one system.

Prefer the repository's runtime decoder or a constructor that returns a refined
value. A predicate named `isX` must check the whole claim it makes. Use the
narrowest sound check that proves the claim. A discriminant, `typeof`,
`instanceof`, `in`, a complete guard, and full decoding solve different input
shapes. Use a complete decoder for an external contract rather than assembling
partial checks by habit.

Keep `any`, non-null assertions, and unchecked casts out of application code. If TypeScript cannot express a verified invariant, keep the cast inside the constructor or adapter and explain the proof in a `SAFETY:` comment.

## 4. Keep failure contracts precise

Classify the outcome before choosing a library:

- A total computation returns its value directly.
- Ordinary absence uses the codebase's established optional type.
- A known failure that changes caller or operator policy is a typed value.
- A violated internal invariant or programmer mistake is a defect.

Choose the expected-failure abstraction in this order:

1. Effect. When the repository uses Effect as its application programming model,
   or the complete changed path already uses Effect, use Effect throughout that
   path and read the `effect` skill.
2. `better-result`. Otherwise, when the owning package or changed path already
   uses `better-result`, keep the path in `better-result` and follow its installed
   API and established local patterns.
3. A precise local discriminated union. Use one for a small synchronous outcome
   whose callers need no shared composition API.

Apply this order to known failures and effectful workflows. A total pure
computation still returns its value directly. Once a path has an established
failure abstraction, keep it from the failure source to the handling boundary.
Translate once where two subsystems meet instead of stacking wrappers that encode
the same failure. Library-specific construction, composition, and recovery belong
to that library's skill.

Catch throwing or rejecting third-party behavior inside the adapter that owns
it. Translate documented operational failures into the selected typed contract
and preserve the cause. Let defects reach the repository's reporting boundary.

## 5. Keep the interface honest

- Keep exported contracts smaller than their implementations. Expose what callers
  need without leaking private representation choices.
- Keep raw framework, transport, SDK, and persistence types inside their owning boundary unless they are the deliberate public contract.
- Use object arguments when same-typed positional values are easy to swap or optional parameters make the call unclear. Keep simple positional calls when their meaning is obvious.
- Match unions exhaustively. Use the codebase's established matcher or a `never` proof so a new variant breaks compilation at every incomplete policy decision.
- Comment constraints, interoperability proofs, and surprising tradeoffs. Ordinary assignments and control flow do not need narration.

## 6. Verify the behavior

Run the compiler against every changed exported contract. Test runtime decoders,
constructors, and guards with valid and invalid values. Add a compile-time test
when the requirement is that TypeScript reject a construction or call.

Run the owning package's focused tests and typecheck while iterating. Before handoff, run every repository gate required by the scoped instructions and report exact failures rather than weakening the types or tests.

**Complete when:** the changed path has one coherent failure contract, untrusted
values are parsed at every trust or representation boundary, no invalid state or
unchecked type claim was introduced, and the applicable checks pass.
