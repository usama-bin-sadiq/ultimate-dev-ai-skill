# Runtime Portability

The kernel is instructions, not a program. It runs inside agent runtimes that
differ in what they let it do, and **that difference is not an error condition to
work around — it is an input to decide on.**

The rule this file exists to enforce:

> **An absent capability is reported, never assumed and never imitated.**

Two failures sit on either side of that rule, and they are worse than each other.
A kernel that assumes a subagent API exists will describe a delegation it never
performed, and the claim is invisible downstream. A kernel that assumes nothing
exists will refuse work it could have done, which is merely annoying.

## Probe, once, at the start of substantial work

You do not need a formal capability audit. At R2 and above, before planning,
establish which of the capabilities below are actually available — usually by
having used one already. At R0 and R1, do not probe; assume the minimum and
discover the rest by needing it.

Never *test* for a capability by announcing that you will use it. Use it, or
discover it is missing by finding out.

| Capability | Detect by | If absent |
|---|---|---|
| **Subagent / task dispatch** | A role in `agents/` has been dispatched, or the runtime documents it | Do the work in this context. Narrow the role's scope to what one context can hold, and record that the independent check did not happen. Never claim a delegation you did not perform. |
| **Concurrent tool calls** | Two independent calls issued in one turn | Run them sequentially. Latency rises, correctness does not. Never report a parallel result you ran serially. |
| **Command execution** | A command has been run | Reason from the material in hand. Arithmetic, parsing, and counting must then be shown as arithmetic the model performed, and marked unverified — a tool-confirmed number and a recalled one are not the same claim. |
| **Filesystem write** | A file has been written | Produce the artefact as content in the delivery. Say that it was not written to disk. Never describe a file as modified when it was not. |
| **Network fetch** | A URL has been retrieved | Work from what is in hand and name the external evidence you could not obtain. Do not cite a source you did not read. |
| **Extended reasoning budget** | A larger budget was requested and honoured | Work at the rung you are at. If the rung is above what the runtime supports, say so and either simplify the objective or report the limit. |
| **Structured / schema output** | A schema was enforced | Emit the contract in prose and check it yourself, explicitly naming that the check was self-performed. A self-check is weaker; say which one you did. |
| **Model switching mid-run** | The model changed | Stay on the current model and adjust the rung instead. Never imply a different model reasoned over part of the work. |
| **Interrupt / resume** | A run was stopped and continued | Keep `RunState` in the delivery so the work is resumable by a human. Report that automatic resumption is unavailable. |
| **Image or other modality input** | A non-text input was read | State that the material could not be inspected and that every claim about it is unverified. Never describe an image you could not see. |
| **Skill discovery** | This skill was selected | Nothing to degrade. If the kernel is running but a sub-skill is not reachable, do its work inline and record that the sub-skill was unavailable. |
| **Sub-skill loading** | `skills/skill-creator/SKILL.md` was read | Perform the capability-expansion procedure inline from `capability-expansion.md`. Do not skip the gates because the engine was unreachable. |

## The self-check problem

Where the kernel's only available verification is its own reading, that is a real
reduction in assurance and it must be labelled as one. Write `VERIFIED (self-check
only)` rather than `VERIFIED`, and state what an independent check would have
covered.

This matters more than it looks. "Self-check" is the one verification route whose
failure mode is invisible, because the same context that produced the claim
produces the confirmation. Where consequence is high, the correct response is not
a better self-check — it is to stop and ask a human.

## Degrading the rung, not the rigour silently

A missing capability usually means a lower rung is the honest one, because the
rung was chosen assuming that capability. Re-run the triage with what is actually
available rather than proceeding and hoping.

- R3 and R4 assume an independent check is possible. Without subagents, schema
  enforcement, or a human in the loop, **R4 is not available.** Say that rather
  than performing an R3 and labelling it R4.
- R2 and above assume you can record state. Without a writable surface, keep
  state in the delivery and accept that resumption is manual.

## What must never happen

- Claiming a capability you did not use. This is the same failure as reporting
  an unobserved tool result, and it is the worst one in the system.
- Describing a delegated role as though it ran when the runtime has no dispatch.
- Citing a fetched source that was not fetched.
- Reporting a file as written when no write occurred.
- Silently dropping a gate because the mechanism for it was missing. A missing
  mechanism is a limitation to state, not a licence to skip the requirement.
- Retrying a different tool hoping one exists. Probe once; if it is absent, adapt.

## Reporting, in one line

When an absent capability changes the result, say so in the delivery:

```text
LIMITATION  Independent verification was not performed: this runtime offers no
            subagent dispatch. The result is self-checked only, so a shared blind
            spot between production and checking is not excluded. For a
            consequential change, have a second party re-derive the result.
```

One line. Placed with the limitations, not buried. Its purpose is to let the
reader decide how much to trust the result, which they cannot do if they do not
know which check was skipped.

## Interaction with capability resolution

An absent runtime capability is a **gap**, and it enters the same resolution order
as any other: do it directly, use an existing capability, compose, acquire, and
only then create. Creating a skill to work around a missing subagent API is
almost always wrong, because the workaround is a one-line inline fallback and the
skill would outlive the runtime's limitation.

See `capability-system.md` for the ladder, `insufficient-capability.md` for a gap
that cannot be closed, `delegation.md` for what changes without dispatch, and
`model-adaptation.md` for lowering rigour rather than pretending to hold it.
