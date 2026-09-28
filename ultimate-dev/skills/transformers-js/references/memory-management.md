<!-- Moved verbatim from transformers-js/SKILL.md, the 'section' section. Relative links were rebased for the new depth; the prose is otherwise unchanged. -->

# Memory Management

**IMPORTANT:** Always call `pipe.dispose()` when finished to prevent memory leaks.

```javascript
const pipe = await pipeline('sentiment-analysis');
const result = await pipe('Great product!');
await pipe.dispose();  // ✓ Free memory (100MB - several GB per model)
```

**When to dispose:**
- Application shutdown or component unmount
- Before loading a different model
- After batch processing in long-running apps

Models consume significant memory and hold GPU/CPU resources. Disposal is critical for browser memory limits and server stability.

For detailed patterns (React cleanup, servers, browser), see **[Code Examples](./EXAMPLES.md)**
