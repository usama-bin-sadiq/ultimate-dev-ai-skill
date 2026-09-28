<!-- Moved verbatim from agent-platform-troubleshooting/SKILL.md, the
     'when-to-use-this-skill' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

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
