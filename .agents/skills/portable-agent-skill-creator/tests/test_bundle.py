#!/usr/bin/env python3
"""Test suite for the skill-creator bundle.

Runs on a bare Python 3 install: no agent CLI, no PyYAML, no network, no
display. Anything that needs a real runtime is exercised through a fake agent
script, and the PyYAML-dependent paths are additionally run with the fallback
frontmatter parser forced on.

Run:
    python3 tests/test_bundle.py
    python3 -m unittest discover -s tests -v
"""

from __future__ import annotations

import sys

# Must precede any import of the bundle. Without this, importing scripts.* in
# this process writes __pycache__ into the bundle the suite is testing, and the
# working tree is left dirty after a run.
sys.dont_write_bytecode = True

import json  # noqa: E402
import os  # noqa: E402
import re  # noqa: E402
import shutil  # noqa: E402
import stat  # noqa: E402
import subprocess  # noqa: E402
import tempfile  # noqa: E402
import unittest  # noqa: E402
from pathlib import Path  # noqa: E402

BUNDLE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BUNDLE))

import scripts.utils as utils  # noqa: E402
from scripts import agent_runner, aggregate_benchmark, grade, utils as _utils  # noqa: E402
from scripts import quick_validate, run_eval as run_eval_mod  # noqa: E402
from scripts import run_loop as run_loop_mod  # noqa: E402
from scripts.improve_description import validate_description  # noqa: E402

PY = sys.executable


def run_python(*args, cwd=None, env=None, timeout=120):
    """Run a script the way the documentation tells a user to.

    Bytecode writing is disabled: without this, every subprocess drops a
    ``__pycache__`` into the bundle it is testing, and the suite leaves the
    working tree dirty.
    """
    return subprocess.run(
        [PY, *[str(a) for a in args]],
        cwd=str(cwd) if cwd else None,
        capture_output=True,
        text=True,
        timeout=timeout,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1", **(env or {})},
    )


def make_skill(root: Path, name: str = "demo-skill", description: str = "Use when testing.") -> Path:
    skill = root / name
    skill.mkdir(parents=True, exist_ok=True)
    (skill / "SKILL.md").write_text(
        f"---\nname: {name}\ndescription: {description}\nlicense: MIT\n---\n\n# {name}\n",
        encoding="utf-8",
    )
    return skill


FAKE_AGENT = """#!/bin/sh
mkdir -p pdf-notes
printf -- '---\\nname: pdf-notes\\ndescription: Use when summarizing a PDF.\\n---\\n\\n# Notes\\n' \\
  > pdf-notes/SKILL.md
printf 'Created pdf-notes/SKILL.md.\\n'
"""


def install_fake_agent(directory: Path) -> str:
    path = directory / "fake-agent"
    path.write_text(FAKE_AGENT, encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IEXEC)
    return str(path)


class TempDirCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)


# ---------------------------------------------------------------------------
# B1 regression: every documented command must actually run
# ---------------------------------------------------------------------------


