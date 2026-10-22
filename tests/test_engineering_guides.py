"""The engineering-guides skill ships a docs tree whose relative links must all resolve."""
import re
import unittest
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent / "skills" / "engineering-guides"
REFERENCE = SKILL / "reference"
LINK = re.compile(r"\]\(([^)#\s]+)(?:#[^)]*)?\)")
LANGUAGES = ("python", "typescript", "cpp")
TOPICS = ("coding-guide", "architecture-guide", "testing-guide")


class TestEngineeringGuides(unittest.TestCase):
    def test_every_language_has_short_and_detailed_for_every_topic(self) -> None:
        for lang in LANGUAGES:
            for topic in TOPICS:
                for kind in ("short", "detailed"):
                    with self.subTest(lang=lang, topic=topic, kind=kind):
                        self.assertTrue((REFERENCE / lang / f"{topic}-{kind}.md").is_file())

    def test_general_principles_exist_in_both_sizes(self) -> None:
        for topic in ("coding", "architecture", "testing", "documentation"):
            for kind in ("short", "detailed"):
                with self.subTest(topic=topic, kind=kind):
                    self.assertTrue(
                        (REFERENCE / "general" / f"{topic}-principles-{kind}.md").is_file())

    def test_relative_links_resolve(self) -> None:
        for doc in sorted(REFERENCE.rglob("*.md")):
            for target in LINK.findall(doc.read_text(encoding="utf-8")):
                if "://" in target:
                    continue
                with self.subTest(doc=doc.relative_to(SKILL).as_posix(), target=target):
                    self.assertTrue((doc.parent / target).exists(), f"broken link {target}")

    def test_skill_router_names_every_reference_directory(self) -> None:
        text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        for name in ("general", "python", "typescript", "cpp"):
            with self.subTest(name=name):
                self.assertIn(f"reference/{name}" if name == "general" else name, text)


if __name__ == "__main__":
    unittest.main()
