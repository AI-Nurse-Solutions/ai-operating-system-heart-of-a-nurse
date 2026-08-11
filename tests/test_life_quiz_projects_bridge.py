"""The Life & Projects Quiz must emit something the installer accepts.

life-quiz.html is a producer: it writes naio-projects.json. naio-os/scripts/
import-projects.py is the consumer, and naio-os/schema/naio-projects.schema.json
is the contract between them. Before this file, nothing tested the pair. The
installer's own self-test used a hand-written sample_projects() fixture, and the
quiz had no test coverage at all — so the two could drift apart silently and
both keep reporting green.

That is not hypothetical. It is exactly what happened to the other bridge in
this repo: soul-quiz.html moved to schema_version 2.0.0 while Mission Control's
copy of the soul schema still pinned ^1., and taking the quiz and importing the
download was refused end to end while every suite stayed green. Fixtures cannot
catch that. Only running the real producer can.

So this runs the quiz's own buildProjectsJson() — the actual function behind the
download button, extracted from the shipped page, not a reimplementation — and
puts the result through the real schema and the real importer.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
QUIZ = ROOT / "life-quiz.html"
SCHEMA = ROOT / "naio-os" / "schema" / "naio-projects.schema.json"
IMPORTER = ROOT / "naio-os" / "scripts" / "import-projects.py"
SOUL_MODEL = ROOT / "soul-quiz" / "soul-quiz-model.mjs"
SOUL_TESTS = ROOT / "tests" / "test_soul_quiz_constellation.py"
INSTALLER = ROOT / "naio-os" / "install.sh"

# A minimal DOM. The quiz touches document in seven places, all for rendering;
# none of them matter to the export path, and stubbing is what lets the real
# function run outside a browser without being rewritten for the test.
DOM_STUB = """
const _node = {innerHTML:'', value:'', checked:false, dataset:{},
               querySelector:()=>null, querySelectorAll:()=>[],
               addEventListener:()=>{}};
globalThis.document = {getElementById:()=>_node, querySelector:()=>_node,
                       querySelectorAll:()=>[], createElement:()=>_node,
                       body:_node};
globalThis.window = {addEventListener:()=>{}};
globalThis.URL = {createObjectURL:()=>'blob:', revokeObjectURL:()=>{}};
globalThis.Blob = function(){};
"""

# Fill it in the way a nurse would: a name, several active domains, and details
# on one of them.
DRIVER = """
state.data.name = 'Jordan Rivera';
const picks = ALL_DOMAINS.slice(0, 4);
picks.forEach(d => { state.data.active[d.id] = true; });
state.data.details[picks[0].id] = {
  projName: 'Night-shift recovery',
  help: 'Sleep and recovery after nights',
  goal: 'Sleep 7h on 5 of 7 days',
  tier: 'green'
};
console.log(JSON.stringify(buildProjectsJson()));
"""


def quiz_export() -> dict:
    """Run the shipped page's own export function and return what it emits."""
    scripts = re.findall(r"<script[^>]*>(.*?)</script>",
                         QUIZ.read_text(encoding="utf-8"), re.DOTALL)
    body = max(scripts, key=len)
    body = re.sub(r"\nrender\(\);\s*$", "\n", body)   # no rendering into a stub

    # The probe goes in a temp dir, never in the repo. A test that leaves an
    # untracked file behind can fail CI's clean-tree gate just by running.
    workdir = Path(tempfile.mkdtemp(prefix="life-quiz-probe-"))
    try:
        probe = workdir / "probe.mjs"
        probe.write_text(DOM_STUB + body + DRIVER, encoding="utf-8")
        run = subprocess.run(["node", str(probe)], capture_output=True,
                             text=True, cwd=str(workdir))
        if run.returncode != 0:
            raise AssertionError(f"life-quiz export failed to run:\n{run.stderr[:2000]}")
        return json.loads(run.stdout)
    finally:
        shutil.rmtree(workdir, ignore_errors=True)


