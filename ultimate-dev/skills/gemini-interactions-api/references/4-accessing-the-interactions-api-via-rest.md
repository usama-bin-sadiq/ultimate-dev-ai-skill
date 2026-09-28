<!-- Moved verbatim from gemini-interactions-api/SKILL.md, the
     '4-accessing-the-interactions-api-via-rest' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## 4. Accessing the Interactions API via REST

For shell-based scripts, debugging, or non-Python/JS environments, you can communicate with the stateful Interactions API directly using raw HTTP/REST requests via `curl`.

### 1. REST Endpoint

The REST API endpoint for interactions is:

```http
POST https://aiplatform.googleapis.com/v1beta1/projects/{PROJECT_ID}/locations/{LOCATION}/interactions
```

*   **LOCATION**: Use `global` (or custom region if required).
*   **PROJECT_ID**: Your Google Cloud Project ID.

### 2. Set up Variables & Authentication Header

Set your target agent ID (e.g., model or custom agent path) and access token generated from Application Default Credentials:

```bash
AGENT_ID="your-agent-id"
ACCESS_TOKEN=$(gcloud auth print-access-token)
```

### 3. Single-Turn Interaction Payload

Send a request to start an interaction using the agent variable:

```bash
curl -X POST "https://aiplatform.googleapis.com/v1beta1/projects/${PROJECT_ID}/locations/global/interactions" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "agent": "'"${AGENT_ID}"'",
    "input": [{
      "type": "user_input",
      "content": [{
        "type": "text",
        "text": "Explain serverless computing in one sentence."
      }]
    }]
  }'
```

#### Response Example
A synchronous POST request returns a JSON object containing the conversation step details and unique identifiers:

```json
{
  "id": "your-interaction-id",
  "status": "completed",
  "steps": [
    {
      "type": "model_output",
      "content": [
        {
          "type": "text",
          "text": "Serverless computing is a cloud execution model where the cloud provider dynamically manages the allocation and provisioning of servers, charging customers based on actual usage rather than pre-purchased capacity."
        }
      ]
    }
  ],
  "usage": {
    "total_tokens": 24751,
    "total_input_tokens": 23894,
    "total_output_tokens": 857
  },
  "created": "2026-05-08T10:44:43Z",
  "updated": "2026-05-08T10:44:43Z",
  "environment_id": "your-environment-id",
  "object": "interaction"
}
```

### 4. Multi-Turn Stateful Interaction Payload

To continue an existing conversation statefully, specify the `previous_interaction_id` in the JSON payload:

```bash
curl -X POST "https://aiplatform.googleapis.com/v1beta1/projects/${PROJECT_ID}/locations/global/interactions" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "agent": "'"${AGENT_ID}"'",
    "store": true,
    "previous_interaction_id": "YOUR_PREVIOUS_INTERACTION_ID",
    "input": [{
      "type": "user_input",
      "content": [{
        "type": "text",
        "text": "Can you elaborate on that?"
      }]
    }]
  }'
```

### 5. Streaming Output Payload
To stream updates in real time (Server-Sent Events format), pass `"stream": true` in the payload:

```bash
curl -X POST "https://aiplatform.googleapis.com/v1beta1/projects/${PROJECT_ID}/locations/global/interactions" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "agent": "'"${AGENT_ID}"'",
    "stream": true,
    "input": [{
      "type": "user_input",
      "content": [{
        "type": "text",
        "text": "Write a long story about space travel."
      }]
    }]
  }'
```

The endpoint will return a chunked stream where each event begins with `data: ` containing JSON updates with the `event_type` and step contents.

> **How `curl` handles streaming:**
> By default, when `"stream": true` is passed, the server responds with `Transfer-Encoding: chunked` and `Content-Type: text/event-stream` (Server-Sent Events). `curl` will automatically keep the connection open and print the incoming data chunks to `stdout` in real time as they are pushed by the server. The user does not need to poll or pull further; the complete sequence of events streams continuously until completion.

--------------------------------------------------------------------------------
