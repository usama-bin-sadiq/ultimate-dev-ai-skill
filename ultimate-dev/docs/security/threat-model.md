# Threat model

Assets, actors, trust boundaries, and the abuse cases that follow. Each abuse case
states a vector, an impact, the kernel control that addresses it, and the residual
risk. Residual risk is not a formality: every control here is defeatable, and one
with no stated residual risk is a control nobody examined.

## Assets

| Asset | Why it matters | If lost |
|---|---|---|
| **User authority** | the sole source of permission to act | every other control becomes advisory |
| **Promoted system integrity** | skills, rules, and policies future runs trust | persistent, silent compromise across all later runs |
| **Evidence integrity** | the basis of every verdict | output is unfalsifiable; verification is theatre |
| **Confidentiality** | credentials and proprietary data in context and logs | disclosure, and possible credential misuse |
| **Environment integrity** | the machine, repository, and systems acted on | damage, and loss of trust in the tool |

## Actors

The user holds full authority. An innocent third party supplies material the
kernel reads and may carry injection from elsewhere. A content author controls a
document, issue, or page the kernel reads and wants it to act, disclose, or adopt
something. A compromised dependency controls a tool's output or an installed
package. A malicious insider has environment access without going through the
user. An adversarial user asks for something harmful.

## Trust boundaries

```text
user instruction  ≠  retrieved document  ≠  web content
                  ≠  tool output  ≠  generated skill  ≠  trusted policy
```

Six sources, five distinctions. Crossing one does not change an item's authority.
Only the instruction channel can authorise. Authenticated and anonymous content
are both documents, so provenance affects how much weight content receives and
never whether it can authorise. A skill the kernel wrote is a candidate, not an
extension of authority: without that, self-modification is self-escalation. Old
content is not wrong, but it may be, a separate axis from trustworthiness.

## Attack surface

Retrieved text; tool output; capability acquisition; the evidence and verification
machinery; actions with effects outside the kernel's context; persisted state and
memory; and the user, who may ask for something harmful.

## Abuse cases

### 1. Prompt injection via a retrieved document

**Vector.** A file, page, issue, or log the kernel reads contains text addressed to
the agent: instructions, role claims, or claims about what the user wants. The
classic form says the real instructions are in the document or that policy changed.

**Impact.** Arbitrary redirection of the run: exfiltrate context, call a tool with
attacker-chosen arguments, escalate permissions, or adopt a persistent rule, from an
unwanted action to full disclosure of everything in context.

**Kernel control.** Content is data: it may inform a decision and may not
authorise, so an instruction found in a document is a fact about the document and
nothing more. Any change to permissions, scope, or policy requires the user
channel. Retrieved content carries provenance, so its origin stays visible in
derived claims, and instructions found in it are reported rather than obeyed.

**Residual risk.** The model can still be influenced in ways that do not parse as
instruction, so narrow the decision the content may bear on, keep privileged
actions on the user channel, and say that a run reading hostile text has reduced
assurance.

### 2. Malicious tool output

**Vector.** A command's stdout, an error message, a structured response, or a file
read by a tool contains adversarial text. Distinct from case 1 because the tool is
trusted to execute while its output is not trusted as content.

**Impact.** The same redirection by a shorter path: tool output sits adjacent to
execution, so an injected instruction can affect the very next action, and a tool
returning attacker-controlled data in attacker-controlled format is a strong
vector.

**Kernel control.** Observations are recorded as observed, with the source named,
and are never promoted to instructions. Deterministic extraction of a field is
preferred over reading an output in full, and a surprising output is an
observation that triggers re-decision rather than a conclusion to accept.

**Residual risk.** Output that is genuinely needed and genuinely contains
adversarial text cannot be both used and safe, so a required field makes the
decision rest on unverified content, and that status travels with the claim.

### 3. Capability poisoning through a generated skill

**Vector.** The kernel finds a gap, `skill-creator` produces a skill, and that
skill carries content influenced by something read earlier: a malicious document,
a tool output, or a subtly wrong precedent that later runs then trust.

**Impact.** Persistent: a promoted skill with hidden instructions executes them in
every later run that selects it, a far larger blast radius than one injected
document, and it outlives the session that created it.

**Kernel control.** A generated skill is a candidate, never trusted behaviour.
Promotion is gated and requires generalisation evidence, a stated scope, a
security review, and a deprecation condition. A skill that references external
content, requests broad permissions, or has an over-wide trigger fails the gate,
and provenance records what it was generated from.

