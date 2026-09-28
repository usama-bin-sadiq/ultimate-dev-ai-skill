<!-- Moved verbatim from huggingface-vision-trainer/SKILL.md, the
     'checking-job-status' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Checking job status

**MCP tool (if available):**
```
hf_jobs("ps")                                   # List all jobs
hf_jobs("logs", {"job_id": "your-job-id"})      # View logs
hf_jobs("inspect", {"job_id": "your-job-id"})   # Job details
```

**Python API fallback:**
```python
from huggingface_hub import HfApi
api = HfApi()
api.list_jobs()                                  # List all jobs
api.get_job_logs(job_id="your-job-id")           # View logs
api.get_job(job_id="your-job-id")                # Job details
```
