---
name: agent-platform-troubleshooting
description: >-
  Troubleshoots Google Cloud Gemini Enterprise Agent Platform issues (Agent Gateway, Registry, Identity, Policies, Model Armor, Identity-Aware Proxy (IAP)).
  Use when agent requests fail with 403 (especially unauthorized egress), Agent Runtime queries return 500, or gateway/IAP logs show permission errors.
  Don't use for general Google Cloud Identity and Access Management (IAM) debugging or networking issues unrelated to the Agent Platform stack.
metadata:
  version: "1.0.0"
  category: AiAndMachineLearning
neutralised: tool-specific paths and single-runtime invocations replaced
---

# Agent Platform Troubleshooting

> [!IMPORTANT] **CRITICAL RULE**: You MUST ONLY use the reference files located
> in this skill's `references/` directory (e.g., `references/field-manual.md`,
> `references/known-issues.md`, `references/agent-registry.md`). Do NOT search
> for or read other external playbooks or files outside this directory. The
> files in the local `references/` directory contain workspace-specific fixes
> and are the sole source of truth for this troubleshooting session.

Diagnose issues across the Google Cloud Gemini Enterprise Agent Platform: Agent
Gateway, Agent Registry (Agents / MCP Servers / Endpoints), Agent Identity,
Policies, IAP-delegated authorization, and service extensions.

## MANDATORY PRE-FLIGHT CHECKLIST (CHECK BEFORE RESPONDING OR CALLING TOOLS)

Detail moved verbatim to `references/mandatory-pre-flight-checklist-check-before-responding-or-calling-tools.md`. Load it when this section matters and the pointer is not enough.

## When to use this skill

Trigger when symptoms involve:

-   Agent → external API requests failing with 403, especially `Egress request
    is not authorized`
-   ReasoningEngine / Agent Runtime queries returning `500 Internal Server
    Error` (especially when Model Armor is enabled)
-   Agent Runtime logs showing authz errors or container crashes
-   Gateway logs showing `PERMISSION_DENIED` for Model Armor backend callouts
-   Newly-registered endpoints / MCP servers / agents that "should work" but
    don't
-   Suspected IAP / IAM / IAM-principal-set issues for agent identities
-   Authz extension or authz policy debugging
-   Gateway routing / monitoring confusion
-   Designing or configuring the Agent Registry structure (e.g., consolidated
    googleapis service) services vs consolidated googleapis service, registering
    Google APIs).
-   Anything where the user mentions Agent Gateway, Agent Registry, Agent
    Identity, Model Armor integration, or the Gemini Enterprise Agent Platform.

When *not* to use:

-   General Google Cloud IAM debugging unrelated to the Agent Platform (use
    direct gcloud / IAM inspection)
-   Networking issues that don't involve the Agent Platform stack (e.g., raw VPC
    SC, plain Cloud Run auth)

## Required context (gather first)

Before doing anything else, pin down the basics. If the user hasn't supplied
them, ask. Don't guess.

| Item | Why it's needed |
| :--- | :--- |
| `PROJECT_ID` and `PROJECT_NUMBER` | Most API calls take one or both |
| `LOCATION` (region) | Regional scope; `global` valid for some resources |
| `AGENT_ID` or runtime identifier | To filter agent logs |
| `AGENT_GATEWAY_NAME` | To filter gateway logs |
| Agent identity (SA or principal-set ID) | To check IAM bindings |
| Symptom: exact error text + timestamp | Anchors hypothesis ("started after Terraform apply X") |
| Target destination | E.g. `aiplatform`, `discoveryengine`, MCP server, peer agent |

If only some are known, proceed but call out unknowns in the report. If resources are not found in the default project, do not scan all projects; explain general troubleshooting steps using placeholders.

## Hypothesis Generation Rules

Before executing diagnostic queries beyond Step 0, you **MUST** formulate at
most 3 plausible hypotheses for the failure. For each hypothesis, explicitly
correlate it with recent changes (e.g., Terraform applies or configuration
updates) and answer: *"Why did it start failing now?"* Limit diagnostics to
validating these hypotheses.

## Diagnostic flow

This is a **process skill** — follow the steps in order. See `references/field-manual.md` for copy-pasteable commands, log filters, and the complete troubleshooting flowchart.

