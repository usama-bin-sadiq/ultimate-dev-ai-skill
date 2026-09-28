---
name: transformers-js
description: Use Transformers.js to run state-of-the-art machine learning models directly in JavaScript/TypeScript. Supports NLP (text classification, translation, summarization), computer vision (image classification, object detection), audio (speech recognition, audio classification), and multimodal tasks. Works in browsers and server-side runtimes (Node.js, Bun, Deno) with WebGPU/WASM using pre-trained models from Hugging Face Hub.
license: Apache-2.0
metadata:
  author: huggingface
  version: "4.x"
  category: machine-learning
  repository: https://github.com/huggingface/transformers.js
compatibility: Requires Node.js 18+ (or compatible Bun/Deno runtime) or modern browser with ES modules support. WebGPU requires runtime and hardware support; WASM is the broad fallback. Internet access is needed for downloading models from Hugging Face Hub (optional if using local models).
---

# Transformers.js - Machine Learning for JavaScript

Transformers.js enables running state-of-the-art machine learning models directly in JavaScript across browsers and server-side runtimes (Node.js, Bun, Deno), with no Python server required.

## When to Use This Skill

Use this skill when you need to:
- Run ML models for text analysis, generation, or translation in JavaScript
- Perform image classification, object detection, or segmentation
- Implement speech recognition or audio processing
- Build multimodal AI applications (text-to-image, image-to-text, etc.)
- Run models client-side in the browser without a backend

## Installation

### NPM Installation
```bash
npm install @huggingface/transformers
```

### Browser Usage (CDN)
```javascript
<script type="module">
  import { pipeline } from 'https://cdn.jsdelivr.net/npm/@huggingface/transformers';
</script>
```

## Core Concepts

### 1. Pipeline API
The pipeline API is the easiest way to use models. It groups together preprocessing, model inference, and postprocessing:

```javascript
import { pipeline } from '@huggingface/transformers';

// Create a pipeline for a specific task
const pipe = await pipeline('sentiment-analysis');

// Use the pipeline
const result = await pipe('I love transformers!');
// Output: [{ label: 'POSITIVE', score: 0.999817686 }]

// IMPORTANT: Always dispose when done to free memory
await pipe.dispose();
```

**⚠️ Memory Management:** All pipelines must be disposed with `pipe.dispose()` when finished to prevent memory leaks. See examples in [Code Examples](./references/EXAMPLES.md) for cleanup patterns across different environments.

### 2. Model Selection
You can specify a custom model as the second argument:

```javascript
const pipe = await pipeline(
  'sentiment-analysis',
  'Xenova/bert-base-multilingual-uncased-sentiment'
);
```

**Finding Models:**

Browse available Transformers.js models on Hugging Face Hub:
- **All models**: https://huggingface.co/models?library=transformers.js&sort=trending
- **By task**: Add `pipeline_tag` parameter
  - Text generation: https://huggingface.co/models?pipeline_tag=text-generation&library=transformers.js&sort=trending
  - Image classification: https://huggingface.co/models?pipeline_tag=image-classification&library=transformers.js&sort=trending
  - Speech recognition: https://huggingface.co/models?pipeline_tag=automatic-speech-recognition&library=transformers.js&sort=trending

**Tip:** Filter by task type, sort by trending/downloads, and check model cards for performance metrics and usage examples.

### 3. Device Selection
Choose where to run the model:

```javascript
// Run on CPU (default for WASM)
const pipe = await pipeline('sentiment-analysis', 'model-id');

// Run on GPU (WebGPU)
const pipe = await pipeline('sentiment-analysis', 'model-id', {
  device: 'webgpu',
});
```

### 4. Quantization Options
Control model precision vs. performance:

```javascript
// Use quantized model (faster, smaller)
const pipe = await pipeline('sentiment-analysis', 'model-id', {
  dtype: 'q4',  // Options: 'fp32', 'fp16', 'q8', 'q4'
});
```

## Supported Tasks

**Note:** All examples below show basic usage.

### Natural Language Processing

#### Text Classification
```javascript
const classifier = await pipeline('text-classification');
const result = await classifier('This movie was amazing!');
```

#### Named Entity Recognition (NER)
```javascript
const ner = await pipeline('token-classification');
const entities = await ner('My name is John and I live in New York.');
```

#### Question Answering
```javascript
const qa = await pipeline('question-answering');
const answer = await qa({
  question: 'What is the capital of France?',
  context: 'Paris is the capital and largest city of France.'
});
```

#### Text Generation
```javascript
const generator = await pipeline('text-generation', 'onnx-community/gemma-3-270m-it-ONNX');
const text = await generator('Once upon a time', {
  max_new_tokens: 100,
  temperature: 0.7
});
```

**For streaming and chat:** See **[Text Generation Guide](./references/TEXT_GENERATION.md)** for:
- Streaming token-by-token output with `TextStreamer`
- Chat/conversation format with system/user/assistant roles
- Generation parameters (temperature, top_k, top_p)
- Browser and Node.js examples
- React components and API endpoints

