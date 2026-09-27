---
name: ci
description:
  A specialized skill for Gemini CLI that provides high-performance, fail-fast
  monitoring of GitHub Actions workflows and automated local verification of CI
  failures. It handles run discovery automatically—simply provide the branch name.
neutralised: tool-specific paths and single-runtime invocations replaced
---

# CI Replicate & Status

This skill enables the agent to efficiently monitor GitHub Actions, triage
failures, and bridge remote CI errors to local development. It defaults to
**automatic replication** of failures to streamline the fix cycle.

## Core Capabilities

- **Automatic Replication**: Automatically monitors CI and immediately executes 
  suggested test or lint commands locally upon failure.
- **Real-time Monitoring**: Aggregated status line for all concurrent workflows
  on the current branch.
- **Fail-Fast Triage**: Immediately stops on the first job failure to provide a
  structured report.

## Workflow

### 1. CI Replicate (`replicate`) - DEFAULT
Use this as the primary path to monitor CI and **automatically** replicate 
failures locally for immediate triage and fixing.
- **Behavior**: When this workflow is triggered, the agent will monitor the CI
  and **immediately and automatically execute** all suggested test or lint
  commands (marked with 🚀) as soon as a failure is detected. 
- **Tool**: `node <agent-config-dir>/skills/ci/scripts/ci.mjs [branch]`
- **Discovery**: The script **automatically** finds the latest active or recent
  run for the branch. Do NOT manually search for run IDs.
- **Goal**: Reproduce the failure locally without manual intervention, then
  proceed to analyze and fix the code.

### 1. CI Status (`status`)
Use this when you have pushed changes and need to monitor the CI and reproduce
any failures locally.
- **Tool**: `node <agent-config-dir>/skills/ci/scripts/ci.mjs [branch] [run_id]`
- **Discovery**: The script **automatically** finds the latest active or recent
  run for the branch. You should NOT manually search for \`run_id\` using \`gh run list\`
  unless a specific historical run is requested. Simply provide the branch name.
- **Step 1 (Monitor)**: Execute the tool with the branch name.
- **Step 2 (Extract)**: Extract suggested \`npm test\` or \`npm run lint\` commands
  from the output (marked with 🚀).
- **Step 3 (Reproduce)**: Execute those commands locally to confirm the failure.
- **Behavior**: It will poll every 15 seconds. If it detects a failure, it will
  exit with a structured report and provide the exact commands to run locally.

## Failure Categories & Actions

- **Test Failures**: Agent should run the specific `npm test -w <pkg> -- <path>`
  command suggested.
- **Lint Errors**: Agent should run `npm run lint:all` or the specific package
  lint command.
- **Build Errors**: Agent should check `tsc` output or build logs to resolve
  compilation issues.
- **Job Errors**: Investigate `gh run view --job <job_id> --log` for
  infrastructure or setup failures.

## Noise Filtering
The underlying scripts automatically filter noise (Git logs, NPM warnings, stack
trace overhead). The agent should focus on the "Structured Failure Report"
provided by the tool.

## Runtime notes

This file was adapted to be tool-neutral: it claimed a general scope and was
bound to one tool. The procedure is unchanged; what changed is that a reader on a
different runtime is told what to substitute.

- `<project-root>` — the repository root. 2 machine-specific path(s) replaced.
- `<agent-config-dir>` — wherever this runtime keeps its configuration. Not a fixed location.
- `<agent-instructions>` — the file this runtime reads for standing instructions. Names differ per runtime and none is assumed.
- **npm** — means. One tool's way of doing a step a different runtime may do another way.
Anything marked **means** is an implementation detail of one tool, and a reader
on a different runtime may need a different mechanism for the same step. Anything
marked **subject** means the capability is genuinely about that tool, and a reader
without it should not expect this file to apply.