@unittest.skipUnless(shutil.which("node"), "node is required to run the quiz")
class LifeQuizProjectsBridgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        for path in (QUIZ, SCHEMA, IMPORTER):
            if not path.is_file():
                raise unittest.SkipTest(f"missing {path.relative_to(ROOT)}")
        cls.emitted = quiz_export()

    def test_the_quiz_actually_produced_projects(self) -> None:
        # Guard the guard. An export of zero projects would satisfy every
        # assertion below without exercising anything.
        self.assertGreater(self.emitted.get("project_count", 0), 0)
        self.assertEqual(self.emitted["project_count"],
                         len(self.emitted.get("projects", [])))

    def test_the_export_matches_the_installer_contract(self) -> None:
        try:
            from jsonschema import Draft7Validator, FormatChecker
        except ImportError as exc:  # pragma: no cover
            self.skipTest(f"jsonschema unavailable: {exc}")
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        errors = list(Draft7Validator(
            schema, format_checker=FormatChecker()).iter_errors(self.emitted))
        self.assertEqual(
            errors, [],
            "life-quiz.html emits something naio-projects.schema.json rejects:\n"
            + "\n".join(f"  {list(e.path)}: {e.message}" for e in errors),
        )

    def test_the_real_importer_accepts_the_real_export(self) -> None:
        # The schema is the contract, but the importer is what a nurse runs. It
        # enforces things the schema does not — path containment, tier/gate
        # agreement, a PHI screen — so check the program, not just the shape.
        workdir = Path(tempfile.mkdtemp(prefix="life-quiz-import-"))
        try:
            payload = workdir / "naio-projects.json"
            payload.write_text(json.dumps(self.emitted), encoding="utf-8")
            run = subprocess.run(
                ["python3", str(IMPORTER), str(payload)],
                capture_output=True, text=True, cwd=str(IMPORTER.parent.parent))
        finally:
            shutil.rmtree(workdir, ignore_errors=True)
        self.assertEqual(run.returncode, 0,
                         f"importer refused the quiz's own export:\n{run.stdout[-2000:]}")
        self.assertIn("VALID", run.stdout)
        self.assertNotIn("REFUSED", run.stdout)

    def test_the_installer_accepts_both_quizzes_together(self) -> None:
        # The Door 2 path is: take both quizzes, hand both downloads to
        # install.sh. Each importer is covered on its own, but the installer is
        # the thing a nurse actually runs, and naio-os's own self-test feeds it
        # a hand-written 1.0.0 soul — never the 2.0.0 the live quiz emits. This
        # walks the whole path with both real exports. ~4s; worth it for the
        # one command that ties the two bridges together.
        if not (INSTALLER.is_file() and SOUL_MODEL.is_file() and SOUL_TESTS.is_file()):
            self.skipTest("installer or soul-quiz not present")
        state = re.search(
            r"def representative_state_js\(\).*?return\s+(?:f?\"\"\"|r?\"\"\")(.*?)\"\"\"",
            SOUL_TESTS.read_text(encoding="utf-8"), re.DOTALL)
        if not state:
            self.skipTest("could not read the soul quiz's representative state")

        workdir = Path(tempfile.mkdtemp(prefix="naio-installer-"))
        try:
            probe = workdir / "soul.mjs"
            probe.write_text(
                "import {createInitialState,buildOsConfig} from "
                f"'{SOUL_MODEL.resolve().as_uri()}';\n" + state.group(1) +
                "\nconsole.log(JSON.stringify(buildOsConfig(s,"
                "'2026-07-20T00:00:00.000Z')));\n", encoding="utf-8")
            gen = subprocess.run(["node", str(probe)], capture_output=True,
                                 text=True, cwd=str(workdir))
            self.assertEqual(gen.returncode, 0, gen.stderr[:1000])
            soul = json.loads(gen.stdout)
            self.assertTrue(str(soul.get("schema_version", "")).startswith("2."),
                            f"expected a 2.x soul, got {soul.get('schema_version')}")

            soul_path = workdir / "naio-soul.json"
            proj_path = workdir / "naio-projects.json"
            soul_path.write_text(json.dumps(soul), encoding="utf-8")
            proj_path.write_text(json.dumps(self.emitted), encoding="utf-8")

            run = subprocess.run(
                ["bash", str(INSTALLER), "--dry-run",
                 "--soul", str(soul_path), "--projects", str(proj_path)],
                capture_output=True, text=True, cwd=str(INSTALLER.parent))
        finally:
            shutil.rmtree(workdir, ignore_errors=True)

        self.assertEqual(
            run.returncode, 0,
            "install.sh refused the exports both quizzes actually produce:\n"
            + (run.stdout + run.stderr)[-2500:])
        self.assertIn("Nothing written", run.stdout + run.stderr)

    def test_project_paths_stay_where_the_importer_requires(self) -> None:
        # import-projects.py refuses any file_path whose first segment is not
        # 04-Projects, and refuses traversal. The quiz builds these strings
        # itself, so the two have to agree on the prefix.
        for project in self.emitted["projects"]:
            path = project["file_path"]
            self.assertTrue(path.startswith("04-Projects/"), path)
            self.assertNotIn("..", path)
            self.assertTrue(path.endswith(".md"), path)


if __name__ == "__main__":
    unittest.main()
