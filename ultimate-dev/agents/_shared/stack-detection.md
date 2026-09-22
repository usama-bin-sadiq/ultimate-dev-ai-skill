---
name: stack-detection
description: Shared fragment for detecting project stack before any analysis
---

# Stack Detection (MANDATORY FIRST STEP)

Before applying any language- or framework-specific reasoning, identify the project's actual stack. Read whichever manifests exist:

- **JavaScript/TypeScript**: `package.json`, `pnpm-lock.yaml`, `yarn.lock`, `bun.lockb`, `tsconfig.json`, `astro.config.mjs`, `next.config.js`, `nuxt.config.ts`, `vite.config.ts`, `svelte.config.js`, `remix.config.js`
- **Python**: `pyproject.toml`, `requirements.txt`, `setup.py`, `poetry.lock`, `Pipfile`, `uv.lock`, `ruff.toml`
- **Go**: `go.mod`, `go.sum`, `go.work`
- **Rust**: `Cargo.toml`, `Cargo.lock`
- **Java**: `pom.xml`, `build.gradle`, `build.gradle.kts`, `settings.gradle`
- **C#**: `*.csproj`, `*.sln`, `Directory.Build.props`, `nuget.config`
- **PHP**: `composer.json`, `composer.lock`
- **Ruby**: `Gemfile`, `Gemfile.lock`, `Rakefile`
- **Dart/Flutter**: `pubspec.yaml`, `pubspec.lock`
- **Elixir**: `mix.exs`, `mix.lock`
- **C++**: `CMakeLists.txt`, `conanfile.txt`, `vcpkg.json`, `meson.build`
- **Swift**: `Package.swift`, `*.xcodeproj`, `*.xcworkspace`

Also read: `CLAUDE.md`, `AGENTS.md`, `README.md`, `CONTRIBUTING.md`, `.github/copilot-instructions.md`, `.cursorrules`, `.windsurfrules`, `opencode/AGENTS.md`

**Adapt your analysis vocabulary, conventions, and concerns to what the project actually uses — do not assume a stack the repo does not have.**