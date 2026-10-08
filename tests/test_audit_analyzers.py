"""Regression tests for run_audit.py scanner and analyzer bugs found in the audits."""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from test_audit_coverage_xml import run_audit


class AuditFixture(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name) / "repo"
        self.root.mkdir()

    def add(self, rel: str, text: str = "") -> None:
        path = self.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def scan(self):
        return run_audit.RepoScanner().scan(self.root)


class TestImportCycles(AuditFixture):
    def cycles(self):
        return run_audit.ArchitectureAnalyzer()._find_python_import_cycles(self.scan())

    def test_plain_import_of_stdlib_name_is_not_a_cycle(self) -> None:
        self.add("pkg/__init__.py")
        self.add("pkg/zzz_os.py", "from pkg import repos\n")
        self.add("pkg/repos.py", "import os\n")
        self.assertEqual(self.cycles(), [])

    def test_from_package_import_submodule_cycle_is_found(self) -> None:
        self.add("pkg/__init__.py")
        self.add("pkg/a.py", "from pkg import b\n")
        self.add("pkg/b.py", "from pkg import a\n")
        self.assertTrue(self.cycles())

    def test_relative_import_cycle_is_found(self) -> None:
        self.add("pkg/__init__.py")
        self.add("pkg/a.py", "from . import b\n")
        self.add("pkg/b.py", "from .a import thing\n")
        self.assertTrue(self.cycles())


class TestScanner(AuditFixture):
    def test_symlinked_file_is_not_read(self) -> None:
        outside = Path(self._tmp.name) / "secret.txt"
        outside.write_text("AKIA" + "ABCDEFGHIJKLMNOP\n", encoding="utf-8")
        os.symlink(outside, self.root / "Dockerfile")
        scan = self.scan()
        self.assertEqual([f.relative_path for f in scan.files], [])


class TestTestingAnalyzerGo(AuditFixture):
    def test_go_tests_are_recognized(self) -> None:
        self.add("main.go", "package main\n")
        self.add("main_test.go", "package main\n")
        result = run_audit.TestingAnalyzer().analyze(self.scan())
        self.assertFalse(any("No source or test files" in f.message for f in result.findings))
        self.assertEqual(result.metrics["test_to_source_file_ratio"], 1.0)


if __name__ == "__main__":
    unittest.main()
