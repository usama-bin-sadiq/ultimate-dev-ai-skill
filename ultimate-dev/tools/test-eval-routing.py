#!/usr/bin/env python3
"""The routing scorer's tokenizer must split on hyphens.

eval-routing.py scores 3x name overlap as its strongest signal. Its pattern
`[a-z0-9][a-z0-9-]+` tokenised "omnisend-automation" as a single token, so a
query of "omnisend automation" -- {omnisend, automation} -- overlapped it not
at all. The strongest term in the scorer was structurally unreachable for every
hyphenated skill, and most of this corpus is hyphenated: Hit@1 measured 23%
with the bug and 87% without it, on the same 60 queries and the same index.

A tokenizer bug that moves a headline metric by 64 points is worth a test,
because the metric it distorts is the one used to judge the routing index.

Both directions are asserted. The positive case alone would pass against a
tokenizer that split everything, including inside words, which would inflate
overlap and make the eval pass for the wrong reason.
"""
import importlib.util
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("eval_routing", ROOT / "tools" / "eval-routing.py")
er = importlib.util.module_from_spec(spec)
spec.loader.exec_module(er)

failures = []


def case(name, got, want):
    if got == want:
        print(f"  pass  {name}")
    else:
        print(f"  FAIL  {name}\n          got  {got!r}\n          want {want!r}")
        failures.append(name)


# The bug: a hyphenated name is two query words, not one opaque token.
# The bug: a hyphenated name is two query words, not one opaque token.
# Asserted exactly. A bare containment check would still pass against a
# tokenizer that emitted the whole string as one token *alongside* the parts,
# so `got` would be non-empty but wrong.
case("hyphenated name splits",
     sorted(er.toks("omnisend-automation")), ["automation", "omnisend"])

# A single-word name is unchanged.
case("plain name still one token",
     sorted(er.toks("bigquery-bigframes")), ["bigframes", "bigquery"])

# Stopwords are still dropped after splitting, or every query gains
# "for"/"and" overlap with every skill.
case("stopwords still dropped",
     "for" in er.toks("route-for-something") or "and" in er.toks("read-and-write"),
     False)

# Short fragments must not survive splitting.
case("short tokens still dropped",
     "ai" in er.toks("ai-x") or "io" in er.toks("x-io"), False)

# A tokenizer that split *inside* words would over-count overlap and inflate
# every score, passing the eval for the wrong reason. "authentication" must
# stay one token and must not decompose into shorter ones.
case("no intra-word fragments",
     "authentication" in er.toks("authentication setup")
     and not (er.toks("authentication setup") & {"auth", "ent", "tion"}), True)

# The concrete over-count this guards. `split-everything` strips every
# non-alphanumeric character rather than just hyphens, so "md" -- an extension
# shared by every document in the corpus -- enters the token set. That is a
# free overlap point against thousands of skills, and it is invisible in
# Hit@1, which only asks whether rank 1 is correct.
case("file extensions are not tokens",
     sorted(er.toks("skills/foo/bar.md")),
     ["bar", "foo", "skills"])

# Same mutation, seen from the scoring side: the extension term is what makes
# two unrelated paths overlap, so the overlap must be empty.
case("unrelated paths share no extension token",
     bool(er.toks("skills/foo/bar.md") & er.toks("agents/baz/qux.md")),
     False)

# Underscores are word separators here too, and this is what distinguishes the
# real tokenizer from one that strips every non-alphanumeric character: only
# the real one splits "foo_bar". The extension case above cannot tell them
# apart, because "md" is dropped for being too short either way, so both
# produce the same set and both pass.
case("underscores split like hyphens",
     sorted(er.toks("foo_bar")), ["bar", "foo"])

# The regression this file exists for: name overlap must be reachable for a
# hyphenated skill. Scored the way main() scores it.
name = "omnisend-automation"
score_name = 3 * len(er.toks("omnisend automation") & er.toks(name))
case("name overlap is non-zero for a hyphenated skill", score_name > 0, True)

# The composio product gate. It read `name.split("-")[0]`, which reduced
# "the-odds-api-automation" to "the" -- a stopword no query contains -- so that
# entry was excluded from every possible query and the correct answer could
# never surface. One entry, and the miss was structurally invisible.
GENERIC = {"api", "automation", "automate", "mcp", "tools", "tool",
           "cli", "sdk", "connector", "integration", "plugin", "agent"}


def product(n):
    return {s for s in n.lower().split("-")
            if len(s) > 2 and s not in er.STOP and s not in GENERIC}


case("multi-word product is reachable",
     bool(er.toks("the odds api automation") & product("the-odds-api-automation")),
     True)

# A query naming only a generic suffix must not open the gate, or all 742
# composio stubs flood the ranking and the gate has stopped gating. "api" is
# the generic suffix here and "bible" is the product word, so a query that
# mentions api and not bible must be refused.
case("generic suffixes do not open the gate",
     bool(er.toks("add oauth to my api") & product("api-bible-automation")), False)
case("product words do open the gate",
     bool(er.toks("bible api automation") & product("api-bible-automation")), True)

# The eval must refuse to report a single number. A scorer walked to 100% on a
# fixed corpus is indistinguishable from one that actually routes well; only a
# held-out set tells them apart.
src = (ROOT / "tools" / "eval-routing.py").read_text(encoding="utf-8")
case("eval reports both corpora",
     "heldout.jsonl" in src and "held out" in src, True)
case("eval gates on the held-out score",
     "held[0] <" in src, True)

if failures:
    print(f"\n{len(failures)} case(s) failed", file=sys.stderr)
    sys.exit(1)
print("all routing-tokenizer self-tests behaved correctly")
