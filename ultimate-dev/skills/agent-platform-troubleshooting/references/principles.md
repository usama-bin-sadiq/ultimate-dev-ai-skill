<!-- Moved verbatim from agent-platform-troubleshooting/SKILL.md, the
     'principles' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

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
