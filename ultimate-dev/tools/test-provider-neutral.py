#!/usr/bin/env python3
"""Self-test for provider neutrality across the harnesses.

Why this test exists
--------------------

Three tools invoked a model, and between them they had a hardcoded agent name, a
hardcoded six-model vendor-namespaced pool, a hardcoded pair of that agent's
command-line flags, a hardcoded adapter path in a home directory, two copies of a
list of provider error strings, and a results field that recorded one vendor's
name whatever actually ran.

A test for that defect which greps for the string "opencode" would pass on
``AGENT = os.environ.get("AGENT", "opencode")``. It would also pass on a file
that had been fixed and then re-broken by a default. So these cases do not look
at the source text for a vendor name. They call the resolver with a name nobody
here uses, and assert it comes back out; and they call it with nothing, and
assert it refuses.

The eight cases, and what each would miss
-----------------------------------------

  N1  an override survives resolution          a flag that is accepted and ignored
  N2  nothing configured is a refusal          a silent default
  N3  the environment is honoured, and         a flag that is accepted and ignored,
      an explicit value beats it               or the wrong precedence
  N4  an agent flag keeps its leading dashes   a flag nobody can actually pass,
      and a flag with a space survives         because argparse eats it
  N5  one classifier, not two                  a second copy of the provider
                                                error table drifting from the first
  N6  the empty configuration names no vendor  the exact shape a grep-based test
                                                certifies while it is still broken
  N7  a report's runtime is the resolved value a report that still writes a
                                                literal into its provenance field
  N8  the endpoint actually changes            a --base-url flag that is accepted
                                                and then never used

N8 is the one that most needs asserting, because it is the most natural way to
claim neutrality: a flag exists, the flag is documented, and the request still
goes to the hardcoded host.
"""

from __future__ import annotations

import importlib.util
import json
import os
import pathlib
import re
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
SHARED = HERE / "agent_invocation.py"
PILOT = HERE / "run-pilot.py"
IMAGE = HERE / "generate-skill-image.py"
TESTBED = HERE.parent.parent / "testbed" / "run-tasks.py"

# A name no vendor here uses. If a default ever comes back, it will not be this.
NOT_A_VENDOR = "zz-nonexistent-runtime-zz"
NOT_A_VENDOR_MODEL = "zz-nobody/zz-model-zz"

FAILURES: list[str] = []


def check(label: str, condition: bool, detail: str = "") -> None:
    if condition:
        print(f"  pass  {label}")
    else:
        print(f"  FAIL  {label}  {detail}")
        FAILURES.append(label)


