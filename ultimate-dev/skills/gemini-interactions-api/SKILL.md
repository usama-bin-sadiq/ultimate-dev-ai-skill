---
name: gemini-interactions-api
metadata:
  version: "1.0.0"
  category: AiAndMachineLearning
description: Guides the usage of Gemini Interactions API on Gemini Enterprise Agent Platform. Use when the user wants to use the stateful, server-managed Interactions API for multi-turn conversations, background execution, streaming, structured output, and function calling on the Agent Platform.
---

# Gemini Interactions API Skill

This skill provides instructions for authenticating, connecting to, and utilizing the stateful, server-managed **Gemini Interactions API** on Gemini Enterprise Agent Platform.


The Interactions API is the modern, recommended way to execute Generative AI agent conversations, background research tasks, multi-turn chats, and structured, multi-step workflows.

> [!IMPORTANT] **CRITICAL: Unified SDK, Latest Models & GEAP Targeting** *
> **Unified SDK**: Use the Google Gen AI SDK (**`google-genai >= 2.3.0`** for
> Python, **`@google/genai >= 2.3.0`** for JS/TS). SDK versions `>= 2.0.0` are
> the minimum floor at which the steps schema activates, but `>= 2.3.0` is the
> supported/recommended floor. Legacy SDKs like `google-cloud-aiplatform`,
> `@google-cloud/vertexai`, and `google-generativeai` are strictly unsupported
> for Interactions. * *Mandatory Instruction*: When explaining client
> initialization or writing import code, you **must** explicitly state/warn the
> user that legacy packages like `google-cloud-aiplatform` or
> `google-generativeai` are strictly unsupported for interactions. * **Latest
> Models Only**: Use `gemini-3.5-flash` (fast, balanced, multimodal — the
> recommended default), `gemini-3.1-pro-preview` (complex reasoning, coding,
> research), or `gemini-3.1-flash-lite` (cost-efficient, high-frequency
> lightweight tasks). Refer to the
> [latest model versions](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/migrate)
> to check for new updates. Legacy models (`gemini-3-flash-preview`,
> `gemini-2.5-*`, `gemini-2.0-*`, `gemini-1.5-*`) are deprecated and do not
> support interactions. * *Mandatory Instruction*: In any interaction response,
> you **must** warn the user that legacy models like `gemini-2.5-*`,
> `gemini-2.0-*`, or `gemini-1.5-*` are deprecated and unsupported for the
> Interactions API. * **GEAP requires a provisioned agent (no direct base-model
> calls yet)**: On Gemini Enterprise Agent Platform (GEAP), direct/base-model
> calls (`model="..."`) via the Interactions API are **not supported yet**. You
> **must** target a provisioned agent or endpoint with the `agent="<AGENT_ID>"`
> parameter instead of `model="..."`. The code examples in this skill use
> `agent=...` for this reason. (This is the primary difference from the
> [ai.google.dev](https://ai.google.dev/gemini-api/docs/interactions)
> documentation for Interactions, which uses `model=...` — while `model=...` is
> valid for other Gemini API contexts, it is **not supported on the Agent
> Platform**.) Provision an agent per the
> [Agent Platform docs](https://docs.cloud.google.com/gemini-enterprise-agent-platform)
> and pass its ID as `agent`. * **Turn-Scoped Parameters**: Parameters like
> `tools`, `system_instruction`, and `generation_config` are turn-scoped. They
> **MUST** be passed with each interaction request.

## 1. Authentication

Before running any code, ensure you are authenticated with Application Default Credentials (ADC) and have the necessary API enabled.

1.  **Login**:
    
    ```bash
    gcloud auth application-default login
    ```
2.  **Enable API** (if not already enabled):
    
    ```bash
    gcloud services enable aiplatform.googleapis.com
    ```

---

## 2. Client Initialization

You can initialize the client using environment variables (recommended) or by passing explicit configuration parameters.

### Option A: Environment Variables (Recommended)

Configure environment variables to let the SDK automatically resolve settings:

```bash
export GOOGLE_GENAI_USE_ENTERPRISE=true
export GOOGLE_CLOUD_PROJECT="your-project-id"
export GOOGLE_CLOUD_LOCATION="global"
```

#### Python

```python
from google import genai

# The SDK automatically picks up the environment variables
client = genai.Client()
```

#### TypeScript/JavaScript

```typescript
import { GoogleGenAI } from "@google/genai";

// The SDK automatically picks up the environment variables
const ai = new GoogleGenAI();
```

### Option B: Explicit Inline Parameters

Alternatively, pass configuration values directly inside your code:

#### Python

```python
from google import genai
import google.auth

_, project_id = google.auth.default()
client = genai.Client(enterprise=True, project=project_id, location="global")
```

#### TypeScript/JavaScript

```typescript
import { GoogleGenAI } from "@google/genai";

const ai = new GoogleGenAI({
    enterprise: {
        project: "your-project-id",
        location: "global"
    }
});
```

---

## 3. Core Interactions API Usage

### Quick Start (Single-Turn)

Submit a single prompt and read the final text response. Under the modern schema, output content is retrieved from the `steps` list.

#### Python

```python
interaction = client.interactions.create(
    agent="your-agent-id",  # GEAP: target a provisioned agent, not a base model
    input="Explain serverless computing in one sentence."
)
# Use the output_text convenience accessor (combined text from the trailing model_output steps)
print(interaction.output_text)
```

#### TypeScript/JavaScript

```typescript
const interaction = await ai.interactions.create({
    agent: "your-agent-id", // GEAP: target a provisioned agent, not a base model
    input: "Explain serverless computing in one sentence."
});
console.log(interaction.output_text);
```

---

### Stateful Conversation (Multi-Turn)

Interactions are stateful by default. Store the conversation state in the cloud and reference it in the subsequent turn using `previous_interaction_id`.

#### Python

```python
# Turn 1: Introduce ourselves
# Interactions are stored by default (store=True); pass store=False to disable
# server-side retention (which also disables previous_interaction_id and background).
turn1 = client.interactions.create(
    agent="your-agent-id",
    input="Hi! My name is John. I am working on AI agents.",
    store=True
)
print(f"Turn 1: {turn1.output_text}")

# Turn 2: Refer back to the stored turn state
turn2 = client.interactions.create(
    agent="your-agent-id",
    input="What is my name?",
    previous_interaction_id=turn1.id
)
print(f"Turn 2: {turn2.output_text}")
```

#### TypeScript/JavaScript

```typescript
// Turn 1 (interactions are stored by default; pass store: false to disable)
const turn1 = await ai.interactions.create({
    agent: "your-agent-id",
    input: "Hi! My name is John. I am working on AI agents.",
    store: true
});

// Turn 2
const turn2 = await ai.interactions.create({
    agent: "your-agent-id",
    input: "What is my name?",
    previousInteractionId: turn1.id
});
console.log(turn2.output_text);
```

---

### Real-Time Streaming

Stream responses in real-time. Passing `stream=True` returns an iterable chunk generator.

#### Python

```python
# The stream yields typed events, not full interaction snapshots. The sequence is:
# interaction.created -> (step.start -> step.delta(s) -> step.stop)+ -> interaction.completed
for event in client.interactions.create(
    agent="your-agent-id",
    input="Write a short poem about debugging.",
    stream=True
):
    if event.event_type == "step.delta":
        if event.delta.type == "text":
            print(event.delta.text, end="", flush=True)
    elif event.event_type == "interaction.completed":
        print()
```

#### TypeScript/JavaScript

```typescript
// The stream yields typed events, not full interaction snapshots. The sequence is:
// interaction.created -> (step.start -> step.delta(s) -> step.stop)+ -> interaction.completed
const responseStream = await ai.interactions.create({
    agent: "your-agent-id",
    input: "Write a short poem about debugging.",
    stream: true
});

for await (const event of responseStream) {
    if (event.event_type === "step.delta") {
        if (event.delta.type === "text") {
            process.stdout.write(event.delta.text);
        }
    } else if (event.event_type === "interaction.completed") {
        console.log();
    }
}
```

---

### Structured Output (Pydantic / Polymorphic `response_format`)

Retrieve structured, type-safe JSON matching a schema. Under the modern Interactions API, a polymorphic `response_format` argument directly takes the target schema structure.

#### Python

```python
from pydantic import BaseModel, Field

class Book(BaseModel):
    title: str = Field(description="The title of the book")
    author: str = Field(description="The book's author")
    year_published: int

interaction = client.interactions.create(
    agent="your-agent-id",
    input="Recommend one famous sci-fi book.",
    response_format=Book
)

# The text will be a valid JSON matching the Book schema
print(interaction.output_text)
```

#### TypeScript/JavaScript

```typescript
import { Type } from "@google/genai";

const BookSchema = {
    type: Type.OBJECT,
    properties: {
        title: { type: Type.STRING, description: "The title of the book" },
        author: { type: Type.STRING, description: "The book's author" },
        yearPublished: { type: Type.INTEGER }
    },
    required: ["title", "author", "yearPublished"]
};

const interaction = await ai.interactions.create({
    agent: "your-agent-id",
    input: "Recommend one famous sci-fi book.",
    responseFormat: BookSchema
});

console.log(interaction.output_text);
```

---

### Function Calling (Agent Tool Use)

Define local tools (functions) and submit execution results to the stateful interaction history.

#### Python

```python
import json

def get_stock_price(ticker: str) -> float:
    """Gets the stock price for a given ticker symbol."""
    if ticker.upper() == "GOOG":
        return 175.50
    return 100.0

# Turn 1: Pass tools to the model
interaction = client.interactions.create(
    agent="your-agent-id",
    input="What is the stock price of GOOG?",
    tools=[get_stock_price]
)

# In the flat steps schema, a tool request is a top-level step of type
# "function_call" with flat `name` and `arguments` fields (no nested tool_calls).
for step in interaction.steps:
    if step.type == "function_call" and step.name == "get_stock_price":
        ticker_arg = step.arguments.get("ticker")
        price = get_stock_price(ticker_arg)

        # Turn 2: Submit the result back as a function_result step. Reference the
        # originating call via call_id=step.id, and pass tools again (turn-scoped).
        final_turn = client.interactions.create(
            agent="your-agent-id",
            input=[
                {
                    "type": "function_result",
                    "name": step.name,
                    "call_id": step.id,
                    "result": [{"type": "text", "text": json.dumps(price)}],
                }
            ],
            tools=[get_stock_price],
            previous_interaction_id=interaction.id
        )
        print(final_turn.output_text)
```

#### TypeScript/JavaScript

```typescript
import { Type } from "@google/genai";

// Define local tool
function getStockPrice({ ticker }: { ticker: string }): number {
    if (ticker.toUpperCase() === "GOOG") {
        return 175.50;
    }
    return 100.00;
}

// Turn 1: Pass tools to the model
const toolDeclaration = {
    functionDeclarations: [{
        name: "getStockPrice",
        description: "Gets the stock price for a given ticker symbol.",
        parameters: {
            type: Type.OBJECT,
            properties: {
                ticker: { type: Type.STRING, description: "The stock ticker symbol" }
            },
            required: ["ticker"]
        }
    }]
};

const interaction = await ai.interactions.create({
    agent: "your-agent-id",
    input: "What is the stock price of GOOG?",
    tools: [toolDeclaration]
});

// In the flat steps schema, a tool request is a top-level step of type
// "function_call" with flat `name` and `arguments` fields (no nested toolCalls).
const fcStep = interaction.steps.find(s => s.type === "function_call");
if (fcStep && fcStep.name === "getStockPrice") {
    const tickerArg = fcStep.arguments.ticker as string;
    const price = getStockPrice({ ticker: tickerArg });

    // Turn 2: Submit the result back as a function_result step. Reference the
    // originating call via call_id=fcStep.id, and pass tools again (turn-scoped).
    const finalTurn = await ai.interactions.create({
        agent: "your-agent-id",
        input: [{
            type: "function_result",
            name: fcStep.name,
            call_id: fcStep.id,
            result: [{ type: "text", text: JSON.stringify(price) }]
        }],
        tools: [toolDeclaration],
        previousInteractionId: interaction.id
    });
    console.log(finalTurn.output_text);
}
```

---

## 4. Accessing the Interactions API via REST

Detail moved to `references/4-accessing-the-interactions-api-via-rest.md`.

## 5. Data Model & Step Types Reference

Detail moved to `references/5-data-model-step-types-reference.md`.

