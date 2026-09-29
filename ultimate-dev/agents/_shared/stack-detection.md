# Stack Detection — Apply Before Any Analysis

You are about to reason about a codebase. Generic assumptions produce wrong recommendations. Detect the project's actual stack and conventions first, and ground every output in them.

## What to read

**Manifests** (read whichever exist):

- JS/TS: package.json, pnpm-workspace.yaml, turbo.json, nx.json, tsconfig.json, deno.json, bun.lockb, next.config.*, nuxt.config.*, svelte.config.*, angular.json, vite.config.*
- PHP: composer.json, artisan
- Python: pyproject.toml, setup.py, setup.cfg, requirements*.txt, Pipfile, poetry.lock, uv.lock
- Go: go.mod
- Rust: Cargo.toml
- Ruby: Gemfile, *.gemspec
- JVM: build.gradle, build.gradle.kts, pom.xml, build.sbt
- Elixir: mix.exs
- .NET: *.csproj, *.fsproj, *.sln
- Dart/Flutter: pubspec.yaml
- Native: Makefile, CMakeLists.txt, BUILD.bazel
- Mobile: Podfile, *.xcodeproj, android/build.gradle, app.json, expo.json
- Infra: Dockerfile, docker-compose.yml, terraform/*.tf, *.k8s.yaml, Pulumi.yaml
- AI/ML: training_config.yaml, model_card.md, llm_config.*
- Embedded: platformio.ini, CMakeLists.txt, Kconfig, sdkconfig

**Project rules** (read whichever exist):

CLAUDE.md, AGENTS.md, .cursorrules, .cursor/rules/*.md, .claude/rules/*.md, .github/copilot-instructions.md, CONTRIBUTING.md, README.md, STYLEGUIDE.md, ARCHITECTURE.md, docs/conventions/*.md, .windsurfrules, .clinerules

If you find a project-rules-discoverer report in your context, prefer it over re-scanning.

**Code structure** — top-level directories: src/, app/, lib/, pkg/, cmd/, internal/, services/, api/, web/, mobile/, apps/, packages/, crates/, modules/, server/, client/, shared/, infrastructure/, terraform/, k8s/, ml/, models/, notebooks/, scripts/

## What to extract

- Language(s) and version
- Framework(s) and version
- Test runner (jest, vitest, pytest, phpunit, go test, cargo test, rspec, mix test, JUnit, NUnit, etc.)
- Linter/formatter (eslint, prettier, ruff, black, gofmt, pint, rubocop, golangci-lint, clippy, swiftlint, ktlint, etc.)
- Build/bundler (vite, webpack, rollup, esbuild, gradle, cargo, swc, turbopack, msbuild, etc.)
- Package manager (npm, pnpm, yarn, bun, pip, poetry, uv, composer, cargo, gem, nuget, pub, mix, etc.)
- Naming conventions (snake_case, camelCase, PascalCase per file type)
- Module style (ESM, CJS, package-by-feature, package-by-layer, monorepo workspaces)
- Test placement (__tests__/, tests/, test/, co-located *.test.* / *_test.*)
- CI provider (.github/workflows/, .gitlab-ci.yml, .circleci/, azure-pipelines.yml, Jenkinsfile)
- Runtime (Node, Deno, Bun, browser, native, JVM, CLR, BEAM, WASM)

## Hard rules

1. **Never recommend a tool, pattern, or library the project does not already use** unless explicitly asked. If the project uses Yarn, do not suggest pnpm. If it uses Pytest, do not suggest unittest. If unsure, ask.
2. **Never use a framework name in your output that the project does not use.** Do not say "the controller" if the project has no controllers. Use the project's own vocabulary.
3. **Carry the detected stack into every finding.** File paths, framework names, test command — all must match the project.
4. **Future-proofing**: If the project uses an unknown manifest or tool, reason from its config structure. The patterns here cover 2024-era ecosystems; extend by analogy for future tools.

## When stack detection is ambiguous

State what you found, list the candidates, and ask the user which one is canonical. Do not pick silently.
