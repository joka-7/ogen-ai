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

import importlib.util
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from importlib.machinery import SourceFileLoader
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


def _load_ai_sync():
    """Import bin/ai-sync as a module, for unit-testing pure functions directly.

    Safe: main() only runs under __main__. The extensionless filename defeats
    spec_from_file_location's normal inference, so the loader is named explicitly.
    """
    loader = SourceFileLoader("ai_sync", str(REPO / "bin" / "ai-sync"))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


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
                    "---\nname: demo\ndescription: Demo agent.\ntools: Read, Grep, Glob, Skill"
                    "\nmodel: sonnet\n---\n\n# Demo\n\nBody text.\n")
        self._write(sm / "agents" / "claude" / "demo-writer.md",
                    "---\nname: demo-writer\ndescription: Demo writer agent.\n"
                    "tools: Read, Grep, Glob, Bash, Edit, Write, Skill\nmodel: opus\n---\n\n"
                    "# Demo Writer\n\nBody text.\n")
        self._write(sm / "agents" / "claude" / "demo-mcp.md",
                    "---\nname: demo-mcp\ndescription: Demo MCP-integrated agent.\n"
                    "tools: Read, Grep, Glob, mcp__atlassian__createJiraIssue, Skill\n"
                    "model: sonnet\n---\n\n# Demo MCP\n\nBody text.\n")
        self._write(sm / "commands" / "claude" / "demo.md",
                    "---\ndescription: Demo command for $ARGUMENTS\n---\n"
                    "Do the thing. $ARGUMENTS\n")

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
            elif isinstance(value, int):
                lines.append(f"{key} = {value}")
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


class TestTokenBudget(SyncHarness):
    def test_default_budget_is_not_exceeded_by_a_small_config(self) -> None:
        self.write_config(languages=["python"])
        result = self.run_sync()

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("tokens (estimated, budget", result.stdout)
        self.assertNotIn("over the", result.stderr)

    def test_exceeding_the_configured_budget_warns_but_does_not_fail(self) -> None:
        self.write_config(languages=["python"], options={"token_budget": 1})
        result = self.run_sync()

        self.assertEqual(result.returncode, 0, "the budget check must never fail the run")
        self.assertIn("over the 1-token budget", result.stderr)
        self.assertTrue(self.agents_md.exists(), "AGENTS.md must still be written")

    def test_zero_budget_disables_the_check(self) -> None:
        self.write_config(languages=["python"], options={"token_budget": 0})
        result = self.run_sync()
        self.assertNotIn("token", result.stdout)
        self.assertNotIn("token", result.stderr)


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

    def test_dry_run_changes_nothing_at_all(self) -> None:
        self.write_config(languages=["python"], targets=["claude", "gemini", "copilot"])
        before = sorted(p.relative_to(self.project) for p in self.project.rglob("*"))

        result = self.run_sync("--dry-run")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("would write", result.stdout)

        after = sorted(p.relative_to(self.project) for p in self.project.rglob("*"))
        self.assertEqual(after, before,
                         "dry-run reports 'nothing changed' and must mean it — "
                         "including the parent directories of would-be targets")


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

    def test_copilot_gets_skills_at_github_skills(self) -> None:
        self.write_config(targets=["copilot"])
        self.run_sync()
        self.assertTrue((self.project / ".github" / "skills" / "demo-skill" / "SKILL.md")
                        .exists())

    def test_cursor_alone_reads_agents_md_natively_but_still_gets_skills(self) -> None:
        self.write_config(languages=["python"], targets=["cursor"])
        self.run_sync()

        self.assertTrue(self.agents_md.exists())
        self.assertFalse((self.project / ".cursor" / "rules").exists(),
                         "no cursor_mdc means no .mdc rules")
        self.assertTrue((self.project / ".cursor" / "skills" / "demo-skill" / "SKILL.md")
                        .exists(), "skills wiring isn't gated behind cursor_mdc")
        self.assertFalse((self.project / ".cursor" / "commands").exists(),
                         "cursor_commands is opt-in, unlike skills")

    def test_cursor_commands_off_by_default_wires_nothing(self) -> None:
        self.write_config(targets=["cursor"])
        self.run_sync()
        self.assertFalse((self.project / ".cursor" / "commands").exists())

    def test_cursor_commands_opt_in_strips_frontmatter_and_adapts_arguments(self) -> None:
        self.write_config(targets=["cursor"], options={"cursor_commands": True})
        self.run_sync()

        out = self.project / ".cursor" / "commands" / "demo.md"
        self.assertTrue(out.exists())
        text = out.read_text(encoding="utf-8")
        self.assertFalse(text.startswith("---"), "frontmatter must be stripped")
        self.assertNotIn("$ARGUMENTS", text, "the Claude-only placeholder must not leak through")
        self.assertIn("Do the thing.", text)
        self.assertTrue(text.rstrip().endswith("applies here."),
                        "a trailing $ARGUMENTS token becomes a closing sentence")

    def test_cursor_commands_dry_run_writes_nothing(self) -> None:
        self.write_config(targets=["cursor"], options={"cursor_commands": True})
        self.run_sync("--dry-run")
        self.assertFalse((self.project / ".cursor" / "commands").exists())

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


