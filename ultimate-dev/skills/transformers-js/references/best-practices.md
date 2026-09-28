<!-- Moved verbatim from transformers-js/SKILL.md, the 'section' section. Relative links were rebased for the new depth; the prose is otherwise unchanged. -->

# Best Practices

1. **Always Dispose Pipelines**: Call `pipe.dispose()` when done - critical for preventing memory leaks
2. **Start with Pipelines**: Use the pipeline API unless you need fine-grained control
3. **Test Locally First**: Test models with small inputs before deploying
4. **Monitor Model Sizes**: Be aware of model download sizes for web applications
5. **Handle Loading States**: Show progress indicators for better UX
6. **Version Pin**: Pin specific model versions for production stability
7. **Error Boundaries**: Always wrap pipeline calls in try-catch blocks
8. **Progressive Enhancement**: Provide fallbacks for unsupported browsers
9. **Reuse Models**: Load once, use many times - don't recreate pipelines unnecessarily
10. **Graceful Shutdown**: Dispose models on SIGTERM/SIGINT in servers
