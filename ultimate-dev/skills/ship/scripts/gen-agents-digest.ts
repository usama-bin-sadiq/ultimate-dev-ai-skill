#!/usr/bin/env bun
/**
 * Generate `agents-digest/gstack-AGENTS.md` from the installed agent tree.
 *
 * WHAT THIS IS
 *   A digest of every agent, command, and skill the harness exposes, written so
 *   an agent can decide *whether to delegate* without reading 300 agent files
 *   first. The full tree is the source of truth; this is a table of contents with
 *   descriptions and a freshness stamp.
 *
 * WHAT IT EXPECTS
 *   Run from the repository root with bun:
 *     bun scripts/gen-agents-digest.ts
 *   Optional flags:
 *     --out <path>        digest path (default agents-digest/gstack-AGENTS.md)
 *     --root <path>       tree to scan (default: alongside the skill install)
 *     --check             do not write; exit 1 if the committed digest is stale
 *     --quiet             print nothing on success
 *
 * WHY THE VERSION STAMP
 *   The stamp is the freshness gate. A digest with no stamp, or a stamp that
 *   does not match VERSION, means the digest was generated against a different
 *   set of agents than the one being shipped — and a digest that describes
 *   agents which no longer exist is worse than no digest, because a reader
 *   trusts it. `--check` is what the release step uses to decide whether the
 *   digest has to be regenerated and staged with the version bump.
 *
 * PROVENANCE
 *   Reconstructed from the `--regen-digest` description in SKILL.md Step 12:
 *   it is repo code run with the same privileges as the ship step, it writes
 *   `agents-digest/gstack-AGENTS.md`, and its VERSION stamp is freshness-gated.
 *   The digest layout is this file's own.
 */

import { existsSync, mkdirSync, readdirSync, readFileSync, statSync, writeFileSync } from "node:fs";
import { basename, dirname, join, relative, resolve } from "node:path";

// ---------------------------------------------------------------- arguments --

interface Args {
  out: string;
  root: string;
  check: boolean;
  quiet: boolean;
  help: boolean;
}

function parseArgs(argv: string[]): Args {
  const args: Args = {
    out: "agents-digest/gstack-AGENTS.md",
    root: "",
    check: false,
    quiet: false,
    help: false,
  };

  for (let index = 0; index < argv.length; index += 1) {
    const flag = argv[index];
    if (flag === "--out") args.out = argv[++index] ?? args.out;
    else if (flag === "--root") args.root = argv[++index] ?? args.root;
    else if (flag === "--check") args.check = true;
    else if (flag === "--quiet") args.quiet = true;
    else if (flag === "--help" || flag === "-h") args.help = true;
    else {
      // A bare positional is treated as the root, which is what someone running
      // `bun gen-agents-digest.ts .` expects.
      if (!flag.startsWith("-")) args.root = flag;
    }
  }
  return args;
}

// -------------------------------------------------------------- frontmatter --

/**
 * Pull `key: value` pairs out of a leading `---` fenced YAML block.
 *
 * Deliberately not a YAML parser. These files are written by this repository and
 * the frontmatter is a flat string map; a dependency to read eleven lines of it
 * would be a worse trade than a regex that fails loudly on anything unexpected.
 */
function frontmatter(text: string): Record<string, string> {
  const fields: Record<string, string> = {};
  if (!text.startsWith("---")) return fields;

  const lines = text.split("\n");
  for (let index = 1; index < lines.length; index += 1) {
    const line = lines[index];
    if (line.trim() === "---") break;
    const match = /^([A-Za-z0-9_.-]+)\s*:\s*(.*)$/.exec(line);
    if (match) fields[match[1].toLowerCase()] = match[2].trim();
  }
  return fields;
}

function body(text: string): string {
  if (!text.startsWith("---")) return text;
  const end = text.indexOf("\n---", 3);
  return end === -1 ? text : text.slice(end + 4);
}

// -------------------------------------------------------------------- scan --

interface Entry {
  name: string;
  path: string;
  description: string;
  tools: string;
  model: string;
  color: string;
  source: "agent" | "skill" | "command";
  warnings: string[];
}

const SKIP_DIRS = new Set([
  "node_modules", ".git", "dist", "build", ".next", "coverage",
  "__pycache__", ".venv", "venv", "target",
]);

function walk(dir: string, out: string[] = [], depth = 0): string[] {
  if (depth > 4 || out.length > 5000) return out;
  let entries: ReturnType<typeof readdirSync>;
  try {
    entries = readdirSync(dir, { withFileTypes: true });
  } catch {
    return out;
  }
  for (const entry of entries) {
    if (entry.name.startsWith(".") || SKIP_DIRS.has(entry.name)) continue;
    const full = join(dir, entry.name);
    if (entry.isSymbolicLink()) continue;
    if (entry.isDirectory()) walk(full, out, depth + 1);
    else if (entry.isFile()) out.push(full);
  }
  return out;
}

/** One description line, unwrapped: a digest table cannot hold a paragraph. */
function oneLine(text: string, limit = 160): string {
  const collapsed = text.replace(/\s+/g, " ").trim();
  return collapsed.length <= limit ? collapsed : `${collapsed.slice(0, limit - 1).trimEnd()}…`;
}

