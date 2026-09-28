<!-- Moved verbatim from agent-platform-troubleshooting/SKILL.md, the
     'diagnostic-flow' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

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
