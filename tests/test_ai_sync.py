"""Behavioral tests for bin/ai-sync.

One test per behavior listed in docs/DESIGN.md section 7, so the design record and
this suite stay in lockstep. Stdlib `unittest` only — ai-sync is stdlib-only by
design, and a test suite that needs pytest would undercut that.

`ai-sync` runs from a *parent* project root, so every test builds the harness
described in CLAUDE.md: a fixture submodule, a project dir, and a `.ai` symlink
between them. The fixture submodule carries a copy of the real `bin/ai-sync` but
its own small rules/skills/agents tree, so these tests assert generator behavior
and do not break when the repo's own content changes. Real repo content is
asserted in test_conventions.py instead.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


class SyncHarness(unittest.TestCase):
    """Builds <tmp>/submodule + <tmp>/project with a .ai symlink, and runs ai-sync."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        root = Path(self._tmp.name)

        self.submodule = root / "submodule"
        self.project = root / "project"
        self.project.mkdir()

        self._build_submodule()
        (self.project / ".ai").symlink_to(os.path.relpath(self.submodule, self.project))

    def _build_submodule(self) -> None:
        sm = self.submodule
        (sm / "bin").mkdir(parents=True)
        shutil.copy2(REPO / "bin" / "ai-sync", sm / "bin" / "ai-sync")

        # The cursor template is read verbatim by emit_cursor_mdc, so use the real one.
        (sm / "adapters").mkdir()
        shutil.copy2(REPO / "adapters" / "cursor-rule.mdc.tmpl",
                     sm / "adapters" / "cursor-rule.mdc.tmpl")

        self._write(sm / "rules" / "base.md", "## Working agreement\n\n- BASE-MARKER\n")
        self._write(sm / "rules" / "languages" / "python.md", "## Python\n\n- PY-MARKER\n")
        self._write(sm / "rules" / "languages" / "typescript.md", "## TypeScript\n\n- TS-MARKER\n")
        self._write(sm / "rules" / "frameworks" / "react.md", "## React\n\n- REACT-MARKER\n")
        self._write(sm / "rules" / "practices" / "testing.md", "## Testing\n\n- TEST-MARKER\n")

        self._write(sm / "skills" / "demo-skill" / "SKILL.md",
                    "---\nname: demo-skill\ndescription: Demo.\n---\n\n# Demo\n")
        self._write(sm / "agents" / "claude" / "demo.md",
                    "---\nname: demo\ndescription: Demo agent.\ntools: Read\nmodel: sonnet\n---\n")
        self._write(sm / "commands" / "claude" / "demo.md",
                    "---\ndescription: Demo command\n---\nDo the thing. $ARGUMENTS\n")

    @staticmethod
    def _write(path: Path, content: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def write_config(
        self,
        *,
        languages: list[str] | None = None,
        frameworks: list[str] | None = None,
        practices: list[str] | None = None,
        targets: list[str] | None = None,
        options: dict[str, object] | None = None,
    ) -> None:
        def toml_list(items: list[str]) -> str:
            return "[" + ", ".join(f'"{i}"' for i in items) + "]"

        lines = [
            "[stack]",
            f"languages = {toml_list(languages or [])}",
            f"frameworks = {toml_list(frameworks or [])}",
            f"practices = {toml_list(practices or [])}",
            "",
            "[tools]",
            f"targets = {toml_list(targets if targets is not None else ['claude'])}",
            "",
            "[options]",
        ]
        for key, value in (options or {}).items():
            if isinstance(value, bool):
                lines.append(f"{key} = {'true' if value else 'false'}")
            else:
                lines.append(f'{key} = "{value}"')
        self._write(self.project / "ai-config.toml", "\n".join(lines) + "\n")

    def run_sync(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(self.project / ".ai" / "bin" / "ai-sync"),
             "--project", str(self.project), *args],
            capture_output=True, text=True,
        )

    # Convenience accessors -------------------------------------------------
    @property
    def agents_md(self) -> Path:
        return self.project / "AGENTS.md"

    @property
    def claude_md(self) -> Path:
        return self.project / "CLAUDE.md"


