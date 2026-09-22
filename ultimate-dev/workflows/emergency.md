# Emergency / Hotfix Workflow
# For critical production issues requiring immediate resolution.

name: emergency
description: >
  Emergency workflow for production incidents and critical bugs.
  Priority: speed and safety. triage → minimal fix → test → deploy → post-mortem.

principles:
  - "Speed matters, but a bad fix is worse than no fix."
  - "Minimal changes reduce the chance of introducing new bugs."
  - "Always have a rollback plan before deploying."
  - "Document everything — post-mortem starts during the incident."
  - "Communicate clearly and frequently during the incident."

steps:
  - id: triage
    name: "Triage Incident"
    description: >
      Quickly assess the severity and impact of the issue.
    actions:
      - "Determine severity: Is the system down? Is data at risk? Are users affected?"
      - "Check monitoring dashboards for anomalies"
      - "Read error logs and stack traces"
      - "Identify the affected components and users"
      - "Check if there's a known fix or workaround"
    severity_levels:
      P0_system_down:
        description: "Complete system outage or data loss"
        response_time: "Immediate"
        action: "Full team alert, all-hands on fix"
      P1_critical:
        description: "Major feature broken, significant user impact"
        response_time: "15 minutes"
        action: "Dedicated fix agent, others on standby"
      P2_significant:
        description: "Feature degraded, workaround available"
        response_time: "1 hour"
        action: "Scheduled fix, monitor for escalation"
      P3_minor:
        description: "Minor issue, low user impact"
        response_time: "Next business day"
        action: "Normal workflow, no emergency treatment"
    outputs:
      - "severity: P0 | P1 | P2 | P3"
      - "impact: Who and what is affected"
      - "workaround: Available workaround (if any)"

  - id: minimal_fix
    name: "Implement Minimal Fix"
    description: >
      The smallest possible change that resolves the critical issue.
      Do NOT refactor, optimize, or improve anything else.
    actions:
      - "Identify the minimal change needed to resolve the issue"
      - "If the root cause is unclear, consider a revert or feature flag"
      - "Write the fix with extreme care — every line must be correct"
      - "NO refactoring, NO improvements, NO 'while I'm here' changes"
      - "Document what you changed and why"
    rollback_options:
      - "Revert the last deployment (preferred if the issue is new)"
      - "Feature flag to disable the problematic feature"
      - "Configuration change to work around the issue"
      - "Database rollback (last resort, requires data team)"
    outputs:
      - "fix: The minimal change implemented"
      - "rollback_plan: How to undo this fix if it causes problems"
      - "confidence: How confident we are this fix resolves the issue"

  - id: test
    name: "Test Fix"
    description: >
      Verify the fix works without introducing new problems.
      Speed is important but accuracy matters more.
    actions:
      - "Verify the specific issue is resolved"
      - "Run affected test suite (not full suite — time is critical)"
      - "Smoke test critical user flows"
      - "Check for obvious regressions in related areas"
      - "Have a second pair of eyes review if possible"
    outputs:
      - "fix_verified: true | false"
      - "regression_check: pass | fail | not_checked"
      - "ready_to_deploy: true | false"

  - id: deploy
    name: "Deploy Fix"
    description: >
      Deploy the fix with maximum safety.
    actions:
      - "Ensure rollback mechanism is ready"
      - "Deploy to production"
      - "Monitor error rates and key metrics after deployment"
      - "Verify the issue is resolved in production"
      - "If issues arise, execute rollback immediately"
    monitoring:
      - "Error rate should return to baseline within 5 minutes"
      - "Response times should not increase"
      - "No new error types should appear"
      - "User-reported issues should stop"
    outputs:
      - "deployed: true | false"
      - "monitoring_results: Post-deployment metrics"
      - "incident_resolved: true | false"

  - id: post_mortem
    name: "Post-Mortem"
    description: >
      Document what happened, why, and how to prevent it.
      This is not optional. Every incident must have a post-mortem.
    format: |
      ## Incident Post-Mortem

      ### Summary
      - **Date:** [date]
      - **Duration:** [how long was the issue active]
      - **Severity:** P0/P1/P2/P3
      - **Impact:** [who was affected and how]

      ### Timeline
      | Time | Event |
      |------|-------|
      | HH:MM | Issue detected |
      | HH:MM | Triage completed |
      | HH:MM | Fix deployed |
      | HH:MM | Issue confirmed resolved |

      ### Root Cause
      [What caused the incident. Be specific and technical.]

      ### What Went Well
      - [Things that helped resolve the incident quickly]

      ### What Went Wrong
      - [Things that slowed down resolution or contributed to the incident]

      ### Action Items
      | # | Action | Owner | Priority | Due Date |
      |---|--------|-------|----------|----------|
      | 1 | [Prevention measure] | [name] | [high/med/low] | [date] |
      | 2 | [Detection improvement] | [name] | [high/med/low] | [date] |
      | 3 | [Process change] | [name] | [high/med/low] | [date] |

      ### Lessons Learned
      - [Key takeaways for the team]
    outputs:
      - "post_mortem: Complete incident document"
      - "action_items: List of prevention measures with owners"
      - "monitoring_gaps: What we should monitor but don't"

# Escalation rules
escalation:
  when_to_escalate:
    - "Fix is not working after one attempt"
    - "Root cause cannot be identified within the time box"
    - "Fix requires changes to infrastructure or external services"
    - "Fix requires coordination with other teams"
  escalation_path:
    - "First: Senior engineer or team lead"
    - "Second: Engineering manager"
    - "Third: VP of engineering (for P0 only)"
