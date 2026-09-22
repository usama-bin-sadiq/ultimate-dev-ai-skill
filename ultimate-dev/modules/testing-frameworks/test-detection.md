---
name: test-detection
description: >
  Pattern-based test framework detection and execution for ANY language/framework.
  Auto-detects test configuration and runs appropriate commands with coverage enforcement.
triggers: [test detection, test runner, coverage, unit test, integration test, e2e test, pytest, jest, vitest, playwright, cypress]
anti_triggers: [code implementation, database design, API design, Git operations]
last_verified: 2026-09-22
---

# Test Framework Detection & Execution Patterns

## Purpose

Universal patterns for detecting test frameworks in ANY project and executing the testing pyramid (unit → integration → e2e) with enforced coverage thresholds. Language and framework agnostic.

---

## Detection Patterns

### 1. Project File Signatures

| File | Frameworks Detected |
|------|---------------------|
| `package.json` | Jest, Vitest, Mocha, Playwright, Cypress, K6, WebdriverIO |
| `pyproject.toml` / `pytest.ini` / `setup.cfg` | Pytest, Unittest, Playwright Python |
| `Cargo.toml` | Rust built-in test, cargo-nextest |
| `go.mod` | Go testing, testify, ginkgo |
| `pom.xml` | Maven Surefire, JUnit, TestNG |
| `build.gradle` / `build.gradle.kts` | Gradle, JUnit, TestNG, Spock |
| `*.csproj` | xUnit, NUnit, MSTest |
| `composer.json` | PHPUnit, Pest |
| `mix.exs` | ExUnit |
| `rebar.config` | EUnit, Common Test |
| `CMakeLists.txt` | CTest, GoogleTest, Catch2 |

### 2. Configuration Patterns

```yaml
# JavaScript/TypeScript (package.json)
{
  "scripts": {
    "test": "jest",
    "test:unit": "jest --testPathPattern=unit",
    "test:integration": "jest --testPathPattern=integration",
    "test:e2e": "playwright test"
  },
  "jest": { "coverageThreshold": { "global": { "lines": 80 } } }
}

# Python (pyproject.toml)
[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "--cov=src --cov-report=term-missing"
[tool.coverage.run]
branch = true

# Rust (Cargo.toml)
[[test]]
name = "integration_test"
harness = false

# Go (go.mod + test files)
# *_test.go files with build tags: //go:build integration

# Java (pom.xml)
<plugin>
  <artifactId>maven-surefire-plugin</artifactId>
  <configuration>
    <includes><include>**/*UnitTest.java</include></includes>
  </configuration>
</plugin>
```

---

## Execution Patterns

### Pattern: Unit Tests

```bash
# Detection priority order
detect_unit_runner():
  1. package.json → check scripts.test:unit, scripts.test
  2. pyproject.toml → pytest with unit markers
  3. Cargo.toml → cargo test --lib --bins
  4. go.mod → go test ./... -short
  5. pom.xml → mvn test -Dtest=*UnitTest
  6. build.gradle → ./gradlew test --tests "*UnitTest"
  7. *.csproj → dotnet test --filter "Category=Unit"
```

**Coverage Enforcement:**
```yaml
thresholds:
  lines: 80
  branches: 90
  functions: 80
  statements: 80
```

### Pattern: Integration Tests

```bash
detect_integration_runner():
  1. package.json → scripts.test:integration
  2. pyproject.toml → pytest -m integration
  3. Cargo.toml → cargo test --test integration_test
  4. go.mod → go test -tags=integration ./...
  5. pom.xml → mvn failsafe:integration-test
  5. build.gradle → ./gradlew integrationTest
  6. *.csproj → dotnet test --filter "Category=Integration"
```

**Coverage Enforcement:**
```yaml
thresholds:
  lines: 60
  branches: 50
```

### Pattern: E2E Tests

```bash
detect_e2e_runner():
  1. package.json → scripts.test:e2e (playwright, cypress, k6, testcafe)
  2. pyproject.toml → playwright test / pytest -m e2e
  3. Cargo.toml → cargo test --test e2e
  4. *.csproj → dotnet test --filter "Category=E2E"
```

**Critical Path Enforcement:**
```yaml
thresholds:
  critical_paths: 80  # percentage of defined critical journeys
```

---

## Universal Test Runner Wrapper

