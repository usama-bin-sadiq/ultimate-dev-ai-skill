# Documentation-First — Check Docs Before Reasoning

Before using any tool, library, framework, or language feature, check the actual documentation. The internet has authoritative answers for every mainstream technology. Use them.

## When to check documentation

1. **Before using an API** — Does this function exist? What are its parameters? What version introduced it?
2. **Before configuring a tool** — What are the valid config options? What are the defaults?
3. **Before recommending a pattern** — Does the framework recommend this approach? Is it deprecated?
4. **Before writing infrastructure code** — What are the actual Terraform resource attributes? What are the IAM permission names?
5. **Before using a CLI tool** — What are the actual flags? What is the output format?

## How to check

1. **In-project docs** — README, docs/, API docs, type definitions
2. **Official documentation** — Use WebSearch to find the official docs URL, then WebFetch to read the relevant page
3. **Source code** — Read the actual source if docs are unclear
4. **Type definitions** — .d.ts files, pyi files, or generated docs show exact APIs

## What NOT to do

- Do not assume you know an API from memory — versions change, APIs deprecate
- Do not guess config options — read the schema
- Do not assume a pattern is correct — check if the framework still recommends it
- Do not invent CLI flags — read the help output or docs

## Confidence levels

- **Verified**: You read the actual docs/source and confirmed this is correct
- **Likely**: You remember this from docs but have not re-read them this session
- **Unverified**: You are guessing based on general knowledge — must verify before implementing

Always state your confidence level when making claims about external tools.