#### Translation
```javascript
const translator = await pipeline('translation', 'Xenova/nllb-200-distilled-600M');
const output = await translator('Hello, how are you?', {
  src_lang: 'eng_Latn',
  tgt_lang: 'fra_Latn'
});
```

#### Summarization
```javascript
const summarizer = await pipeline('summarization');
const summary = await summarizer(longText, {
  max_length: 100,
  min_length: 30
});
```

#### Zero-Shot Classification
```javascript
const classifier = await pipeline('zero-shot-classification');
const result = await classifier('This is a story about sports.', ['politics', 'sports', 'technology']);
```

### Computer Vision

#### Image Classification
```javascript
const classifier = await pipeline('image-classification');
const result = await classifier('https://example.com/image.jpg');
// Or with local file
const result = await classifier(imageUrl);
```

#### Object Detection
```javascript
const detector = await pipeline('object-detection');
const objects = await detector('https://example.com/image.jpg');
// Returns: [{ label: 'person', score: 0.95, box: { xmin, ymin, xmax, ymax } }, ...]
```

#### Image Segmentation
```javascript
const segmenter = await pipeline('image-segmentation');
const segments = await segmenter('https://example.com/image.jpg');
```

#### Depth Estimation
```javascript
const depthEstimator = await pipeline('depth-estimation');
const depth = await depthEstimator('https://example.com/image.jpg');
```

#### Zero-Shot Image Classification
```javascript
const classifier = await pipeline('zero-shot-image-classification');
const result = await classifier('image.jpg', ['cat', 'dog', 'bird']);
```

### Audio Processing

#### Automatic Speech Recognition
```javascript
const transcriber = await pipeline('automatic-speech-recognition');
const result = await transcriber('audio.wav');
// Returns: { text: 'transcribed text here' }
```

#### Audio Classification
```javascript
const classifier = await pipeline('audio-classification');
const result = await classifier('audio.wav');
```

#### Text-to-Speech
```javascript
const synthesizer = await pipeline('text-to-speech', 'Xenova/speecht5_tts');
const audio = await synthesizer('Hello, this is a test.', {
  speaker_embeddings: speakerEmbeddings
});
```

### Multimodal

#### Image-to-Text (Image Captioning)
```javascript
const captioner = await pipeline('image-to-text');
const caption = await captioner('image.jpg');
```

#### Document Question Answering
```javascript
const docQA = await pipeline('document-question-answering');
const answer = await docQA('document-image.jpg', 'What is the total amount?');
```

#### Zero-Shot Object Detection
```javascript
const detector = await pipeline('zero-shot-object-detection');
const objects = await detector('image.jpg', ['person', 'car', 'tree']);
```

### Feature Extraction (Embeddings)

```javascript
const extractor = await pipeline('feature-extraction');
const embeddings = await extractor('This is a sentence to embed.');
// Returns: tensor of shape [1, sequence_length, hidden_size]

// For sentence embeddings (mean pooling)
const extractor = await pipeline('feature-extraction', 'onnx-community/all-MiniLM-L6-v2-ONNX');
const embeddings = await extractor('Text to embed', { pooling: 'mean', normalize: true });
```

## Finding and Choosing Models

### Browsing the Hugging Face Hub

Discover compatible Transformers.js models on Hugging Face Hub:

**Base URL (all models):**
```
https://huggingface.co/models?library=transformers.js&sort=trending
```

**Filter by task** using the `pipeline_tag` parameter:

| Task | URL |
|------|-----|
| **Text Generation** | https://huggingface.co/models?pipeline_tag=text-generation&library=transformers.js&sort=trending |
| **Text Classification** | https://huggingface.co/models?pipeline_tag=text-classification&library=transformers.js&sort=trending |
| **Translation** | https://huggingface.co/models?pipeline_tag=translation&library=transformers.js&sort=trending |
| **Summarization** | https://huggingface.co/models?pipeline_tag=summarization&library=transformers.js&sort=trending |
| **Question Answering** | https://huggingface.co/models?pipeline_tag=question-answering&library=transformers.js&sort=trending |
| **Image Classification** | https://huggingface.co/models?pipeline_tag=image-classification&library=transformers.js&sort=trending |
| **Object Detection** | https://huggingface.co/models?pipeline_tag=object-detection&library=transformers.js&sort=trending |
| **Image Segmentation** | https://huggingface.co/models?pipeline_tag=image-segmentation&library=transformers.js&sort=trending |
| **Speech Recognition** | https://huggingface.co/models?pipeline_tag=automatic-speech-recognition&library=transformers.js&sort=trending |
| **Audio Classification** | https://huggingface.co/models?pipeline_tag=audio-classification&library=transformers.js&sort=trending |
| **Image-to-Text** | https://huggingface.co/models?pipeline_tag=image-to-text&library=transformers.js&sort=trending |
| **Feature Extraction** | https://huggingface.co/models?pipeline_tag=feature-extraction&library=transformers.js&sort=trending |
| **Zero-Shot Classification** | https://huggingface.co/models?pipeline_tag=zero-shot-classification&library=transformers.js&sort=trending |

