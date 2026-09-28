<!-- Moved verbatim from transformers-js/SKILL.md, the
     'finding-and-choosing-models' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

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
