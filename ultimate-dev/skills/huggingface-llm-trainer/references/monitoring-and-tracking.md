<!-- Moved verbatim from huggingface-llm-trainer/SKILL.md, the 'Monitoring and Tracking' section. Relative links were rebased for the new depth; the prose is otherwise unchanged. -->

# Monitoring and Tracking

**Trackio** provides real-time metrics visualization. See `./trackio_guide.md` for complete setup guide.

**Key points:**
- Add `trackio` to dependencies
- Configure trainer with `report_to="trackio" and run_name="meaningful_name"`

### Trackio Configuration Defaults

**Use sensible defaults unless user specifies otherwise.** When generating training scripts with Trackio:

**Default Configuration:**
- **Space ID**: `{username}/trackio` (use "trackio" as default space name)
- **Run naming**: Unless otherwise specified, name the run in a way the user will recognize (e.g., descriptive of the task, model, or purpose)
- **Config**: Keep minimal - only include hyperparameters and model/dataset info
- **Project Name**: Use a Project Name to associate runs with a particular Project 

**User overrides:** If user requests specific trackio configuration (custom space, run naming, grouping, or additional config), apply their preferences instead of defaults.


This is useful for managing multiple jobs with the same configuration or keeping training scripts portable.

See `./trackio_guide.md` for complete documentation including grouping runs for experiments.

### Check Job Status

```python
# List all jobs
hf_jobs("ps")

# Inspect specific job
hf_jobs("inspect", {"job_id": "your-job-id"})

# View logs
hf_jobs("logs", {"job_id": "your-job-id"})
```

**Remember:** Wait for user to request status checks. Avoid polling repeatedly.
