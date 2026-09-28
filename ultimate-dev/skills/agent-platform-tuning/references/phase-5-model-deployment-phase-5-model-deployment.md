<!-- Moved verbatim from agent-platform-tuning/SKILL.md, the
     'phase-5-model-deployment-phase-5-model-deployment' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Phase 5: Model Deployment {#phase-5-model-deployment}

Once the tuning job is `SUCCEEDED`, deploy the model.

Deployment requires a real region — `--region=global` is not valid here. If the
job ran on `global`, read the region out of the tuned model's resource name
(`projects/.../locations/<REGION>/models/...`) and deploy there; do not guess.

```bash
ARTIFACTS="gs://YOUR_BUCKET/tuning_agent_job_<datetime>/output/postprocess/node-0/checkpoints/final"
gcloud ai model-garden models deploy \
    --project=YOUR_PROJECT \
    --region=YOUR_LOCATION \
    --model="$ARTIFACTS" \
    --machine-type=MACHINE_TYPE \
    --accelerator-type=ACCELERATOR_TYPE \
    --accelerator-count=COUNT
```

> [!IMPORTANT] **Interactive Confirmation Required (Tier M):** Before proceeding
> with deployment, you **MUST** present the proposed command string showing all
> literal flags in a confirmation prompt to the user with 'Yes' and 'No'
> options.

> **CRITICAL:** When presenting this confirmation prompt to the user, you MUST
> output it as a direct plain text response and stop tool execution immediately.
> Do NOT call any command execution or interactive tools in the same turn, as
> unexpected tool calls may be auto-replied by the simulation harness and cause
> an infinite loop. Yield immediately for the user's reply.

Refer to [Models Catalog](references/models.md) for hardware recommendations for
specific open models.