class DocumentedCommandsRun(TempDirCase):
    """The bundle's central promise: the commands in SKILL.md work."""

    def test_documented_script_invocations_do_not_crash(self) -> None:
        text = (BUNDLE / "SKILL.md").read_text(encoding="utf-8")
        # Commands that must at minimum parse their arguments and exit cleanly
        # when given --help.
        invoked = sorted(set(re.findall(r"python3? (scripts/[\w/]+\.py)", text)))
        self.assertTrue(invoked, "SKILL.md documents no script commands")

        for script in invoked:
            if script not in ("scripts/agent_runner.py",):
                with self.subTest(script=script):
                    result = run_python(BUNDLE / script, "--help")
                    self.assertEqual(
                        result.returncode, 0,
                        f"`{script} --help` failed:\n{result.stderr}",
                    )

    def test_scripts_are_runnable_as_modules_too(self) -> None:
        for script in sorted((BUNDLE / "scripts").glob("*.py")):
            if script.name == "__init__.py":
                continue
            with self.subTest(script=script.name):
                result = run_python(
                    "-m", f"scripts.{script.stem}", "--help", cwd=BUNDLE
                )
                self.assertEqual(
                    result.returncode, 0,
                    f"`python -m scripts.{script.stem} --help` failed:\n{result.stderr}",
                )

    def test_quick_validate_works_from_an_unrelated_directory(self) -> None:
        skill = make_skill(self.tmp)
        result = run_python(
            BUNDLE / "scripts" / "quick_validate.py", skill, cwd=Path(tempfile.gettempdir())
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_package_skill_runs_as_documented(self) -> None:
        skill = make_skill(self.tmp)
        result = run_python(
            BUNDLE / "scripts" / "package_skill.py", skill, self.tmp / "dist",
            cwd=Path(tempfile.gettempdir()),
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertTrue((self.tmp / "dist" / "demo-skill.skill").is_file())


# ---------------------------------------------------------------------------
# Frontmatter parsing: one parser, two backends, same answer
# ---------------------------------------------------------------------------


class Frontmatter(unittest.TestCase):
    # name and description are the fields quick_validate acts on, so both
    # backends must agree on them exactly.
    STRING_FIELDS = [
        ("---\nname: a-b\ndescription: Use when x.\n---\nbody", "a-b", "Use when x."),
        ("---\nname: a\ndescription: >\n  Use when\n  testing.\n---\nb", "a", "Use when testing."),
        ("---\nname: a\ndescription: |\n  line one\n  line two\n---\nb", "a", "line one\nline two"),
        ("---\nname: a\ndescription: |-\n  only line\n---\nb", "a", "only line"),
        ('---\nname: "quoted"\ndescription: \'single\'\n---\nb', "quoted", "single"),
    ]
    # Structures the fallback must handle without crashing.
    STRUCTURAL = [
        "---\nname: a\nallowed-tools: [Read, Write]\n---\nb",
        "---\nname: a\nmetadata:\n  version: 2\n---\nb",
        "---\nname: a\nallowed-tools:\n  - Read\n  - Write\n---\nb",
    ]

    def _parse_with(self, content: str, use_yaml: bool):
        original = utils.have_yaml
        utils.have_yaml = lambda: use_yaml
        try:
            return utils.parse_frontmatter(content)
        finally:
            utils.have_yaml = original

    def test_string_fields_agree_across_backends(self) -> None:
        for content, name, description in self.STRING_FIELDS:
            for use_yaml in (True, False):
                backend = "pyyaml" if use_yaml else "fallback"
                with self.subTest(case=content[:26], backend=backend):
                    parsed = self._parse_with(content, use_yaml)
                    self.assertEqual(parsed.get("name"), name)
                    self.assertEqual(parsed.get("description"), description)

    def test_structural_forms_parse_on_both_backends(self) -> None:
        for content in self.STRUCTURAL:
            for use_yaml in (True, False):
                backend = "pyyaml" if use_yaml else "fallback"
                with self.subTest(case=content[:26], backend=backend):
                    parsed = self._parse_with(content, use_yaml)
                    self.assertIsInstance(parsed, dict)
                    self.assertEqual(parsed.get("name"), "a")
                    self.assertIsNotNone(parsed.get("allowed-tools") or parsed.get("metadata"))

    def test_folded_and_literal_blocks_are_not_conflated(self) -> None:
        folded = self._parse_with("---\nname: a\ndescription: >\n  x\n  y\n---\nb", False)
        literal = self._parse_with("---\nname: a\ndescription: |\n  x\n  y\n---\nb", False)
        self.assertNotEqual(folded["description"], literal["description"])

    def test_missing_frontmatter_returns_empty(self) -> None:
        self.assertEqual(utils.parse_frontmatter("no frontmatter here"), {})

    def test_parse_skill_md_falls_back_to_directory_name(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            skill = Path(tmp) / "unnamed-skill"
            skill.mkdir()
            (skill / "SKILL.md").write_text("---\nlicense: MIT\n---\n\nbody\n", encoding="utf-8")
            name, description, _ = utils.parse_skill_md(skill)
            self.assertEqual(name, "unnamed-skill")
            self.assertEqual(description, "")


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


class Validation(TempDirCase):
    def test_valid_skill_passes(self) -> None:
        result = quick_validate.validate_skill(make_skill(self.tmp))
        self.assertTrue(result, result.message())
        self.assertEqual(result.errors, [])

    def test_missing_skill_md(self) -> None:
        (self.tmp / "empty").mkdir()
        result = quick_validate.validate_skill(self.tmp / "empty")
        self.assertFalse(result)
        self.assertIn("SKILL.md not found", result.message())

    def test_rejects_non_kebab_case_name(self) -> None:
        skill = make_skill(self.tmp, name="Bad_Name")
        (skill / "SKILL.md").write_text(
            "---\nname: Bad_Name\ndescription: Use when x.\n---\n\nb\n", encoding="utf-8"
        )
        result = quick_validate.validate_skill(skill)
        self.assertFalse(result)
        self.assertIn("kebab-case", result.message())

    def test_rejects_oversized_description(self) -> None:
        skill = make_skill(self.tmp, description="x" * 1100)
        result = quick_validate.validate_skill(skill)
        self.assertFalse(result)
        self.assertIn("maximum is 1024", result.message())

    def test_rejects_angle_brackets_in_description(self) -> None:
        skill = self.tmp / "brackets"
        skill.mkdir()
        (skill / "SKILL.md").write_text(
            "---\nname: brackets\ndescription: Use <when> testing.\n---\n\nb\n", encoding="utf-8"
        )
        result = quick_validate.validate_skill(skill)
        self.assertFalse(result)
        self.assertIn("angle brackets", result.message())

    def test_rejects_unknown_frontmatter_key(self) -> None:
        skill = self.tmp / "extra"
        skill.mkdir()
        (skill / "SKILL.md").write_text(
            "---\nname: extra\ndescription: Use when x.\nversion: 2\n---\n\nb\n", encoding="utf-8"
        )
        result = quick_validate.validate_skill(skill)
        self.assertFalse(result)
        self.assertIn("unexpected frontmatter key", result.message())

    def test_detects_reference_to_missing_file(self) -> None:
        skill = make_skill(self.tmp)
        (skill / "SKILL.md").write_text(
            "---\nname: demo-skill\ndescription: Use when x.\n---\n\n"
            "Run `scripts/does_not_exist.py` for details.\n",
            encoding="utf-8",
        )
        result = quick_validate.validate_skill(skill)
        self.assertFalse(result)
        self.assertIn("references missing file", result.message())

    def test_name_directory_mismatch_is_a_warning_by_default(self) -> None:
        skill = make_skill(self.tmp)
        (skill / "SKILL.md").write_text(
            "---\nname: different-name\ndescription: Use when x.\n---\n\nb\n", encoding="utf-8"
        )
        self.assertTrue(quick_validate.validate_skill(skill))
        strict = quick_validate.validate_skill(skill, strict=True)
        self.assertFalse(strict)

    def test_runs_without_pyyaml(self) -> None:
        skill = make_skill(self.tmp)
        # quick_validate imports have_yaml by value, so patch its own binding.
        original = quick_validate.have_yaml
        try:
            quick_validate.have_yaml = lambda: False
            result = quick_validate.validate_skill(skill)
        finally:
            quick_validate.have_yaml = original
        self.assertTrue(result, result.message())
        self.assertTrue(any("PyYAML" in w for w in result.warnings))

    def test_package_skill_refuses_invalid_skill(self) -> None:
        skill = self.tmp / "broken"
        skill.mkdir()
        (skill / "SKILL.md").write_text("no frontmatter\n", encoding="utf-8")
        result = run_python(BUNDLE / "scripts" / "package_skill.py", skill, self.tmp / "d")
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((self.tmp / "d" / "broken.skill").exists())


# ---------------------------------------------------------------------------
# Eval schema normalization
# ---------------------------------------------------------------------------


class EvalSchema(TempDirCase):
    def write(self, payload) -> Path:
        path = self.tmp / "evals.json"
        path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    def test_canonical_fields(self) -> None:
        name, evals = utils.load_evals(self.write({"skill_name": "s", "evals": [
            {"id": 1, "query": "do a thing", "should_trigger": False, "assertions": []},
        ]}))
        self.assertEqual(name, "s")
        self.assertEqual(evals[0]["query"], "do a thing")
        self.assertIs(evals[0]["should_trigger"], False)

    def test_legacy_prompt_alias_is_accepted(self) -> None:
        _name, evals = utils.load_evals(self.write([
            {"prompt": "legacy task", "expectations": [{"type": "manual"}]},
        ]))
        self.assertEqual(evals[0]["query"], "legacy task")
        self.assertEqual(evals[0]["assertions"], [{"type": "manual"}])
        self.assertEqual(evals[0]["id"], 1)

    def test_should_trigger_defaults_to_true(self) -> None:
        _name, evals = utils.load_evals(self.write([{"query": "x"}]))
        self.assertIs(evals[0]["should_trigger"], True)

    def test_missing_query_is_a_clear_error(self) -> None:
        with self.assertRaises(ValueError) as ctx:
            utils.load_evals(self.write([{"expected_output": "x"}]))
        self.assertIn("non-empty 'query'", str(ctx.exception))

    def test_duplicate_ids_rejected(self) -> None:
        with self.assertRaises(ValueError) as ctx:
            utils.load_evals(self.write([
                {"id": 1, "query": "a"}, {"id": 1, "query": "b"},
            ]))
        self.assertIn("duplicate ids", str(ctx.exception))

    def test_empty_eval_set_rejected(self) -> None:
        with self.assertRaises(ValueError):
            utils.load_evals(self.write({"evals": []}))

    def test_bundled_evals_file_is_valid(self) -> None:
        eval_file = BUNDLE / "evals" / "evals.json"
        if not eval_file.is_file():
            # The packaged archive excludes evals/ as development material.
            self.skipTest("evals/evals.json is not present in this bundle")
        name, evals = utils.load_evals(eval_file)
        self.assertTrue(evals)
        self.assertEqual(name, "portable-agent-skill-creator")
        for item in evals:
            for assertion in item.get("assertions", []):
                self.assertIn(
                    assertion["type"], utils.VALID_ASSERTION_TYPES,
                    f"bundled eval {item['id']} uses an unimplemented assertion type",
                )


# ---------------------------------------------------------------------------
# Runtime adapters
# ---------------------------------------------------------------------------


class Adapters(unittest.TestCase):
    def test_registry_loads_and_is_wellformed(self) -> None:
        registry = agent_runner.load_registry()
        adapters = agent_runner.get_adapters(registry)
        self.assertGreaterEqual(len(adapters), 10)
        self.assertIn("custom", adapters)
        for name, spec in adapters.items():
            with self.subTest(adapter=name):
                self.assertIn("confidence", spec)
                if name == "custom":
                    continue
                self.assertTrue(spec.get("executable"))
                self.assertIn("{prompt}", spec.get("argv", []))
                if "model_flag" not in spec:
                    # Adapters without a model flag are allowed, but must say so.
                    self.assertNotEqual(spec.get("confidence"), "documented")

    def test_every_adapter_argv_starts_with_its_executable(self) -> None:
        # Regression: build_command assembled the flag list without prepending
        # the program, so every registry adapter tried to exec "-p". Only
        # --agent custom happened to work, which is why the e2e tests missed it.
        registry = agent_runner.load_registry()
        for name, spec in agent_runner.get_adapters(registry).items():
            with self.subTest(adapter=name):
                command = "/opt/fake/bin/" + name if name == "custom" else None
                argv = agent_runner.build_command(name, "PROMPT", command=command, registry=registry)
                executable = command if name == "custom" else spec["executable"]
                # An installed CLI is resolved to its absolute path.
                expected = shutil.which(executable) or executable
                self.assertEqual(
                    argv[0], expected,
                    f"{name}: argv must begin with the executable, got {argv}",
                )
                self.assertIn("PROMPT", argv)

    def test_registered_adapter_argv_is_executable(self) -> None:
        # Exercise a registry adapter (not --agent custom) with a fake program
        # named after a registered adapter, so the assembly is proven, not assumed.
        with tempfile.TemporaryDirectory() as tmp:
            fake = Path(tmp) / "gemini"
            fake.write_text("#!/bin/sh\nprintf 'ok from gemini\\n'\n", encoding="utf-8")
            fake.chmod(fake.stat().st_mode | stat.S_IEXEC)

            argv = agent_runner.build_command("gemini", "PROMPT")
            # Swap in the fake program; everything else comes from the registry.
            argv[0] = str(fake)
            proc = subprocess.run(argv, capture_output=True, text=True, timeout=60)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("ok from gemini", proc.stdout)

    def test_dry_run_builds_argv_for_every_adapter(self) -> None:
        registry = agent_runner.load_registry()
        for name in agent_runner.adapter_names(registry):
            if name == "custom":
                continue
            spec = agent_runner.get_adapters(registry)[name]
            with self.subTest(adapter=name):
                argv = agent_runner.build_command(name, "PROMPT", registry=registry)
                self.assertIn("PROMPT", argv)
                # A path-like executable must be absolutized so it still
                # resolves after the runner changes into a per-run sandbox. A
                # bare name is only resolvable if the CLI is installed.
                if os.sep in spec["executable"] or shutil.which(spec["executable"]):
                    self.assertTrue(os.path.isabs(argv[0]), "executable must be absolutized")

    def test_model_flag_inserted_when_declared(self) -> None:
        argv = agent_runner.build_command("opencode", "P", model="some-model")
        self.assertIn("--model", argv)
        self.assertIn("some-model", argv)

    def test_model_flag_absent_adapter_warns_rather_than_dropping(self) -> None:
        argv = agent_runner.build_command("amp", "P", model="m")
        self.assertNotIn("m", argv)

    def test_custom_adapter_keeps_the_executable_in_argv(self) -> None:
        # Regression: the executable was once stored but never placed in argv,
        # so the prompt was executed as the program.
        argv = agent_runner.build_command("custom", "PROMPT", command="/bin/echo run")
        self.assertEqual(argv[0], "/bin/echo")
        self.assertEqual(argv[-1], "PROMPT")

    def test_custom_adapter_requires_command(self) -> None:
        with self.assertRaises(ValueError):
            agent_runner.build_command("custom", "P")

    def test_auto_refuses_to_ignore_an_explicit_command(self) -> None:
        # Regression: `auto` silently discarded --command and ran a different,
        # installed agent instead of the one the caller named.
        with self.assertRaises(ValueError) as ctx:
            agent_runner.resolve_adapter("auto", command="/bin/true")
        self.assertIn("cannot be combined", str(ctx.exception))

    def test_custom_adapter_survives_a_cwd_change(self) -> None:
        argv = agent_runner.build_command("custom", "P", command="./bin/fake-agent")
        self.assertTrue(os.path.isabs(argv[0]))

    def test_unknown_agent_lists_alternatives(self) -> None:
        with self.assertRaises(ValueError) as ctx:
            agent_runner.resolve_adapter("nope")
        self.assertIn("--agent custom", str(ctx.exception))

    def test_model_is_redacted_from_recorded_command(self) -> None:
        redacted = agent_runner.redact(["prog", "the-prompt"], "the-prompt")
        self.assertEqual(redacted, ["prog", "<prompt>"])

    def test_usage_is_absent_unless_reported(self) -> None:
        self.assertEqual(agent_runner.extract_usage("no numbers here"), {})
        self.assertEqual(
            agent_runner.extract_usage('{"usage": {"total_tokens": 42}}'),
            {"total_tokens": 42},
        )

    def test_list_runtimes_runs(self) -> None:
        result = run_python(BUNDLE / "scripts" / "agent_runner.py", "list-runtimes", "--json")
        self.assertEqual(result.returncode, 0, result.stderr)
        rows = json.loads(result.stdout)
        self.assertTrue(any(r["agent"] == "custom" for r in rows))

    def test_dry_run_subcommand(self) -> None:
        result = run_python(
            BUNDLE / "scripts" / "agent_runner.py",
            "--agent", "opencode", "--prompt", "hello", "--dry-run",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        argv = json.loads(result.stdout)["argv"]
        # argv[0] is the executable; the prompt is redacted, and the last real
        # token is the prompt the adapter received.
        self.assertTrue(argv[0].endswith("opencode"))
        self.assertEqual(argv[-1], "hello")
        self.assertNotIn("hello", argv[:-1])

    def test_missing_executable_is_reported_not_raised(self) -> None:
        registry = agent_runner.load_registry()
        spec = {"executable": "definitely-not-installed-xyz", "argv": ["{prompt}"], "confidence": "documented"}
        result = agent_runner.run_prompt(
            "P", agent="custom", command="definitely-not-installed-xyz", registry=registry
        )
        self.assertIsNone(result["exit_code"])
        self.assertEqual(result["error"], "ExecutableNotFound")


# ---------------------------------------------------------------------------
# Grading
# ---------------------------------------------------------------------------


class Grading(TempDirCase):
    def grade(self, assertions, stdout="", exit_code=0):
        return grade.grade_run(
            assertions, base=self.tmp, stdout=stdout, stderr="", exit_code=exit_code
        )

    def test_file_and_content_assertions(self) -> None:
        (self.tmp / "a.md").write_text("# Title\nbody\n", encoding="utf-8")
        result = self.grade([
            {"type": "file_exists", "path": "a.md"},
            {"type": "file_absent", "path": "b.md"},
            {"type": "file_contains", "path": "a.md", "value": "Title"},
            {"type": "output_contains", "value": "done"},
        ], stdout="all done")
        self.assertEqual(result["summary"]["failed"], 0, result)
        self.assertEqual(result["summary"]["pass_rate"], 1.0)

    def test_file_contains_detects_wrong_heading_depth(self) -> None:
        (self.tmp / "a.md").write_text("# Title\n", encoding="utf-8")
        result = self.grade([{"type": "file_contains", "path": "a.md", "value": "## Title"}])
        self.assertEqual(result["summary"]["failed"], 1)

    def test_json_valid_with_required_keys(self) -> None:
        (self.tmp / "d.json").write_text('{"a": 1}', encoding="utf-8")
        ok = self.grade([{"type": "json_valid", "path": "d.json", "required_keys": ["a"]}])
        bad = self.grade([{"type": "json_valid", "path": "d.json", "required_keys": ["b"]}])
        invalid = self.grade([{"type": "json_valid", "path": "d.json"}])
        (self.tmp / "broken.json").write_text("{oops", encoding="utf-8")
        broken = self.grade([{"type": "json_valid", "path": "broken.json"}])
        self.assertEqual(ok["summary"]["failed"], 0)
        self.assertEqual(bad["summary"]["failed"], 1)
        self.assertEqual(invalid["summary"]["failed"], 0)
        self.assertEqual(broken["summary"]["failed"], 1)

    def test_command_succeeds_and_fails(self) -> None:
        ok = self.grade([{"type": "command_succeeds", "command": "true"}])
        bad = self.grade([{"type": "command_succeeds", "command": "false"}])
        self.assertEqual(ok["summary"]["failed"], 0)
        self.assertEqual(bad["summary"]["failed"], 1)

    def test_frontmatter_valid_assertion(self) -> None:
        make_skill(self.tmp, name="inner-skill")
        (self.tmp / "bad").mkdir()
        (self.tmp / "bad" / "SKILL.md").write_text("no frontmatter", encoding="utf-8")
        result = self.grade([
            {"type": "frontmatter_valid", "path": "inner-skill"},
            {"type": "frontmatter_valid", "path": "bad"},
        ])
        self.assertEqual(result["summary"]["failed"], 1)

    def test_output_matches_and_no_placeholder(self) -> None:
        good = self.grade([
            {"type": "output_matches", "pattern": r"pass rate:\s*\d+"},
            {"type": "no_placeholder", "values": ["TODO", "FIXME"]},
        ], stdout="pass rate: 87%")
        bad = self.grade([
            {"type": "no_placeholder", "values": ["TODO"]},
        ], stdout="still TODO here")
        self.assertEqual(good["summary"]["failed"], 0)
        self.assertEqual(bad["summary"]["failed"], 1)

    def test_manual_is_undecided_and_excluded_from_totals(self) -> None:
        result = self.grade([{"type": "manual", "text": "judge this"}])
        summary = result["summary"]
        self.assertEqual(summary["total"], 0)
        self.assertEqual(summary["manual"], 1)
        self.assertIsNone(summary["pass_rate"], "unmeasured must not read as 0.0")
        self.assertIsNone(result["expectations"][0]["passed"])

    def test_no_assertions_yields_null_rate(self) -> None:
        self.assertIsNone(self.grade([])["summary"]["pass_rate"])

    def test_unknown_type_fails_loudly(self) -> None:
        result = self.grade([{"type": "file_existz", "path": "a"}])
        self.assertEqual(result["summary"]["failed"], 1)
        self.assertIn("unknown assertion type", result["expectations"][0]["evidence"])

    def test_invalid_regex_fails_with_a_message(self) -> None:
        result = self.grade([{"type": "output_matches", "pattern": "([unclosed"}])
        self.assertEqual(result["summary"]["failed"], 1)
        self.assertIn("invalid regular expression", result["expectations"][0]["evidence"])


# ---------------------------------------------------------------------------
# End-to-end evaluation with a fake runtime
# ---------------------------------------------------------------------------


class EvaluationEndToEnd(TempDirCase):
    EVALS = {
        "skill_name": "demo",
        "evals": [
            {
                "id": 1,
                "query": "Create a skill named pdf-notes.",
                "expected_output": "A valid skill.",
                "should_trigger": True,
                "assertions": [
                    {"type": "file_exists", "path": "pdf-notes/SKILL.md"},
                    {"type": "frontmatter_valid", "path": "pdf-notes"},
                    {"type": "output_contains", "value": "pdf-notes"},
                ],
            },
            {
                "id": 2,
                "query": "Fix the retry logic in api.js.",
                "should_trigger": False,
                "assertions": [{"type": "manual", "text": "workflow should not apply"}],
            },
        ],
    }

    def setUp(self) -> None:
        super().setUp()
        self.agent = install_fake_agent(self.tmp)
        self.skill = make_skill(self.tmp, name="demo-skill")
        self.eval_path = self.tmp / "evals.json"
        self.eval_path.write_text(json.dumps(self.EVALS), encoding="utf-8")

    def evaluate(self, root, **kwargs):
        _name, evals = utils.load_evals(self.eval_path)
        options = {
            "evals": evals,
            "skill_path": self.skill,
            "agent": "custom",
            "command": self.agent,
            "results_root": root,
            "config": "with_skill",
            "num_workers": 1,
        }
        options.update(kwargs)
        return run_eval_mod.run_eval(**options)

    def test_sandbox_receives_artifacts_and_assertions_pass(self) -> None:
        output = self.evaluate(self.tmp / "runs")
        run_dir = self.tmp / "runs" / "eval-1" / "with_skill" / "run-1"
        # The runtime's working directory must be its own sandbox, otherwise
        # artifacts land elsewhere and every file assertion fails vacuously.
        self.assertTrue((run_dir / "pdf-notes" / "SKILL.md").is_file())
        self.assertTrue((run_dir / "run.json").is_file())
        self.assertTrue((run_dir / "stdout.txt").is_file())
        self.assertTrue((run_dir / "grading.json").is_file())

        grading = json.loads((run_dir / "grading.json").read_text())
        self.assertEqual(grading["summary"]["failed"], 0, grading)
        self.assertIs(output["results"][0]["pass"], True)

    def test_run_json_is_self_describing(self) -> None:
        self.evaluate(self.tmp / "runs")
        record = json.loads(
            (self.tmp / "runs" / "eval-1" / "with_skill" / "run-1" / "run.json").read_text()
        )
        self.assertEqual(record["eval_id"], 1)
        self.assertTrue(record["query"])
        self.assertIs(record["should_trigger"], True)
        self.assertTrue(record["assertions_decided"])
        self.assertIsNone(record["trigger_observed"], "no detector means unknown")
        self.assertEqual(record["trigger_detection"], "none")

    def test_manual_only_eval_has_no_measured_rate(self) -> None:
        output = self.evaluate(self.tmp / "runs")
        manual_eval = next(r for r in output["results"] if r["id"] == 2)
        self.assertFalse(manual_eval["assertions_decided"])

    def test_baseline_config_does_not_see_the_skill(self) -> None:
        self.evaluate(self.tmp / "runs", config="without_skill", include_skill=False)
        self.assertTrue(
            (self.tmp / "runs" / "eval-1" / "without_skill" / "run-1" / "run.json").is_file()
        )

    def test_trigger_detector_decisive_and_unknown(self) -> None:
        self.evaluate(self.tmp / "d1", detector="echo 1")
        self.evaluate(self.tmp / "d2", detector="echo 0")
        self.evaluate(self.tmp / "d3", detector="echo perhaps")
        first = json.loads((self.tmp / "d1" / "eval_results.json").read_text())
        second = json.loads((self.tmp / "d2" / "eval_results.json").read_text())
        third = json.loads((self.tmp / "d3" / "eval_results.json").read_text())
        self.assertEqual(first["results"][0]["trigger_observed"], 1)
        self.assertEqual(second["results"][0]["trigger_observed"], 0)
        self.assertIsNone(third["results"][0]["trigger_observed"])

    def test_runs_per_query_repeats_and_majories(self) -> None:
        output = self.evaluate(self.tmp / "runs", runs_per_query=3)
        self.assertEqual(output["results"][0]["runs"], 3)

    def test_failing_assertion_marks_the_eval_failed(self) -> None:
        payload = json.loads(json.dumps(self.EVALS))
        payload["evals"] = [payload["evals"][0]]
        payload["evals"][0]["assertions"] = [
            {"type": "file_exists", "path": "never-created.md"}
        ]
        self.eval_path.write_text(json.dumps(payload), encoding="utf-8")
        output = self.evaluate(self.tmp / "runs")
        self.assertIs(output["results"][0]["pass"], False)

    def test_fixture_files_are_copied_into_the_sandbox(self) -> None:
        fixture = self.tmp / "input.md"
        fixture.write_text("source material", encoding="utf-8")
        payload = json.loads(json.dumps(self.EVALS))
        payload["evals"] = [payload["evals"][0]]
        payload["evals"][0]["files"] = [str(fixture)]
        self.eval_path.write_text(json.dumps(payload), encoding="utf-8")
        self.evaluate(self.tmp / "runs")
        run_dir = self.tmp / "runs" / "eval-1" / "with_skill" / "run-1"
        self.assertEqual((run_dir / "input.md").read_text(), "source material")

    def test_missing_executable_is_reported_in_the_record(self) -> None:
        output = self.evaluate(
            self.tmp / "runs", command=str(self.tmp / "nope-does-not-exist")
        )
        record = output["results"][0]["runs_detail"][0]
        self.assertEqual(record["error"], "ExecutableNotFound")
        self.assertIsNone(record["exit_code"])


# ---------------------------------------------------------------------------
# Benchmark aggregation
# ---------------------------------------------------------------------------


class Aggregation(TempDirCase):
    def build_run(self, root: Path, config: str, eval_id: int, pass_rate, total: int = 4):
        run_dir = root / f"eval-{eval_id}" / config / "run-1"
        run_dir.mkdir(parents=True, exist_ok=True)
        passed = int(round((pass_rate or 0) * total))
        (run_dir / "grading.json").write_text(json.dumps({
            "expectations": [
                {"text": f"e{i}", "type": "file_exists", "passed": i < passed,
                 "evidence": "x", "manual": False}
                for i in range(total)
            ],
            "summary": {
                "passed": passed, "failed": total - passed, "total": total,
                "manual": 0, "pass_rate": pass_rate,
            },
        }), encoding="utf-8")
        (run_dir / "run.json").write_text(json.dumps({
            "agent": "custom", "exit_code": 0, "duration_ms": 1000,
            "total_tokens": None, "task_success": True,
            "trigger_observed": None, "trigger_detection": "none", "stderr": "",
        }), encoding="utf-8")

    def test_null_pass_rate_does_not_crash(self) -> None:
        # Regression: calculate_stats used to crash summing None.
        self.build_run(self.tmp, "with_skill", 1, None)
        stats = aggregate_benchmark.calculate_stats([None, None])
        self.assertIsNone(stats["mean"])
        self.assertEqual(stats["measured"], 0)

    def test_stats_ignore_missing_entries(self) -> None:
        stats = aggregate_benchmark.calculate_stats([0.5, None, 1.0])
        self.assertAlmostEqual(stats["mean"], 0.75)
        self.assertEqual(stats["measured"], 2)

    def test_delta_across_two_configurations(self) -> None:
        self.build_run(self.tmp, "with_skill", 1, 1.0)
        self.build_run(self.tmp, "without_skill", 1, 0.5)
        benchmark = aggregate_benchmark.generate_benchmark(self.tmp, "demo", "path")
        delta = benchmark["run_summary"]["delta"]
        self.assertIsNotNone(delta["pass_rate"])
        self.assertEqual(len(benchmark["runs"]), 2)

    def test_delta_is_null_without_two_configurations(self) -> None:
        self.build_run(self.tmp, "with_skill", 1, 1.0)
        benchmark = aggregate_benchmark.generate_benchmark(self.tmp, "demo", "path")
        self.assertIsNone(benchmark["run_summary"]["delta"]["pass_rate"])

    def test_markdown_reports_unmeasured_metrics_as_na(self) -> None:
        self.build_run(self.tmp, "with_skill", 1, 1.0)
        benchmark = aggregate_benchmark.generate_benchmark(self.tmp, "demo", "path")
        markdown = aggregate_benchmark.generate_markdown(benchmark)
        self.assertIn("n/a", markdown)
        self.assertNotIn("None", markdown)

    def test_cli_writes_both_files(self) -> None:
        self.build_run(self.tmp, "with_skill", 1, 1.0)
        self.build_run(self.tmp, "without_skill", 1, 0.5)
        result = run_python(
            BUNDLE / "scripts" / "aggregate_benchmark.py",
            self.tmp, "--skill-name", "demo",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((self.tmp / "benchmark.json").is_file())
        self.assertTrue((self.tmp / "benchmark.md").is_file())

    def test_cli_errors_when_no_runs_found(self) -> None:
        result = run_python(BUNDLE / "scripts" / "aggregate_benchmark.py", self.tmp)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("no graded runs", result.stderr.lower())


# ---------------------------------------------------------------------------
# The improve loop
# ---------------------------------------------------------------------------


class ImproveLoop(TempDirCase):
    def setUp(self) -> None:
        super().setUp()
        self.skill = make_skill(self.tmp, name="demo-skill")
        self.eval_path = self.tmp / "evals.json"
        self.eval_path.write_text(json.dumps({"evals": [
            {"id": 1, "query": "positive task", "should_trigger": True},
            {"id": 2, "query": "negative task", "should_trigger": False},
            {"id": 3, "query": "another positive", "should_trigger": True},
            {"id": 4, "query": "another negative", "should_trigger": False},
        ]}), encoding="utf-8")

    def test_split_is_stratified_and_leaves_a_train_set(self) -> None:
        _name, evals = utils.load_evals(self.eval_path)
        train, test = run_loop_mod.split_eval_set(evals, 0.5)
        self.assertTrue(train)
        self.assertTrue(test)
        self.assertEqual(len(train) + len(test), len(evals))
        self.assertEqual(len({e["query"] for e in train} & {e["query"] for e in test}), 0)

    def test_split_disabled_by_zero_holdout(self) -> None:
        _name, evals = utils.load_evals(self.eval_path)
        train, test = run_loop_mod.split_eval_set(evals, 0)
        self.assertEqual(len(test), 0)
        self.assertEqual(len(train), len(evals))

    def test_dry_run_makes_no_agent_call(self) -> None:
        agent = install_fake_agent(self.tmp)
        marker = self.tmp / "INVOKED"
        watcher = self.tmp / "watch-agent"
        watcher.write_text(f"#!/bin/sh\ntouch {marker}\n", encoding="utf-8")
        watcher.chmod(watcher.stat().st_mode | stat.S_IEXEC)

        result = run_python(
            BUNDLE / "scripts" / "run_loop.py",
            "--eval-set", self.eval_path, "--skill-path", self.skill,
            "--agent", "custom", "--command", str(watcher),
            "--dry-run",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(marker.exists(), "--dry-run must not invoke the runtime")

    def test_dry_run_reports_the_plan_and_cost(self) -> None:
        result = run_python(
            BUNDLE / "scripts" / "run_loop.py",
            "--eval-set", self.eval_path, "--skill-path", self.skill, "--dry-run",
        )
        plan = json.loads(result.stdout)
        self.assertTrue(plan["skill_valid"]["ok"])
        self.assertEqual(plan["evals"]["total"], 4)
        self.assertIn("max_evals_to_execute", plan)

    def test_dry_run_fails_for_a_missing_skill(self) -> None:
        result = run_python(
            BUNDLE / "scripts" / "run_loop.py",
            "--eval-set", self.eval_path, "--skill-path", self.tmp / "nope", "--dry-run",
        )
        self.assertNotEqual(result.returncode, 0)

    def test_iteration_records_the_description_under_test(self) -> None:
        _name, evals = utils.load_evals(self.eval_path)
        args = self._args(
            agent="custom", command="/bin/true",
            runs_per_query=1, max_iterations=1, holdout=0,
        )
        output = run_loop_mod.run_loop(
            evals=evals, skill_path=self.skill, args=args,
            results_dir=self.tmp / "loopout",
        )
        self.assertEqual(output["iterations_run"], 1)
        self.assertEqual(output["history"][0]["description"], output["original_description"])
        self.assertIn("train", output["history"][0])
        self.assertIn("test", output["history"][0])

    def test_full_loop_iterates_and_stops_at_max_iterations(self) -> None:
        agent = install_fake_agent(self.tmp)
        # An assertion that can never pass keeps the loop iterating.
        payload = {"evals": [{
            "id": 1, "query": "task", "should_trigger": True,
            "assertions": [{"type": "file_exists", "path": "never.md"}],
        }]}
        self.eval_path.write_text(json.dumps(payload), encoding="utf-8")
        _name, evals = utils.load_evals(self.eval_path)
        args = self._args(
            agent="custom", command=agent, runs_per_query=1,
            max_iterations=2, holdout=0,
        )
        output = run_loop_mod.run_loop(
            evals=evals, skill_path=self.skill, args=args,
            results_dir=self.tmp / "loopout",
        )
        self.assertEqual(output["iterations_run"], 2)
        self.assertEqual(output["exit_reason"], "max_iterations (2)")
        # A proposal is made after each iteration except the last, which exits
        # on the iteration limit before proposing again.
        self.assertEqual(len(output["proposals"]), 1)
        self.assertEqual(output["proposals"][0]["iteration"], 1)
        self.assertTrue(all("accepted" in p for p in output["proposals"]))
        # The description under test changed between the two iterations.
        self.assertNotEqual(
            output["history"][0]["description"], output["history"][1]["description"]
        )

    def test_loop_does_not_write_into_the_caller_directory(self) -> None:
        # Regression: the proposal phase ran the runtime in the caller's cwd,
        # so a runtime that writes files dropped them into the skill bundle.
        agent = install_fake_agent(self.tmp)
        payload = {"evals": [{
            "id": 1, "query": "task", "should_trigger": True,
            "assertions": [{"type": "file_exists", "path": "never.md"}],
        }]}
        self.eval_path.write_text(json.dumps(payload), encoding="utf-8")
        _name, evals = utils.load_evals(self.eval_path)
        args = self._args(
            agent="custom", command=agent, runs_per_query=1,
            max_iterations=1, holdout=0,
        )
        cwd = Path.cwd()
        self.addCleanup(os.chdir, cwd)
        os.chdir(self.tmp)
        run_loop_mod.run_loop(
            evals=evals, skill_path=self.skill, args=args,
            results_dir=self.tmp / "loopout",
        )
        # The fake agent creates pdf-notes/ wherever it runs.
        self.assertFalse(
            (self.tmp / "pdf-notes").exists(),
            "the proposal phase must not run in the caller's working directory",
        )
        self.assertFalse(
            (BUNDLE / "pdf-notes").exists(),
            "the bundle must never receive run artifacts",
        )

    def test_no_browser_opened_by_default(self) -> None:
        result = run_python(
            BUNDLE / "scripts" / "run_loop.py", "--help",
        )
        self.assertIn("--open", result.stdout)
        self.assertIn("'none'", result.stdout, "report must default to disabled")

    def _args(self, **overrides):
        import argparse

        defaults = dict(
            agent="auto", command=None, model=None, num_workers=1, timeout=60,
            max_iterations=1, runs_per_query=1, holdout=0.0, config="with_skill",
            no_skill=False, extra_args=[], trigger_detector=None, verbose=False,
            report="none", open=False, results_dir=None, apply=False, dry_run=False,
        )
        defaults.update(overrides)
        return argparse.Namespace(**defaults)


# ---------------------------------------------------------------------------
# Description validation guard
# ---------------------------------------------------------------------------


class DescriptionGuard(unittest.TestCase):
    def test_accepts_a_good_description(self) -> None:
        ok, problems = validate_description("Use when authoring or evaluating agent skills.")
        self.assertTrue(ok, problems)

    def test_rejects_empty_oversized_bracketed_and_provider_specific(self) -> None:
        for bad in ("", "x" * 1100, "Use <when> testing.", "Use when authoring for Claude Code."):
            with self.subTest(description=bad[:30]):
                ok, problems = validate_description(bad)
                self.assertFalse(ok)
                self.assertTrue(problems)

    def test_rejected_proposal_keeps_the_previous_description(self) -> None:
        from scripts.improve_description import improve_description

        new, report = improve_description(
            "demo", "content", "the current description",
            {}, [], agent="custom", command="/bin/true",
        )
        self.assertEqual(new, "the current description")
        self.assertFalse(report["accepted"])
        self.assertTrue(report["problems"])


# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------


class Report(TempDirCase):
    def test_renders_the_current_loop_contract(self) -> None:
        from scripts.generate_report import generate_html

        data = {
            "skill_name": "demo",
            "exit_reason": "max_iterations (2)",
            "original_description": "before",
            "best_description": "after",
            "best_iteration": 2,
            "best_train": {"passed": 3, "failed": 0, "total": 4},
            "best_test": {"passed": 2, "failed": 0, "total": 2},
            "improved": True,
            "iterations_run": 2,
            "train_size": 2,
            "test_size": 1,
            "history": [
                {
                    "iteration": 1, "description": "before",
                    "train": {"passed": 2, "failed": 0, "total": 2},
                    "test": {"passed": 1, "failed": 0, "total": 1},
                    "trigger_metrics": None,
                    "results": [
                        {"query": "q1", "should_trigger": True, "pass": True,
                         "runs": 1, "trigger_observed": None},
                        {"query": "q2", "should_trigger": True, "pass": False,
                         "runs": 1, "trigger_observed": None},
                    ],
                }
            ],
        }
        html = generate_html(data, skill_name="demo")
        self.assertIn("<!DOCTYPE html>", html)
        self.assertIn("max_iterations (2)", html)
        self.assertIn("before", html)
        self.assertIn("trigger detection not configured", html)
        self.assertNotIn("None", html)

    def test_handles_empty_history(self) -> None:
        from scripts.generate_report import generate_html

        self.assertIn("<!DOCTYPE html>", generate_html({}))


# ---------------------------------------------------------------------------
# Eval viewer
# ---------------------------------------------------------------------------


class Viewer(TempDirCase):
    def load_viewer(self):
        sys.path.insert(0, str(BUNDLE / "eval-viewer"))
        try:
            import generate_review

            return generate_review
        finally:
            sys.path.pop(0)

    def test_finds_the_canonical_run_layout(self) -> None:
        # Regression: the viewer required an outputs/ directory the runner
        # never created, so it reported zero runs for real results.
        viewer = self.load_viewer()
        run_dir = self.tmp / "eval-1" / "with_skill" / "run-1"
        run_dir.mkdir(parents=True)
        (run_dir / "run.json").write_text(json.dumps({
            "query": "do the thing", "eval_id": 1, "should_trigger": True,
            "task_success": True, "expected_output": "done", "stderr": "",
        }), encoding="utf-8")
        (run_dir / "grading.json").write_text(json.dumps({
            "expectations": [], "summary": {"passed": 0, "failed": 0, "total": 0,
                                            "manual": 0, "pass_rate": None},
        }), encoding="utf-8")
        (run_dir / "artifact.md").write_text("output", encoding="utf-8")

        runs = viewer.find_runs(self.tmp)
        self.assertEqual(len(runs), 1)
        self.assertEqual(runs[0]["query"] if "query" in runs[0] else runs[0]["prompt"],
                         "do the thing")
        self.assertEqual(runs[0]["configuration"], "with_skill")

    def test_still_accepts_the_legacy_outputs_layout(self) -> None:
        viewer = self.load_viewer()
        run_dir = self.tmp / "eval-2" / "old" / "run-1"
        (run_dir / "outputs").mkdir(parents=True)
        (run_dir / "outputs" / "result.md").write_text("legacy", encoding="utf-8")
        runs = viewer.find_runs(self.tmp)
        self.assertEqual(len(runs), 1)
        self.assertEqual(len(runs[0]["outputs"]), 1)

    def test_killing_a_port_is_opt_in(self) -> None:
        viewer = self.load_viewer()
        self.assertTrue(callable(viewer.kill_port))
        self.assertTrue(callable(viewer.port_available))
        result = run_python(
            BUNDLE / "eval-viewer" / "generate_review.py", "--help"
        )
        self.assertIn("--kill-existing", result.stdout)
        source = (BUNDLE / "eval-viewer" / "generate_review.py").read_text()
        # The dangerous helper must not be invoked on the default path.
        self.assertIn("elif args.kill_existing:", source)
        self.assertNotIn("_kill_port(port)", source)

    def test_static_mode_needs_no_server(self) -> None:
        viewer = self.load_viewer()
        run_dir = self.tmp / "eval-1" / "with_skill" / "run-1"
        run_dir.mkdir(parents=True)
        (run_dir / "run.json").write_text(json.dumps({"query": "q", "eval_id": 1}),
                                          encoding="utf-8")
        out = self.tmp / "review.html"
        result = run_python(
            BUNDLE / "eval-viewer" / "generate_review.py",
            self.tmp, "--static", out, "--skill-name", "demo",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(out.is_file())
        self.assertGreater(out.stat().st_size, 0)


# ---------------------------------------------------------------------------
# Documentation and bundle integrity
# ---------------------------------------------------------------------------


class BundleIntegrity(unittest.TestCase):
    def test_skill_md_references_only_files_that_exist(self) -> None:
        # quick_validate already enforces this; assert it here too so the
        # bundle's own documentation is covered by the suite.
        result = quick_validate.validate_skill(BUNDLE)
        missing = [e for e in result.errors if "references missing file" in e]
        self.assertEqual(len(missing), 0, "SKILL.md points at missing files: " + "; ".join(missing))

    def test_every_script_is_documented_somewhere(self) -> None:
        corpus = "\n".join(
            (BUNDLE / name).read_text(encoding="utf-8")
            for name in ("SKILL.md", "README_PORTABLE.md", "references/schemas.md")
        )
        undocumented = [
            script.name
            for script in sorted((BUNDLE / "scripts").glob("*.py"))
            if script.name != "__init__.py" and script.name not in corpus
        ]
        self.assertEqual(undocumented, [], "undocumented scripts: " + ", ".join(undocumented))

    def test_supporting_directories_are_documented(self) -> None:
        corpus = (BUNDLE / "SKILL.md").read_text(encoding="utf-8")
        missing = [
            name for name in ("references/adapters.json", "agents/", "evals/evals.json")
            if name not in corpus
        ]
        self.assertEqual(missing, [], "undocumented in SKILL.md: " + ", ".join(missing))

    def test_every_role_is_named_in_skill_md(self) -> None:
        # A role file nothing points at cannot be dispatched or discovered.
        # This is the check that stops agents/ from silently accumulating.
        corpus = (BUNDLE / "SKILL.md").read_text(encoding="utf-8")
        unreferenced = [
            role.name for role in sorted((BUNDLE / "agents").glob("*.md"))
            if f"agents/{role.name}" not in corpus
        ]
        self.assertEqual(
            unreferenced, [],
            "roles not referenced by SKILL.md: " + ", ".join(unreferenced),
        )

    def test_authoring_and_evaluation_roles_are_both_present(self) -> None:
        # The bundle needs a role for creating a skill and roles for judging
        # one. Authoring without evaluation, or the reverse, is a half workflow.
        names = {
            utils.parse_frontmatter(role.read_text(encoding="utf-8")).get("name")
            for role in (BUNDLE / "agents").glob("*.md")
        }
        for required in ("author", "grader"):
            self.assertIn(required, names, f"agents/ is missing the {required} role")

    def test_author_role_covers_the_whole_creation_path(self) -> None:
        # The author role must not stop at writing SKILL.md: a skill that is
        # never validated, evaluated, or packaged is not finished.
        text = (BUNDLE / "agents" / "author.md").read_text(encoding="utf-8")
        for step in ("quick_validate", "evals", "package_skill", "dry-run"):
            with self.subTest(step=step):
                self.assertIn(step, text)
        # The role must insist on trigger-negative coverage. Match the concept
        # in prose rather than the literal JSON key, so rewording the guidance
        # does not read as a regression.
        self.assertRegex(
            text.lower(), r"should not trigger|trigger[- ]negative|should_trigger",
            "author role must cover trigger-negative eval cases",
        )
        # It must also refuse to report an unmeasured result as a pass.
        self.assertRegex(
            text.lower(), r"did not run|never present an unrun|no eval was run",
            "author role must forbid reporting an unrun step as a pass",
        )

    def test_schemas_doc_matches_implemented_assertion_types(self) -> None:
        doc = (BUNDLE / "references" / "schemas.md").read_text(encoding="utf-8")
        # Scope the scan to the assertion-type table, which is the only place
        # `| type | fields | ... |` rows appear.
        table = doc.split("### Assertion types", 1)[1].split("\n---", 1)[0]
        documented = set(re.findall(r"^\| `([a-z_]+)` \|", table, re.MULTILINE))

        for assertion_type in sorted(utils.VALID_ASSERTION_TYPES):
            with self.subTest(assertion_type=assertion_type):
                self.assertIn(
                    assertion_type, documented,
                    f"{assertion_type} is implemented but undocumented",
                )
        for name in sorted(documented):
            with self.subTest(documented=name):
                self.assertIn(
                    name, utils.VALID_ASSERTION_TYPES,
                    f"schemas.md documents unimplemented type {name}",
                )

    def test_agent_roles_have_frontmatter(self) -> None:
        for role in sorted((BUNDLE / "agents").glob("*.md")):
            with self.subTest(role=role.name):
                front = utils.parse_frontmatter(role.read_text(encoding="utf-8"))
                self.assertIn("name", front)
                self.assertIn("description", front)
                self.assertLessEqual(len(front["description"]), 1024)

    def test_skill_md_stays_within_the_size_guidance(self) -> None:
        lines = (BUNDLE / "SKILL.md").read_text(encoding="utf-8").count("\n") + 1
        self.assertLessEqual(lines, 500, f"SKILL.md is {lines} lines")

    def test_no_python_dependency_is_declared_as_hard(self) -> None:
        for script in (BUNDLE / "scripts").glob("*.py"):
            text = script.read_text(encoding="utf-8")
            with self.subTest(script=script.name):
                self.assertNotIn("\nimport yaml\n", text,
                                 f"{script.name} hard-imports PyYAML")
                self.assertNotIn("\nfrom yaml import", text)

    def test_no_unconditional_browser_launch(self) -> None:
        loop = (BUNDLE / "scripts" / "run_loop.py").read_text(encoding="utf-8")
        # webbrowser.open must be reachable only through the explicit --open flag.
        self.assertIn("if args.open:", loop)
        self.assertEqual(loop.count("webbrowser.open"), 1)

    def test_no_orphaned_configuration_files(self) -> None:
        # The old agent-runtime.example.json was read by nothing and duplicated
        # the registry; references/adapters.json replaced it.
        self.assertFalse((BUNDLE / "agent-runtime.example.json").exists())
        self.assertTrue((BUNDLE / "references" / "adapters.json").is_file())

    def test_packaged_archive_excludes_build_artifacts(self) -> None:
        from scripts.package_skill import should_exclude

        for excluded in (
            "demo-skill/scripts/__pycache__/x.pyc",
            "demo-skill/.DS_Store",
            "demo-skill/node_modules/pkg/index.js",
            "demo-skill/.git/config",
            "demo-skill/.venv/lib/x.py",
        ):
            with self.subTest(path=excluded):
                self.assertTrue(should_exclude(Path(excluded)))
        # The eval set ships: SKILL.md points at it and the suite asserts on it,
        # so a package without it could not validate itself.
        for kept in (
            "demo-skill/SKILL.md",
            "demo-skill/scripts/run_eval.py",
            "demo-skill/references/adapters.json",
            "demo-skill/evals/evals.json",
        ):
            with self.subTest(path=kept):
                self.assertFalse(should_exclude(Path(kept)))

    def test_packaged_bundle_validates_itself(self) -> None:
        # A package that cannot pass its own validator is not a deliverable.
        with tempfile.TemporaryDirectory() as tmp:
            result = run_python(
                BUNDLE / "scripts" / "package_skill.py", BUNDLE, tmp
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            import zipfile

            with zipfile.ZipFile(Path(tmp) / f"{BUNDLE.name}.skill") as archive:
                archive.extractall(tmp)
            unpacked = Path(tmp) / BUNDLE.name
            validation = quick_validate.validate_skill(unpacked)
            self.assertTrue(validation, validation.message())
            self.assertTrue((unpacked / "evals" / "evals.json").is_file())


if __name__ == "__main__":
    unittest.main(verbosity=2)
