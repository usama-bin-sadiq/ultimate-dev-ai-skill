<!-- Moved verbatim from claude-api/SKILL.md, the
     'language-detection' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Language Detection

Before reading code examples, determine which language the user is working in (exception: for the `prompt-audit` subcommand, skip this section's ask steps - the audit is non-interactive and its inventory is language-agnostic; when no language is inferable, proceed without asking and state the assumption in the report):

1. **Look at project files** to infer the language:

   - `*.py`, `requirements.txt`, `pyproject.toml`, `setup.py`, `Pipfile` -> **Python** - read from `python/`
   - `*.ts`, `*.tsx`, `package.json`, `tsconfig.json` -> **TypeScript** - read from `typescript/`
   - `*.js`, `*.jsx` (no `.ts` files present) -> **TypeScript** - JS uses the same SDK, read from `typescript/`
   - `*.java`, `pom.xml`, `build.gradle` -> **Java** - read from `java/`
   - `*.kt`, `*.kts`, `build.gradle.kts` -> **Java** - Kotlin uses the Java SDK, read from `java/`
   - `*.scala`, `build.sbt` -> **Java** - Scala uses the Java SDK, read from `java/`
   - `*.go`, `go.mod` -> **Go** - read from `go/`
   - `*.rb`, `Gemfile` -> **Ruby** - read from `ruby/`
   - `*.cs`, `*.csproj` -> **C#** - read from `csharp/`
   - `*.php`, `composer.json` -> **PHP** - read from `php/`

2. **If multiple languages detected** (e.g., both Python and TypeScript files):

   - Check which language the user's current file or question relates to
   - If still ambiguous, ask: "I detected both Python and TypeScript files. Which language are you using for the Claude API integration?"

3. **If language can't be inferred** (empty project, no source files, or unsupported language):

   - Use AskUserQuestion with options: Python, TypeScript, Java, Go, Ruby, cURL/raw HTTP, C#, PHP
   - If AskUserQuestion is unavailable, default to Python examples and note: "Showing Python examples. Let me know if you need a different language."

4. **If unsupported language detected** (Rust, Swift, C++, Elixir, etc.):

   - Suggest cURL/raw HTTP examples from `curl/` and note that community SDKs may exist
   - Offer to show Python or TypeScript examples as reference implementations

5. **If user needs cURL/raw HTTP examples**, read from `curl/`.

### Language-Specific Feature Support

Every SDK language above supports both the beta Tool Runner and Managed Agents (beta) - Python (`@beta_tool` decorator), TypeScript (`betaZodTool` + Zod), Java (annotated classes), Go (`BetaToolRunner` in the `toolrunner` pkg), Ruby (`BaseTool` + `tool_runner`), C# (`BetaToolRunner` + raw JSON schema), PHP (`BetaRunnableTool` + `toolRunner()`); code entry points are in the Tool Use Patterns quick reference below. cURL is raw HTTP (no SDK features) and supports Managed Agents.

> **Managed Agents code examples**: see the reading guide in the `## Managed Agents (Beta)` section below.

---