class TestCodexTarget(SyncHarness):
    """Codex reads AGENTS.md natively; skills wiring is unconditional on the target,
    matching every other tool, since it's an unchanged symlink/copy — no opt-in flag."""

    def test_codex_gets_skills_at_dot_codex_skills(self) -> None:
        self.write_config(targets=["codex"])
        self.run_sync()
        self.assertTrue((self.project / ".codex" / "skills" / "demo-skill" / "SKILL.md")
                        .exists())

    def test_codex_alone_reads_agents_md_natively_no_other_wiring(self) -> None:
        self.write_config(languages=["python"], targets=["codex"])
        self.run_sync()
        self.assertTrue(self.agents_md.exists())
        self.assertFalse((self.project / ".codex" / "commands").exists(),
                         "no command port exists for Codex")
        self.assertFalse((self.project / ".codex" / "agents").exists(),
                         "no agent port exists for Codex")


class TestGeminiCommandsPort(SyncHarness):
    def test_off_by_default(self) -> None:
        self.write_config(targets=["gemini"])
        self.run_sync()
        self.assertFalse((self.project / ".gemini" / "commands").exists())

    def test_opt_in_produces_valid_toml_with_args_substituted(self) -> None:
        import tomllib as _toml
        self.write_config(targets=["gemini"], options={"gemini_commands": True})
        self.run_sync()

        out = self.project / ".gemini" / "commands" / "demo.toml"
        self.assertTrue(out.exists())
        data = _toml.loads(out.read_text(encoding="utf-8"))
        self.assertEqual(set(data.keys()), {"description", "prompt"})
        self.assertNotIn("$ARGUMENTS", data["description"])
        self.assertNotIn("$ARGUMENTS", data["prompt"])
        self.assertIn("{{args}}", data["description"])
        self.assertIn("{{args}}", data["prompt"])
        self.assertIn("Do the thing.", data["prompt"])


class TestWindsurfCommandsPort(SyncHarness):
    def test_off_by_default(self) -> None:
        self.write_config(targets=["windsurf"])
        self.run_sync()
        self.assertFalse((self.project / ".windsurf" / "commands").exists())
        self.assertFalse((self.project / ".windsurf" / "workflows").exists())

    def test_opt_in_keeps_description_frontmatter_and_adapts_arguments(self) -> None:
        self.write_config(targets=["windsurf"], options={"windsurf_commands": True})
        self.run_sync()

        out = self.project / ".windsurf" / "workflows" / "demo.md"
        text = out.read_text(encoding="utf-8")
        self.assertTrue(text.startswith("---\ndescription:"),
                        "Windsurf keeps description: frontmatter, unlike Cursor")
        self.assertNotIn("$ARGUMENTS", text)
        self.assertIn("Do the thing.", text)

    def test_windsurf_alone_reads_agents_md_natively(self) -> None:
        self.write_config(languages=["python"], targets=["windsurf"])
        self.run_sync()
        self.assertTrue(self.agents_md.exists())
        self.assertFalse((self.project / ".windsurf").exists())


