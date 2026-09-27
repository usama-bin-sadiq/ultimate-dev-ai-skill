# Security

The security model for a kernel that reads untrusted material, acquires
capabilities it did not ship with, and changes itself.

## What is protected

Four assets, in descending order of how bad their compromise is:

1. **The user's authority.** What the kernel is permitted to do, and on whose
   instruction. Compromise here turns every other weakness into a full
   compromise.
2. **The integrity of the promoted system.** Skills, rules, and policies that
   future runs will trust. A single poisoned promotion is a persistent
   backdoor, because it affects every subsequent run and looks like the
   architecture working.
3. **The integrity of evidence and verification.** If these can be forged, the
   output contract is decorative and the user has no way to tell.
4. **Confidential material.** Credentials, personal data, and proprietary
   content in context, logs, and generated skills.

The ordering is deliberate. A system that protects its own configuration but not
the user's authority has the wrong priorities: the attacker wants the authority,
and will route through anything.

## Documents

- `threat-model.md` — assets, actors, trust boundaries, and each abuse case with
  its vector, impact, kernel control, and residual risk.
- `controls.md` — the concrete controls, what each one enforces, and what the
  kernel must refuse to do.
- `incident-response.md` — what to do when a control fails anyway.

## The model in one paragraph

Content that crosses into the kernel is data until the user authorises
otherwise. A retrieved document, a file you were told to read, a tool's stdout,
and a skill the kernel generated are all data. Data may inform a decision. Data
may not authorise an action, widen permissions, introduce instructions, or
become trusted behaviour. This is the whole model, and every control in
`controls.md` is a mechanism for enforcing it. Its corollary is that the kernel's
own generated skills are untrusted until validated, which is uncomfortable and
correct: the most dangerous content in the system is the content the system
wrote itself.

## Assumptions

These are assumed to be true. If one is false, the model above does not hold.

- The user is the authority. Content is not.
- The host provides a trustworthy instruction channel distinct from the data
  channel. Without that separation, injection is undefeatable at this layer and
  the control has to live in the host.
- Tools can be restricted. A tool that can do anything can be used by an
  adversary who controls its input, and no amount of kernel discipline helps.
- Verification is cheaper than the damage. Where it is not, the answer is human
  confirmation, not a stronger prompt.
- The human at an R4 checkpoint is reachable and paying attention. A checkpoint
  to nobody is not a control.

## Why this is the hard part

The kernel is built to be convinced by evidence and to acquire what it lacks.
Those two properties are the attack surface. An architecture that could not be
persuaded would be safe and useless; an architecture that can be persuaded
without a trust distinction is the vulnerability.

The controls here are therefore mostly about one thing: keeping the ability to
persuade separate from the ability to authorise. That separation is the only
part that cannot be delegated to a model, a tool, or a skill, because all three
can be influenced by content the kernel has not yet classified.
