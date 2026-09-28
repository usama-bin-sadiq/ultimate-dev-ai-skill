---
name: claude-api
description: "Reference for the Claude API and Anthropic SDK: model ids, pricing, parameters, streaming, tool use, MCP, agents, caching, token counting, and model migration. Read this BEFORE opening the target file whenever the task names Claude or Anthropic, or names another provider and the work may migrate to one. It is a reference, not a procedure: it answers what the API is, so that the implementation is not written from memory. The body carries the detail, and a host that has read it can decide the migration question without a second lookup."
license: Complete terms in LICENSE.txt
---

# Building LLM-Powered Applications with Claude

This skill helps you build LLM-powered applications with Claude. Choose the right surface based on your needs, detect the project language, then read the relevant language-specific documentation.

## Before You Start

Scan the target file (or, if no target file, the prompt and project) for non-Anthropic provider markers - `import openai`, `from openai`, `langchain_openai`, `OpenAI(`, `gpt-4`, `gpt-5`, file names like `agent-openai.py` or `*-generic.py`, or any explicit instruction to keep the code provider-neutral. If you find any, stop and tell the user that this skill produces Claude/Anthropic SDK code; ask whether they want to switch the file to Claude or want a non-Claude implementation. Do not edit a non-Anthropic file with Anthropic SDK calls. (Exception: the `prompt-audit` subcommand is non-interactive and does not stop here - it records non-Anthropic provider markers in its report's stated assumptions and never proposes switching a non-Anthropic file to the Anthropic SDK.)

## Output Requirement

When the user asks you to add, modify, or implement a Claude feature, your code must call Claude through one of:

1. **The official Anthropic SDK** for the project's language (`anthropic`, `@anthropic-ai/sdk`, `com.anthropic.*`, etc.). This is the default whenever a supported SDK exists for the project.
2. **Raw HTTP** (`curl`, `requests`, `fetch`, `httpx`, etc.) - only when the user explicitly asks for cURL/REST/raw HTTP, the project is a shell/cURL project, or the language has no official SDK.

Never mix the two - don't reach for `requests`/`fetch` in a Python or TypeScript project just because it feels lighter. Never fall back to OpenAI-compatible shims.

**Never guess SDK usage.** Function names, class names, namespaces, method signatures, and import paths must come from explicit documentation - either the `{lang}/` files in this skill or the official SDK repositories or documentation links listed in `shared/live-sources.md`. If the binding you need is not explicitly documented in the skill files, WebFetch the relevant SDK repo from `shared/live-sources.md` before writing code. Do not infer Ruby/Java/Go/PHP/C# APIs from cURL shapes or from another language's SDK.

**If WebFetch or repository access fails** (network restricted, timeouts, clone blocked): do not keep retrying - write code from the patterns and namespace/package tables in the `{lang}/` file, run the compiler or interpreter on it, and iterate on the error output. For statically-typed SDKs (C#, Java, Go) a compile-fix loop against local errors reaches working code faster than blocked network research.

## Defaults

Unless the user requests otherwise:

For the Claude model version, please use Claude Opus 5, which you can access via the exact model string `claude-opus-5`. Please default to using adaptive thinking (`thinking: {type: "adaptive"}`) for anything remotely complicated. And finally, please default to streaming for any request that may involve long input, long output, or high `max_tokens` - it prevents hitting request timeouts. Use the SDK's `.get_final_message()` / `.finalMessage()` helper to get the complete response if you don't need to handle individual stream events

## Warning: API Drift - Your Training Prior May Be Stale

Detail moved verbatim to `references/warning-api-drift-your-training-prior-may-be-stale.md`. Load it when this section matters and the pointer is not enough.

## Subcommands

Detail moved verbatim to `references/subcommands.md`. Load it when this section matters and the pointer is not enough.

## Language Detection

Detail moved verbatim to `references/language-detection.md`. Load it when this section matters and the pointer is not enough.

## Which Surface Should I Use?

Detail moved verbatim to `references/which-surface-should-i-use.md`. Load it when this section matters and the pointer is not enough.

## Architecture

Everything goes through `POST /v1/messages`. Tools and output constraints are features of this single endpoint - not separate APIs.

**User-defined tools** - You define tools (via decorators, Zod schemas, or raw JSON), and the SDK's tool runner handles calling the API, executing your functions, and looping until Claude is done. For full control, you can write the loop manually.

**Server-side tools** - Anthropic-hosted tools that run on Anthropic's infrastructure. Code execution is fully server-side (declare it in `tools`, Claude runs code automatically). Computer use can be server-hosted or self-hosted.

**Structured outputs** - Constrains the Messages API response format (`output_config.format`) and/or tool parameter validation (`strict: true`). The recommended approach is `client.messages.parse()` which validates responses against your schema automatically. Note: the old `output_format` parameter is deprecated; use `output_config: {format: {...}}` on `messages.create()`.

**Supporting endpoints** - Batches (`POST /v1/messages/batches`), Files (`POST /v1/files`), Token Counting (`POST /v1/messages/count_tokens` - see `shared/token-counting.md`), and Models (`GET /v1/models`, `GET /v1/models/{id}` - live capability/context-window discovery) feed into or support Messages API requests.

---

## Current Models (cached: 2026-06-24)

Detail moved verbatim to `references/current-models-cached-2026-06-24.md`. Load it when this section matters and the pointer is not enough.

## Authentication (Quick Reference)

**An unset `ANTHROPIC_API_KEY` does NOT mean there are no credentials.** The SDKs and the `ant` CLI resolve credentials in this order (first match wins): `ANTHROPIC_API_KEY` -> `ANTHROPIC_AUTH_TOKEN` -> the `ANTHROPIC_PROFILE`-selected or active OAuth profile from `ant auth login` -> Workload Identity Federation env vars -> the default profile on disk. A bare `Anthropic()` / `new Anthropic()` / `anthropic.NewClient()` works after `ant auth login` with no env var set.

**When you need to call the API and `ANTHROPIC_API_KEY` is unset, don't ask the user for a key.** First run `ant auth status` - it shows which credential source and profile is active. If it reports an active profile:

- **SDK code or `ant` CLI:** just run it. The zero-arg client constructor and every `ant ...` subcommand pick up the profile automatically - no env var needed.
- **Raw `curl` / HTTP:** get a short-lived token with `ant auth print-credentials --access-token` and send it as `Authorization: Bearer <token>` **plus** the header `anthropic-beta: oauth-2025-04-20` (OAuth tokens go on `Authorization: Bearer`, not `x-api-key:` - converting a curl from an API key is a header change, not a key swap). Always pass `--access-token`; the no-flag form prints JSON, not a bare token.

Only ask the user for a key if `ant auth status` reports no active credential source (or `ant` itself isn't installed). Suggest `ant auth login` as the first option - it stores a profile under `~/.config/anthropic/` that the SDKs read automatically - and an exported `ANTHROPIC_API_KEY` as the alternative.

Full auth details (named profiles, scopes, the API-key-shadows-profile trap, refresh-token expiry): `shared/anthropic-cli.md`.

---

## Thinking & Effort (Quick Reference)

Detail moved verbatim to `references/thinking-effort-quick-reference.md`. Load it when this section matters and the pointer is not enough.

## Compaction (Quick Reference)

**Beta, Fable 5/5.1, Opus 5, Opus 4.8, Opus 4.7, Opus 4.6, Sonnet 5, and Sonnet 4.6.** For long-running conversations that may exceed the 1M context window, enable server-side compaction. The API automatically summarizes earlier context when it approaches the trigger threshold (default: 150K tokens). Requires beta header `compact-2026-01-12`.

**Critical:** Append `response.content` (not just the text) back to your messages on every turn. Compaction blocks in the response must be preserved - the API uses them to replace the compacted history on the next request. Extracting only the text string and appending that will silently lose the compaction state.

See `{lang}/claude-api/README.md` (Compaction section) for code examples. Full docs via WebFetch in `shared/live-sources.md`.

---

## Prompt Caching (Quick Reference)

**Prefix match.** Any byte change anywhere in the prefix invalidates everything after it. Render order is `tools` -> `system` -> `messages`. Keep stable content first (frozen system prompt, deterministic tool list), put volatile content (timestamps, per-request IDs, varying questions) after the last `cache_control` breakpoint.

**Mid-conversation operator instructions** (Claude Opus 5, Claude Opus 4.8, Claude Fable 5, Claude Fable 5.1, Claude Mythos 5, Claude Mythos 5.1; not Claude Sonnet 5; no beta header): append `{"role": "system", ...}` to `messages[]` instead of editing top-level `system`. Preserves the cached history prefix and is the prompt-injection-safe operator channel. See `shared/prompt-caching.md` § Mid-conversation system messages.

**Top-level auto-caching** (`cache_control: {type: "ephemeral"}` on `messages.create()`) is the simplest option when you don't need fine-grained placement. Max 4 breakpoints per request. Minimum cacheable prefix is model-dependent (512-4096 tokens - see `shared/prompt-caching.md` § API reference) - shorter prefixes silently won't cache.

**Verify with `usage.cache_read_input_tokens`** - if it's zero across repeated requests, a silent invalidator is at work (`datetime.now()` in system prompt, unsorted JSON, varying tool set).

For placement patterns, architectural guidance, and the silent-invalidator audit checklist: read `shared/prompt-caching.md`. Language-specific syntax: `{lang}/claude-api/README.md` (Prompt Caching section).

---

## Fast Mode (Quick Reference)

Detail moved verbatim to `references/fast-mode-quick-reference.md`. Load it when this section matters and the pointer is not enough.

## Task Budgets (Quick Reference)

Detail moved verbatim to `references/task-budgets-quick-reference.md`. Load it when this section matters and the pointer is not enough.

## Provider Clients (Quick Reference)

Detail moved verbatim to `references/provider-clients-quick-reference.md`. Load it when this section matters and the pointer is not enough.

## Context Editing (Quick Reference)

**Beta.** Context editing **clears** old tool results or thinking blocks from the conversation before the model sees it; it is **not compaction** (which summarizes). On `client.beta.messages.*` with beta `context-management-2025-06-27`, pass `context_management.edits` with a strategy type:

```python
client.beta.messages.create(
    model="claude-opus-5", max_tokens=4096,
    betas=["context-management-2025-06-27"],
    context_management={"edits": [{"type": "clear_tool_uses_20250919"}]},
    tools=[...], messages=[...],
)
```

Strategy types: `clear_tool_uses_20250919` (clears old tool results; optional `clear_tool_inputs: true` also clears the tool_use params) and `clear_thinking_20251015` (clears thinking blocks). Do **not** use `compact_20260112` or beta `compact-2026-01-12` - those are the separate compaction feature.

---

## Mid-Conversation System Messages (Quick Reference)

**Claude Opus 5, Claude Opus 4.8, Claude Fable 5, Claude Fable 5.1, Claude Mythos 5, and Claude Mythos 5.1; not Claude Sonnet 5; no beta header.** Append `{"role": "system", "content": "..."}` to the `messages` array (not the top-level `system` field) to add an operator instruction mid-conversation without invalidating the cached prefix. Use the regular `client.messages.create` - there is no beta. A mid-conversation system message must follow a `user` message (or an `assistant` message ending in server-tool use), and must be either the last entry in `messages` or be followed by an `assistant` turn - it cannot be `messages[0]`. Availability: `shared/platform-availability.md`. See `shared/prompt-caching.md` § Mid-conversation system messages. A beta extension shipped with Claude Fable 5.1: `output_config: {effort: ...}` with `content: []` changes effort from that point on without a cache reset (beta `mid-conversation-output-config-2026-07-01`; Claude Fable 5.1, Claude Mythos 5.1, Claude Opus 5; Claude API). An effort-only message (empty `content`) is exempt from the placement rules above - it can sit anywhere in `messages`, including first or between an assistant turn and the next user turn; the rules apply to text and `clear_at` messages. For a per-turn reminder, give the message `clear_at: "next_user_message"` (beta `mid-conversation-system-clear-at-2026-08-21`): it renders for one turn, then stays in the transcript cleared - never delete earlier copies (on Claude Fable 5.1 deleting one invalidates later thinking blocks); without the beta, a text block after the tool results, earlier copies kept. See `shared/model-migration.md` -> Migrating to Claude Fable 5.1 from Claude Fable 5 -> New API features.

---

## Managed Agents (Beta)

Detail moved verbatim to `references/managed-agents-beta.md`. Load it when this section matters and the pointer is not enough.

## Server Tools (Quick Reference)

Detail moved verbatim to `references/server-tools-quick-reference.md`. Load it when this section matters and the pointer is not enough.

## Document & File Input (Quick Reference)

**PDF (base64, no beta):** `{"type": "document", "source": {"type": "base64", "media_type": "application/pdf", "data": <b64 string>}}` in user content, placed before the text block. Base64 string must have no newlines. Limits: 32 MB request, 600 pages (100 for 200k-context models). Java: `ContentBlockParam.ofDocument(DocumentBlockParam... Base64PdfSource.builder().data(...))`.

**Files API (no beta):** upload via `client.files.upload(...)` -> response `id` is the `file_id`. Reference it as `{"type": "document", "source": {"type": "file", "file_id": "..."}}` for PDF/text, or `{"type": "image", ...}` for images - the content-block type must match the file's MIME type. To migrate code off `files-api-2025-04-14`, WebFetch the Files API row in `shared/live-sources.md`. Availability: `shared/platform-availability.md`.

**Citations (no beta):** set `citations: {enabled: true}` on each `document` content block (all or none). Response splits into multiple `text` blocks; cited blocks carry a `citations` array. Each citation has `cited_text`, `document_index`, `document_title`, and a location by `type`: `char_location` (`start_char_index`/`end_char_index`) for plain text, `page_location` (`start_page_number`/`end_page_number`, 1-indexed) for PDF, `content_block_location` for custom content. Incompatible with `output_config.format` (returns a 400).

## Tool Use Patterns (Quick Reference)

Detail moved verbatim to `references/tool-use-patterns-quick-reference.md`. Load it when this section matters and the pointer is not enough.

## Other API Surfaces (Quick Reference)

Detail moved verbatim to `references/other-api-surfaces-quick-reference.md`. Load it when this section matters and the pointer is not enough.

## Workload Identity Federation (Quick Reference)

**GA, no beta header.** Construct the normal zero-arg client (`Anthropic()` / `new Anthropic()` / `anthropic.NewClient()` / `AnthropicOkHttpClient.fromEnv()`); the SDK auto-detects WIF when **all** of `ANTHROPIC_FEDERATION_RULE_ID`, `ANTHROPIC_ORGANIZATION_ID`, `ANTHROPIC_SERVICE_ACCOUNT_ID`, and `ANTHROPIC_IDENTITY_TOKEN_FILE` (or `ANTHROPIC_IDENTITY_TOKEN`) are set, exchanges the JWT at `/v1/oauth/token`, and auto-refreshes. `ANTHROPIC_WORKSPACE_ID` does not gate activation - required only when the federation rule spans multiple workspaces (else 400 `workspace_id_required`), optional for single-workspace rules. `ANTHROPIC_API_KEY` or `ANTHROPIC_AUTH_TOKEN` (even empty) outrank WIF, and a set `ANTHROPIC_PROFILE` also wins over the federation env vars (a missing named profile is an error, not a fall-through) - unset all three.

---

## Reading Guide

Detail moved verbatim to `references/reading-guide.md`. Load it when this section matters and the pointer is not enough.

## When to Use WebFetch

Use WebFetch to get the latest documentation when:

- User asks for "latest" or "current" information
- Cached data seems incorrect
- User asks about features not covered here

Live documentation URLs are in `shared/live-sources.md`.

## Common Pitfalls

Detail moved verbatim to `references/common-pitfalls.md`. Load it when this section matters and the pointer is not enough.


Each file below is loaded on demand, not at triage. 12 file(s):

- `references/architecture.md` — Architecture. <!-- Moved verbatim from claude-api/SKILL.md, the
- `references/authentication-quick-reference.md` — Authentication (Quick Reference). <!-- Moved verbatim from claude-api/SKILL.md, the
- `references/before-you-start.md` — Before You Start. <!-- Moved verbatim from claude-api/SKILL.md, the
- `references/compaction-quick-reference.md` — Compaction (Quick Reference). <!-- Moved verbatim from claude-api/SKILL.md, the
- `references/context-editing-quick-reference.md` — Context Editing (Quick Reference). <!-- Moved verbatim from claude-api/SKILL.md, the
- `references/defaults.md` — Defaults. <!-- Moved verbatim from claude-api/SKILL.md, the
- `references/document-file-input-quick-reference.md` — Document & File Input (Quick Reference). <!-- Moved verbatim from claude-api/SKILL.md, the
- `references/mid-conversation-system-messages-quick-reference.md` — Mid-Conversation System Messages (Quick Reference). <!-- Moved verbatim from claude-api/SKILL.md, the
- `references/output-requirement.md` — Output Requirement. <!-- Moved verbatim from claude-api/SKILL.md, the
- `references/prompt-caching-quick-reference.md` — Prompt Caching (Quick Reference). <!-- Moved verbatim from claude-api/SKILL.md, the
- `references/when-to-use-webfetch.md` — When to Use WebFetch. <!-- Moved verbatim from claude-api/SKILL.md, the
- `references/workload-identity-federation-quick-reference.md` — Workload Identity Federation (Quick Reference). <!-- Moved verbatim from claude-api/SKILL.md, the

