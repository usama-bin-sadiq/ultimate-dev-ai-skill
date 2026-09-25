# Ultimate-Dev Installation and Development Guide

**Version:** 3.0.2
**Measured:** 2026-09-25 from a real staged project installation

This guide separates three different things that are often confused:

1. **Prompt-only use** — install the Markdown skill into an agent host.
2. **Development/validation** — run the repository checks and tests.
3. **Optional runtime/provider features** — explicitly opt into host/runtime
   behavior; they are not required for the core skill.

## 1. Prompt-only installation

The core product is Markdown. It does **not** require Python packages, Node.js,
a model provider, a browser, Docker, MCP, or a running Ultimate-Dev service.

### Generic host

```bash
./scripts/install.sh --generic --global --yes
```

### Project-local generic host

```bash
./scripts/install.sh --generic --project /path/to/project --yes
```

### Host-specific examples

```bash
./scripts/install.sh --tool claude-code --global --yes
./scripts/install.sh --tool codex --project /path/to/project --yes
./scripts/install.sh --tool opencode --global --yes
```

The installer is copy-only. It does not create symlinks, `.memory`, templates,
`.gitignore`, `.cursor`, or host configuration files outside the selected skill
destination. It excludes local development caches and the three protected local
runtime bridges from release payload.

## 2. Measured installation size

The following was measured by running the installer into a temporary project,
not by measuring the Git checkout:

| Measure | Result |
|---|---:|
| Installed payload (`du -sk`) | **3,496 KiB** (~3.41 MiB) |
| Logical file bytes | **2,663,555 bytes** (~2.54 MiB) |
| Installed files | **422** |
| Symlinks | **0** |
| Development cache directories | **0** |
| Protected local bridges | **0** |

The number varies slightly by filesystem block allocation and platform. The
full payload includes the optional runtime, tests, evaluation fixtures, and
maintenance scripts so that an installed copy can be verified. It does **not**
include local caches such as `__pycache__`, `.pytest_cache`, `.DS_Store`, or
virtual environments.

Approximate full-payload directory breakdown:

| Area | Allocated size |
|---|---:|
| `runtime/` | ~1.1 MiB |
| `agents/` | ~524 KiB |
| `tests/` | ~372 KiB |
| `modules/` | ~304 KiB |
| `scripts/` | ~228 KiB |
| `evals/` | ~52 KiB |
| `router/` | ~64 KiB |
| `config/` | ~164 KiB |
| `skills/` | ~160 KiB |

The repository also includes a reproducible measurement command:

```bash
python3 scripts/measure-install.py --strict
python3 scripts/measure-install.py --json
```

It stages a real temporary project installation, reports allocated/logical
bytes and file count, and fails if caches, symlinks, or protected local bridges
remain.

For a dependency-free benchmark against any local checkout:

```bash
python3 scripts/benchmark-project-context.py --project /path/to/repository --strict
```

This checks context extraction, provenance, unknowns, path rules, and the
`not_run` status of candidate commands. It does not build or execute the target
project.

The same benchmark was run against complete working trees of
`microsoft/vscode`, `JetBrains/intellij-community`, and `kubernetes/kubernetes`
using shallow history and blob-filtered Git object storage. No npm, Gradle,
Maven, Go, or other project dependencies were installed, and every temporary
clone was removed afterward.

The installer prints the measured payload size after every successful install:

```text
Payload size: 3496 KiB (development caches excluded)
```

### Measure another installation yourself

```bash
TMP_DIR="$(mktemp -d)"
./scripts/install.sh --generic --project "$TMP_DIR" --yes
TARGET="$TMP_DIR/.agents/skills/ultimate-dev"
du -sh "$TARGET"
find "$TARGET" -type f | wc -l
rm -rf "$TMP_DIR"
```

Do not use the size of the source checkout as the install size: a checkout can
contain test caches, local worktrees, and untracked development files.

## 3. Development dependencies

Development dependencies are pinned in [`requirements-dev.txt`](requirements-dev.txt).
They are optional for prompt-only users.

### Python

| Dependency | Version | Required for | Required for prompt-only? |
|---|---:|---|---|
| Python | 3.11+ | Test and maintenance commands | No |
| PyYAML | 6.0.2 | Manifest generation, consistency checks, prompt audit | No |
| pytest | 8.3.5 | Python test suite | No |
| requests | 2.32.3 | Optional legacy model-adapter tests and CI | No |