class TestAgentsAssembly(SyncHarness):
    def test_fragments_are_assembled_in_manifest_order(self) -> None:
        self.write_config(languages=["python", "typescript"], frameworks=["react"],
                          practices=["testing"])
        result = self.run_sync()
        self.assertEqual(result.returncode, 0, result.stderr)

        text = self.agents_md.read_text(encoding="utf-8")
        order = [text.index(m) for m in
                 ("BASE-MARKER", "PY-MARKER", "TS-MARKER", "REACT-MARKER", "TEST-MARKER")]
        self.assertEqual(order, sorted(order),
                         "expected base -> languages -> frameworks -> practices")

    def test_local_tail_is_appended_last_under_its_own_heading(self) -> None:
        self.write_config(languages=["python"])
        self._write(self.project / "ai-config.local.md", "- LOCAL-MARKER\n")
        self.run_sync()

        text = self.agents_md.read_text(encoding="utf-8")
        self.assertIn("## Project-specific", text)
        self.assertLess(text.index("PY-MARKER"), text.index("LOCAL-MARKER"))
        self.assertLess(text.index("## Project-specific"), text.index("LOCAL-MARKER"))

    def test_custom_local_tail_path_is_honored(self) -> None:
        self.write_config(options={"local_tail": "docs/house-rules.md"})
        self._write(self.project / "docs" / "house-rules.md", "- CUSTOM-TAIL\n")
        self.run_sync()
        self.assertIn("CUSTOM-TAIL", self.agents_md.read_text(encoding="utf-8"))

    def test_generated_file_carries_the_ownership_banner(self) -> None:
        self.write_config()
        self.run_sync()
        self.assertIn("AUTO-GENERATED by ai-sync", self.agents_md.read_text(encoding="utf-8"))

    def test_missing_fragment_warns_and_is_skipped_without_failing(self) -> None:
        self.write_config(languages=["python", "nosuchlang"])
        result = self.run_sync()

        self.assertEqual(result.returncode, 0, "a missing fragment must not be fatal")
        self.assertIn("no such language fragment: nosuchlang", result.stderr)
        self.assertIn("PY-MARKER", self.agents_md.read_text(encoding="utf-8"))

    def test_missing_manifest_exits_with_guidance(self) -> None:
        result = self.run_sync()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("ai-config.example.toml", result.stderr)


class TestSymlinkMode(SyncHarness):
    def test_claude_md_symlinks_to_agents_md(self) -> None:
        self.write_config(languages=["python"])
        self.run_sync()

        self.assertTrue(self.claude_md.is_symlink())
        self.assertEqual(self.claude_md.resolve(), self.agents_md.resolve())
        self.assertIn("PY-MARKER", self.claude_md.read_text(encoding="utf-8"))

    def test_symlinks_are_relative_not_absolute(self) -> None:
        self.write_config()
        self.run_sync()

        for link in (self.claude_md, self.project / ".claude" / "skills"):
            with self.subTest(link=link.name):
                self.assertTrue(link.is_symlink())
                self.assertFalse(os.path.isabs(os.readlink(link)),
                                 "symlinks must be relative so the tree stays portable")

    def test_skills_and_commands_are_wired_as_whole_directories(self) -> None:
        self.write_config()
        self.run_sync()

        self.assertTrue((self.project / ".claude" / "skills" / "demo-skill" / "SKILL.md").exists())
        self.assertTrue((self.project / ".claude" / "commands" / "demo.md").exists())

    def test_rerun_is_idempotent(self) -> None:
        self.write_config(languages=["python"])
        self.run_sync()
        before = self.agents_md.read_text(encoding="utf-8")

        result = self.run_sync()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("ok (symlink current)", result.stdout)
        self.assertEqual(self.agents_md.read_text(encoding="utf-8"), before)
        self.assertTrue(self.claude_md.is_symlink())

    def test_unknown_link_mode_warns_and_falls_back_to_symlink(self) -> None:
        self.write_config(options={"link_mode": "hardlink"})
        result = self.run_sync()

        self.assertIn("unknown link_mode", result.stderr)
        self.assertTrue(self.claude_md.is_symlink())


class TestNoClobber(SyncHarness):
    def test_hand_written_file_at_a_target_path_is_skipped(self) -> None:
        self.write_config()
        self.claude_md.write_text("hand-written, precious\n", encoding="utf-8")

        result = self.run_sync()
        self.assertIn("is not a symlink — skipped", result.stderr)
        self.assertEqual(self.claude_md.read_text(encoding="utf-8"), "hand-written, precious\n")

    def test_force_replaces_a_hand_written_file(self) -> None:
        self.write_config()
        self.claude_md.write_text("hand-written, precious\n", encoding="utf-8")

        self.run_sync("--force")
        self.assertTrue(self.claude_md.is_symlink())
        self.assertEqual(self.claude_md.resolve(), self.agents_md.resolve())

    def test_unmanaged_directory_at_a_target_path_is_skipped_in_copy_mode(self) -> None:
        self.write_config(options={"link_mode": "copy"})
        skills = self.project / ".claude" / "skills"
        skills.mkdir(parents=True)
        (skills / "mine.md").write_text("mine\n", encoding="utf-8")

        result = self.run_sync()
        self.assertIn("is not managed by ai-sync — skipped", result.stderr)
        self.assertTrue((skills / "mine.md").exists())

    def test_dry_run_writes_no_files(self) -> None:
        self.write_config(languages=["python"], targets=["claude", "gemini", "copilot"])
        result = self.run_sync("--dry-run")

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("would write", result.stdout)
        for path in (self.agents_md, self.claude_md, self.project / "GEMINI.md",
                     self.project / ".claude" / "skills"):
            with self.subTest(path=path.name):
                self.assertFalse(path.exists() or path.is_symlink(),
                                 f"dry-run must not create {path}")


