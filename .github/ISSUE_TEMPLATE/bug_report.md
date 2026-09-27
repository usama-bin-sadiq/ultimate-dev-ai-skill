---
name: Bug report
description: A defect in the kernel, a reference, a delegated role, a tool, an evaluation case, or the installer.
title: "[bug] "
labels: bug
---

This repository is a specification and an evaluation suite, not an application.
It does not crash. A bug here is a documented rule the kernel, a tool, or an
evaluation case did not follow, or a claim in the prose that nothing checks.

Use this form for a defect. A missing capability is a feature request. A change
to a layer, a gate, a boundary, the rung ladder, or what the kernel may do
without asking is an architecture decision, and `CONTRIBUTING.md` says to open
an issue and discuss it before writing the change.

## Summary

One sentence. What happened, and what the specification requires instead.

## Class of defect

- [ ] Kernel behaviour. The kernel departed from a rule in `ultimate-dev/SKILL.md` or a reference.
- [ ] Reference integrity. A path does not resolve, a file is unreachable, or an index omits a file.
- [ ] Delegated role. An `agents/` role produced output its contract forbids, or omitted required fields.
- [ ] Tool or validator. A tool passed a broken tree, or failed a clean one.
- [ ] Install, bundle, or fixtures. `install.sh` or a `tools/` generator misbehaved.
- [ ] Security or trust boundary. A control in `ultimate-dev/docs/security/controls.md` did not hold.
- [ ] Evaluation. A case can be passed without the property it claims to test, or the generated projection is stale.
- [ ] Documentation drift. Prose no longer matches what the code does.

## Environment

| Field | Value |
|---|---|
| Version (`VERSION` at the repository root) | |
| Commit SHA (`git rev-parse --short HEAD`) | |
| How the kernel was obtained | repository checkout, `./install.sh`, or the distribution bundle |
| Runtime and its version | |
| Operating system | |

## The rule that was violated

Quote the file and the rule. The claim you are reporting is that the observed
behaviour contradicts this line, and the contradiction is what makes it a defect
rather than a preference.

If the defect is rung discipline, give the rung the kernel chose and the rung
the task warranted. The ladder is in `ultimate-dev/references/triage.md`.

If the defect is a trust boundary or an unauthorised action, name the control
from `ultimate-dev/docs/security/controls.md` that failed, and check
`ultimate-dev/docs/operations/troubleshooting.md` before filing.

## Reproduction

The smallest input that shows the defect. Reduce until removing anything else
stops the behaviour.

**For a kernel or role defect**, give:

- The task, in the terms you gave the kernel.
- What the kernel did, quoted from the transcript. Not a summary of it.
- The decision record at the boundary where it went wrong, if the run produced one.

**For a tool defect**, give the exact command, the exit code, and the output.

```bash
python3 ultimate-dev/tools/validate-skills.py --strict
```

State the output you observed, not the output you expected. A defect in a
validator is often that it reports success on a tree that is broken, so a
clean-looking run is part of the report.

## Observed and expected

| | |
|---|---|
| Observed | |
| Expected, and the file that says so | |
| Frequency | every run, one run in N, or under a condition you can name |

If a part of this is inference rather than observation, mark it as inference.
The distinction is the report's value.

## Evaluation coverage

Give the case id if you ran one. The families are `BM-` benchmark, `DM-`
domain, `FC-` failure, `SC-` security, `TN-` negative trigger, `NM-` negative
trigger, and `RG-` regression.

- Case id, if any:
- Does an existing case cover this? If not, say so. `CONTRIBUTING.md` requires a case for every behavioural change, and a case needs a trap and a required plan deviation to be worth adding.

## Initial read on the layer

Where you believe the defect lives, and why. This is your first read, not a
decision. A change to a layer, a gate, a boundary, the rung ladder, the output
contract, or the kernel's authority needs an ADR, and the layer choice is
yours to make.

- [ ] `ultimate-dev/SKILL.md`
- [ ] `ultimate-dev/references/`
- [ ] `ultimate-dev/agents/`
- [ ] `ultimate-dev/skills/skill-creator/`
- [ ] `ultimate-dev/tools/`
- [ ] `ultimate-dev/evaluation/` or `ultimate-dev/evals/`
- [ ] `ultimate-dev/docs/`, `research/`, `examples/`
- [ ] `install.sh` or `INSTALL.md`
- [ ] Not known yet

## Security

Do not paste credentials, tokens, private data, or another person's content.
If the defect is a vulnerability rather than a functional bug, follow the
disclosure process in `SECURITY.md` instead of this form.

## Checklist

- [ ] The reproduction is minimal, and it still reproduces after removing what is not needed.
- [ ] Every command quoted was run, and its output is pasted rather than described.
- [ ] The violated rule is quoted with its file path.
- [ ] Observed output is separated from expected behaviour.
- [ ] Observed facts are separated from inference.
- [ ] No credential, token, or private data is included.
