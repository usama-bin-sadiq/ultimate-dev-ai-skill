# Sub-skills

Skills owned by the kernel. A sub-skill is loaded on demand by `SKILL.md` when a
specific capability is required — it is not loaded automatically, and its
description does not compete with the kernel's own.

## Contents

| Sub-skill | Owns | Loaded when |
|---|---|---|
| [skill-creator](skill-creator/) | Capability gap analysis, specification, generation, security review, testing, promotion, versioning, deprecation | The kernel's capability resolution reaches step 4 or 5 |

## Why a sub-skill and not a sibling

The distinction is the trigger signal.

Two skills whose descriptions both match a request will both fire, and the user
receives two half-processes instead of one. A sub-skill is scoped to its parent:
it is reached *from* the kernel's decision, not *instead of* the kernel, so it
does not compete for the same requests. Its description says what it produces,
and the kernel's says when to want it.

The same reasoning rules out making the delegated roles in `../agents/` skills.
They are execution resources selected at a decision boundary, not capabilities
the user asks for, and promoting them to skills would give them descriptions that
compete with the kernel's own.

## Publishing: the sub-skill will be indexed separately

Registries that crawl public repositories — SkillsMP states it collects every
`SKILL.md` on GitHub — will index `skills/skill-creator/SKILL.md` as a **standalone
skill**, with no knowledge that it is a sub-skill of anything.

That creates a split-trigger risk with the kernel, and it is not hypothetical: an
earlier version of the sub-skill's description read "when a repeated manual
procedure should become a reusable asset", which is nearly the kernel's own
phrasing. Both would have matched the same user request.

The mitigation is in the description, and it is deliberate: the sub-skill's
description now opens by declaring itself internal, states that it is *selected by
the kernel*, and explicitly disclaims the user-facing case — "if the request is a
user asking whether some repeated work should become a skill, that is the kernel's
decision to make first, not this sub-skill's." The kernel's description is the one
that claims the user-facing intent.

Note also that nested `skills/` has no precedent in the major public collections:
`skills/` is a collection root, never a child. The layout is legal and the
marketplace supports deep paths, but it is unusual, so it will not be what a
reviewer expects to see.

## The boundary

A sub-skill may:

- be invoked by the kernel, and inherit the context the kernel passes it;
- carry its own reference tree, loaded on demand;
- state prohibitions that narrow the kernel's behaviour.

A sub-skill may **not**:

- widen the kernel's authority — `skill-creator` cannot grant itself permission
  the kernel does not have;
- be reachable by a user request that the kernel would not have routed to it,
  because that reintroduces the split trigger;
- promote itself. Promotion is a kernel decision on the sub-skill's evidence, not
  an act the sub-skill performs on itself.

That last point is the one that matters most. `skill-creator` produces
*candidates*; the kernel decides which become capabilities. A sub-skill that
could install itself would make the whole gating structure decorative.
