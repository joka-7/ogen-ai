"""Behavioral tests for skills/role_review/run_manifest.py."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SCRIPT = REPO / "skills" / "role_review" / "run_manifest.py"


class ManifestHarness(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.project = Path(self._tmp.name)
        self._git("init", "-q")
        self._git("config", "user.email", "test@example.com")
        self._git("config", "user.name", "Test")
        self._commit("init")

    def _git(self, *args: str) -> str:
        result = subprocess.run(["git", "-C", str(self.project), *args],
                                capture_output=True, text=True, check=True)
        return result.stdout.strip()

    def _commit(self, message: str) -> str:
        self._git("commit", "-q", "--allow-empty", "-m", message)
        return self._git("rev-parse", "--short", "HEAD")

    def run_manifest(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), "--project", str(self.project), *args],
            capture_output=True, text=True,
        )

    @property
    def manifest(self) -> dict:
        return json.loads((self.project / ".ai-reviews" / "manifest.json")
                          .read_text(encoding="utf-8"))


class TestStatusWithNoRun(ManifestHarness):
    def test_status_exits_2_when_nothing_recorded(self) -> None:
        result = self.run_manifest("--status")
        self.assertEqual(result.returncode, 2)
        self.assertIn("none recorded", result.stdout)


class TestBeginAndRecord(ManifestHarness):
    def test_begin_opens_a_run_at_head(self) -> None:
        sha = self._git("rev-parse", "--short", "HEAD")
        result = self.run_manifest("--begin")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.manifest["runs"][-1]["sha"], sha)

    def test_record_notes_role_reports_and_backlog(self) -> None:
        self.run_manifest("--begin")
        result = self.run_manifest("--record", "qa=qa.md", "--record", "ciso=ciso.md",
                                   "--backlog", "BACKLOG.md", "--audit-score", "80")
        self.assertEqual(result.returncode, 0, result.stderr)

        run = self.manifest["runs"][-1]
        self.assertEqual(run["roles"], {"qa": "qa.md", "ciso": "ciso.md"})
        self.assertEqual(run["backlog"], "BACKLOG.md")
        self.assertEqual(run["audit_score"], 80)

    def test_record_without_a_prior_begin_fails(self) -> None:
        result = self.run_manifest("--record", "qa=qa.md")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("no open run", result.stderr)

    def test_malformed_record_pair_warns_and_is_ignored(self) -> None:
        self.run_manifest("--begin")
        result = self.run_manifest("--record", "not-a-pair")
        self.assertEqual(result.returncode, 0)
        self.assertIn("malformed", result.stderr)
        self.assertEqual(self.manifest["runs"][-1]["roles"], {})


class TestStatusCurrency(ManifestHarness):
    def test_status_is_current_right_after_begin(self) -> None:
        self.run_manifest("--begin")
        result = self.run_manifest("--status")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("current:", result.stdout)

    def test_status_is_stale_after_a_new_commit(self) -> None:
        self.run_manifest("--begin")
        self._commit("second")
        result = self.run_manifest("--status")
        self.assertEqual(result.returncode, 1)
        self.assertIn("STALE", result.stdout)


class TestReRunSameSha(ManifestHarness):
    def test_begin_twice_at_the_same_sha_reuses_the_run(self) -> None:
        self.run_manifest("--begin")
        self.run_manifest("--record", "qa=qa.md")
        result = self.run_manifest("--begin")

        self.assertIn("reusing run", result.stdout)
        self.assertEqual(len(self.manifest["runs"]), 1)
        self.assertEqual(self.manifest["runs"][-1]["roles"], {"qa": "qa.md"})


class TestArchiveOnNewCommit(ManifestHarness):
    def test_begin_after_a_new_commit_archives_prior_reports(self) -> None:
        self.run_manifest("--begin")
        reviews = self.project / ".ai-reviews"
        (reviews / "qa.md").write_text("# qa\n", encoding="utf-8")
        (reviews / "audit_data.json").write_text("{}", encoding="utf-8")
        self.run_manifest("--record", "qa=qa.md")
        old_sha = self.manifest["runs"][-1]["sha"]

        self._commit("second")
        result = self.run_manifest("--begin")

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse((reviews / "qa.md").exists())
        self.assertTrue((reviews / "archive" / old_sha / "qa.md").exists())
        self.assertTrue((reviews / "archive" / old_sha / "audit_data.json").exists())
        self.assertEqual(len(self.manifest["runs"]), 2)

    def test_manifest_json_itself_is_never_archived(self) -> None:
        self.run_manifest("--begin")
        self._commit("second")
        self.run_manifest("--begin")
        self.assertFalse(
            list((self.project / ".ai-reviews" / "archive").rglob(("manifest.json"))),
            "the ledger must outlive the runs it describes")


class TestCliValidation(ManifestHarness):
    def test_no_flags_is_a_usage_error(self) -> None:
        result = self.run_manifest()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("nothing to do", result.stderr)

    def test_missing_project_directory_is_a_usage_error(self) -> None:
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--project", "/no/such/dir", "--status"],
            capture_output=True, text=True,
        )
        self.assertNotEqual(result.returncode, 0)


if __name__ == "__main__":
    unittest.main()
