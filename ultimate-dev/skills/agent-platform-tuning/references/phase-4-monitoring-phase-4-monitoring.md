<!-- Moved verbatim from agent-platform-tuning/SKILL.md, the 'section' section. Relative links were rebased for the new depth; the prose is otherwise unchanged. -->

# Phase 4: Monitoring {#phase-4-monitoring}

Monitor the job via the Cloud Console link provided in the script output.
`--location` is required and must be the same location you submitted with: an
open model job submitted on `global` is polled with `--location global`, even
though the work runs in a real region behind the scenes.

Additionally, ask the user if they want you to monitor the job status for them
in the background. If they agree, execute `scripts/monitor_tuning_job.py` as a
background task to periodically poll the job status and notify the user to show
the status. If the user declines, leave it completely to the user to check on
the status.
