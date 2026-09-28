<!-- Moved verbatim from agent-platform-troubleshooting/SKILL.md, the
     'hypothesis-generation-rules' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Hypothesis Generation Rules

Before executing diagnostic queries beyond Step 0, you **MUST** formulate at
most 3 plausible hypotheses for the failure. For each hypothesis, explicitly
correlate it with recent changes (e.g., Terraform applies or configuration
updates) and answer: *"Why did it start failing now?"* Limit diagnostics to
validating these hypotheses.