function collect(root: string, subdir: string, source: Entry["source"], dir: string): Entry[] {
  const target = join(root, subdir, dir);
  if (!existsSync(target)) return [];

  const entries: Entry[] = [];
  for (const file of walk(target)) {
    if (!file.endsWith(".md")) continue;

    const text = readFileSync(file, "utf8");
    const fields = frontmatter(text);
    const name = fields.name || basename(dirname(file));
    const warnings: string[] = [];

    if (basename(file) === "SKILL.md" && !fields.name) {
      warnings.push("SKILL.md has no name in its frontmatter");
    }
    if (!fields.description) warnings.push("no description: nothing to match a request against");
    if (source === "agent") {
      if (!fields.model) warnings.push("no model declared");
      if (!fields.color) warnings.push("no color declared");
    }

    entries.push({
      name,
      path: relative(root, file),
      description: oneLine(fields.description || ""),
      tools: fields.tools || "",
      model: fields.model || "",
      color: fields.color || "",
      source,
      warnings,
    });
  }
  return entries.sort((a, b) => a.name.localeCompare(b.name));
}

function readVersion(root: string): string | null {
  const file = join(root, "VERSION");
  if (!existsSync(file)) return null;
  const value = readFileSync(file, "utf8").trim();
  return value || null;
}

// ------------------------------------------------------------------ render --

function escapeCell(text: string): string {
  return text.replace(/\|/g, "\\|");
}

function render(entries: Entry[], version: string | null, root: string, generatedAt: string): string {
  const bySource: Record<Entry["source"], Entry[]> = {
    agent: entries.filter((e) => e.source === "agent"),
    skill: entries.filter((e) => e.source === "skill"),
    command: entries.filter((e) => e.source === "command"),
  };

  const warningCount = entries.reduce((total, e) => total + e.warnings.length, 0);
  const undescribed = entries.filter((e) => !e.description).length;

  const lines: string[] = [
    "---",
    "# GENERATED FILE. Do not edit by hand.",
    "#",
    "# Regenerate with:  bun scripts/gen-agents-digest.ts",
    "# Verify freshness with:  bun scripts/gen-agents-digest.ts --check",
    `version: ${version || "unknown"}`,
    `generated: ${generatedAt}`,
    `agent_count: ${bySource.agent.length}`,
    `skill_count: ${bySource.skill.length}`,
    `command_count: ${bySource.command.length}`,
    "---",
    "",
    "# Agent digest",
    "",
    "Every agent, skill, and command this install exposes, with the description that",
    "decides whether to delegate. Read one agent file before dispatching to it; this",
    "digest is for *choosing*, not for working from.",
    "",
    `Generated from \`${root}\` at version \`${version || "unknown"}\`.`,
    "",
    "## What is here",
    "",
    "| Kind | Count | Undescribed |",
    "| --- | ---: | ---: |",
    `| agents | ${bySource.agent.length} | ${bySource.agent.filter((e) => !e.description).length} |`,
    `| skills | ${bySource.skill.length} | ${bySource.skill.filter((e) => !e.description).length} |`,
    `| commands | ${bySource.command.length} | ${bySource.command.filter((e) => !e.description).length} |`,
    "",
  ];

  if (warningCount > 0) {
    lines.push(
      `${warningCount} frontmatter warning(s) below. An entry with no description cannot`,
      "be matched against a request, so it is an agent the harness will never choose.",
      "",
    );
  }

  for (const source of ["agent", "skill", "command"] as const) {
    const group = bySource[source];
    lines.push(`## ${source[0].toUpperCase()}${source.slice(1)}s (${group.length})`, "");
    if (group.length === 0) {
      lines.push(`None found under the scanned tree.`, "");
      continue;
    }
    lines.push("| Name | Description | File |", "| --- | --- | --- |");
    for (const entry of group) {
      const description = entry.description || "*(no description)*";
      lines.push(
        `| \`${escapeCell(entry.name)}\` | ${escapeCell(description)} | \`${entry.path}\` |`,
      );
    }
    lines.push("");
  }

  if (bySource.agent.length > 0) {
    lines.push("## Agent configuration", "");
    lines.push("| Name | Model | Color | Tools |", "| --- | --- | --- | --- |");
    for (const entry of bySource.agent) {
      const tools = entry.tools ? entry.tools.replace(/^\[|\]$/g, "") : "*all tools*";
      lines.push(
        `| \`${escapeCell(entry.name)}\` | ${escapeCell(entry.model || "—")} | `
        + `${escapeCell(entry.color || "—")} | ${escapeCell(tools)} |`,
      );
    }
    lines.push("");
  }

  if (warningCount > 0) {
    lines.push("## Frontmatter warnings", "");
    for (const entry of entries) {
      if (entry.warnings.length === 0) continue;
      lines.push(`- \`${entry.name}\` (${entry.path}): ${entry.warnings.join("; ")}`);
    }
    lines.push("");
  }

  if (undescribed > 0) {
    lines.push(
      "## Agents with no description",
      "",
      `${undescribed} entr${undescribed === 1 ? "y has" : "ies have"} no description. The harness`,
      "matches a request against the description, so an entry without one is never",
      "selected. This is the single most common reason an agent seems not to exist.",
      "",
    );
    for (const entry of entries.filter((e) => !e.description)) {
      lines.push(`- \`${entry.name}\` — \`${entry.path}\``);
    }
    lines.push("");
  }

  lines.push(
    "## How to use this",
    "",
    "1. Match the request against the descriptions above.",
    "2. Read the agent file for the one you picked, in full, before dispatching.",
    "3. If nothing matches, the right answer is to do the work, not to widen the match.",
    "",
    "This digest is regenerated on every version bump. If its `version` stamp does not",
    "match the repository VERSION, it is describing agents from a different tree and",
    "must not be trusted: run the generator and stage the result with the bump.",
  );

  return `${lines.join("\n")}\n`;
}

