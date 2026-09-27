# TypeScript patterns

Load the section that matches the problem. These examples show shapes, not repository naming or architecture rules.

## Replace contradictory fields with variants

```ts
type ImportState =
  | { readonly _tag: "Waiting" }
  | { readonly _tag: "Running"; readonly startedAt: Date }
  | { readonly _tag: "Completed"; readonly artifactId: ArtifactId }
  | { readonly _tag: "Failed"; readonly error: ImportFailed };
```

This prevents combinations such as `completed: true` with no artifact. Use the discriminant already established by the surrounding domain.

## Strengthen only at partial operations

```ts
type NonEmpty<T> = readonly [T, ...ReadonlyArray<T>];

const newest = (sessions: NonEmpty<Session>): Session => sessions[0];

const sum = (values: ReadonlyArray<number>): number =>
  values.reduce((total, value) => total + value, 0);
```

`newest` needs a non-empty input. `sum` has a valid answer for an empty array, so a stronger type would add ceremony without removing a failure.

## Brand through a validated constructor

```ts
declare const UserIdBrand: unique symbol;
type UserId = string & { readonly [UserIdBrand]: true };

const makeUserId = (value: string): UserId | undefined => {
  if (value.length === 0) return undefined;
  // SAFETY: This module owns UserId construction and checked its only invariant.
  return value as UserId;
};
```

Callers obtain `UserId` through `makeUserId`. They do not assert that arbitrary
strings are valid IDs. Use the repository's runtime validation library when the
value crosses a trust boundary.

## Keep transport and application meanings distinct

```ts
type CreateAccountRequest = {
  readonly email: string;
  readonly marketingConsent: boolean;
};

type CreateAccountInput = {
  readonly email: EmailAddress;
  readonly consent: MarketingConsent;
};
```

Use a separate application input because the wire fields need parsing and their
names do not carry the full domain meaning. Reuse a boundary type only when it
already represents the exact application value.

## Keep a small local outcome small

```ts
type Lookup<T> = { readonly _tag: "Found"; readonly value: T } | { readonly _tag: "Missing" };

const findBySlug = (items: ReadonlyArray<Item>, slug: string): Lookup<Item> => {
  const item = items.find((candidate) => candidate.slug === slug);
  return item === undefined ? { _tag: "Missing" } : { _tag: "Found", value: item };
};
```

This is a domain outcome, not a generic Result implementation. Promote it to the
repository's established failure abstraction only when callers need shared
composition, recovery, or matching operations.

## Prove exhaustive handling

```ts
const renderState = (state: ImportState): string => {
  switch (state._tag) {
    case "Waiting":
      return "Waiting";
    case "Running":
      return `Started ${state.startedAt.toISOString()}`;
    case "Completed":
      return `Artifact ${state.artifactId}`;
    case "Failed":
      return state.error.message;
    default: {
      const unhandled: never = state;
      return unhandled;
    }
  }
};
```

Use an established exhaustive matcher when the selected union type already provides one.