def load(path: pathlib.Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    # Registered before exec, not after. @dataclass resolves string annotations
    # by looking the defining module up in sys.modules, and a module that is not
    # there yet is None -- so a dataclass loaded this way dies inside the
    # decorator, before any of this file's assertions run.
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


# Loaded under its REAL module name, not a private alias. run-pilot.py does
# `from agent_invocation import ...`, so loading the file here under any other
# name creates a second module object -- and the identity assertion then fails
# for a reason that has nothing to do with the code: two copies of one file, not
# two copies of the logic. Registering it under the real name is what makes
# "is it the same object" a question about the source rather than about imports.
sys.path.insert(0, str(HERE))
ai = load(SHARED, "agent_invocation")


# ---- N1: an override survives resolution ---------------------------------
fake_runner = HERE / "agent_invocation.py"          # any existing file will do
inv = ai.Invocation.resolve(
    runner=fake_runner, agent=NOT_A_VENDOR, model=NOT_A_VENDOR_MODEL,
    agent_args=["--some-agent-flag", "--another"],
    env={},
)
check("N1 the agent name survives resolution", inv.agent == NOT_A_VENDOR, repr(inv.agent))
check("N1 the model survives resolution", inv.model == NOT_A_VENDOR_MODEL, repr(inv.model))
check("N1 the agent args survive resolution", list(inv.agent_args) == ["--some-agent-flag", "--another"],
      repr(inv.agent_args))
argv = inv.command("a prompt", timeout=7, cwd="/tmp")
check("N1 the agent reaches argv", "--agent" in argv and NOT_A_VENDOR in argv, repr(argv))
check("N1 the model reaches argv", NOT_A_VENDOR_MODEL in argv, repr(argv))
check("N1 the timeout reaches argv", argv[-1] == "7", repr(argv[-3:]))
check("N1 the cwd reaches argv", "/tmp" in argv, repr(argv))
check("N1 agent flags are passed as extra-args, not spliced",
      argv.count("--extra-args=--some-agent-flag") == 1, repr(argv))
check("N1 a dash-prefixed flag is not mistaken for an option",
      "--some-agent-flag" not in argv, repr(argv))


# ---- N2: nothing configured is a refusal, not a default ------------------
bare = ai.Invocation.resolve(env={})
check("N2 nothing configured names no agent", bare.agent is None, repr(bare.agent))
check("N2 nothing configured names no model", bare.model is None, repr(bare.model))
check("N2 nothing configured names no runner", bare.runner is None, repr(bare.runner))
check("N2 nothing configured is not ready", not bare.is_ready(), "reported ready")
gaps = bare.missing()
check("N2 it reports both gaps", len(gaps) == 2, repr(gaps))
check("N2 the gaps are actionable", all("ULTIMATE_DEV_" in g for g in gaps), repr(gaps))
raised = False
try:
    bare.command("p", timeout=1)
except ai.InvocationUnconfigured:
    raised = True
check("N2 command() refuses rather than guessing", raised, "no exception")
check("N2 a nonexistent runner is reported as such",
      "does not exist" in " ".join(
          ai.Invocation.resolve(runner=pathlib.Path("/nonexistent/runner.py"),
                                agent=NOT_A_VENDOR, env={}).missing()),
      "missing path not reported as missing")


# ---- N3: environment honoured, explicit beats it -------------------------
env = {"ULTIMATE_DEV_AGENT": "from-environment",
       "ULTIMATE_DEV_MODEL": "env/model",
       "ULTIMATE_DEV_AGENT_RUNNER": str(fake_runner),
       "ULTIMATE_DEV_AGENT_ARGS": "--from-env"}
from_env = ai.Invocation.resolve(env=env)
check("N3 the agent is read from the environment", from_env.agent == "from-environment",
      repr(from_env.agent))
check("N3 the model is read from the environment", from_env.model == "env/model",
      repr(from_env.model))
check("N3 the runner is read from the environment",
      from_env.runner == fake_runner, repr(from_env.runner))
check("N3 the agent args are read from the environment",
      list(from_env.agent_args) == ["--from-env"], repr(from_env.agent_args))
overridden = ai.Invocation.resolve(agent="from-argument", env=env)
check("N3 an explicit value beats the environment",
      overridden.agent == "from-argument", repr(overridden.agent))
# an explicit list replaces rather than extends, so "add one" cannot surprise you
replaced = ai.Invocation.resolve(agent_args=["--only-this"], env=env)
check("N3 an explicit arg list replaces the environment's",
      list(replaced.agent_args) == ["--only-this"], repr(replaced.agent_args))
# a flag whose value contains a space survives the environment path
spaced = ai.Invocation.resolve(
    env={"ULTIMATE_DEV_AGENT_ARGS": '--flag "two words"', "ULTIMATE_DEV_AGENT": "a"})
check("N3 a quoted value with a space survives",
      list(spaced.agent_args) == ["--flag", "two words"], repr(spaced.agent_args))


# ---- N4: agent flags keep their dashes; the = form is usable --------------
help_text = subprocess.run([sys.executable, str(PILOT), "--help"],
                           capture_output=True, text=True).stdout
check("N4 the pilot documents the = form for dash-prefixed flags",
      "--agent-arg=" in help_text, "--agent-arg= not in --help")
for tool in (PILOT, TESTBED):
    name = tool.name
    proc = subprocess.run(
        [sys.executable, str(tool), "--help"], capture_output=True, text=True)
    check(f"N4 {name} --help works", proc.returncode == 0, proc.stderr[-120:])
    check(f"N4 {name} --help documents --agent", "--agent" in proc.stdout, "")


# ---- N5: one classifier, not two ------------------------------------------
for tool in (PILOT, TESTBED, SHARED):
    src = tool.read_text(encoding="utf-8")
    definitions = len(re.findall(r"^ENVIRONMENT_ERRORS\s*[:=]", src, re.M))
    if tool is SHARED:
        check("N5 the shared module defines the classifier once", definitions == 1,
              f"{definitions} definitions")
    else:
        check(f"N5 {tool.name} does not define its own copy", definitions == 0,
              f"{definitions} definitions")
        check(f"N5 {tool.name} imports the shared one",
              "classify_environment_failure" in src
              and ("from agent_invocation import" in src),
              "no import of agent_invocation")

# Identity, not equality by name. A caller that re-declared the function would
# satisfy every check above -- one definition in the shared module, none in the
# caller, an import of the name -- while quietly running its own logic. Only
# object identity catches that.
pilot_mod = load(PILOT, "run_pilot_under_test")
check("N5 the pilot's classifier IS the shared object",
      pilot_mod.classify_environment_failure is ai.classify_environment_failure,
      "a same-named copy, not the shared one")
check("N5 the pilot no longer exposes a provider-error table",
      not hasattr(pilot_mod, "ENVIRONMENT_ERRORS"), "")


# ---- N6: the empty configuration names no vendor --------------------------
described = bare.describe()
for key in ("agent", "model", "runner"):
    value = described.get(key)
    check(f"N6 the unconfigured {key} is null, not a vendor",
          value is None, repr(value))
check("N6 describe() marks it unconfigured", described["configured"] is False, "")
check("N6 describe() lists the gaps", len(described["missing"]) == 2, "")


# ---- N7: a report's runtime is the resolved value, not a literal ----------
pilot_src = PILOT.read_text(encoding="utf-8")
# Comment text is stripped first. The first textual match for `"runtime":` in
# that file is the comment explaining that the literal was removed, so searching
# raw text asserts against the description of a fix rather than the fix itself.
# That is the stale-fixture mistake the CI suite's `edit()` helper made: the
# needle was not where the check believed it was, and the test reported a defect
# that was not in the code.
pilot_code = "\n".join(line.split("#", 1)[0] for line in pilot_src.splitlines())
runtime_fields = re.findall(r'"runtime":\s*(.+)', pilot_code)
check("N7 the pilot has exactly one runtime field", len(runtime_fields) == 1,
      repr(runtime_fields))
check("N7 the pilot's runtime field is not a string literal",
      bool(runtime_fields) and not re.match(r"""\s*["'][a-z]""", runtime_fields[0]),
      runtime_fields[0][:60] if runtime_fields else "no runtime field")
check("N7 no vendor literal appears anywhere in executable pilot code",
      not re.search(r"""["']opencode["']""", pilot_code), "vendor literal in code")
check("N7 the runtime field comes from describe()",
      "invocation.describe()" in pilot_code, "")

# and the rows file records it too
testbed_src = TESTBED.read_text(encoding="utf-8")
check("N7 the testbed results file records the runtime",
      '"runtime": target.describe()' in testbed_src, "")


# ---- N8: the endpoint actually changes ------------------------------------
gi = load(IMAGE, "generate_skill_image_under_test")
check("N8 the image tool exposes an image model", hasattr(gi, "DEFAULT_IMAGE_MODEL"), "")
check("N8 the image tool exposes a base URL", hasattr(gi, "DEFAULT_BASE_URL"), "")

parser = gi.build_parser()
for flag in ("--image-model", "--base-url", "--prompt-model", "--api-key"):
    check(f"N8 the image tool accepts {flag}",
          any(flag in a.option_strings for a in parser._actions), "")

# the payload must carry the requested model, not the module default
args = parser.parse_args(["--skill", "does-not-exist", "--prompt-only",
                          "--image-model", NOT_A_VENDOR_MODEL])
check("N8 --image-model reaches the parsed args",
      args.image_model == NOT_A_VENDOR_MODEL, repr(args.image_model))
payload = gi.build_payload("a prompt", args)
check("N8 the payload carries the requested model",
      payload.get("model") == NOT_A_VENDOR_MODEL, repr(payload.get("model")))

args2 = parser.parse_args(["--skill", "x", "--prompt-only", "--base-url",
                           "https://example.invalid/v9"])
check("N8 --base-url reaches the parsed args",
      args2.base_url == "https://example.invalid/v9", repr(args2.base_url))
# and the request URL is derived from it, which is the part a flag-shaped fix misses
images_url = args2.base_url.rstrip("/") + "/images"
chat_url = args2.base_url.rstrip("/") + "/chat/completions"
check("N8 the images endpoint follows the base URL",
      images_url == "https://example.invalid/v9/images", images_url)
check("N8 the chat endpoint follows the base URL",
      chat_url == "https://example.invalid/v9/chat/completions", chat_url)
src_img = IMAGE.read_text(encoding="utf-8")
check("N8 no hardcoded images host survives in code",
      not re.search(r'''post_json\(\s*["']https?://''', src_img), "")
check("N8 no hardcoded chat host survives in code",
      not re.search(r'''["']https?://[^"']*/chat/completions["']''', src_img), "")
check("N8 the prompt model is also overridable",
      "default=DEFAULT_PROMPT_MODEL" in src_img
      and "--prompt-model" in src_img, "")


# ---- report ---------------------------------------------------------------
if FAILURES:
    print(f"\nFAIL  {len(FAILURES)} case(s) failed: {', '.join(FAILURES)}")
    sys.exit(1)
print("\nall self-tests passed")
sys.exit(0)
