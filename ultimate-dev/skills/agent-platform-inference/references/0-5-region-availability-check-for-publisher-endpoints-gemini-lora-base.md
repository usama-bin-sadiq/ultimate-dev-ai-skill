<!-- Moved verbatim from agent-platform-inference/SKILL.md, the
     '0-5-region-availability-check-for-publisher-endpoints-gemini-lora-base' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## 0.5 Region Availability Check for Publisher Endpoints (Gemini + LoRA base)

> [!NOTE] **Skip this section** if either of these applies:
>
> - The user is calling a custom endpoint (§4) — a tuned Gemini model served on
>   a numeric `projects/.../endpoints/<id>`, a self-deployed OSS LLM (Llama,
>   DeepSeek, Qwen, Gemma, etc.), or a legacy custom model. Those requests hit
>   a specific endpoint resource whose region is fixed at deploy time; if the
>   caller-side region doesn't match, the endpoint lookup returns a clean 404
>   without incurring inference cost. Go to §4.
> - The user is calling an OpenMaaS publisher model (§2) — Llama, DeepSeek,
>   Qwen, etc. served via the global `openapi` base URL. These don't have
>   per-region availability restrictions in the same way first-party Gemini
>   does. Go to §2.
>
> **Apply this section** only if the user is calling a first-party managed
> Gemini model (`gemini-*`, via §1), including fine-tuned LoRA adapters on
> top of Gemini — these route through a publisher endpoint whose regional
> availability actually varies.

Before responding to any inference request that names a specific region for a
first-party managed Gemini model (`gemini-*`) or a fine-tuned Gemini LoRA
adapter (identified by numeric endpoint ID + user-stated base model), you
**MUST** verify the model is actually available in that region by making a
live API call. Do not rely on Google Search, training-corpus knowledge, or
publisher documentation for availability claims — regional availability
changes frequently and grounded text can be stale or wrong.

Probe only the exact model and region the user asked about. Do not probe other
models as a "control" — you cannot infer anything about model A's availability
from model B's status, because a different model may itself be unavailable in
the reference region for unrelated reasons.

For first-party Gemini models, probe with a real `:generateContent` call using
a minimal valid payload:

```bash
curl -sS -o /dev/null -w "%{http_code}\n" \
    -H "Authorization: Bearer $(gcloud auth print-access-token)" \
    -H "Content-Type: application/json" \
    "https://${LOCATION_ID}-aiplatform.googleapis.com/v1/projects/${PROJECT_ID}/locations/${LOCATION_ID}/publishers/google/${MODEL_ID}:generateContent" \
    -d "{\"contents\":{\"role\":\"user\",\"parts\":{\"text\":\"${PROBE_TEXT:-hi}\"}}}"
```

For inference against a fine-tuned Gemini LoRA adapter, probe the **base
model** in the target region using the same `:generateContent` call above with
`${MODEL_ID}` set to the base (e.g. `gemini-2.5-flash` if the adapter was
tuned on `gemini-2.5-flash`). The LoRA adapter cannot serve in a region where
its base model isn't available.

Interpret the probe result and act:

-   **200** — model is available in that region. Proceed with the SDK setup in
    §1.
-   **404** — model is not available in that region. STOP. Tell the user
    plainly that the model isn't offered in that region and list the regions
    where it is available (from
    [Gemini Models][gemini-models-docs] or `gcloud ai model-garden models list
    --filter="name~$MODEL_NAME"` without `--region`). Do not silently switch
    regions. Do not proceed to write inference code or SDK initialization for
    the unsupported region. Do not run additional "control" probes to
    double-check the 404 — the target-region probe is authoritative.
-   **Any other outcome** (permission denied, quota, transient failure, etc.)
    — do not conclude the model is available or unavailable. Explain the
    underlying cause in plain language (e.g. "your account doesn't have access
    to this project's Vertex AI API — enable it in the console or switch
    projects") and the concrete next action.