class TestCopilotCommandsPort(SyncHarness):
    def test_off_by_default(self) -> None:
        self.write_config(targets=["copilot"])
        self.run_sync()
        self.assertFalse((self.project / ".github" / "prompts").exists())

    def test_opt_in_produces_prompt_file_with_input_placeholder(self) -> None:
        self.write_config(targets=["copilot"], options={"copilot_commands": True})
        self.run_sync()

        out = self.project / ".github" / "prompts" / "demo.prompt.md"
        text = out.read_text(encoding="utf-8")
        self.assertTrue(text.startswith("---\ndescription:"))
        self.assertIn("agent: 'agent'", text)
        self.assertNotIn("$ARGUMENTS", text)
        self.assertIn("${input:arguments}", text)
        self.assertIn("Do the thing.", text)


class TestCursorAgentsPort(SyncHarness):
    def test_off_by_default(self) -> None:
        self.write_config(targets=["cursor"])
        self.run_sync()
        self.assertFalse((self.project / ".cursor" / "agents").exists())

    def test_no_bash_role_gets_readonly_and_disclaimer(self) -> None:
        self.write_config(targets=["cursor"], options={"cursor_agents": True})
        self.run_sync()

        out = self.project / ".cursor" / "agents" / "demo.md"
        text = out.read_text(encoding="utf-8")
        self.assertIn("readonly: true", text)
        self.assertIn("model: inherit", text)
        self.assertIn("A note on this port's guarantee", text,
                      "a role with no Bash on Claude must carry the weaker-guarantee disclaimer")

    def test_bash_and_write_capable_role_gets_no_disclaimer(self) -> None:
        self.write_config(targets=["cursor"], options={"cursor_agents": True})
        self.run_sync()

        out = self.project / ".cursor" / "agents" / "demo-writer.md"
        text = out.read_text(encoding="utf-8")
        self.assertIn("readonly: false", text,
                      "a role with Edit/Write on Claude must not claim readonly on Cursor")
        self.assertNotIn("A note on this port's guarantee", text,
                         "a role that already has Bash on Claude needs no weakened-guarantee note")

    def test_mcp_tool_bearing_role_is_skipped_not_defanged(self) -> None:
        self.write_config(targets=["cursor"], options={"cursor_agents": True})
        result = self.run_sync()

        self.assertFalse((self.project / ".cursor" / "agents" / "demo-mcp.md").exists(),
                         "an mcp__* tool has no confirmed Cursor equivalent — porting it "
                         "unmapped would silently drop the tool, not skipping it would hide that")
        self.assertIn("demo-mcp", result.stderr)
        self.assertIn("skipped for Cursor", result.stderr)


class TestGeminiAgentsPort(SyncHarness):
    def test_off_by_default(self) -> None:
        self.write_config(targets=["gemini"])
        self.run_sync()
        self.assertFalse((self.project / ".gemini" / "agents").exists())

    def test_no_bash_role_gets_only_read_tools_no_disclaimer(self) -> None:
        self.write_config(targets=["gemini"], options={"gemini_agents": True})
        self.run_sync()

        out = self.project / ".gemini" / "agents" / "demo.md"
        text = out.read_text(encoding="utf-8")
        self.assertIn("- read_file", text)
        self.assertIn("- grep_search", text)
        self.assertIn("- glob", text)
        self.assertNotIn("run_shell_command", text)
        self.assertNotIn("A note on this port's guarantee", text,
                         "Gemini's tools: grant is a confirmed real allowlist — no weaker claim needed")

    def test_bash_capable_role_maps_every_confirmed_tool(self) -> None:
        self.write_config(targets=["gemini"], options={"gemini_agents": True})
        self.run_sync()

        text = (self.project / ".gemini" / "agents" / "demo-writer.md").read_text(encoding="utf-8")
        for tool in ("read_file", "grep_search", "glob", "run_shell_command", "replace", "write_file"):
            with self.subTest(tool=tool):
                self.assertIn(f"- {tool}", text)

    def test_mcp_tool_bearing_role_is_skipped_not_defanged(self) -> None:
        self.write_config(targets=["gemini"], options={"gemini_agents": True})
        result = self.run_sync()

        self.assertFalse((self.project / ".gemini" / "agents" / "demo-mcp.md").exists(),
                         "Gemini addresses MCP tools as mcp_<server>_<tool>, not Claude's "
                         "mcp__<server>__<tool> — passing the name through unmapped would "
                         "silently drop the tool rather than port it")
        self.assertIn("demo-mcp", result.stderr)
        self.assertIn("skipped for Gemini", result.stderr)


