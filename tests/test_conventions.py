"""Conformance tests for this repo's own agents, skills, and commands.

`ai-sync` deliberately performs no frontmatter validation — it symlinks or copies
whole directories and never opens these files. Every rule below is therefore
convention-only in the generator, and this suite is the only thing enforcing it.

The tool matrix in particular is load-bearing: docs/DESIGN.md section 10 states that
the trust boundary between the role agents is enforced by tool grants rather than by
instructions in the agent bodies. That claim is only true while the grants below hold,
so the expected matrix is spelled out explicitly. Changing a grant should require
editing this table — that is the point, not an inconvenience.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
AGENTS_DIR = REPO / "agents" / "claude"
COMMANDS_DIR = REPO / "commands" / "claude"
SKILLS_DIR = REPO / "skills"

# Every role agent, its exact tool grant, and its model tier.
EXPECTED_AGENTS: dict[str, tuple[list[str], str]] = {
    "qa": (["Read", "Grep", "Glob", "Bash", "Skill"], "sonnet"),
    "architect": (["Read", "Grep", "Glob", "Bash", "Skill"], "opus"),
    "product": (["Read", "Grep", "Glob", "Bash", "Skill"], "sonnet"),
    "engineering-manager": (["Read", "Grep", "Glob", "Bash", "Skill"], "sonnet"),
    "ciso": (["Read", "Grep", "Glob", "Skill"], "opus"),
    "planner": (["Read", "Grep", "Glob", "Skill"], "opus"),
    "developer": (["Read", "Grep", "Glob", "Bash", "Edit", "Write", "Skill"], "opus"),
}

# Reviewing roles fan out in parallel and share the role-review output contract.
# Each owns a finding-ID prefix that the aggregation step cites when deduplicating.
REVIEWER_PREFIXES: dict[str, str] = {
    "qa": "QA",
    "architect": "ARC",
    "product": "PRD",
    "engineering-manager": "EM",
    "ciso": "SEC",
}

# Roles that do not review source: planner reads reports, developer implements.
NON_REVIEWERS = {"planner", "developer"}

FRONTMATTER = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)


def parse_frontmatter(path: Path) -> tuple[dict[str, str], list[str], str]:
    """Return (fields, key order, body). Hand-rolled to keep the repo stdlib-only."""
    text = path.read_text(encoding="utf-8")
    match = FRONTMATTER.match(text)
    if match is None:
        raise AssertionError(f"{path} has no YAML frontmatter block")
    fields: dict[str, str] = {}
    order: list[str] = []
    for line in match.group(1).splitlines():
        if not line.strip():
            continue
        key, _, value = line.partition(":")
        key = key.strip()
        fields[key] = value.strip()
        order.append(key)
    return fields, order, text[match.end():]


def agent_files() -> list[Path]:
    return sorted(AGENTS_DIR.glob("*.md"))


class TestAgentFrontmatter(unittest.TestCase):
    def test_every_expected_agent_exists_and_nothing_extra_does(self) -> None:
        found = {p.stem for p in agent_files()}
        self.assertEqual(found, set(EXPECTED_AGENTS),
                         "an agent was added or removed without updating this table, "
                         "which means the role enumerations elsewhere are likely stale too")

    def test_frontmatter_keys_are_exactly_name_description_tools_model_in_order(self) -> None:
        for path in agent_files():
            with self.subTest(agent=path.stem):
                _, order, _ = parse_frontmatter(path)
                self.assertEqual(order, ["name", "description", "tools", "model"])

    def test_name_matches_filename(self) -> None:
        for path in agent_files():
            with self.subTest(agent=path.stem):
                fields, _, _ = parse_frontmatter(path)
                self.assertEqual(fields["name"], path.stem)

    def test_model_is_a_bare_alias_not_a_pinned_id(self) -> None:
        for path in agent_files():
            with self.subTest(agent=path.stem):
                fields, _, _ = parse_frontmatter(path)
                expected = EXPECTED_AGENTS[path.stem][1]
                self.assertEqual(fields["model"], expected)
                self.assertNotIn("-", fields["model"],
                                 "use an alias so agents survive model version bumps")

    def test_description_says_when_not_to_use_the_agent(self) -> None:
        for path in agent_files():
            with self.subTest(agent=path.stem):
                fields, _, _ = parse_frontmatter(path)
                self.assertIn("Do NOT", fields["description"],
                              "auto-delegation keys off the negative clause")


class TestToolGrants(unittest.TestCase):
    """The trust boundary. Withholding a tool is the only real enforcement."""

    @staticmethod
    def tools_of(name: str) -> list[str]:
        fields, _, _ = parse_frontmatter(AGENTS_DIR / f"{name}.md")
        return [t.strip() for t in fields["tools"].split(",")]

    def test_grants_match_the_expected_matrix(self) -> None:
        for name, (expected, _) in EXPECTED_AGENTS.items():
            with self.subTest(agent=name):
                self.assertEqual(self.tools_of(name), expected)

    def test_only_developer_can_modify_a_repo(self) -> None:
        for name in EXPECTED_AGENTS:
            with self.subTest(agent=name):
                writers = {"Edit", "Write", "NotebookEdit"} & set(self.tools_of(name))
                if name == "developer":
                    self.assertTrue(writers, "developer must be able to edit")
                else:
                    self.assertEqual(writers, set(),
                                     f"{name} must not be able to modify the target repo")

    def test_ciso_and_planner_have_no_shell_at_all(self) -> None:
        for name in ("ciso", "planner"):
            with self.subTest(agent=name):
                self.assertNotIn("Bash", self.tools_of(name),
                                 "no Bash is a harder guarantee than any deny list")

    def test_every_agent_can_load_skills(self) -> None:
        for name in EXPECTED_AGENTS:
            with self.subTest(agent=name):
                self.assertEqual(self.tools_of(name)[-1], "Skill")


class TestSharedReviewContract(unittest.TestCase):
    def setUp(self) -> None:
        self.skill = (SKILLS_DIR / "role_review" / "SKILL.md").read_text(encoding="utf-8")

    def test_reviewers_load_the_shared_contract_rather_than_restating_it(self) -> None:
        for name in REVIEWER_PREFIXES:
            with self.subTest(agent=name):
                _, _, body = parse_frontmatter(AGENTS_DIR / f"{name}.md")
                self.assertIn("role-review", body,
                              "reviewing roles must load the shared schema skill")

    def test_every_reviewer_owns_a_finding_id_prefix(self) -> None:
        self.assertEqual(set(REVIEWER_PREFIXES) | NON_REVIEWERS, set(EXPECTED_AGENTS),
                         "every agent is either a reviewer with a prefix or a known non-reviewer")

    def test_finding_id_prefixes_are_documented_in_the_skill(self) -> None:
        for name, prefix in REVIEWER_PREFIXES.items():
            with self.subTest(agent=name):
                self.assertIn(f"{prefix}-01", self.skill,
                              f"{name}'s finding-ID prefix is missing from the shared contract")

    def test_prefixes_are_unique(self) -> None:
        prefixes = list(REVIEWER_PREFIXES.values())
        self.assertEqual(len(prefixes), len(set(prefixes)))

    def test_skill_names_every_reviewing_role(self) -> None:
        for name in REVIEWER_PREFIXES:
            with self.subTest(agent=name):
                self.assertIn(name, self.skill)

    def test_schema_sections_are_fixed(self) -> None:
        for section in ("## Summary", "## Findings", "## Recommendations", "## Open questions"):
            with self.subTest(section=section):
                self.assertIn(section, self.skill)


class TestSkills(unittest.TestCase):
    @staticmethod
    def skill_files() -> list[Path]:
        return sorted(SKILLS_DIR.glob("*/SKILL.md"))

    def test_frontmatter_is_exactly_name_and_description(self) -> None:
        for path in self.skill_files():
            with self.subTest(skill=path.parent.name):
                _, order, _ = parse_frontmatter(path)
                self.assertEqual(order, ["name", "description"])

    def test_names_are_kebab_case(self) -> None:
        for path in self.skill_files():
            with self.subTest(skill=path.parent.name):
                fields, _, _ = parse_frontmatter(path)
                self.assertRegex(fields["name"], r"\A[a-z0-9]+(-[a-z0-9]+)*\Z")

    def test_descriptions_are_specific_enough_to_trigger(self) -> None:
        for path in self.skill_files():
            with self.subTest(skill=path.parent.name):
                fields, _, _ = parse_frontmatter(path)
                self.assertGreater(len(fields["description"]), 120,
                                   "a terse description will not trigger reliably")


class TestCommands(unittest.TestCase):
    @staticmethod
    def command_files() -> list[Path]:
        return sorted(COMMANDS_DIR.glob("*.md"))

    def test_frontmatter_is_description_only(self) -> None:
        for path in self.command_files():
            with self.subTest(command=path.stem):
                _, order, _ = parse_frontmatter(path)
                self.assertEqual(order, ["description"])

    def test_every_command_uses_the_arguments_placeholder(self) -> None:
        for path in self.command_files():
            with self.subTest(command=path.stem):
                self.assertIn("$ARGUMENTS", path.read_text(encoding="utf-8"))

    def test_roles_named_by_the_single_role_command_all_exist(self) -> None:
        text = (COMMANDS_DIR / "role.md").read_text(encoding="utf-8")
        line = next(ln for ln in text.splitlines() if ln.startswith("Valid roles:"))
        named = set(re.findall(r"`([a-z-]+)`", line))
        self.assertEqual(named, set(REVIEWER_PREFIXES),
                         "/role must offer exactly the reviewing roles")

    def test_fan_out_launches_every_reviewing_role(self) -> None:
        text = (COMMANDS_DIR / "role-review.md").read_text(encoding="utf-8")
        for name in REVIEWER_PREFIXES:
            with self.subTest(agent=name):
                self.assertIn(f"`{name}`", text,
                              "a reviewing role that is never launched is dead weight")

    def test_developer_is_never_invoked_by_the_review_commands(self) -> None:
        for stem in ("role", "role-review"):
            with self.subTest(command=stem):
                text = (COMMANDS_DIR / f"{stem}.md").read_text(encoding="utf-8")
                self.assertIn("developer", text)
                self.assertRegex(text, r"(?i)(never invoke `developer`|not invocable)",
                                 "the human approval gate must be stated, not implied")


class TestMountPathReferences(unittest.TestCase):
    """`.ai` is the mount path every command and agent hardcodes; keep it honest."""

    SCRIPT_REF = re.compile(r"\.ai/(skills/[\w-]+/[\w-]+\.py)")

    def test_referenced_scripts_exist(self) -> None:
        sources = list(COMMANDS_DIR.glob("*.md")) + list(AGENTS_DIR.glob("*.md")) \
            + list(SKILLS_DIR.glob("*/SKILL.md"))
        seen = 0
        for path in sources:
            for rel in self.SCRIPT_REF.findall(path.read_text(encoding="utf-8")):
                seen += 1
                with self.subTest(source=path.name, script=rel):
                    self.assertTrue((REPO / rel).exists(),
                                    f"{path.name} points at .ai/{rel}, which does not exist")
        self.assertGreater(seen, 0, "expected at least one .ai/ script reference")


if __name__ == "__main__":
    unittest.main()
