# Copyright 2026 Robert Domondon
# SPDX-License-Identifier: Apache-2.0

"""Keep host dependencies out of domain code and writes out of read requests."""

import ast
import unittest
from pathlib import Path

import _bootstrap  # noqa: F401

from nurse_manager import app, cli, http_transport

SOURCE = Path(__file__).resolve().parents[1] / "src" / "nurse_manager"


class ArchitectureTests(unittest.TestCase):
    def test_domain_modules_do_not_depend_on_transport_or_command_parsing(self):
        adapters = {"app", "devhost", "http_transport", "cli", "__main__"}
        for path in SOURCE.glob("*.py"):
            if path.stem in adapters:
                continue
            for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
                imports = set()
                if isinstance(node, ast.ImportFrom) and node.level == 1:
                    imports = ({node.module.split(".")[0]} if node.module else
                               {alias.name for alias in node.names})
                elif isinstance(node, ast.ImportFrom) and node.module:
                    if node.module == "nurse_manager":
                        imports = {alias.name for alias in node.names}
                    elif node.module.startswith("nurse_manager."):
                        imports = {node.module.split(".")[1]}
                elif isinstance(node, ast.Import):
                    imports = {alias.name.split(".")[1] for alias in node.names
                               if alias.name.startswith("nurse_manager.")}
                if imports:
                    with self.subTest(module=path.stem, line=node.lineno):
                        self.assertFalse(imports & adapters, imports & adapters)

    def test_production_app_does_not_load_development_host(self):
        tree = ast.parse(Path(app.__file__).read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                self.assertNotIn(node.module, ("devhost", "nurse_manager.devhost"))
                if node.module in (None, "nurse_manager"):
                    self.assertNotIn("devhost", {alias.name for alias in node.names})
            if isinstance(node, ast.Import):
                self.assertNotIn("nurse_manager.devhost", {alias.name for alias in node.names})

    def test_read_translation_refuses_every_non_read_cli_command(self):
        parser = cli.build_parser()
        subcommands = next(action.choices for action in parser._actions
                           if getattr(action, "choices", None))
        for command in {*subcommands, "unknown"} - set(http_transport.READ_ONLY_COMMANDS):
            with self.subTest(command=command):
                result = http_transport.read_argv(command, Path("unused"), {}, "2026-10-03")
                self.assertEqual(result, "Unknown or non-read-only command")

    def test_browser_read_and_write_capabilities_are_disjoint(self):
        self.assertFalse(set(http_transport.READ_ONLY_COMMANDS) & set(app.WRITE_COMMANDS))