The optional model adapter is not part of the prompt-first product. `requests`
is not needed for the Markdown skill, provider-free benchmark, or JEV reference
engine.

### Node.js

| Dependency | Version | Required for | Required for prompt-only? |
|---|---:|---|---|
| Node.js | 20+ | `tests/jev/engine.test.mjs` and host-native JEV tests | No |

JEV itself is optional. The host-native reference engine has no npm package or
package-manager dependency.

### Optional host tools

- PowerShell 7+ is needed only to run/verify `install.ps1` on Windows.
- Bash, a POSIX shell, and standard file utilities are needed for the POSIX
  installer and `verify.sh`.
- Git is needed for repository development, generated-file checks, and CI diff
  checks; it is not needed to use an installed prompt skill.

## 4. Set up a development environment

From the repository root:

### macOS/Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r ultimate-dev/requirements-dev.txt
```

### Windows PowerShell

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r .\ultimate-dev\requirements-dev.txt
```

No provider credentials or external service configuration are required for
these commands.

## 5. Run development checks

Run repository checks from the `ultimate-dev/` directory unless a command says
otherwise.

```bash
cd ultimate-dev

# Metadata, contracts, catalog, adapters, and versions
python scripts/validate-consistency.py

# Prompt packaging and routing audit
python scripts/audit-prompt-suite.py --strict

# Provider-free fixture benchmark; explicitly not a model benchmark
python scripts/benchmark-prompt-routing.py --strict

# Full Python suite
python -m pytest tests -q

# Host-native JEV conformance tests
node --test tests/jev/engine.test.mjs

# Full host-native verification (POSIX)
./scripts/verify.sh
```

For a complete CI-equivalent run:

```bash
cd ultimate-dev
python scripts/audit-prompt-suite.py --strict
python scripts/benchmark-prompt-routing.py --strict
python scripts/validate-consistency.py
python scripts/validate.py
python -m pytest tests -q
node --test tests/jev/engine.test.mjs
```

## 6. What is intentionally not installed

The prompt-first guide does not install or require:

- OpenAI, Anthropic, Ollama, or another provider client;
- a browser automation stack such as Playwright or Puppeteer;
- Docker, Kubernetes, a cluster, or a sandbox service;
- an MCP server;
- a mandatory Ultimate-Dev runtime service.

Those are host or project concerns. If a selected task needs one, the task
must report the missing capability and use the universal fallback or request
explicit host support.

## 7. Update and uninstall

### Update

Run the installer again with the same target. Installation is staged and
replaces only the selected skill directory. Existing project memory and
unrelated files are not managed by the installer.

```bash
./scripts/install.sh --generic --global --yes
```

### Uninstall

```bash
./scripts/install.sh --generic --global --uninstall --yes
```

For a project-local install, use the same `--project` path and `--uninstall`.

## 8. Validate an optional company context pack

Company-owned references remain external to the universal package. Validate a
locally managed pack before using it:

```bash
python3 scripts/validate-company-context.py path/to/company-context.yaml
python3 scripts/validate-company-context.py reference/company-context-template.yaml --template
```

The validator checks scope, dates, ownership, required sections, placeholder
cleanup, and accidental secret-like fields. It does not fetch links, approve
policy, or replace a qualified legal/finance/security reviewer.

## 9. Troubleshooting

### `ModuleNotFoundError: yaml`

Install the development requirements:

```bash
python -m pip install -r ultimate-dev/requirements-dev.txt
```

### `node: command not found`

Install Node.js 20+ only if you want to run JEV conformance tests. The
prompt-only skill does not need Node.js.

### PowerShell installer unavailable

Use the POSIX installer on macOS/Linux, or install PowerShell 7+ before running
`install.ps1`. The skill payload itself is host-neutral.

### Payload is larger than expected

Check whether you measured the source checkout or a previous install. Remove
local caches from the checkout, then reinstall:

```bash
find ultimate-dev -type d \( -name '__pycache__' -o -name '.pytest_cache' \) -prune -exec rm -rf {} +
find ultimate-dev -type f -name '*.pyc' -delete
```

The installer performs this cleanup in its staging copy automatically.

## 10. Rating interpretation

The install and dependency work improves **packaging quality, portability, and
honest evidence**. It does not by itself justify a 10/10 prompt rating. The
current prompt-only estimate is **8.6/10** until independent model/host
behavioral benchmarks and organization-specific evaluations are available.
