"""Check every configurable parameter and relative-path resolution."""

import tempfile
import unittest
from pathlib import Path

from settings import load_settings

PROJECT = Path(__file__).resolve().parents[1]
TEMPLATE = (
    "[analysis]\npackage=A\nrepository=repo.json\ntest_mode=true\n"
    "ascii_tree=true\nmax_depth=3\n"
)


class SettingsTests(unittest.TestCase):
    def parse(self, content):
        """Load a temporary INI and repository."""
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "repo.json").write_text('{"A":[]}')
            path = root / "settings.ini"
            path.write_text(content, encoding="utf-8")
            return load_settings(path)

    def test_valid_relative_path(self):
        config = self.parse(TEMPLATE)
        self.assertTrue(Path(config.repository).is_absolute())
        self.assertEqual(config.max_depth, 3)
        self.assertEqual(config.package, "A")

    def test_invalid_values_for_all_parameters(self):
        replacements = (
            ("package=A", "package=a"),
            ("repository=repo.json", "repository=missing.json"),
            ("test_mode=true", "test_mode=maybe"),
            ("ascii_tree=true", "ascii_tree=maybe"),
            ("max_depth=3", "max_depth=-1"),
            ("max_depth=3", "max_depth=text"),
        )
        for before, after in replacements:
            with self.subTest(parameter=after):
                with self.assertRaises(ValueError):
                    self.parse(TEMPLATE.replace(before, after))

    def test_missing_extra_and_duplicate_keys(self):
        for content in (
            TEMPLATE.replace("ascii_tree=true\n", ""),
            TEMPLATE + "unknown=1\n",
            TEMPLATE + "max_depth=2\n",
            TEMPLATE.replace("[analysis]", "[wrong]"),
        ):
            with self.subTest(content=content):
                with self.assertRaises(ValueError):
                    self.parse(content)

    def test_real_registry_configuration(self):
        text = TEMPLATE.replace("package=A", "package=itoa@1.0.15")
        text = text.replace("repository=repo.json",
                            "repository=https://index.crates.io")
        text = text.replace("test_mode=true", "test_mode=false")
        self.assertFalse(self.parse(text).test_mode)
        with self.assertRaises(ValueError):
            self.parse(text.replace("https://index.crates.io", "file:///tmp"))


if __name__ == "__main__":
    unittest.main()