-   **Step 0: Context & Pre-Flight**: Match mandatory pre-flight rules (Rules 1-13). Verify project access via `gcloud projects describe $PROJECT_ID`. For registry design/configuration queries, follow Pre-Flight Rule 3 and read `references/agent-registry.md` §2.
-   **Step 1: Agent Logs**: Confirm error type (403 vs connection vs crash). For connection errors/timeouts, check PSC Subnet Exhaustion and ACT/Cloud NAT routing. For container crashes, perform runtime health check.
-   **Step 2: Gateway Logs**: Find exact failing hostname.
-   **Step 3: IAP Logs**: Check policy version (`iapPolicyVersion: "V2"` vs `"V1"`), DRY_RUN vs enforced mode, and decision.
-   **Step 4: Registry State**: Verify if exact hostname is registered. If unregistered, recommend registering all hostname forms.
-   **Step 5: Identity & Policies**: Verify agent identity has `roles/iap.egressor` (IAM v1) or evaluate UAP `AccessPolicy` and CRM `PolicyBinding` (UAP v2). Check `constraints/iam.managed.disableAccessPolicyBinding` blocker.
-   **Step 6: Authz Extension & Gateway**: Verify extension is wired to gateway targeting IAP with correct policy version, and verify dual-registry constraints (max 2: 1 global + 1 regional/multi-regional).
-   **Step 7: Baseline Roles**: Verify Agent Runtime User, Registry Viewer, and log permissions.
-   **Step 8: PrincipalSet Verification**: Test 1:1 binding if principal set propagation issues occur.

## Tools to use

The skill assumes the agent has access to:

-   **`run_gcloud_command (via the host's MCP layer)`** (or **`default_api:run_command`**
    running raw `gcloud` CLI) — for `gcloud` invocations (registry listing,
    authz-extensions describe, IAM, project lookup).
-   **`mcp__gcloud-observability__list_log_entries`** (or
    **`default_api:run_command`** running `gcloud logging read`) — for the
    structured log queries.
-   **`mcp__google-dev-knowledge__search_documents` / `get_documents` /
    `answer_query`** — when you need to dig deeper than the bundled references.
-   **`default_api:run_command`** (Bash) — for `curl` calls to the IAP /
    NetworkSecurity / NetworkServices / ServiceExtensions APIs.

Run independent log queries in parallel if supported.

## How to use the references

The `references/` folder is layered:

-   **`field-manual.md`** — read this first on every invocation. It's the
    operational core.
-   **`known-issues.md`** — read when the symptom matches a recurring pattern.
-   **`agent-gateway.md`** — when the gateway itself is the suspect.
-   **`policies.md`** — when the question is about IAM modeling.
-   **`agent-registry.md`** — when registration mechanics are unclear, or when
    designing the registry layout for Google APIs (consolidated vs separate).
-   **`agent-identity.md`** — when the question is about *who* the agent is.

Read the smallest set that answers the question. Don't preload everything.

## Output report

Always produce a structured report. Use this template exactly.

```markdown
# Agent Platform Diagnostic — <one-line summary>

## Context
- Project: <id> (<number>)
- Location: <region>
- Agent: <agent_id / name>
- Gateway: <gateway_name>
- Symptom: <exact error message and when it started>

## Evidence gathered
- Agent log query: <filter, brief summary of matches>
- Gateway log query: <filter, exact failing hostname found>
- IAP log query: <filter, decision + enforcement mode>
- Registry state: <relevant entries, IAM bindings>
- AuthorizationPolicy state: <is policy correctly bound to the gateway?>
- Agent Identity Roles: <does identity have roles/iap.egressor?>
- (any other tool output that mattered)

## Root cause hypothesis
<single most likely cause, stated plainly. If multiple, rank them.>

## Why this fits the evidence
<brief — connect the dots. Show which evidence rules in / rules out the hypothesis.>

## Recommended fix
<concrete actions in order. Show exact gcloud / curl / Terraform changes the user can run. If the fix is in the user's repo (Terraform), point at file:line.>

## What to verify after the fix
<the queries to re-run to confirm resolution.>

## Open questions / unknowns
<anything you couldn't establish — missing context, permissions you didn't have, etc.>

## Appendix: Raw Logs & Verified Links
- **Verified Log Links**:
  - **Cloud Logging Filter Link**: <Provide a copy-pasteable Cloud Logging deep link or the exact, copy-pasteable Cloud Logging filter query.>
- **Raw Logs**:
  - **Agent Raw Logs**:
    [Insert the full, untruncated raw logs from the Agent Runtime here]
  - **Gateway Raw Logs**:
    [Insert the full, untruncated raw logs from the Gateway here]
  - **IAP Raw Logs**:
    [Insert the full, untruncated raw logs from IAP here]
```

