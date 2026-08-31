"""Behavioral tests for the coverage.xml reader in skills/audit_repo/run_audit.py.

The audited project is untrusted input, so this reader deliberately does not use an
XML parser (see `_parse_coverage_xml`). These cases pin both halves of that contract:
the values it must still extract, and the hostile documents it must not choke on.
"""

from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


def _load_run_audit():
    """Import skills/audit_repo/run_audit.py as a module."""
    path = REPO / "skills" / "audit_repo" / "run_audit.py"
    spec = importlib.util.spec_from_file_location("run_audit", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


run_audit = _load_run_audit()


class ParseCoverageXml(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)

    def _parse(self, body: str | bytes | None) -> float | None:
        if body is not None:
            path = self.root / "coverage.xml"
            if isinstance(body, bytes):
                path.write_bytes(body)
            else:
                path.write_text(body, encoding="utf-8")
        return run_audit.TestingAnalyzer._parse_coverage_xml(self.root)

    def test_parse_coverage_xml(self) -> None:
        billion_laughs = (
            '<?xml version="1.0"?>\n'
            "<!DOCTYPE coverage [\n"
            '  <!ENTITY a "aaaaaaaaaa">\n'
            '  <!ENTITY b "&a;&a;&a;&a;&a;&a;&a;&a;&a;&a;">\n'
            '  <!ENTITY c "&b;&b;&b;&b;&b;&b;&b;&b;&b;&b;">\n'
            "]>\n"
            '<coverage line-rate="0.5" branch-rate="0.1">&c;</coverage>'
        )
        cases: list[tuple[str, str | bytes | None, float | None]] = [
            ("missing file", None, None),
            ("typical report", '<coverage line-rate="0.9234" branch-rate="0.8"/>', 92.34),
            ("single quotes", "<coverage line-rate='0.5'/>", 50.0),
            ("spaces around =", '<coverage line-rate = "0.25"/>', 25.0),
            ("xml declaration first", '<?xml version="1.0"?><coverage line-rate="1.0"/>', 100.0),
            ("zero coverage", '<coverage line-rate="0.0"/>', 0.0),
            ("no line-rate attribute", '<coverage branch-rate="0.8"/>', None),
            # branch-rate ends in the same six characters; the attribute boundary
            # must not let it match.
            ("only branch-rate", '<coverage branch-rate="0.42"/>', None),
            ("non-numeric line-rate", '<coverage line-rate="abc"/>', None),
            ("empty file", "", None),
            ("not xml at all", "totally not xml", None),
            # line-rate on a child element is not the project total.
            ("line-rate only on a child", "<coverage><package line-rate='0.7'/></coverage>", None),
            ("entity-expansion bomb", billion_laughs, 50.0),
            ("undecodable bytes", b"\xff\xfe<coverage line-rate=\"0.3\"/>", 30.0),
        ]
        for name, body, expected in cases:
            with self.subTest(name):
                self.setUp()
                actual = self._parse(body)
                if expected is None:
                    self.assertIsNone(actual)
                else:
                    self.assertIsNotNone(actual)
                    self.assertAlmostEqual(expected, actual, places=6)

    def test_reads_only_a_bounded_prefix(self) -> None:
        # A hostile report could be arbitrarily large. Only the head is ever read,
        # so a line-rate buried past the bound is not found rather than loaded.
        padding = b"<!--" + b"x" * (run_audit._COVERAGE_HEAD_BYTES * 2) + b"-->"
        (self.root / "coverage.xml").write_bytes(padding + b'<coverage line-rate="0.9"/>')

        self.assertIsNone(run_audit.TestingAnalyzer._parse_coverage_xml(self.root))


if __name__ == "__main__":
    unittest.main()
