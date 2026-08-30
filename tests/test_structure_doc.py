"""Behavioral tests for skills/repo_tree/gen_tree.py, and a drift gate on docs/STRUCTURE.md.

The drift gate is the reason this skill exists. `docs/INVENTORY.md` states plainly
that it is hand-maintained and unchecked, and this repo previously restated its own
layout in four places that disagreed with each other. `TestRepoIsCurrent` makes
`docs/STRUCTURE.md` the one map that cannot rot: add, rename, or delete a tracked
file without regenerating and CI fails.

Everything else here covers the contract the generator has to hold for that gate to
be trustworthy — that overrides beat heuristics, that prose outside the markers
survives, and that a marked block round-trips its own parameters.
"""

from __future__ import annotations

import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SCRIPT = REPO / "skills" / "repo_tree" / "gen_tree.py"

MARKERS = "<!-- BEGIN GENERATED TREE -->\n<!-- END GENERATED TREE -->\n"


def _load_gen_tree():
    """Import gen_tree.py as a module.

    Registered in sys.modules before execution because the module's dataclasses
    resolve their annotations through it at class-creation time.
    """
    spec = importlib.util.spec_from_file_location("gen_tree", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules["gen_tree"] = module
    spec.loader.exec_module(module)
    return module


gen_tree = _load_gen_tree()


class TestRepoIsCurrent(unittest.TestCase):
    """The gate: this repo's own generated trees match the real tree."""

    def test_generated_trees_are_not_stale(self) -> None:
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--project", str(REPO), "--check"],
            capture_output=True, text=True,
        )
        self.assertEqual(
            result.returncode, 0,
            "docs/STRUCTURE.md (or another marked file) is stale. Regenerate:\n"
            "  python skills/repo_tree/gen_tree.py --project . --output docs/STRUCTURE.md\n"
            f"{result.stdout}{result.stderr}",
        )

    def test_structure_doc_exists_and_is_marked(self) -> None:
        text = (REPO / "docs" / "STRUCTURE.md").read_text(encoding="utf-8")
        self.assertRegex(text, gen_tree.MARKER_BEGIN_RE)
        self.assertIn(gen_tree.MARKER_END, text)

    def test_readme_carries_a_short_tree(self) -> None:
        text = (REPO / "README.md").read_text(encoding="utf-8")
        match = gen_tree.MARKER_BEGIN_RE.search(text)
        self.assertIsNotNone(match, "README.md should carry a depth-limited repo tree")
        max_depth, _ = gen_tree.parse_params(match.group(1))
        self.assertEqual(max_depth, 1, "the README tree stays top-level only")