## Reference files

These ship with the skill and are read on demand; none is needed to
use it. Each answers one question the sections above do not.

- [
Each file below is loaded on demand, not at triage. 21 file(s):

- `references/agent-gateway.md` — Agent Gateway — Debugging Reference. Curated from Google Cloud's Gemini Enterprise Agent Platform architecture.
- `references/appendix-raw-logs-verified-links.md` — Appendix: Raw Logs & Verified Links. <!-- Moved verbatim from agent-platform-troubleshooting/SKILL.md, the
- `references/context.md` — Context. <!-- Moved verbatim from agent-platform-troubleshooting/SKILL.md, the
- `references/diagnostic-flow.md` — Diagnostic flow. <!-- Moved verbatim from agent-platform-troubleshooting/SKILL.md, the
- `references/evidence-gathered.md` — Evidence gathered. <!-- Moved verbatim from agent-platform-troubleshooting/SKILL.md, the
- `references/how-to-use-the-references.md` — How to use the references. <!-- Moved verbatim from agent-platform-troubleshooting/SKILL.md, the
- `references/hypothesis-generation-rules.md` — Hypothesis Generation Rules. <!-- Moved verbatim from agent-platform-troubleshooting/SKILL.md, the
- `references/open-questions-unknowns.md` — Open questions / unknowns. <!-- Moved verbatim from agent-platform-troubleshooting/SKILL.md, the
- `references/output-report.md` — Output report. <!-- Moved verbatim from agent-platform-troubleshooting/SKILL.md, the
- `references/policies.md` — Agent Platform Policies — Debugging Reference. Reference for diagnosing IAM, IAP, and Agent Gateway policy denials in the
- `references/principles.md` — Principles. <!-- Moved verbatim from agent-platform-troubleshooting/SKILL.md, the
- `references/recommended-fix.md` — Recommended fix. <!-- Moved verbatim from agent-platform-troubleshooting/SKILL.md, the
- `references/reference-files.md` — Reference files. <!-- Moved verbatim from agent-platform-troubleshooting/SKILL.md, the
- `references/required-context-gather-first.md` — Required context (gather first). <!-- Moved verbatim from agent-platform-troubleshooting/SKILL.md, the
- `references/root-cause-hypothesis.md` — Root cause hypothesis. <!-- Moved verbatim from agent-platform-troubleshooting/SKILL.md, the
- `references/runtime-notes.md` — Runtime notes. <!-- Moved verbatim from agent-platform-troubleshooting/SKILL.md, the
- `references/supporting-links.md` — Supporting Links. <!-- Moved verbatim from agent-platform-troubleshooting/SKILL.md, the
- `references/tools-to-use.md` — Tools to use. <!-- Moved verbatim from agent-platform-troubleshooting/SKILL.md, the
- `references/what-to-verify-after-the-fix.md` — What to verify after the fix. <!-- Moved verbatim from agent-platform-troubleshooting/SKILL.md, the
- `references/when-to-use-this-skill.md` — When to use this skill. <!-- Moved verbatim from agent-platform-troubleshooting/SKILL.md, the
- `references/why-this-fits-the-evidence.md` — Why this fits the evidence. <!-- Moved verbatim from agent-platform-troubleshooting/SKILL.md, the

`references/agent-identity.md`](references/agent-identity.md)

## Principles

-   **Hostname mismatch is the #1 cause.** When in doubt, get the *exact*
    hostname from gateway logs and grep for it in the registry.
-   **Default-deny is the model with multiple layers.** Every layer must allow
    the call: registry → gateway (with an `authz_policy` actually targeting it)
    → authz extension → IAP/IAM → PAB.
