<!-- Moved verbatim from transformers-js/SKILL.md, the 'section' section. Relative links were rebased for the new depth; the prose is otherwise unchanged. -->

# Troubleshooting

### Model Not Found
- Verify model exists on Hugging Face Hub
- Check model name spelling
- Ensure model has ONNX files (look for `onnx` folder in model repo)

### Memory Issues
- Use smaller models or quantized versions (`dtype: 'q4'`)
- Reduce batch size
- Limit sequence length with `max_length`

### WebGPU Errors
- Check browser compatibility (Chrome 113+, Edge 113+)
- Try `dtype: 'fp16'` if `fp32` fails
- Fall back to WASM if WebGPU unavailable