**Sort options:**
- `&sort=trending` - Most popular recently
- `&sort=downloads` - Most downloaded overall
- `&sort=likes` - Most liked by community
- `&sort=modified` - Recently updated

### Choosing the Right Model

Consider these factors when selecting a model:

**1. Model Size**
- **Small (< 100MB)**: Fast, suitable for browsers, limited accuracy
- **Medium (100MB - 500MB)**: Balanced performance, good for most use cases
- **Large (> 500MB)**: High accuracy, slower, better for Node.js or powerful devices

**2. Quantization**
Models are often available in different quantization levels:
- `fp32` - Full precision (largest, most accurate)
- `fp16` - Half precision (smaller, still accurate)
- `q8` - 8-bit quantized (much smaller, slight accuracy loss)
- `q4` - 4-bit quantized (smallest, noticeable accuracy loss)

**3. Task Compatibility**
Check the model card for:
- Supported tasks (some models support multiple tasks)
- Input/output formats
- Language support (multilingual vs. English-only)
- License restrictions

**4. Performance Metrics**
Model cards typically show:
- Accuracy scores
- Benchmark results
- Inference speed
- Memory requirements

### Example: Finding a Text Generation Model

```javascript
// 1. Visit: https://huggingface.co/models?pipeline_tag=text-generation&library=transformers.js&sort=trending

// 2. Browse and select a model (e.g., onnx-community/gemma-3-270m-it-ONNX)

// 3. Check model card for:
//    - Model size: ~270M parameters
//    - Quantization: q4 available
//    - Language: English
//    - Use case: Instruction-following chat

// 4. Use the model:
import { pipeline } from '@huggingface/transformers';

const generator = await pipeline(
  'text-generation',
  'onnx-community/gemma-3-270m-it-ONNX',
  { dtype: 'q4' } // Use quantized version for faster inference
);

const output = await generator('Explain quantum computing in simple terms.', {
  max_new_tokens: 100
});

await generator.dispose();
```

### Tips for Model Selection

1. **Start Small**: Test with a smaller model first, then upgrade if needed
2. **Check ONNX Support**: Ensure the model has ONNX files (look for `onnx` folder in model repo)
3. **Read Model Cards**: Model cards contain usage examples, limitations, and benchmarks
4. **Test Locally**: Benchmark inference speed and memory usage in your environment
5. **Filter by Library**: Use `library=transformers.js` to find compatible models: https://huggingface.co/models?library=transformers.js
6. **Version Pin**: Use specific git commits in production for stability:
   ```javascript
   const pipe = await pipeline('task', 'model-id', { revision: 'abc123' });
   ```

## Advanced Configuration

Detail moved to `references/advanced-configuration.md`.

## Runtime-Specific Considerations

Detail moved to `references/runtime-specific-considerations.md`.

## Error Handling

Detail moved to `references/error-handling.md`.

## Performance Tips

1. **Reuse Pipelines**: Create pipeline once, reuse for multiple inferences
2. **Use Quantization**: Start with `q8` or `q4` for faster inference
3. **Batch Processing**: Process multiple inputs together when possible
4. **Cache Models**: Models are cached automatically (see **[Caching Reference](./references/CACHE.md)** for details on browser Cache API, Node.js filesystem cache, and custom implementations)
5. **WebGPU for Large Models**: Use WebGPU for models that benefit from GPU acceleration
6. **Prune Context**: For text generation, limit `max_new_tokens` to avoid memory issues
7. **Clean Up Resources**: Call `pipe.dispose()` when done to free memory

## Memory Management

Detail moved to `references/memory-management.md`.

## Troubleshooting

Detail moved to `references/troubleshooting.md`.

## Reference Documentation

Detail moved to `references/reference-documentation.md`.

## Best Practices

Detail moved to `references/best-practices.md`.

## Quick Reference: Task IDs

| Task | Task ID |
|------|---------|
| Text classification | `text-classification` or `sentiment-analysis` |
| Token classification | `token-classification` or `ner` |
| Question answering | `question-answering` |
| Fill mask | `fill-mask` |
| Summarization | `summarization` |
| Translation | `translation` |
| Text generation | `text-generation` |
| Text-to-text generation | `text2text-generation` |
| Zero-shot classification | `zero-shot-classification` |
| Image classification | `image-classification` |
| Image segmentation | `image-segmentation` |
| Object detection | `object-detection` |
| Depth estimation | `depth-estimation` |
| Image-to-image | `image-to-image` |
| Zero-shot image classification | `zero-shot-image-classification` |
| Zero-shot object detection | `zero-shot-object-detection` |
| Automatic speech recognition | `automatic-speech-recognition` |
| Audio classification | `audio-classification` |
| Text-to-speech | `text-to-speech` or `text-to-audio` |
| Image-to-text | `image-to-text` |
| Document question answering | `document-question-answering` |
| Feature extraction | `feature-extraction` |
| Sentence similarity | `sentence-similarity` |

---

This skill enables you to integrate state-of-the-art machine learning capabilities directly into JavaScript applications without requiring separate ML servers or Python environments.

## Reference files

Detail moved to `references/reference-files.md`.


## Reference Index

7 reference file(s) are named in `references/README.md`.