class GenTreeHarness(unittest.TestCase):
    """A throwaway git repo to generate against."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.project = Path(self._tmp.name)
        self._git("init", "-q")
        self._git("config", "user.email", "test@example.com")
        self._git("config", "user.name", "Test")

    def _git(self, *args: str) -> str:
        result = subprocess.run(["git", "-C", str(self.project), *args],
                                capture_output=True, text=True, check=True)
        return result.stdout.strip()

    def write(self, rel: str, text: str) -> Path:
        path = self.project / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def track(self) -> None:
        self._git("add", "-A")

    def run_script(self, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(SCRIPT), "--project", str(self.project), *args],
            capture_output=True, text=True,
        )

    def block_of(self, rel: str = "docs/STRUCTURE.md") -> str:
        return (self.project / rel).read_text(encoding="utf-8")


class TestAnnotationSources(GenTreeHarness):
    def test_frontmatter_description_wins_over_heading(self) -> None:
        self.write("skills/demo/SKILL.md",
                   "---\nname: demo\ndescription: Does the demo thing.\n---\n\n# Not This\n")
        self.write("docs/STRUCTURE.md", MARKERS)
        self.track()
        self.run_script("--output", "docs/STRUCTURE.md")
        self.assertIn("Does the demo thing", self.block_of())
        self.assertNotIn("Not This", self.block_of())

    def test_heading_used_when_there_is_no_frontmatter(self) -> None:
        self.write("rules/base.md", "## Working agreement\n\nbody\n")
        self.write("docs/STRUCTURE.md", MARKERS)
        self.track()
        self.run_script("--output", "docs/STRUCTURE.md")
        self.assertIn("Working agreement", self.block_of())

    def test_python_module_docstring_is_used_and_stem_is_stripped(self) -> None:
        self.write("tool.py", '"""tool.py — does a thing well."""\n')
        self.write("docs/STRUCTURE.md", MARKERS)
        self.track()
        self.run_script("--output", "docs/STRUCTURE.md")
        self.assertIn("Does a thing well", self.block_of())

    def test_extensionless_python_script_is_annotated_via_shebang(self) -> None:
        self.write("bin/runner", '#!/usr/bin/env python3\n"""runner — wires everything."""\n')
        self.write("docs/STRUCTURE.md", MARKERS)
        self.track()
        self.run_script("--output", "docs/STRUCTURE.md")
        self.assertIn("Wires everything", self.block_of())

    def test_override_beats_every_derived_source(self) -> None:
        self.write("skills/demo/SKILL.md",
                   "---\nname: demo\ndescription: Derived text.\n---\n")
        self.write("docs/.structure-notes.toml",
                   '[notes]\n"skills/demo/SKILL.md" = "Hand-written text."\n')
        self.write("docs/STRUCTURE.md", MARKERS)
        self.track()
        self.run_script("--output", "docs/STRUCTURE.md")
        self.assertIn("Hand-written text", self.block_of())
        self.assertNotIn("Derived text", self.block_of())

    def test_malformed_override_file_degrades_instead_of_failing(self) -> None:
        self.write("rules/base.md", "## Working agreement\n")
        self.write("docs/.structure-notes.toml", "this is not valid toml [[[\n")
        self.write("docs/STRUCTURE.md", MARKERS)
        self.track()
        result = self.run_script("--output", "docs/STRUCTURE.md")
        self.assertEqual(result.returncode, 0)
        self.assertIn("Working agreement", self.block_of())


class TestSplicing(GenTreeHarness):
    def test_prose_outside_the_markers_is_preserved(self) -> None:
        self.write("rules/base.md", "## Base\n")
        self.write("docs/STRUCTURE.md", f"# Title\n\nIntro prose.\n\n{MARKERS}\nTrailing prose.\n")
        self.track()
        self.run_script("--output", "docs/STRUCTURE.md")
        text = self.block_of()
        self.assertIn("Intro prose.", text)
        self.assertIn("Trailing prose.", text)
        self.assertIn("rules/", text)

    def test_missing_markers_is_an_error_not_an_overwrite(self) -> None:
        original = "# Hand-written\n\nNo markers here.\n"
        self.write("docs/STRUCTURE.md", original)
        self.track()
        result = self.run_script("--output", "docs/STRUCTURE.md")
        self.assertEqual(result.returncode, 2)
        self.assertIn("BEGIN GENERATED TREE", result.stderr)
        self.assertEqual(self.block_of(), original)

    def test_absent_output_file_is_created_with_a_default_header(self) -> None:
        self.write("rules/base.md", "## Base\n")
        self.track()
        result = self.run_script("--output", "docs/STRUCTURE.md")
        self.assertEqual(result.returncode, 0)
        self.assertIn("# Repository structure", self.block_of())
        self.assertIn("rules/", self.block_of())

    def test_regeneration_is_idempotent(self) -> None:
        self.write("rules/base.md", "## Base\n")
        self.write("docs/STRUCTURE.md", MARKERS)
        self.track()
        self.run_script("--output", "docs/STRUCTURE.md")
        first = self.block_of()
        self.run_script("--output", "docs/STRUCTURE.md")
        self.assertEqual(first, self.block_of())


class TestParameterRoundTrip(GenTreeHarness):
    def test_depth_limit_is_stamped_and_honored(self) -> None:
        self.write("a/b/c/deep.md", "## Deep\n")
        self.write("README.md", MARKERS)
        self.track()
        self.run_script("--output", "README.md", "--max-depth", "1")
        text = self.block_of("README.md")
        self.assertIn("(depth=1 entries=all)", text)
        self.assertIn("a/", text)
        self.assertNotIn("deep.md", text)

    def test_check_rebuilds_using_the_stamped_parameters(self) -> None:
        self.write("a/b/c/deep.md", "## Deep\n")
        self.write("README.md", MARKERS)
        self.track()
        self.run_script("--output", "README.md", "--max-depth", "1")
        # A --check with no flags must not rebuild this at full depth.
        self.assertEqual(self.run_script("--check").returncode, 0)

    def test_entries_limit_collapses_wide_directories(self) -> None:
        for index in range(8):
            self.write(f"many/file{index}.md", f"## File {index}\n")
        self.write("docs/STRUCTURE.md", MARKERS)
        self.track()
        self.run_script("--output", "docs/STRUCTURE.md", "--max-entries", "3")
        self.assertIn("… 5 more", self.block_of())


class TestCheckMode(GenTreeHarness):
    def test_check_passes_immediately_after_generation(self) -> None:
        self.write("rules/base.md", "## Base\n")
        self.write("docs/STRUCTURE.md", MARKERS)
        self.track()
        self.run_script("--output", "docs/STRUCTURE.md")
        self.assertEqual(self.run_script("--check").returncode, 0)

    def test_check_fails_with_a_diff_once_a_file_is_added(self) -> None:
        self.write("rules/base.md", "## Base\n")
        self.write("docs/STRUCTURE.md", MARKERS)
        self.track()
        self.run_script("--output", "docs/STRUCTURE.md")

        self.write("rules/new-fragment.md", "## Brand New\n")
        self.track()
        result = self.run_script("--check")
        self.assertEqual(result.returncode, 1)
        self.assertIn("new-fragment.md", result.stdout)
        self.assertIn("stale", result.stderr)

    def test_a_doc_that_merely_mentions_the_marker_is_not_treated_as_a_block(self) -> None:
        """Regression: DESIGN.md describes this convention in prose.

        A lone BEGIN with no matching END used to abort the entire check run.
        """
        self.write("rules/base.md", "## Base\n")
        self.write("docs/STRUCTURE.md", MARKERS)
        self.write("docs/DESIGN.md",
                   "# Design\n\nThe tree is written between "
                   "<!-- BEGIN GENERATED TREE --> and its closing marker.\n")
        self.track()
        self.run_script("--output", "docs/STRUCTURE.md")

        result = self.run_script("--check")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("1 generated tree(s) current", result.stdout)

    def test_check_is_a_no_op_when_nothing_is_marked(self) -> None:
        self.write("rules/base.md", "## Base\n")
        self.track()
        result = self.run_script("--check")
        self.assertEqual(result.returncode, 0)
        self.assertIn("nothing to check", result.stdout)


class TestDiscoveryFallback(unittest.TestCase):
    def test_non_git_directory_still_produces_a_tree(self) -> None:
        """`git ls-files` is the fast path, not the only one."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "src").mkdir()
            (root / "src" / "app.py").write_text('"""app — entry point."""\n')
            (root / "__pycache__").mkdir()
            (root / "__pycache__" / "junk.pyc").write_text("x")

            paths = gen_tree.collect_paths(root)
            self.assertIn("src/app.py", paths)
            self.assertFalse([p for p in paths if "__pycache__" in p])


