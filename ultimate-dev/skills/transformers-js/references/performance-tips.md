<!-- Moved verbatim from transformers-js/SKILL.md, the
     'performance-tips' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Performance Tips

1. **Reuse Pipelines**: Create pipeline once, reuse for multiple inferences
2. **Use Quantization**: Start with `q8` or `q4` for faster inference
3. **Batch Processing**: Process multiple inputs together when possible
4. **Cache Models**: Models are cached automatically (see **[Caching Reference](./references/CACHE.md)** for details on browser Cache API, Node.js filesystem cache, and custom implementations)
5. **WebGPU for Large Models**: Use WebGPU for models that benefit from GPU acceleration
6. **Prune Context**: For text generation, limit `max_new_tokens` to avoid memory issues
7. **Clean Up Resources**: Call `pipe.dispose()` when done to free memory
