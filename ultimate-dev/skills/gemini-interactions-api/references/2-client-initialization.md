<!-- Moved verbatim from gemini-interactions-api/SKILL.md, the
     '2-client-initialization' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

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
