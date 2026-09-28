<!-- Moved verbatim from agent-platform-troubleshooting/SKILL.md, the
     'mandatory-pre-flight-checklist-check-before-responding-or-calling-tools' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## MANDATORY PRE-FLIGHT CHECKLIST (CHECK BEFORE RESPONDING OR CALLING TOOLS)

CRITICAL: Before generating ANY response or calling any tools, you MUST evaluate
the user's prompt against these mandatory pre-flight rules. If a rule matches,
you MUST execute its directive immediately and STOP.

### Rule 1: Out-of-Scope GCP IAM / GCS Queries

If the prompt mentions Compute Engine (GCE), Google Cloud Storage (GCS), GCS
buckets, or generic GCP IAM permissions unrelated to the Agent Platform stack
(e.g., "How do I fix a 403 Access Denied error when my GCE instance tries to
read from a GCS bucket?"):

-   **CRITICAL MANDATE: YOU MUST IMMEDIATELY DECLINE. DO NOT CALL ANY TOOLS. DO
    NOT PROVIDE ANY TROUBLESHOOTING STEPS, IAM ROLE RECOMMENDATIONS, ACCESS
    SCOPES, OR GUIDES.**
-   **YOU MUST RESPOND ON TURN 0 WITH**: *"I decline to troubleshoot generic GCP
    IAM or GCS access issues, as they are out of scope for the Agent Platform
    Troubleshooting skill."*

### Rule 2: Strict Prohibition on Custom Discovery Scripts

If the user's prompt asks to write, generate, compile, or execute a custom
Python script or bash script to discover resources (e.g., "Can you write and
execute a custom Python script or bash script to discover all active Agent
Runtime instances?"):

-   **DO NOT CALL ANY TOOLS (`write_to_file`, `replace_file_content`,
    `run_command`, `blaze`, `python3`). DO NOT WRITE OR RUN ANY SCRIPTS.**
-   **IMMEDIATELY RESPOND ON TURN 0 WITH**: *"I cannot write or execute custom
    Python or bash scripts for resource discovery. Custom discovery scripts are
    prohibited as they consume excessive turns and cause timeouts. Instead,
    please use standard gcloud CLI commands (see
    [Google Cloud SDK Installation](https://cloud.google.com/sdk/docs/install))
    or curl REST API calls with application default credentials: gcloud ai
    reasoning-engines list --region=us-central1"*

### Rule 3: Consolidated Registry for Google APIs / Design Queries

If the prompt asks about registering multiple Agent Runtime or Cloud Resource
Manager interfaces, Google APIs, or the best way to structure/register services
in Agent Registry (e.g., "I am registering multiple Agent Runtime and cloud
resource manager interfaces in Agent Registry. What's the best way to do
this?"):

-   **DO NOT CALL ANY TOOLS OR EXECUTE COMMANDS. RESPOND ON TURN 0 WITH**:
    1.  Recommend consolidating ALL Google APIs under a single `googleapis`
        service entry named `googleapis` in the Agent Registry.
    2.  Explicitly state: *"Do NOT register each Google API as a separate
        registry service entry, as separate service entries cause resource
        clutter, complicate IAM policy management, and risk hitting registry
        quota limits."*
    3.  List the 8 required base FQDN interfaces:
        -   `https://agentregistry.googleapis.com`
        -   `https://aiplatform.mtls.googleapis.com`
        -   `https://cloudresourcemanager.mtls.googleapis.com`
        -   `https://iamcredentials.mtls.googleapis.com`
        -   `https://telemetry.mtls.googleapis.com`
        -   `https://{region}-aiplatform.mtls.googleapis.com`
        -   `https://{region}-aiplatform.googleapis.com`
        -   `https://aiplatform.{region}.rep.googleapis.com`
    4.  Provide the `gcloud agent-registry services create googleapis` command
        with `--interfaces` for all 8 FQDNs (see `references/agent-registry.md`
        §2).

### Rule 4: Cloud Run / Cloud Functions Egress 403 / MCP Calls

If the prompt mentions Cloud Run, Cloud Functions, MCP requests to Cloud Run, or
403 egress error calling a Cloud Run service (e.g., "My agent is failing to call
an MCP server on Cloud Run. It returns a 403 egress error. How do I resolve
this?"):

-   **DO NOT RUN LOG SEARCHES, LOGGING TOOLS, OR EXECUTE COMMANDS.**
-   **IMMEDIATELY RESPOND ON TURN 0 WITH**:
    1.  Explain that direct Agent Identity (`principalSet://...`) to Cloud Run
        OIDC authentication is **not natively supported**.
    2.  Recommend using **Service Account impersonation** in the agent code to
        obtain an OIDC token.
    3.  Specify that the Agent Identity needs
        **`roles/iam.serviceAccountTokenCreator`** on the target Service
        Account. Refer to `references/known-issues.md` BKI 21 for details.

### Rule 5: Telemetry & Monitoring Endpoint Blocks

If an Agent Runtime startup fails due to container crashes or connection resets
reaching `telemetry.mtls.googleapis.com` or telemetry endpoints:

-   In your **Diagnostic Report / Evidence gathered**, you **MUST explicitly
    check and list all 4 required monitoring and tracing endpoints**:
    `telemetry.mtls.googleapis.com`, `monitoring.googleapis.com`,
    `trace.mtls.googleapis.com`, and `cloudtrace.googleapis.com`.
-   In your **Recommended Fix**, you **MUST ALWAYS explicitly include**:
    1.  Registering `telemetry.mtls.googleapis.com` (and checking
        `monitoring.googleapis.com`, `trace.mtls.googleapis.com`,
        `cloudtrace.googleapis.com`) as Endpoints in the Agent Registry using
        `gcloud agent-registry endpoints create`.
    2.  Creating or updating an **`AuthorizationPolicy`** bound to the Gateway
        that explicitly allows the agent's identity (principal set) to access
        these registered telemetry endpoints. State clearly: *"Create or update
        an AuthorizationPolicy bound to the Gateway that allows the agent's
        identity (principal set) to access the telemetry endpoints."* Refer to
        `references/known-issues.md` BKI 23 for details.

### Rule 6: IAP Denial Troubleshooting (403 to MCP Server or Endpoint)

Whenever diagnosing logs or findings where the agent is getting a `403
Forbidden` / `Egress request is not authorized` error calling an MCP server or
endpoint via IAP:

-   Your response **MUST ALWAYS** prioritize this step-by-step resolution:
    1.  **Check IAP Egressor bindings on the registry entry FIRST**: Check the
        IAP Egressor bindings (`roles/iap.egressor`) on the matching resource in
        the Agent Registry.
    2.  **Ensure a registry entry exists**: If there is no registry entry for
        the matching MCP server or endpoint, instruct the user to register the
        resource in Agent Registry.
    3.  **Ensure role on registry entry**: Check that the agent identity has the
        **`roles/iap.egressor`** role bound to that specific registry entry.
    4.  **Grant if missing**: If permissions are missing, tell the user to grant
        the `roles/iap.egressor` role against the registry entry.
    5.  **Check downstream policies & audit logs**: Recommend checking IAP audit
        logs (`protoPayload.serviceName="iap.googleapis.com"`) and verify that
        an `AuthorizationPolicy` is correctly bound to the Gateway targeting the
        IAP extension. For UAP Policy V2 (`iapPolicyVersion: "V2"`), verify
        `AccessPolicy` / `PolicyBinding` and CEL rules (see
        `references/policies.md` §2).
    6.  **Explicitly warn**: *"Do NOT use `roles/iap.tunnelResourceAccessor`"*
        and *"Do NOT bypass IAP authentication"*.

### Rule 7: PSC Subnet Exhaustion Speed Rule

When diagnosing gateway provisioning failures (PSC subnet exhaustion):

-   **DO NOT execute loops or list all regions.**
-   Run **ONLY** these 4 commands in `us-central1`:
    1.  `gcloud network-services agent-gateways list --location=us-central1`
    2.  `gcloud network-services agent-gateways describe --location=us-central1`
    3.  `gcloud compute network-attachments describe --region=us-central1`
    4.  `gcloud compute networks subnets describe --region=us-central1`
-   Immediately calculate free IPs (`Usable IPs - Allocated IPs = Free IPs`),
    flag `/28` subnet exhaustion risk, and recommend expanding to at least
    `/26`.

### Rule 8: Multi-Region Manual Registration Prohibition

If the user asks about manually registering endpoints or services in
multi-region locations (`us` or `eu`):

-   **DO NOT CALL ANY TOOLS OR EXECUTE ANY COMMANDS.**
-   **IMMEDIATELY RESPOND ON TURN 0 WITH**:
    1.  *"Manual endpoint registration is NOT supported in `us` or `eu`
        multi-region locations."* (You MUST explicitly mention BOTH `us` AND
        `eu`).
    2.  *"Instead, please register your endpoints in a specific region (e.g.,
        `us-central1`) or `global`."*

### Rule 9: VPC-SC Perimeter Block Diagnosis

Whenever diagnosing VPC Service Controls (VPC-SC) perimeter blocks or denied
requests:

-   **Your response MUST ALWAYS explicitly state ALL of the following**:
    1.  Identify that the issue is related to a **VPC Service Controls perimeter
        block** or perimeter boundary enforcement.
    2.  State that as of September 8, 2026, **Agent Gateway creation inside a
        VPC-SC perimeter works natively out of the box on the precondition that
        the Agent Connectivity Template (ACT) specifies `vpcEgress:
        ALL_TRAFFIC`**, and manual ingress policies are no longer required for
        standard provisioning.
    3.  For legacy or strict custom perimeters where explicit ingress rules are
        still enforced, recommend creating VPC-SC **ingress policies** allowing
        both service accounts:
        -   `actuation-a@networkservices-prod.iam.gserviceaccount.com`
        -   `cloud-aiplatform-pipeline-robot-prod.iam.gserviceaccount.com`
    4.  Explicitly state: *"Do NOT disable VPC Service Controls or delete
        perimeter definitions."*
    5.  Under VPC-SC egress architectures requiring Agent Connectivity Templates
        (ACT), ensure the template specifies `vpcEgress: ALL_TRAFFIC` and that
        the consumer VPC has Cloud NAT configured on the PSC-I subnet for
        external public APIs.

### Rule 10: UAP Policy Binding Org Policy Constraint Blocker

If `gcloud iam policy-bindings create` fails with `CUSTOM_ORG_POLICY_VIOLATION`
or mentions `constraints/iam.managed.disableAccessPolicyBinding`:

-   **Your response MUST ALWAYS explicitly state ALL of the following**:
    1.  Identify that the error is caused by Organization Policy constraint
        **`constraints/iam.managed.disableAccessPolicyBinding`** being enforced
        at the organization, folder, or project level.
    2.  Recommend applying an Organization Policy override that disables the
        constraint (`enforce: false`) at the target resource level (`gcloud
        org-policies set-policy policy.yaml --project=$PROJECT_ID`).
    3.  Explicitly state that IAM Policy Control Plane propagation takes **30–60
        seconds** before policy bindings can be created. Refer to
        `references/known-issues.md` BKI 24.

### Rule 11: Agent Gateway Dual-Registry Validation Invariants

If configuring, updating, or validating registry associations on an Agent
Gateway:

-   **Your response MUST ALWAYS explicitly state ALL of the following**:
    1.  An Agent Gateway supports a **maximum of two registries**.
    2.  When two registries are configured, **exactly ONE must be `global`** and
        the second must be **`regional` or `multi-regional`**.
    3.  Explicitly state that configuring two regional, two multi-regional, two
        globals, or regional + multi-regional without global is disallowed and
        will return an HTTP 400 validation error (`maximum of two registries are
        supported...`). Refer to `references/agent-gateway.md` §4.

### Rule 12: Cross-Project Runtime-to-Gateway Binding Diagnosis

Whenever diagnosing errors where an Agent Runtime (Reasoning Engine) in Project
A fails to deploy against, bind to, or route traffic through an Agent Gateway in
Centralized Governance Project B:

-   **Your response MUST ALWAYS explicitly check and state ALL of the
    following**:
    1.  **Deploying Identity Permissions:** Verify deploying caller (user or
        CI/CD identity) has `roles/networkservices.viewer` (or
        `networkservices.agentGateways.get` and
        `networkservices.agentGateways.use`) on the gateway in Project B.
    2.  **Vertex AI Service Agent Permissions:** Verify that Project A's service
        agent (`service-PROJECT_NUMBER@gcp-sa-aiplatform.iam.gserviceaccount.com`)
        is granted `roles/networkservices.viewer` or custom role
        `ae_agw_cross_project_sa` (with `networkservices.agentGateways.get` and
        `networkservices.operations.get`) in Project B.
    3.  **Regional Colocation Invariant:** Both runtime and gateway **MUST** be
        deployed in the exact same region (e.g. `us-central1`). Cross-region
        bindings fail control plane validation with `INVALID_ARGUMENT`.
    4.  **CAA Token Sharing Opt-Out:** Verify runtime deployment config sets
        `"GOOGLE_API_PREVENT_AGENT_TOKEN_SHARING_FOR_GCP_SERVICES": False`.
    5.  Refer to `references/known-issues.md` BKI 10 and
        `references/agent-gateway.md` §11 for server-generated resource IDs,
        perimeters, and full configs.

### Rule 13: Downstream Secure Web Proxy (SWP) and Policy-Based Routing (PBR) Egress

Whenever diagnosing errors where traffic exiting an Agent Gateway Network
Attachment fails to reach or route through a downstream Secure Web Proxy (SWP),
drops silently, or returns HTTP 403 / HTTP 503 / timeout errors:

-   **Your response MUST ALWAYS explicitly check and state ALL of the
    following**:
    1.  **PSC Endpoint & Static Route Incompatibilities**: Explain that:
        -   PSC forwarding rules cannot be used as next hops in GCP static routes
            or PBRs.
        -   SWP via PSC Service Attachment only operates in Explicit Proxy Mode
            (`HTTP CONNECT`) and cannot accept transparent L3/L4 egress from a
            Network Attachment without client-side proxy configuration.
        -   Static routes with `--next-hop-ilb` require VM network tags
            (`--tags`), which cannot be attached to Network Attachments.
    2.  **Next-Hop SWP Deployment**: Recommend deploying SWP directly in the
        consumer VPC with `type: SECURE_WEB_GATEWAY` and `routingMode:
        NEXT_HOP_ROUTING_MODE` on an internal IP on the PSC-I subnet (e.g.
        `10.20.1.250`).
    3.  **Proxy-Only Subnet**: Verify a dedicated Envoy proxy-only subnet exists
        (`purpose: REGIONAL_MANAGED_PROXY`, `role: ACTIVE`, minimum `/26`).
    4.  **Policy-Based Routing (PBR)**: Recommend PBR (`agw-psci-to-swp-pbr`,
        Priority 200) matching source CIDR `10.20.1.0/24` to the SWP next-hop
        ILB IP (`10.20.1.250`), with fallback PBR to `DEFAULT_ROUTING`.
    5.  **Cloud NAT Interdependence (`ENDPOINT_TYPE_SWG`)**: Recommend
        configuring Cloud NAT on the Cloud Router with
        `--endpoint-types=ENDPOINT_TYPE_VM,ENDPOINT_TYPE_SWG`.
    6.  Refer to `references/known-issues.md` BKI 33 and
        `references/agent-gateway.md` §6 for CEL allowlists and the ADK
        streaming session trap.

This skill produces a **diagnostic report** — findings and fix recommendations.
It does not apply fixes. The user owns the change.