class TestCopilotAgentsPort(SyncHarness):
    def test_off_by_default(self) -> None:
        self.write_config(targets=["copilot"])
        self.run_sync()
        self.assertFalse((self.project / ".github" / "agents").exists())

    def test_no_bash_role_gets_only_read_and_search(self) -> None:
        self.write_config(targets=["copilot"], options={"copilot_agents": True})
        self.run_sync()

        out = self.project / ".github" / "agents" / "demo.agent.md"
        text = out.read_text(encoding="utf-8")
        self.assertIn("tools: ['read', 'search']", text)
        self.assertNotIn("'execute'", text)
        self.assertNotIn("'edit'", text)

    def test_bash_and_write_capable_role_includes_execute_and_edit(self) -> None:
        self.write_config(targets=["copilot"], options={"copilot_agents": True})
        self.run_sync()

        text = (self.project / ".github" / "agents" / "demo-writer.agent.md").read_text(
            encoding="utf-8")
        self.assertIn("'execute'", text)
        self.assertIn("'edit'", text)

    def test_mcp_tool_bearing_role_is_skipped_not_defanged(self) -> None:
        self.write_config(targets=["copilot"], options={"copilot_agents": True})
        result = self.run_sync()

        self.assertFalse(
            (self.project / ".github" / "agents" / "demo-mcp.agent.md").exists(),
            "Copilot's MCP tool-addressing convention isn't confirmed at all — passing "
            "the mcp__<server>__<tool> name through unmapped would silently drop it")
        self.assertIn("demo-mcp", result.stderr)
        self.assertIn("skipped for Copilot", result.stderr)