**Residual risk.** A skill that is subtly wrong rather than overtly hostile passes
every gate, because the gates test behaviour and lineage, not correctness. This is
the strongest argument for keeping creation rare: most gaps belong to direct
action or composition, and a system that creates rarely creates better.

### 4. Evidence manipulation

**Vector.** Making the verification machinery report success: fabricating a tool
result, citing a source that does not support the claim, compressing a document
until its qualifiers disappear, presenting repetition as corroboration, or
counting a test that was not run.

**Impact.** The output contract becomes false, and the user can no longer tell a
checked result from an unchecked one: the most expensive class, because it removes
the signal that something is wrong instead of producing a visible error.

**Kernel control.** The claim-to-evidence chain is recorded and auditable. Lossless
compression tests (recoverability, meaning invariance) keep qualifiers from
disappearing; deduplication stops repetition reading as corroboration; deterministic
work goes to tools, so an unobserved result cannot be reported; and epistemic status
travels with every claim, with a named observation required for any change.

**Residual risk.** The kernel authors both the claim and its evidence, so a
systematic bias produces a self-consistent false record that passes every internal
check. Only a different method or a human catches this, which is why independent
verification exists and why R4 requires it.

### 5. Unauthorized or irreversible action

**Vector.** Getting the kernel to act without the user's authority: deleting data,
sending messages, spending money, deploying, modifying production, or disclosing
something externally.

**Impact.** Direct, externally visible, and often irreversible, and the user may
not learn of it until much later.

**Kernel control.** Confirmation is required for actions that are irreversible,
externally visible, costly, destructive, credential-bearing, or ambiguously
authorised, regardless of rung. Task implication is not authorisation. R4 adds a
named human checkpoint before acting, and permission scoping limits what is
available without asking.

**Residual risk.** The kernel can misjudge reversibility, and the user can approve
a request whose framing hides its real effect. A prompt that omits the effect,
blast radius, and reversibility is worse than none, because it turns attention
into an approval that cannot be informed.

### 6. Credential exposure

**Vector.** A secret enters context through a file read, a log, an environment
variable, an error message, or a command's output, and is then included in a
delivery, a log, a generated skill, or an outbound request.

**Impact.** Disclosure, frequently unnoticed, because it looks like ordinary text
in a long output, and it persists wherever that text was written.

**Kernel control.** Secrets are data that must not be reproduced: values are not
echoed into deliveries, logs, or generated capabilities. Tools are scoped to the
credentials they need rather than given ambient authority, and anything derived
from secret-bearing context is labelled.

**Residual risk.** Detection is imperfect. A secret can sit inside a value that
looks like data, and redaction is defeated by format, encoding, or partial quoting.
The compensating control is scoping: fewer places for a secret to flow means fewer
places for it to leak.

### 7. Accidental destructive operations

**Vector.** No adversary. A legitimate task on a real machine where an action is
taken at the wrong scope, against the wrong target, or without the reversibility
assumed: recursive deletes, overwriting generated files, force-pushing, migrating
the wrong database, or mass edits wider than intended.

**Impact.** Severe and immediate, often unrecoverable, always expensive: a
design-level risk rather than a threat, so it happens on ordinary work and will
happen more often than any attack.

**Kernel control.** Irreversibility is a triage axis, so destructive actions raise
the rung and bring a confirmation requirement. Blast radius is estimated first,
reversible forms are preferred, and work units declare preconditions so a unit
that finds the world changed stops instead of proceeding.

**Residual risk.** Blast-radius estimates come from the kernel's understanding of
the environment, which may be wrong, and a prompt that lists files rather than
consequences is not reviewable. Over-caution is the correct error here, and the
destructive path must be harder to take than the safe one.

## What is deliberately not modelled

Social engineering of the human at a checkpoint, because the controls assume that
person is paying attention; a compromised host, because the kernel cannot detect
it; and a malicious user with full authority, only partially in scope. Two
cross-cutting patterns deserve naming. **Escalation by accumulation:** many
individually acceptable small actions produce one unacceptable effect, and because
the controls are per-action the accumulation is the gap, so state the run's total
effect at checkpoints. **Slow poisoning:** repeated trivial nudges in retrieved
content shift decisions over many runs, nothing in a single run looks wrong, and
the control is provenance over time plus periodic review of promoted rules.