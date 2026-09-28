<!-- Moved verbatim from transformers-js/SKILL.md, the 'section' section. Relative links were rebased for the new depth; the prose is otherwise unchanged. -->

# Advanced Configuration

### Environment Configuration (`env`)

The `env` object provides comprehensive control over Transformers.js execution, caching, and model loading.

**Quick Overview:**

```javascript
import { env, LogLevel } from '@huggingface/transformers';

// View version
console.log(env.version); // e.g., '4.x'

// Common settings
env.allowRemoteModels = true;  // Load from Hugging Face Hub
env.allowLocalModels = false;  // Load from file system
env.localModelPath = '/models/'; // Local model directory
env.useFSCache = true;         // Cache models on disk (Node.js)
env.useBrowserCache = true;    // Cache models in browser
env.cacheDir = './.cache';     // Cache directory location
// Optional: override logging level (default is LogLevel.WARNING)
env.logLevel = LogLevel.INFO;

// Optional: custom fetch for auth headers, retries, abort signals, etc.
env.fetch = (url, options) =>
  fetch(url, {
    ...options,
    headers: {
      ...options?.headers,
      Authorization: `Bearer ${HF_TOKEN}`,
    },
  });
```

**Configuration Patterns:**

```javascript
// Development: Fast iteration with remote models
env.allowRemoteModels = true;
env.useFSCache = true;

// Production: Local models only
env.allowRemoteModels = false;
env.allowLocalModels = true;
env.localModelPath = '/app/models/';

// Custom CDN
env.remoteHost = 'https://cdn.example.com/models';

// Disable caching (testing)
env.useFSCache = false;
env.useBrowserCache = false;
```

For complete documentation on all configuration options, caching strategies, cache management, pre-downloading models, and more, see:

**→ [Configuration Reference](./CONFIGURATION.md)**

### ModelRegistry (v4)

`ModelRegistry` gives you visibility and control over model assets before loading a pipeline. Use it to estimate download size, check cache status, inspect available dtypes, and clear cached artifacts for a specific task/model/options tuple.

```javascript
import { ModelRegistry } from '@huggingface/transformers';

const task = 'feature-extraction';
const modelId = 'onnx-community/all-MiniLM-L6-v2-ONNX';
const modelOptions = { dtype: 'fp32' };

// List required files for this pipeline
const files = await ModelRegistry.get_pipeline_files(task, modelId, modelOptions);

// Check if assets are already cached
const cached = await ModelRegistry.is_pipeline_cached(task, modelId, modelOptions);

// Inspect precision formats available for this model
const dtypes = await ModelRegistry.get_available_dtypes(modelId);

console.log({ files: files.length, cached, dtypes });
```

For production patterns and full API coverage, see **[ModelRegistry Reference](./MODEL_REGISTRY.md)**.

### Standalone Tokenization (`@huggingface/tokenizers`)

For tokenization-only workflows, use `@huggingface/tokenizers`. It is a separate lightweight package useful when you need fast tokenization/encoding without loading full model inference pipelines.

```bash
npm install @huggingface/tokenizers
```

```javascript
import { Tokenizer } from '@huggingface/tokenizers';
```

### Working with Tensors

```javascript
import { AutoTokenizer, AutoModel } from '@huggingface/transformers';

// Load tokenizer and model separately for more control
const tokenizer = await AutoTokenizer.from_pretrained('bert-base-uncased');
const model = await AutoModel.from_pretrained('bert-base-uncased');

// Tokenize input
const inputs = await tokenizer('Hello world!');

// Run model
const outputs = await model(inputs);
```

### Batch Processing

```javascript
const classifier = await pipeline('sentiment-analysis');

// Process multiple texts
const results = await classifier([
  'I love this!',
  'This is terrible.',
  'It was okay.'
]);
```
