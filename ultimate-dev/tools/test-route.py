#!/usr/bin/env python3
"""route.py must agree with eval-routing.py, and must fail loudly when it cannot.

Two properties, both load-bearing:

  1. The dispatcher and the measurement of the dispatcher must not drift.
     eval-routing.py exists to tell whether routing works. If it scores with
     different rules from the tool that actually routes, it measures a system
     nobody uses, and can pass while real requests route badly. Both must call
     the same tokeniser and weight the same terms.

  2. A route that finds nothing must say so and exit non-zero. The failure
     this guards is the expensive one: a dispatcher that returns its best
     guess for a task no capability covers, which is worse than returning
     nothing, because the guess reads as an answer.

Every case mutates the real tool and asserts the suite catches it. A self-test
that cannot fail proves nothing.
"""
import importlib.util
import json
import pathlib
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
failures = []


def load(name):
    spec = importlib.util.spec_from_file_location(name, TOOLS / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


route = load("route")
evalr = load("eval-routing")


def case(name, ok, detail=""):
    if ok:
        print(f"  pass  {name}")
    else:
        print(f"  FAIL  {name}{(': ' + detail) if detail else ''}")
        failures.append(name)


def run(*argv):
    return subprocess.run([sys.executable, str(TOOLS / "route.py"), *argv],
                          capture_output=True, text=True, cwd=ROOT)


# 1. Shared tokeniser. Divergence here means the eval measures a scorer nobody
#    routes with, which is how a routing bug hides behind a passing eval.
case("tokenisers agree",
     all(route.toks(s) == evalr.toks(s)
         for s in ("omnisend-automation", "add oauth", "skills/foo/bar.md",
                   "python automation", "3d-scene-developer")))

case("weights match the eval's",
     (route.WEIGHTS["name"], route.WEIGHTS["when"],
      route.WEIGHTS["description"], route.WEIGHTS["body"]) == (3, 2, 1, 2),
     f"route.py weights {route.WEIGHTS}")

# The name term must be reachable for a hyphenated skill, or the strongest
# signal is dead for most of the corpus.
case("name term reachable",
     route.WEIGHTS["name"] * len(route.toks("omnisend automation")
                                 & route.toks("omnisend-automation")) > 0)


# 2. Determinism. The same query must rank the same way twice, or the ranking
#    carries no information a reader can rely on.
a = run("wire up an mcp server", "--limit", "5", "--json")
b = run("wire up an mcp server", "--limit", "5", "--json")
case("deterministic", a.stdout == b.stdout and a.returncode == 0)
if a.returncode == 0:
    payload = json.loads(a.stdout)
    case("returns candidates", bool(payload["candidates"]))
    case("respects --limit",
         len(payload["candidates"]) <= 5, str(len(payload["candidates"])))
    case("candidates carry their not-list",
         all("not" in c for c in payload["candidates"]))
    case("candidates carry a path",
         all((ROOT / c["path"]).is_file() for c in payload["candidates"]),
         "every returned path must exist on disk")

# A task nothing covers must exit non-zero and say so. Exit 0 with a confident
# wrong answer is the expensive failure. The tokens must be non-words: an
# earlier version of this used "nonsense task with no matching capability",
# whose real words matched real bodies and returned candidates, so the case
# passed for the wrong reason and asserted nothing.
junk = run("zzqxy wqvbtr", "--json")
case("empty result exits non-zero", junk.returncode != 0, f"rc={junk.returncode}")
case("empty result explains itself",
     "nothing in the index matches" in junk.stdout + junk.stderr)

# --kind must restrict, not merely relabel.
agent = run("verify the agent role", "--kind", "agent", "--limit", "3", "--json")
if agent.returncode == 0:
    kinds = {c["kind"] for c in json.loads(agent.stdout)["candidates"]}
    case("--kind filters", kinds == {"agent"}, str(kinds))

# Composable stubs must not flood a non-composio query. 742 entries share a
# near-identical description, so without the product gate they crowd out real
# skills.
compo = run("edit a photo", "--limit", "5", "--json")
if compo.returncode == 0:
    names = [c["name"] for c in json.loads(compo.stdout)["candidates"]]
    case("no composio flood",
         not any(n.endswith("-automation") for n in names), str(names))


# 3. Mutation control. Break route.py and confirm the suite notices.
#
# Each mutation re-runs this whole file as a subprocess, so the nested run must
# skip this section or it spawns another nested run for its own mutations, and
# the suite never returns. The guard is an env var rather than an argument
# because the nested process has to be a plain invocation of the same file.
import os

MUTATIONS = [
    ("json.loads(INDEX.read_text(encoding=\"utf-8\"))[\"entries\"]",
     "json.loads(INDEX.read_text(encoding=\"utf-8\"))[\"entries\"][:3]",
     "truncating the candidate set must break a routing assertion"),
    ('                  "forcing a fit")\n        return 1',
     '                  "forcing a fit")\n        return 0',
     "swallowing the empty-result exit code must break a case"),
    ('        if total < args.min_score:\n            continue',
     '        if total < args.min_score + 50:\n            continue',
     "an unreachable threshold that empties every result must break a case"),
]

if os.environ.get("ROUTE_MUTATION_CHILD"):
    # Nested run: report and stop before recursing further.
    print("  (nested mutation run: skipping mutation control)")
else:
    # A pristine copy, taken once, is the only safe thing to restore from.
    #
    # The first version of this harness read the file inside each mutation,
    # replaced, and wrote the original string back. That is wrong twice over,
    # and both failures were observed rather than imagined. The anchor
    # `["entries"]` is a substring of `["entries"][:3]`, so each run appended
    # another `[:3]` to whatever it found -- and "restoring" the string it had
    # read captured the mutation, not the file. The file ended up carrying
    # several thousand chained `[:3]` and a duplicate `return 0`, and the
    # suite still reported which cases failed.
    #
    # So: refuse to mutate unless the anchor occurs exactly once, and restore
    # from a snapshot taken before any mutation rather than from a re-read.
    PRISTINE = (TOOLS / "route.py").read_text(encoding="utf-8")

    def with_mutation(old, new):
        path = TOOLS / "route.py"
        if PRISTINE.count(old) != 1:
            raise AssertionError(
                f"anchor occurs {PRISTINE.count(old)} times, not once: {old!r}. "
                "A non-unique anchor is what compounded the mutation before."
            )
        path.write_text(PRISTINE.replace(old, new, 1), encoding="utf-8")
        try:
            proc = subprocess.run(
                [sys.executable, str(__file__)],
                capture_output=True, text=True, cwd=ROOT,
                env=dict(os.environ, ROUTE_MUTATION_CHILD="1"),
                timeout=300,
            )
            return proc.returncode != 0, proc.stdout + proc.stderr
        finally:
            path.write_text(PRISTINE, encoding="utf-8")
            # Prove the restore, rather than assuming it.
            assert path.read_text(encoding="utf-8") == PRISTINE, \
                "route.py was not restored; refusing to leave a mutated tool behind"
    for old, new, why in MUTATIONS:
        try:
            caught, output = with_mutation(old, new)
        except AssertionError as exc:
            print(f"  SKIP  {why}: {exc}")
            continue
        if not caught:
            print(f"        mutation was NOT caught; suite output:\n{output[-800:]}")
        case(f"mutation caught: {why}", caught)

if failures:
    print(f"\n{len(failures)} case(s) failed", file=sys.stderr)
    sys.exit(1)
print("all routing-dispatcher self-tests behaved correctly")