class TestLocalOnly(SyncHarness):
    """`[options] local_only` / `--local-only`: everything written goes to .git/info/exclude."""

    def _git_init(self) -> None:
        subprocess.run(["git", "init", "-q"], cwd=self.project, check=True)

    def _exclude_text(self) -> str:
        return (self.project / ".git" / "info" / "exclude").read_text(encoding="utf-8")

    def test_manifest_option_excludes_every_written_path_and_the_manifest_itself(self) -> None:
        self._git_init()
        self.write_config(targets=["claude"], options={"claude_agents": True, "local_only": True})
        result = self.run_sync()
        self.assertEqual(result.returncode, 0, result.stderr)

        text = self._exclude_text()
        for expected in (".claude", "AGENTS.md", "CLAUDE.md", "ai-config.toml"):
            self.assertIn(expected, text.splitlines(), f"{expected!r} missing from exclude")

        status = subprocess.run(["git", "status", "--porcelain"], cwd=self.project,
                                capture_output=True, text=True, check=True)
        # .ai itself is the one thing local-only deliberately leaves alone (see docstring
        # in bin/ai-sync) — everything ai-sync actually wrote must be gone from status.
        self.assertEqual(status.stdout.strip(), "?? .ai")

    def test_cli_flag_works_without_the_manifest_key(self) -> None:
        self._git_init()
        self.write_config(targets=["claude"])  # local_only left at its default (false)
        result = self.run_sync("--local-only")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("AGENTS.md", self._exclude_text().splitlines())

    def test_default_is_false_and_leaves_git_status_dirty(self) -> None:
        self._git_init()  # git init itself seeds exclude with its own sample comments
        before = self._exclude_text()
        self.write_config(targets=["claude"])
        self.run_sync()
        self.assertEqual(self._exclude_text(), before)
        status = subprocess.run(["git", "status", "--porcelain"], cwd=self.project,
                                capture_output=True, text=True, check=True)
        self.assertIn("AGENTS.md", status.stdout)

    def test_rerun_is_idempotent_and_does_not_duplicate_the_block(self) -> None:
        self._git_init()
        self.write_config(targets=["claude"], options={"local_only": True})
        self.run_sync()
        first = self._exclude_text()
        self.run_sync()
        second = self._exclude_text()
        self.assertEqual(first, second)
        self.assertEqual(second.count("ai-sync (local-only)"), 2)  # one BEGIN, one END

    def test_shrinking_targets_refreshes_the_block_rather_than_appending(self) -> None:
        self._git_init()
        self.write_config(targets=["claude", "gemini"], options={"local_only": True})
        self.run_sync()
        self.assertIn(".agents", self._exclude_text().splitlines())  # gemini's skills port

        self.write_config(targets=["claude"], options={"local_only": True})
        self.run_sync()
        self.assertNotIn(".agents", self._exclude_text().splitlines())
        self.assertIn("AGENTS.md", self._exclude_text().splitlines())

    def test_dry_run_reports_but_writes_nothing(self) -> None:
        self._git_init()
        before = self._exclude_text()
        self.write_config(targets=["claude"], options={"local_only": True})
        result = self.run_sync("--dry-run")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("exclude (local-only)", result.stdout)
        self.assertEqual(self._exclude_text(), before)

    def test_non_git_project_warns_instead_of_crashing(self) -> None:
        # Deliberately no _git_init() — project has no .git at all.
        self.write_config(targets=["claude"], options={"local_only": True})
        result = self.run_sync()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("doesn't look like a git checkout", result.stderr)
        self.assertIn("AGENTS.md", result.stderr)

    def test_worktree_style_git_file_redirect_is_followed(self) -> None:
        """`.git` as a file (a worktree/submodule checkout) points at its real gitdir."""
        self._git_init()
        real_git_dir = self.project / ".git"
        moved = self.project.parent / "real-gitdir"
        real_git_dir.rename(moved)
        (self.project / ".git").write_text(f"gitdir: {moved}\n", encoding="utf-8")

        self.write_config(targets=["claude"], options={"local_only": True})
        result = self.run_sync()
        self.assertEqual(result.returncode, 0, result.stderr)
        text = (moved / "info" / "exclude").read_text(encoding="utf-8")
        self.assertIn("AGENTS.md", text.splitlines())

    def test_copy_mode_is_also_covered(self) -> None:
        self._git_init()
        self.write_config(targets=["claude"],
                          options={"link_mode": "copy", "local_only": True})
        result = self.run_sync()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(".claude", self._exclude_text().splitlines())


class TestAdaptArgumentsForCursor(unittest.TestCase):
    """Unit tests on the pure transform, since the end-to-end fixture only exercises
    the trailing-token case. Loads bin/ai-sync directly rather than via subprocess."""

    def setUp(self) -> None:
        self.adapt = _load_ai_sync().adapt_arguments_for_cursor

    def test_trailing_token_becomes_a_closing_sentence(self) -> None:
        result = self.adapt("Do the thing. $ARGUMENTS")
        self.assertEqual(result,
                         "Do the thing. Any extra context the user typed when "
                         "invoking this command applies here.")

    def test_inline_mid_sentence_stays_lowercase(self) -> None:
        result = self.adapt("The target given in $ARGUMENTS is used.")
        self.assertEqual(result,
                         "The target given in whatever the user typed alongside "
                         "this command is used.")

    def test_inline_at_start_of_body_is_capitalized(self) -> None:
        result = self.adapt("$ARGUMENTS is `<role> [path]`.")
        self.assertTrue(result.startswith("Whatever the user typed"))

    def test_inline_after_sentence_boundary_is_capitalized(self) -> None:
        result = self.adapt("Resolve the target first. $ARGUMENTS is the input.")
        self.assertIn(". Whatever the user typed", result)

    def test_inline_after_newline_is_capitalized(self) -> None:
        result = self.adapt("First line.\n$ARGUMENTS starts the second line.")
        self.assertIn("\nWhatever the user typed", result)

    def test_no_placeholder_leaks_through_in_any_case(self) -> None:
        for body in ("$ARGUMENTS", "trailing. $ARGUMENTS",
                     "$ARGUMENTS mid. and $ARGUMENTS again."):
            with self.subTest(body=body):
                self.assertNotIn("$ARGUMENTS", self.adapt(body))


if __name__ == "__main__":
    unittest.main()
