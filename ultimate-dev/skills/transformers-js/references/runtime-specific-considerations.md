<!-- Moved verbatim from transformers-js/SKILL.md, the
     'runtime-specific-considerations' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Runtime-Specific Considerations

### WebGPU Usage
WebGPU provides GPU acceleration in browsers and server-side runtimes (when supported):

```javascript
const pipe = await pipeline('text-generation', 'onnx-community/gemma-3-270m-it-ONNX', {
  device: 'webgpu',
  dtype: 'fp32'
});
```

**Note**: Use `webgpu` when available and fall back to WASM/CPU when not supported in the current runtime.

### WASM Performance
WASM is the most compatible execution backend across runtimes:

```javascript
// Optimized for browsers with quantization
const pipe = await pipeline('sentiment-analysis', 'model-id', {
  dtype: 'q8'  // or 'q4' for even smaller size
});
```

### Progress Tracking & Loading Indicators

Models can be large (ranging from a few MB to several GB) and consist of multiple files. Track download progress by passing a callback to the `pipeline()` function:

```javascript
import { pipeline } from '@huggingface/transformers';

// Track progress for each file
const fileProgress = {};

function onProgress(info) {
  if (info.status === 'progress_total') {
    console.log(`Total: ${info.progress.toFixed(1)}%`);
    return;
  }

  console.log(`${info.status}: ${info.file ?? ''}`);
  
  if (info.status === 'progress') {
    fileProgress[info.file] = info.progress;
    console.log(`${info.file}: ${info.progress.toFixed(1)}%`);
  }
  
  if (info.status === 'done') {
    console.log(`✓ ${info.file} complete`);
  }
}

// Pass callback to pipeline
const classifier = await pipeline('sentiment-analysis', null, {
  progress_callback: onProgress
});
```

**Progress Info Properties:**

```typescript
interface ProgressInfo {
  status: 'initiate' | 'download' | 'progress' | 'progress_total' | 'done' | 'ready';
  name: string;      // Model id or path
  file?: string;     // File being processed (per-file events)
  progress?: number; // Percentage (0-100, for 'progress' and 'progress_total')
  loaded?: number;   // Bytes downloaded (only for 'progress' status)
  total?: number;    // Total bytes (only for 'progress' status)
}
```

For complete examples including browser UIs, React components, CLI progress bars, and retry logic, see:

**→ [Pipeline Options - Progress Callback](./references/PIPELINE_OPTIONS.md#progress-callback)**