```bash
#!/usr/bin/env bash
# universal-test-runner.sh
# Usage: universal-test-runner.sh <layer> [--ci]

set -euo pipefail

LAYER="${1:-unit}"
CI_MODE="${2:-false}"

detect_framework() {
  if [[ -f "package.json" ]]; then
    echo "javascript"
  elif [[ -f "pyproject.toml" ]] || [[ -f "pytest.ini" ]]; then
    echo "python"
  elif [[ -f "Cargo.toml" ]]; then
    echo "rust"
  elif [[ -f "go.mod" ]]; then
    echo "go"
  elif [[ -f "pom.xml" ]]; then
    echo "java-maven"
  elif [[ -f "build.gradle" ]] || [[ -f "build.gradle.kts" ]]; then
    echo "java-gradle"
  elif ls *.csproj 1> /dev/null 2>&1; then
    echo "dotnet"
  else
    echo "unknown"
  fi
}

run_unit() {
  local fw=$(detect_framework)
  case $fw in
    javascript)
      if npm run test:unit 2>/dev/null; then :; elif npm test; then :; else return 1; fi ;;
    python)
      pytest -m "not integration and not e2e" --cov --cov-fail-under=80 ;;
    rust)
      cargo test --lib --bins ;;
    go)
      go test ./... -short -coverprofile=coverage.out ;;
    java-maven)
      mvn test -Dtest=*UnitTest ;;
    java-gradle)
      ./gradlew test --tests "*UnitTest" ;;
    dotnet)
      dotnet test --filter "Category=Unit" ;;
    *) return 1 ;;
  esac
}

run_integration() {
  local fw=$(detect_framework)
  case $fw in
    javascript) npm run test:integration ;;
    python) pytest -m integration ;;
    rust) cargo test --test integration_test ;;
    go) go test -tags=integration ./... ;;
    java-maven) mvn failsafe:integration-test ;;
    java-gradle) ./gradlew integrationTest ;;
    dotnet) dotnet test --filter "Category=Integration" ;;
    *) return 1 ;;
  esac
}

run_e2e() {
  local fw=$(detect_framework)
  case $fw in
    javascript) npm run test:e2e ;;
    python) 
      if command -v playwright &> /dev/null; then playwright test; 
      else pytest -m e2e; fi ;;
    rust) cargo test --test e2e ;;
    dotnet) dotnet test --filter "Category=E2E" ;;
    *) return 1 ;;
  esac
}

case $LAYER in
  unit) run_unit ;;
  integration) run_integration ;;
  e2e) run_e2e ;;
  *) echo "Unknown layer: $LAYER"; exit 1 ;;
esac
```

---

## CI/CD Integration Patterns

### GitHub Actions
```yaml
# .github/workflows/test.yml
jobs:
  test-pyramid:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Unit Tests
        run: ./scripts/universal-test-runner.sh unit
      - name: Integration Tests
        if: success()
        run: ./scripts/universal-test-runner.sh integration
      - name: E2E Tests
        if: success() && github.ref == 'refs/heads/main'
        run: ./scripts/universal-test-runner.sh e2e
```

### GitLab CI
```yaml
# .gitlab-ci.yml
stages:
  - unit
  - integration
  - e2e

unit_tests:
  stage: unit
  script: ./scripts/universal-test-runner.sh unit

integration_tests:
  stage: integration
  script: ./scripts/universal-test-runner.sh integration

e2e_tests:
  stage: e2e
  script: ./scripts/universal-test-runner.sh e2e
  only:
    - main
    - /^release\/.*/
```

---

## Anti-Patterns to Reject

| Anti-Pattern | Detection | Action |
|--------------|-----------|--------|
| No test config found | `detect_framework()` returns "unknown" | FAIL: "Add test configuration" |
| Only one test layer | Only unit OR only e2e scripts exist | WARN: "Add missing pyramid layers" |
| Coverage thresholds missing | No coverageThreshold in config | FAIL: "Add coverage thresholds" |
| Flaky tests not quarantined | Tests fail intermittently in CI | FAIL: "Fix or quarantine flaky tests" |
| Tests skipped in CI | `skip_tests: true` or similar | FAIL: "Remove test skip" |

---

## Agent Usage

When executing test pyramid validation, the agent should:

1. **Run `detect_framework()`** to identify the project's test setup
2. **Execute layer by layer** — stop on first failure
3. **Parse coverage output** and compare against thresholds
4. **Report actual numbers** — not "tests passed"
5. **Block the build** if any BLOCKING gate fails

```yaml
# Example agent output format
test_results:
  unit:
    passed: true
    coverage: { lines: 85.2, branches: 91.5, functions: 82.0 }
    duration_seconds: 12
  integration:
    passed: true
    coverage: { lines: 65.0, branches: 55.0 }
    duration_seconds: 45
  e2e:
    passed: true
    critical_paths_covered: 85
    total_critical_paths: 20
    duration_seconds: 120
```