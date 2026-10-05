"""The support guide and onboarding say only what the code does (build step 6.3).

A guide that promises a command, a button, a folder, or a behavior the code
does not have is worse than no guide. These tests hold the guide to the
code: every command it names exists with the options it shows, every label
it quotes is on a screen, the folders are the ones the app uses, and the
privacy screen's limits are stated, never softened (validation report,
correction 9).
"""

import os
import re
import unittest
from pathlib import Path
from unittest import mock

import _bootstrap  # noqa: F401

from nurse_manager import app as local_app
from nurse_manager import cli, resources

ROOT = Path(__file__).resolve().parents[1]
GUIDE = ROOT / "docs" / "04-support-guide.md"
TEXT = GUIDE.read_text(encoding="utf-8")
RENDERER = "\n".join(p.read_text(encoding="utf-8") for p in sorted((ROOT / "renderer").glob("*.*")))
# Anything that calls content free of patient information, or certifies it.
OVERCLAIM = re.compile(r"phi[- ]free|free of phi|de-identified|hipaa[- ]compliant|certified clean",
                       re.IGNORECASE)


def _commands(text: str) -> list[list[str]]:
    """Every ``python3 -m nurse_manager ...`` line in the guide's code blocks."""
    lines = []
    for block in re.findall(r"```bash\n(.*?)```", text, re.S):
        for line in block.splitlines():
            if line.startswith("python3 -m nurse_manager "):
                lines.append(re.findall(r'"[^"]*"|\S+', line)[3:])
    return lines


class GuideCoversTheStepTests(unittest.TestCase):
    def test_every_topic_the_step_asks_for_has_a_section(self):
        headings = re.findall(r"^## \d+\. (.+)$", TEXT, re.M)
        for topic in ("Install and launch", "Back up", "Restore", "After a crash",
                      "Stopping assistants", "JEV, the optional classifier",
                      "How packs are reviewed", "Pilot feedback", "Where to get help"):
            with self.subTest(topic=topic):
                self.assertIn(topic, headings)

    def test_it_says_plainly_that_there_is_no_build_for_managers_yet(self):
        self.assertIn("there is no build for managers yet", TEXT)
        self.assertIn("unsigned test builds", TEXT)


class CommandsExistTests(unittest.TestCase):
    def test_every_command_it_shows_exists_with_the_options_it_shows(self):
        shown = _commands(TEXT)
        self.assertEqual(sorted({argv[0] for argv in shown}), ["backup", "reconcile", "restore"])
        parser = cli.build_parser()
        for argv in shown:
            with self.subTest(command=argv[0]):
                self.assertIn(argv[0], cli.commands())
                parsed = parser.parse_args([a.strip('"') for a in argv])
                self.assertEqual(parsed.command, argv[0])

    def test_every_command_and_option_named_in_the_text_exists(self):
        for name in re.findall(
                r"`(pilot-feedback[a-z-]*|classifier[a-z-]*|reconcile|export|approve|run|backup|restore|"
                r"project-add|task-[a-z-]+|decision-add|priorities-set)\b", TEXT):
            with self.subTest(command=name):
                self.assertIn(name, cli.commands())
        options = {o for a in cli.build_parser()._subparsers._group_actions[0].choices.values()
                   for o in a._option_string_actions}
        for option in set(re.findall(r"(--[a-z][a-z-]+)", TEXT)):
            with self.subTest(option=option):
                self.assertIn(option, options)

    def test_the_app_itself_cannot_export_backup_restore_or_reconcile(self):
        # The guide says these need the command surface: the screens cannot reach them.
        for command in ("export", "approve", "run", "backup", "restore", "reconcile",
                        "classifier-action", "classifier-acknowledge"):
            with self.subTest(command=command):
                self.assertNotIn(command, local_app.WRITE_COMMANDS)


class WhatItQuotesIsOnScreenTests(unittest.TestCase):
    def test_every_label_it_quotes_is_on_a_screen(self):
        for label in ("Explore the sample workspace", "Start your own workspace", "Quit Nurse AI OS",
                      "Nurse AI OS has stopped", "Assistants at work", "Stop all assistants",
                      "Stop assistants", "Let assistants work again", "AI assistance",
                      "Disconnect the AI model", "Help and feedback", "Preview what will be shared",
                      "Save as a file", "JEV classifier", "Connect JEV", "Save jobs",
                      "Refusal check", "Routing", "Attention order", "Action review",
                      "Where does this belong?", "Suggest an order with JEV",
                      "Show my usual order", "Disconnect JEV"):
            with self.subTest(label=label):
                self.assertIn(label, RENDERER)
        self.assertIn('"This page is not connected to Nurse AI OS. Reopen the app."',
                      (ROOT / "src" / "nurse_manager" / "app.py").read_text(encoding="utf-8"))

    def test_the_idle_stop_it_states_is_the_apps(self):
        self.assertEqual(local_app.DEFAULT_IDLE_TIMEOUT, 15 * 60)
        self.assertIn("after 15 minutes", TEXT)

    def test_the_files_it_names_are_the_apps(self):
        for name in (local_app.LOCK_NAME, local_app.INSTANCE_NAME, "workspace.sqlite",
                     "exports/", "backups/"):
            with self.subTest(name=name):
                self.assertIn(f"`{name}`", TEXT)

    def test_the_data_folders_it_lists_are_where_the_app_keeps_records(self):
        home = Path("/home/manager")
        cases = (
            ("win32", {"LOCALAPPDATA": r"C:\Users\m\AppData\Local"}, "`%LOCALAPPDATA%\\Nurse AI OS`",
             Path(r"C:\Users\m\AppData\Local") / "Nurse AI OS"),
            ("darwin", {}, "`~/Library/Application Support/Nurse AI OS`",
             home / "Library" / "Application Support" / "Nurse AI OS"),
            ("linux", {}, "`~/.local/share/nurse-ai-os`", home / ".local" / "share" / "nurse-ai-os"),
        )
        for platform, env, stated, expected in cases:
            with self.subTest(platform=platform):
                self.assertIn(stated, TEXT)
                clean = {k: v for k, v in os.environ.items()
                         if k not in ("NURSE_AI_OS_HOME", "XDG_DATA_HOME", "LOCALAPPDATA")}
                with mock.patch.object(resources.sys, "platform", platform), \
                        mock.patch.dict(os.environ, {**clean, **env}, clear=True), \
                        mock.patch.object(resources.Path, "home", return_value=home):
                    self.assertEqual(resources.user_data_dir(), expected)

    def test_every_relative_link_resolves(self):
        for target in re.findall(r"\]\(([^)#]+)\)", TEXT):
            if "://" in target:
                continue
            with self.subTest(link=target):
                self.assertTrue((GUIDE.parent / target).exists(), target)


class PrivacyLimitsAreStatedTests(unittest.TestCase):
    def test_the_guide_onboarding_and_readme_say_names_are_not_detected(self):
        self.assertIn("The privacy screen does not detect names.", TEXT)
        self.assertIn("It does not detect people’s names.", RENDERER)
        self.assertIn("does not detect names", (ROOT / "README.md").read_text(encoding="utf-8"))

    def test_nothing_calls_content_free_of_patient_information(self):
        for path in [GUIDE, ROOT / "README.md", *sorted((ROOT / "renderer").glob("*.*")),
                     ROOT / "src" / "nurse_manager" / "pilot.py"]:
            with self.subTest(path=path.name):
                self.assertIsNone(OVERCLAIM.search(path.read_text(encoding="utf-8")))


if __name__ == "__main__":
    unittest.main()