if __name__ == "__main__":
    unittest.main()


class TestMarkerDiscovery(GenTreeHarness):
    """Which files `--check` treats as generated blocks."""

    #: A complete BEGIN/END pair, as a doc teaching the convention would show it.
    EXAMPLE_PAIR = (
        "# Documentation conventions\n\n"
        "Generated content lives between explicit markers:\n\n"
        "```markdown\n"
        "<!-- BEGIN GENERATED TREE -->\n"
        "(the generator rewrites everything here)\n"
        "<!-- END GENERATED TREE -->\n"
        "```\n\n"
        "Never hand-edit between them.\n"
    )

    def test_marker_pair_inside_a_code_fence_is_not_a_generated_block(self) -> None:
        # Arrange: a guide that *illustrates* the marker convention, and a real
        # generated doc alongside it so --check has something legitimate to do.
        self.write("docs/conventions.md", self.EXAMPLE_PAIR)
        self.write("docs/STRUCTURE.md",
                   "# Structure\n\n<!-- BEGIN GENERATED TREE -->\n<!-- END GENERATED TREE -->\n")
        self.track()
        self.run_script("--output", "docs/STRUCTURE.md")
        self.track()

        # Act
        result = self.run_script("--check")

        # Assert: the fenced example is untouched and does not make --check fail.
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(
            (self.project / "docs/conventions.md").read_text(encoding="utf-8"),
            self.EXAMPLE_PAIR,
        )

    def test_marker_pair_outside_a_fence_is_still_a_generated_block(self) -> None:
        # Arrange: the same markers as real content, not an example.
        self.write("docs/STRUCTURE.md",
                   "# Structure\n\n<!-- BEGIN GENERATED TREE -->\nstale\n<!-- END GENERATED TREE -->\n")
        self.track()

        # Act
        result = self.run_script("--check")

        # Assert: a genuine block that has drifted is still reported.
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