-   **PAB beats IAM Allow.** A correct `roles/iap.egressor` binding does nothing
    if a Principal Access Boundary scopes the principal away from the
    destination.
-   **DRY_RUN changes everything.** If IAP is in dry-run, denials are logged but
    not enforced.
-   **The role is `roles/iap.egressor` (for IAM v1) and FQDN permission
    `iap.googleapis.com/resources.egressViaIAP` (for UAP v2).**
-   **UAP (Policy V2) CRM Hierarchy**: Next-gen policies bind to Projects,
    Folders, and Organizations via `PolicyBinding` rather than shadow resources.
    Evaluation follows absolute DENY precedence and additive ALLOW aggregation
    across the CRM tree.
-   **Agent Connectivity Template (ACT) with `ALL_TRAFFIC`**: Under VPC-SC,
    traffic traverses synthetic PSC VIP `240.0.0.2:443`. External public API
    traffic exiting the consumer VPC requires Cloud NAT on the PSC-I subnet to
    avoid silent connection hangs.
-   **Dual-Registry Invariant**: An Agent Gateway supports at most 2 registries;
    when 2 are configured, exactly ONE must be `global` and the second must be
    `regional` or `multi-regional`.
-   **Read evidence, don't assume.** Pull logs first.
-   **Cite exact resource names in the report.**
-   **Stay in diagnosis mode.** Don't apply Terraform changes or run destructive
    gcloud commands. Read-only inspection only.
-   **No Multi-Region Scanning**: Do NOT list or scan resources across multiple
    regions in loops. Check default region (`us-central1`) unless logs point
    elsewhere.
-   **Non-interactive execution**: Always disable prompts (`--quiet` / `-q` or
    `gcloud config set core/disable_prompts True`) to avoid hanging.

## Supporting Links

-   [Agent Runtime Overview](https://docs.cloud.google.com/gemini-enterprise-agent-platform/agents.md.txt)
-   [Agent Gateway Overview](https://docs.cloud.google.com/gemini-enterprise-agent-platform/govern/gateways/agent-gateway-overview.md.txt)
-   [Policies Overview](https://docs.cloud.google.com/gemini-enterprise-agent-platform/govern/policies/overview.md.txt)
-   [Agent Identity Overview](https://docs.cloud.google.com/gemini-enterprise-agent-platform/govern/agent-identity-overview.md.txt)
-   [Agent Registry Overview](https://docs.cloud.google.com/gemini-enterprise-agent-platform/govern/agent-registry.md.txt)
-   [Deploy Agent Gateway Runtime](https://docs.cloud.google.com/gemini-enterprise-agent-platform/scale/runtime/agent-gateway-runtime-deploy.md.txt)
-   [Private Service Connect Interface](https://docs.cloud.google.com/gemini-enterprise-agent-platform/scale/runtime/private-service-connect-interface.md.txt)
-   [Troubleshoot Agent Gateway](https://docs.cloud.google.com/gemini-enterprise-agent-platform/troubleshooting/troubleshoot-agent-gateway.md.txt)
-   [Troubleshoot Agent Deployment](https://docs.cloud.google.com/gemini-enterprise-agent-platform/troubleshooting/agent-deployment.md.txt)
-   [Troubleshoot Runtime Setup](https://docs.cloud.google.com/gemini-enterprise-agent-platform/troubleshooting/runtime-setup.md.txt)

## Runtime notes

This file was adapted to be tool-neutral: it claimed a general scope and was
bound to one tool. The procedure is unchanged; what changed is that a reader on a
different runtime is told what to substitute.

- `<project-root>` — the repository root. 1 machine-specific path(s) replaced.
- `<agent-config-dir>` — wherever this runtime keeps its configuration. Not a fixed location.
- `<agent-instructions>` — the file this runtime reads for standing instructions. Names differ per runtime and none is assumed.
- **cloud-cli** — means. One tool's way of doing a step a different runtime may do another way.
Anything marked **means** is an implementation detail of one tool, and a reader
on a different runtime may need a different mechanism for the same step. Anything
marked **subject** means the capability is genuinely about that tool, and a reader
without it should not expect this file to apply.
