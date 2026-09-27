# Upstream skill audit

This audit compares every shared global skill in `~/.agents/skills` with its mapped original. The comparison used current upstream `main` on 2026-08-24. "Package" is a recursive directory comparison, so references, scripts, assets, and Codex metadata all count.

Every package with outside lineage differed from its original. The repository now owns those installed Codex forks. The three native packages already matched their canonical copies here.

## Source revisions

| Original | Revision | Compared packages | Result |
|---|---|---:|---|
| [Cursor pstack](https://github.com/cursor/plugins/tree/main/pstack) | `4612556` | 28 | Promoted as Codex forks |
| [mattpocock/skills](https://github.com/mattpocock/skills) | `6654f6b` | 23 | Promoted as Codex forks |
| [humanlayer/skills](https://github.com/humanlayer/skills) | `3c26291` | 1 | Promoted as a Codex fork |
| [kitlangton/skills](https://github.com/kitlangton/skills) | `0cace2a` | 1 | Promoted in the preceding audit |
| This repository | `33802bb` | 3 | Already canonical |

## Per-skill comparison

| Skill | Original | Revision | `SKILL.md` | Package | Outcome |
|---|---|---|---|---|---|
| `architect` | [Cursor pstack](https://github.com/cursor/plugins/tree/main/pstack) | `4612556` | Different | Different | Promoted |
| `arena` | [Cursor pstack](https://github.com/cursor/plugins/tree/main/pstack) | `4612556` | Different | Different | Promoted |
| `blast-radius` | [Cursor pstack](https://github.com/cursor/plugins/tree/main/pstack) | `4612556` | Different | Different | Promoted |
| `bro` | [Cursor pstack](https://github.com/cursor/plugins/tree/main/pstack) | `4612556` | Different | Different | Promoted |
| `code-review` | [mattpocock/skills](https://github.com/mattpocock/skills) | `6654f6b` | Different | Different | Promoted |
| `codebase-design` | [mattpocock/skills](https://github.com/mattpocock/skills) | `6654f6b` | Different | Different | Promoted |
| `deslop` | This repository | `33802bb` | Same | Same | Already canonical |
| `diagnosing-bugs` | [mattpocock/skills](https://github.com/mattpocock/skills) | `6654f6b` | Different | Different | Promoted |
| `domain-modeling` | [mattpocock/skills](https://github.com/mattpocock/skills) | `6654f6b` | Different | Different | Promoted |
| `effect` | [kitlangton/skills](https://github.com/kitlangton/skills) | `0cace2a` | Different | Different | Promoted |
| `grill-me` | [mattpocock/skills](https://github.com/mattpocock/skills) | `6654f6b` | Different | Different | Promoted |
| `grill-with-docs` | [mattpocock/skills](https://github.com/mattpocock/skills) | `6654f6b` | Different | Different | Promoted |
| `grilling` | [mattpocock/skills](https://github.com/mattpocock/skills) | `6654f6b` | Different | Different | Promoted |
| `handoff` | [mattpocock/skills](https://github.com/mattpocock/skills) | `6654f6b` | Different | Different | Promoted |
| `how` | [Cursor pstack](https://github.com/cursor/plugins/tree/main/pstack) | `4612556` | Different | Different | Promoted |
| `implement` | [mattpocock/skills](https://github.com/mattpocock/skills) | `6654f6b` | Different | Different | Promoted |
| `improve-codebase-architecture` | [mattpocock/skills](https://github.com/mattpocock/skills) | `6654f6b` | Different | Different | Promoted |
| `interrogate` | [Cursor pstack](https://github.com/cursor/plugins/tree/main/pstack) | `4612556` | Different | Different | Promoted |
| `principle-boundary-discipline` | [Cursor pstack](https://github.com/cursor/plugins/tree/main/pstack) | `4612556` | Different | Different | Promoted |
| `principle-encode-lessons-in-structure` | [Cursor pstack](https://github.com/cursor/plugins/tree/main/pstack) | `4612556` | Different | Different | Promoted |
| `principle-exhaust-the-design-space` | [Cursor pstack](https://github.com/cursor/plugins/tree/main/pstack) | `4612556` | Different | Different | Promoted |
| `principle-fix-root-causes` | [Cursor pstack](https://github.com/cursor/plugins/tree/main/pstack) | `4612556` | Different | Different | Promoted |
| `principle-foundational-thinking` | [Cursor pstack](https://github.com/cursor/plugins/tree/main/pstack) | `4612556` | Different | Different | Promoted |
| `principle-guard-the-context-window` | [Cursor pstack](https://github.com/cursor/plugins/tree/main/pstack) | `4612556` | Different | Different | Promoted |
| `principle-laziness-protocol` | [Cursor pstack](https://github.com/cursor/plugins/tree/main/pstack) | `4612556` | Different | Different | Promoted |
| `principle-make-operations-idempotent` | [Cursor pstack](https://github.com/cursor/plugins/tree/main/pstack) | `4612556` | Different | Different | Promoted |
| `principle-minimize-reader-load` | [Cursor pstack](https://github.com/cursor/plugins/tree/main/pstack) | `4612556` | Different | Different | Promoted |
| `principle-outcome-oriented-execution` | [Cursor pstack](https://github.com/cursor/plugins/tree/main/pstack) | `4612556` | Different | Different | Promoted |
| `principle-prove-it-works` | [Cursor pstack](https://github.com/cursor/plugins/tree/main/pstack) | `4612556` | Different | Different | Promoted |
| `principle-redesign-from-first-principles` | [Cursor pstack](https://github.com/cursor/plugins/tree/main/pstack) | `4612556` | Different | Different | Promoted |
| `principle-separate-before-serializing-shared-state` | [Cursor pstack](https://github.com/cursor/plugins/tree/main/pstack) | `4612556` | Different | Different | Promoted |
| `principle-sequence-verifiable-units` | [Cursor pstack](https://github.com/cursor/plugins/tree/main/pstack) | `4612556` | Different | Different | Promoted |
| `principle-subtract-before-you-add` | [Cursor pstack](https://github.com/cursor/plugins/tree/main/pstack) | `4612556` | Different | Different | Promoted |
| `prototype` | [mattpocock/skills](https://github.com/mattpocock/skills) | `6654f6b` | Different | Different | Promoted |
| `recall` | [Cursor pstack](https://github.com/cursor/plugins/tree/main/pstack) | `4612556` | Different | Different | Promoted |
| `research` | [mattpocock/skills](https://github.com/mattpocock/skills) | `6654f6b` | Different | Different | Promoted |
| `resolving-merge-conflicts` | [mattpocock/skills](https://github.com/mattpocock/skills) | `6654f6b` | Different | Different | Promoted |
| `setup-matt-pocock-skills` | [mattpocock/skills](https://github.com/mattpocock/skills) | `6654f6b` | Different | Different | Promoted |
| `show-me` | [humanlayer/skills](https://github.com/humanlayer/skills) | `3c26291` | Different | Different | Promoted |
| `show-me-your-work` | [Cursor pstack](https://github.com/cursor/plugins/tree/main/pstack) | `4612556` | Different | Different | Promoted |
| `swarm` | [Cursor pstack](https://github.com/cursor/plugins/tree/main/pstack) | `4612556` | Different | Different | Promoted |
| `systems-lab-ui` | This repository | `33802bb` | Same | Same | Already canonical |
| `tdd` | [mattpocock/skills](https://github.com/mattpocock/skills) | `6654f6b` | Different | Different | Promoted |
| `teach` | [mattpocock/skills](https://github.com/mattpocock/skills) | `6654f6b` | Different | Different | Promoted |
| `technical-writing` | [Cursor pstack](https://github.com/cursor/plugins/tree/main/pstack) | `4612556` | Different | Different | Promoted |
| `thermo-nuclear-code-quality-review` | This repository | `33802bb` | Same | Same | Already canonical |
| `to-questionnaire` | [mattpocock/skills](https://github.com/mattpocock/skills) | `6654f6b` | Different | Different | Promoted |
| `to-spec` | [mattpocock/skills](https://github.com/mattpocock/skills) | `6654f6b` | Different | Different | Promoted |
| `to-tickets` | [mattpocock/skills](https://github.com/mattpocock/skills) | `6654f6b` | Different | Different | Promoted |
| `triage` | [mattpocock/skills](https://github.com/mattpocock/skills) | `6654f6b` | Different | Different | Promoted |
| `typescript-best-practices` | [Cursor pstack](https://github.com/cursor/plugins/tree/main/pstack) | `4612556` | Different | Different | Promoted |
| `unslop` | [Cursor pstack](https://github.com/cursor/plugins/tree/main/pstack) | `4612556` | Same | Different | Promoted |
| `wayfinder` | [mattpocock/skills](https://github.com/mattpocock/skills) | `6654f6b` | Different | Different | Promoted |
| `why` | [Cursor pstack](https://github.com/cursor/plugins/tree/main/pstack) | `4612556` | Different | Different | Promoted |
| `wizard` | [mattpocock/skills](https://github.com/mattpocock/skills) | `6654f6b` | Different | Different | Promoted |
| `writing-for-agents` | [mattpocock/skills](https://github.com/mattpocock/skills) | `6654f6b` | Different | Different | Promoted |

## License notices

The promoted forks remain subject to their original MIT notices.

### Cursor pstack

```text
MIT License

Copyright (c) 2026 Lauren Tan

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

### Matt Pocock skills

```text
MIT License

Copyright (c) 2026 Matt Pocock

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

### HumanLayer skills

```text
MIT License

Copyright (c) 2026 HumanLayer

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

### Kit Langton skills

The Effect skill also keeps this notice in `skills/engineering/effect/LICENSE`.

```text
MIT License

Copyright (c) 2026 Kit Langton

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```
