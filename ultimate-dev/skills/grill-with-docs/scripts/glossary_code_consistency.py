#!/usr/bin/env python3
"""Cross-reference a CONTEXT.md glossary against the code, both directions.

What it does
------------
Two checks, in opposite directions, both aimed at producing a good opening
question for a grilling session:

**Dead glossary** — a term defined in CONTEXT.md that appears nowhere in the
code. Either the code does not implement what the glossary says, or the glossary
describes an intention. Those are very different situations and the difference
is worth asking about before it is assumed.

**Code-only nouns** — a domain-shaped noun that appears in the code and is not in
the glossary. This is the weaker signal of the two: most code nouns are
implementation. It is reported only for nouns that pass a domain test, because a
glossary that has absorbed every class name is no longer a glossary.

What it deliberately does not do
--------------------------------
It does not judge whether a definition is *correct*, and it does not propose a
definition for a code-only noun. Both need someone who knows the domain, and a
guessed definition written into CONTEXT.md is worse than a missing one: the next
session will treat it as settled.

Usage
-----
    python3 scripts/glossary_code_consistency.py --context CONTEXT.md --code src/
    python3 scripts/glossary_code_consistency.py --context CONTEXT.md --code src/ --code tests/
    python3 scripts/glossary_code_consistency.py --context CONTEXT.md --format json

Exit codes: 0 no dead glossary terms, 1 dead terms found, 2 bad input.

Provenance
----------
Reconstructed to serve the pre-flight and closing steps the SKILL.md describes
("flags defined-but-unused terms (dead glossary) and code-only common nouns that
may need definitions"). The matching, the domain-noun test, and the output are
this file's own.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

MAX_FILE_BYTES = 4 * 1024 * 1024
MAX_FILES = 20000
MAX_TERM_CHARS = 60
BOLD = re.compile(r"^\s*[-*]?\s*\*\*(?P<term>[^*]+?)\*\*\s*:\s*(?P<definition>.*)$")

# Extensions worth reading. Everything else is binary, generated, or a lockfile.
CODE_SUFFIXES = {
    ".py", ".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".svelte", ".vue",
    ".go", ".rs", ".java", ".kt", ".kts", ".rb", ".php", ".cs", ".swift", ".scala",
    ".c", ".h", ".cc", ".cpp", ".hpp", ".m", ".mm", ".sql", ".sh", ".bash", ".zsh",
    ".ex", ".exs", ".erl", ".hs", ".ml", ".mli", ".clj", ".cljs", ".dart", ".lua",
}
SKIP_DIRS = {
    ".git", "node_modules", "__pycache__", "dist", "build", "target", "vendor",
    ".venv", "venv", ".next", ".nuxt", "coverage", ".pytest_cache", ".mypy_cache",
    ".tox", "migrations", ".idea", ".vscode",
}

# Words that are almost always implementation rather than domain. A code noun
# containing one of these is not offered as a candidate definition.
IMPLEMENTATION_NOUNS = {
    "test", "tests", "config", "settings", "options", "opts", "args", "argv",
    "kwargs", "params", "param", "util", "utils", "helper", "helpers", "manager",
    "handler", "controller", "service", "repository", "repo", "factory", "builder",
    "adapter", "wrapper", "proxy", "decorator", "middleware", "plugin", "provider",
    "client", "server", "request", "response", "router", "route", "view", "views",
    "model", "models", "schema", "schemas", "migration", "migrations", "entity",
    "dto", "dao", "entity_factory", "base", "abstract", "interface", "impl",
    "error", "errors", "exception", "logger", "log", "logging", "cache", "store",
    "storage", "db", "database", "sql", "http", "json", "yaml", "xml", "csv",
    "file", "files", "path", "paths", "dir", "directory", "name", "names", "id",
    "uuid", "key", "keys", "value", "values", "data", "info", "meta", "metadata",
    "item", "items", "element", "elements", "node", "nodes", "list", "array",
    "obj", "object", "str", "string", "int", "number", "index", "map", "set",
    "result", "results", "response", "output", "input", "source", "target",
    "buffer", "stream", "queue", "task", "job", "worker", "process", "thread",
    "event", "events", "signal", "callback", "fn", "func", "method", "class",
    "api", "url", "uri", "host", "port", "token", "secret", "password", "user",
    "users", "version", "build", "make", "run", "main", "init", "setup", "app",
    "component", "components", "state", "props", "style", "styles", "css",
}

# Nouns that are domain-shaped enough to be worth a question even though they
# look generic. Being in this list earns a term a look; it does not grant a
# definition.
DOMAIN_CANDIDATES = {
    "order", "orders", "customer", "customers", "client", "clients", "user",
    "account", "accounts", "invoice", "invoices", "payment", "payments",
    "subscription", "subscriptions", "plan", "plans", "cart", "basket", "quote",
    "quotes", "contract", "contracts", "shipment", "shipments", "delivery",
    "inventory", "stock", "warehouse", "product", "products", "catalog",
    "catalogue", "price", "pricing", "discount", "refund", "refunds", "charge",
    "billing", "ledger", "journal", "transaction", "transactions", "budget",
    "tenant", "tenants", "workspace", "project", "projects", "team", "teams",
    "organisation", "organization", "member", "members", "role", "roles",
    "permission", "permissions", "policy", "policies", "session", "sessions",
    "booking", "bookings", "reservation", "ticket", "tickets", "claim", "claims",
    "policy_holder", "premium", "deductible", "coverage", "benefit", "provider",
    "patient", "appointment", "encounter", "diagnosis", "prescription", "dose",
    "cohort", "sample", "specimen", "assay", "batch", "run", "experiment",
    "measurement", "observation", "reading", "sensor", "device", "telemetry",
    "metric", "metrics", "alert", "incident", "ticket_triage", "appointment_slot",
    "waitlist", "referral", "enrollment", "consent", "case", "report", "finding",
}

# Identifier splitting, so `order_item` yields `order` and `item`.
IDENTIFIER_SPLIT = re.compile(r"[^A-Za-z0-9]+|(?<=[a-z0-9])(?=[A-Z])")
CAMEL_BOUNDARY = re.compile(r"(?<=[a-z])(?=[A-Z])")


def load_terms(context_path: str) -> list[dict]:
    """Read the bold terms from CONTEXT.md. The same shape the linter expects."""
    file_path = Path(context_path)
    if not file_path.is_file():
        raise SystemExit(f"error: context file not found: {context_path}")
    try:
        text = file_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        raise SystemExit(f"error: {context_path} is not valid UTF-8")

    terms: list[dict] = []
    for number, line in enumerate(text.splitlines(), start=1):
        match = BOLD.match(line)
        if not match:
            continue
        term = match.group("term").strip()
        if not term or len(term) > MAX_TERM_CHARS:
            continue
        terms.append({
            "term": term,
            "definition": match.group("definition").strip(),
            "line": number,
            "slug": term.lower().replace(" ", "_"),
        })
    return terms


def iter_code_files(roots: list[str]):
    """Yield readable source files under the given roots, bounded."""
    seen = 0
    for root in roots:
        root_path = Path(root)
        if not root_path.exists():
            raise SystemExit(f"error: --code path not found: {root}")
        if root_path.is_file():
            yield root_path
            continue
        for path in root_path.rglob("*"):
            if seen >= MAX_FILES:
                log(f"stopped after {MAX_FILES} files; narrow the --code path")
                return
            if not path.is_file() or path.is_symlink():
                continue
            if any(part in SKIP_DIRS for part in path.parts):
                continue
            if path.suffix.lower() not in CODE_SUFFIXES:
                continue
            seen += 1
            yield path


def build_word_index(files):
    """Count whole words and whole identifiers across the codebase.

    Words are produced by splitting every identifier on underscores, camel-case
    boundaries, and digits, so ``create_invoice``, ``createInvoice`` and
    ``Invoice`` all contribute the word ``invoice``. Matching on whole words
    rather than substrings is what keeps ``order`` from being found in
    ``reorder`` and every other identifier that happens to contain the letters.

    Returns ``(words, identifiers, compounds, stats)``.
    """
    words: Counter = Counter()
    identifiers: Counter = Counter()
    compounds: dict[str, list[str]] = {}
    files_read = 0
    total_bytes = 0

    for path in files:
        try:
            if path.stat().st_size > MAX_FILE_BYTES:
                continue
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        files_read += 1
        total_bytes += len(text)

        for identifier in re.findall(r"[A-Za-z][A-Za-z0-9_]*", text):
            lowered = identifier.lower()
            if len(lowered) >= 2:
                identifiers[lowered] += 1
            parts = [
                part for part in IDENTIFIER_SPLIT.split(identifier)
                if part and part.lower().isalpha() and len(part) > 1
            ]
            for part in parts:
                words[part.lower()] += 1
            if len(parts) >= 2:
                compounds[lowered] = [part.lower() for part in parts]

    return words, identifiers, compounds, {
        "files_read": files_read,
        "bytes_read": total_bytes,
        "distinct_words": len(words),
        "distinct_identifiers": len(identifiers),
    }


def term_occurrences(term: dict, words: Counter, identifiers: Counter,
                     compounds: dict[str, list[str]]) -> tuple[int, str]:
    """How often a glossary term appears in the code, and how strong the evidence is.

    Three routes, strongest first:

    ``exact``      the term appears as one whole identifier, or as the plural of
                   a single-word term.
    ``compound``   every word of a multi-word term appears in the *same*
                   identifier, as in ``order_item`` for "order item".
    ``co_occurrence`` every word of the term appears somewhere in the code. This
                   is weak: it will be satisfied by two unrelated identifiers
                   that happen to share words, so the caller reports it as weak
                   rather than treating it as proof the term is implemented.
    """
    slug = term["slug"]
    parts = [part for part in re.split(r"[^a-z0-9]+", slug) if len(part) > 1]
    if not parts:
        return 0, "none"

    if identifiers.get(slug):
        return identifiers[slug], "exact"

    if len(parts) == 1:
        # A single word appearing as a whole word is a real hit: `invoice` in
        # `create_invoice` is the concept being used, whatever the verb is.
        for variant in {parts[0], plural_of(parts[0])}:
            if words.get(variant):
                return words[variant], "exact"
        return 0, "none"

    for identifier, count in identifiers.items():
        compound_parts = compounds.get(identifier)
        if compound_parts and all(_part_in(part, compound_parts) for part in parts):
            return count, "compound"

    total = 0
    if all(_word_present(part, words) for part in parts):
        for part in parts:
            total += words.get(part, 0) + words.get(plural_of(part), 0)
        return total, "co_occurrence"
    return 0, "none"


def _part_in(part: str, candidates: list[str]) -> bool:
    """Whether a term word appears in an identifier, allowing a plural."""
    return part in candidates or plural_of(part) in candidates


def _word_present(part: str, words: Counter) -> bool:
    return bool(words.get(part)) or bool(words.get(plural_of(part)))


def plural_of(noun: str) -> str:
    """A simple plural, enough to catch order/orders and invoice/invoices."""
    if noun.endswith(("s", "x", "z", "ch", "sh")):
        return noun + "es"
    if noun.endswith("y") and len(noun) > 1 and noun[-2] not in "aeiou":
        return noun[:-1] + "ies"
    return noun + "s"


def find_code_only_nouns(words: Counter, defined: set[str]) -> list[dict]:
    """Domain-shaped nouns in the code that the glossary does not define."""
    candidates: list[dict] = []
    seen: set[str] = set()

    for noun, count in words.most_common():
        if noun in seen or count < 3:
            continue
        if noun in defined or noun in IMPLEMENTATION_NOUNS:
            continue
        if noun not in DOMAIN_CANDIDATES and not (
            len(noun) > 4 and noun.endswith("s") and noun[:-1] in DOMAIN_CANDIDATES
        ):
            continue
        seen.add(noun)
        candidates.append({
            "noun": noun,
            "occurrences": count,
            "in_domain_vocabulary": noun in DOMAIN_CANDIDATES,
            "note": "Offered as a question, not a definition. If the code name is the "
                    "domain name, it belongs in CONTEXT.md; if it is an implementation "
                    "name that happens to look like a noun, ignore it.",
        })
        if len(candidates) >= 40:
            break
    return candidates


def log(message: str) -> None:
    print(message, file=sys.stderr, flush=True)


def analyse(context_path: str, code_roots: list[str]) -> dict:
    terms = load_terms(context_path)
    if not terms:
        return {
            "context": context_path,
            "terms": 0,
            "dead_terms": [
                {"term": t["term"], "line": t["line"],
                 "note": "CONTEXT.md defines no bold terms, so there is nothing to "
                         "cross-reference."}
                for t in terms
            ],
            "code_only_nouns": [],
            "code_stats": {},
        }

    words, identifiers, compounds, stats = build_word_index(iter_code_files(code_roots))

    dead: list[dict] = []
    weak: list[dict] = []
    for term in terms:
        occurrences, evidence = term_occurrences(term, words, identifiers, compounds)
        if occurrences and evidence == "co_occurrence":
            weak.append({
                "term": term["term"],
                "definition": term["definition"],
                "line": term["line"],
                "word_occurrences": occurrences,
                "note": "every word of this term appears in the code, but not in the same "
                        "identifier. That is weak evidence: the concept may be implemented "
                        "under another name, or the words may be unrelated. Worth a "
                        "question, not worth an assumption.",
            })
        elif occurrences == 0:
            dead.append({
                "term": term["term"],
                "definition": term["definition"],
                "line": term["line"],
                "note": "defined in CONTEXT.md but absent from the code. Either the code "
                        "does not implement what the glossary says, or the glossary "
                        "describes an intention. Those are different situations, and which "
                        "one it is changes what to do next.",
            })

    defined = {term["slug"] for term in terms}
    code_only = find_code_only_nouns(words, defined)

    return {
        "context": context_path,
        "terms": len(terms),
        "code_roots": code_roots,
        "dead_terms": dead,
        "weak_matches": weak,
        "code_only_nouns": code_only,
        "code_stats": stats,
    }


def render_text(report: dict) -> str:
    lines = [
        f"context: {report['context']}",
        f"terms defined: {report['terms']}",
        f"code roots: {', '.join(report.get('code_roots', [])) or 'none'}",
    ]
    stats = report.get("code_stats") or {}
    if stats:
        lines.append(
            f"code read: {stats.get('files_read', 0)} files, "
            f"{stats.get('bytes_read', 0)} bytes, "
            f"{stats.get('distinct_words', 0)} distinct identifier words"
        )
    lines += [
        "",
        f"dead glossary terms: {len(report['dead_terms'])}",
        "",
    ]
    for entry in report["dead_terms"]:
        definition = entry.get("definition", "")
        if definition:
            definition = " — " + (definition[:70] + ("..." if len(definition) > 70 else ""))
        lines.append(f"  **{entry['term']}**{definition}")
        lines.append(f"    line {entry['line']}: {entry['note']}")
        lines.append("")

    if not report["dead_terms"]:
        lines.append("  Every defined term appears in the code.")
        lines.append("")

    weak = report.get("weak_matches") or []
    if weak:
        lines += [f"weak matches: {len(weak)}", ""]
        for entry in weak:
            lines.append(f"  **{entry['term']}**  ({entry['word_occurrences']} word occurrences)")
            lines.append(f"    {entry['note']}")
            lines.append("")

    lines += [
        "",
        f"code-only nouns worth a question: {len(report['code_only_nouns'])}",
        "",
    ]
    for entry in report["code_only_nouns"]:
        suffix = "" if entry["in_domain_vocabulary"] else "  (heuristic: plural or near-match)"
        lines.append(f"  {entry['noun']:<24} {entry['occurrences']:>6} occurrences{suffix}")
    if not report["code_only_nouns"]:
        lines.append("  None passed the domain-noun test.")
        lines += [
            "",
            "  Nothing in the code looked like a domain noun the glossary is missing. That "
            "usually means the glossary is complete, or that the domain language does not "
            "appear in identifiers at all, which is worth noticing.",
        ]
    else:
        lines += ["", "  " + report["code_only_nouns"][0]["note"]]
    lines += [
        "",
        "This tool does not judge whether a definition is correct and it does not write "
        "definitions. A guessed definition placed in CONTEXT.md is worse than a missing "
        "one, because the next session will read it as settled.",
    ]
    return "\n".join(lines) + "\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Cross-reference a CONTEXT.md glossary against the code, both directions.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--context", required=True, help="CONTEXT.md to read terms from")
    parser.add_argument("--code", action="append", default=[], dest="code",
                        help="source root or file to search; repeatable")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if not args.code:
        raise SystemExit("error: give at least one --code path")

    report = analyse(args.context, args.code)
    if args.format == "json":
        print(json.dumps(report, indent=2, default=str))
    else:
        print(render_text(report), end="")
    return 1 if report["dead_terms"] else 0


if __name__ == "__main__":
    sys.exit(main())
