<!-- Moved verbatim from agent-platform-troubleshooting/SKILL.md, the
     'evidence-gathered' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Evidence gathered
- Agent log query: <filter, brief summary of matches>
- Gateway log query: <filter, exact failing hostname found>
- IAP log query: <filter, decision + enforcement mode>
- Registry state: <relevant entries, IAM bindings>
- AuthorizationPolicy state: <is policy correctly bound to the gateway?>
- Agent Identity Roles: <does identity have roles/iap.egressor?>
- (any other tool output that mattered)