// -------------------------------------------------------------------- main --

function main(): number {
  const args = parseArgs(process.argv.slice(2));

  if (args.help) {
    process.stdout.write(
      [
        "Usage: bun scripts/gen-agents-digest.ts [options]",
        "",
        "  --out <path>    digest path (default agents-digest/gstack-AGENTS.md)",
        "  --root <path>   tree to scan (default: the install root)",
        "  --check         do not write; exit 1 when the committed digest is stale",
        "  --quiet         print nothing on success",
        "",
        "Exit codes: 0 written or fresh, 1 stale or failed, 2 bad input.",
        "",
      ].join("\n"),
    );
    return 0;
  }

  // Default root is the working directory, because the documented invocation is
  // `bun scripts/gen-agents-digest.ts` from the repository root. Falling back to
  // the script's own location keeps it working from a checkout, where the install
  // root is two levels above scripts/ (…/skills/<skill>/scripts/).
  let root = args.root ? resolve(args.root) : resolve(process.cwd());
  if (!existsSync(join(root, "agents")) && !existsSync(join(root, "skills"))) {
    const fromScript = resolve(dirname(new URL(import.meta.url).pathname), "..", "..");
    if (existsSync(join(fromScript, "agents")) || existsSync(join(fromScript, "skills"))) {
      root = fromScript;
    }
  }
  if (!existsSync(root)) {
    process.stderr.write(`error: tree root does not exist: ${root}\n`);
    return 2;
  }

  const version = readVersion(root);
  const entries = [
    // Agents live directly under agents/; skills and commands are distinguished
    // by their position inside skills/, not by a separate top-level tree.
    ...collect(root, "", "agent", "agents"),
    ...collect(root, "skills", "skill", ""),
    ...collect(root, "skills", "command", "commands"),
  ];

  if (entries.length === 0) {
    process.stderr.write(
      `error: no agents, skills, or commands found under ${root}.\n`
      + "Check --root. A digest with nothing in it is worse than no digest: it would\n"
      + "look authoritative and match nothing.\n",
    );
    return 1;
  }

  // generatedAt is excluded from the freshness comparison: a regenerated digest
  // with identical content is fresh, and a timestamp alone would make every
  // --check fail and train everyone to ignore it.
  const stamp = new Date().toISOString().replace(/\.\d+Z$/, "Z");
  const content = render(entries, version, root, stamp);
  const comparable = content.replace(/^generated: .*$/m, "generated: <stamp>");

  if (args.check) {
    const outPath = resolve(args.out);
    if (!existsSync(outPath)) {
      process.stderr.write(
        `stale: ${args.out} does not exist. Run: bun scripts/gen-agents-digest.ts\n`,
      );
      return 1;
    }
    const existing = readFileSync(outPath, "utf8").replace(/^generated: .*$/m, "generated: <stamp>");
    if (existing !== comparable) {
      process.stderr.write(
        `stale: ${args.out} does not match the current tree at version ${version || "unknown"}.\n`
        + "Run: bun scripts/gen-agents-digest.ts\n"
        + "and stage the result with the version bump.\n",
      );
      return 1;
    }
    if (!args.quiet) process.stdout.write(`fresh: ${args.out} matches version ${version}\n`);
    return 0;
  }

  const outPath = resolve(args.out);
  mkdirSync(dirname(outPath), { recursive: true });
  writeFileSync(outPath, content, "utf8");

  if (!args.quiet) {
    const agents = entries.filter((e) => e.source === "agent").length;
    const skills = entries.filter((e) => e.source === "skill").length;
    const commands = entries.filter((e) => e.source === "command").length;
    const undescribed = entries.filter((e) => !e.description).length;
    process.stdout.write(
      `wrote ${args.out} (version ${version || "unknown"}): `
      + `${agents} agents, ${skills} skills, ${commands} commands\n`,
    );
    if (undescribed > 0) {
      process.stdout.write(
        `warning: ${undescribed} entr${undescribed === 1 ? "y has" : "ies have"} no description. `
        + "The harness matches on description, so they will never be selected.\n",
      );
    }
  }
  return 0;
}

process.exit(main());
