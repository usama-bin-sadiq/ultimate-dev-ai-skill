<!-- Moved verbatim from agent-platform-eval-flywheel/SKILL.md, the
     'safety-confirmation-tiers-critical' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Safety & Confirmation Tiers (CRITICAL)

Before executing any commands or scripts on behalf of the user, you MUST adhere
to the following safety tiers based on the action requested:

1.  **Tier R**: Read-only (`inspect_results.py`, `compare_results.py`,
    `validate_dataset.py`, `parse_adk_traces.py`, `render_html_report.py`)
    *   **Rule**: No confirmation needed. You may execute these helper scripts
        immediately to inspect data, validate schemas, parse traces, or compare
        evaluation results.
2.  **Tier M: Read-only with Compute Costs (`client.evals.run_inference`,
    `client.evals.evaluate`, `client.evals.generate_conversation_scenarios`,
    `client.evals.generate_loss_clusters`)**
    *   **Rule**: These operations invoke LLMs or remote evaluation services
        that consume compute resources and incur costs. This requires
        **interactive confirmation** with 'Yes'/'No' options.
    *   **Confirmation for EVERY evaluation run**: Every evaluation,
        re-evaluation, metric update, parameter change, or synthetic scenario
        generation requires its own dry-run preview and interactive
        confirmation. Never execute a second evaluation, comparison pass, or
        modified evaluation without presenting a new confirmation preview and
        obtaining user approval.
    *   **Same-turn restriction**: Do not run the evaluation in the same turn as
        presenting the confirmation prompt. End your turn after asking and wait
        for the user's reply; only execute after explicit 'Yes' / approval.
        Printing a preview and then calling the tool before the user can answer
        does not count as obtaining confirmation.
    *   **No Pre-Execution of Remote Evaluation**: NEVER execute
        `client.evals.evaluate()`, `client.evals.run_inference()`,
        `client.evals.generate_conversation_scenarios()`, or run any script
        invoking these remote operations before user confirmation. In the
        initial turn, you may prepare local data structures and compose the
        script, but you MUST present the dry-run preview card and obtain
        explicit user confirmation before running any remote evaluation or
        scenario generation call.
    *   **Immediate Execution Upon Approval**: Once the user explicitly approves
        (e.g., 'Yes', 'Approved', 'Go ahead', 'Proceed'), proceed directly to
        executing the previewed evaluation script via `run_command` and report
        the results. Do not conclude the turn without executing the approved
        action.
