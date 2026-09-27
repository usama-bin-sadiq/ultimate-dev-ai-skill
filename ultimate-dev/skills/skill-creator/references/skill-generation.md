# Skill generation

Body before description. If the body does not work, a beautiful description only
makes the failure easier to find — the reader pays context to discover a
procedure that does not do what it promised.

The governing rule: **if the specification cannot be expressed as a procedure, it
is a document, not a skill.** A procedure is a sequence of decisions. If the
specification in `skill-contract.md` yields explanation instead of decisions,
stop and take it back to the design stage.

## The description is the discovery surface

Write it before the body, while the intent is fresh, and hold it to five rules:

- **Lead with the user goal**, in the user's vocabulary, not the
  implementation's. A description that describes the mechanism is unreadable to
  the person who needs it.
- **State the trigger condition, including when it does not apply.** This is
  what protects the neighbouring requests.
- **Say what it produces**, so a reader can tell whether this is the right tool
  before paying to load it.
- **No vendor, CLI, or absolute path** unless the skill genuinely cannot work
  without one. Naming one narrows discovery and goes stale.
- **No angle brackets, under 1024 characters, ideally under 400.**

Write three candidates and pick the most specific. Vague descriptions are the
commonest reason a correct skill never fires.

The mechanical parts of these rules are checked by `quick_validate.py`, which
enforces the length limit and rejects angle brackets. It checks well-formedness
only. Whether the description is *discoverable* is a judgement, and the only
evidence is a measured trigger rate (`skill-testing.md`).

## The body is a decision procedure

| Element | Requirement |
|---|---|
| Every step | Ends in a decision, a branch, or a stop |
| Failure modes | Named, each with the response |
| Prohibitions | An explicit statement of what the skill must not do |
| Length | Under 500 lines; detail goes to `references/` |
| Reference files | Each one says when to read it |

A step with no decision is an essay. Delete it, or turn it into a question the
reader answers. "Handle errors appropriately" is not a step; "if the file is
missing, stop and report the path you looked for" is.

Scaffold only what the skill needs:

```text
<skill-name>/
├── SKILL.md          required
├── references/       detail loaded on demand
├── scripts/          deterministic utilities
├── evals/            eval set, excluded from the package
├── agents/           optional review roles
└── assets/           templates handed to the reader
```

Start empty. An unused `references/` or `scripts/` directory is a claim you have
not made good on, and no validator will catch it for you.

## Prefer a script to prose for anything repeated

Prose drifts between runs. If the skill computes, compares, counts, parses,
formats, hashes, or validates, that is a script — the same way a tool beats
recall for deterministic work. Three runs of a prose procedure will produce three
slightly different answers, and the difference will be invisible in every one
of them.

State the command, its inputs, and what it returns. If a script cannot be written
because the decision is genuinely a judgement, say so in the body, and say what
the reader must weigh.

## Validate immediately, not at the end

Run `quick_validate.py` the moment `SKILL.md` exists, before writing eval cases.
It is fast and it catches the boring failures: a bad name, a description over the
limit, a reference to a file you have not written yet. Fix everything it reports
rather than planning to ignore it.

**A pass proves the files are well-formed. It proves nothing about whether the
skill is correct, safe, or worth having.** The remaining work is security review
(`skill-security.md`), testing (`skill-testing.md`), and validation
(`skill-validation.md`) — none of which any validator performs.

## Stop conditions

The candidate is finished when: the body is a decision procedure with named
failure modes and prohibitions; `quick_validate.py` reports valid; every
declared path exists; and the spec's verification criteria are observable by a
test. Then stop. It is now a **CANDIDATE**, usable by the creating run only and
only when explicitly invoked — not by anything matching its description.