class TestCopyMode(SyncHarness):
    def test_copy_mode_writes_real_files_that_survive_losing_the_submodule(self) -> None:
        self.write_config(languages=["python"], options={"link_mode": "copy"})
        self.run_sync()

        self.assertFalse(self.claude_md.is_symlink())
        self.assertFalse((self.project / ".claude" / "skills").is_symlink())

        shutil.rmtree(self.submodule)
        (self.project / ".ai").unlink()
        self.assertIn("PY-MARKER", self.claude_md.read_text(encoding="utf-8"))
        self.assertTrue((self.project / ".claude" / "skills" / "demo-skill" / "SKILL.md").exists())

    def test_copied_trees_are_marked_managed_so_reruns_can_refresh_them(self) -> None:
        self.write_config(options={"link_mode": "copy"})
        self.run_sync()

        marker = self.project / ".claude" / "skills" / ".ai-managed"
        self.assertTrue(marker.exists())

        result = self.run_sync()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("skipped", result.stderr)

    def test_copy_mode_excludes_build_artifacts(self) -> None:
        cache = self.submodule / "skills" / "demo-skill" / "__pycache__"
        cache.mkdir(parents=True)
        (cache / "helper.cpython-311.pyc").write_bytes(b"\x00")
        (self.submodule / "skills" / "demo-skill" / "stale.pyc").write_bytes(b"\x00")

        self.write_config(options={"link_mode": "copy"})
        self.run_sync()

        copied = self.project / ".claude" / "skills" / "demo-skill"
        self.assertTrue((copied / "SKILL.md").exists())
        self.assertFalse((copied / "__pycache__").exists())
        self.assertFalse((copied / "stale.pyc").exists())


class TestClaudeAgentsGate(SyncHarness):
    """The opt-in gate on [options] claude_agents — the role agents must ship dormant."""

    def _agents_dir(self) -> Path:
        return self.project / ".claude" / "agents"

    def test_absent_key_wires_nothing(self) -> None:
        self.write_config()
        self.run_sync()
        self.assertFalse(self._agents_dir().exists() or self._agents_dir().is_symlink())

    def test_false_wires_nothing(self) -> None:
        self.write_config(options={"claude_agents": False})
        self.run_sync()
        self.assertFalse(self._agents_dir().exists() or self._agents_dir().is_symlink())

    def test_true_wires_the_agents_directory(self) -> None:
        self.write_config(options={"claude_agents": True})
        self.run_sync()
        self.assertTrue((self._agents_dir() / "demo.md").exists())

    def test_true_without_the_claude_target_wires_nothing(self) -> None:
        self.write_config(targets=["gemini"], options={"claude_agents": True})
        self.run_sync()
        self.assertFalse(self._agents_dir().exists() or self._agents_dir().is_symlink())

    def test_dry_run_reports_the_gate_without_wiring_it(self) -> None:
        self.write_config(options={"claude_agents": True})
        result = self.run_sync("--dry-run")
        self.assertIn(".claude/agents", result.stdout)
        self.assertFalse(self._agents_dir().exists() or self._agents_dir().is_symlink())


class TestOtherTargets(SyncHarness):
    def test_gemini_gets_its_own_entrypoint_and_skills_path(self) -> None:
        self.write_config(languages=["python"], targets=["gemini"])
        self.run_sync()

        self.assertIn("PY-MARKER", (self.project / "GEMINI.md").read_text(encoding="utf-8"))
        self.assertTrue((self.project / ".agents" / "skills" / "demo-skill").exists())
        self.assertFalse(self.claude_md.exists(), "gemini alone must not wire CLAUDE.md")

    def test_copilot_gets_the_instructions_file(self) -> None:
        self.write_config(languages=["python"], targets=["copilot"])
        self.run_sync()
        instructions = self.project / ".github" / "copilot-instructions.md"
        self.assertIn("PY-MARKER", instructions.read_text(encoding="utf-8"))

    def test_cursor_alone_wires_nothing_because_it_reads_agents_md_natively(self) -> None:
        self.write_config(languages=["python"], targets=["cursor"])
        self.run_sync()
        self.assertTrue(self.agents_md.exists())
        self.assertFalse((self.project / ".cursor").exists())

    def test_cursor_mdc_emits_glob_scoped_rules_for_languages_and_frameworks(self) -> None:
        self.write_config(languages=["python"], frameworks=["react"], practices=["testing"],
                          targets=["cursor"], options={"cursor_mdc": True})
        self.run_sync()

        rules = self.project / ".cursor" / "rules"
        self.assertIn("**/*.py", (rules / "python.mdc").read_text(encoding="utf-8"))
        self.assertIn("PY-MARKER", (rules / "python.mdc").read_text(encoding="utf-8"))
        self.assertTrue((rules / "react.mdc").exists())
        self.assertFalse((rules / "testing.mdc").exists(),
                         "practices have no meaningful glob scope and must be excluded")


if __name__ == "__main__":
    unittest.main()
