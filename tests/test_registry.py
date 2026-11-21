"""Test registry parsing through a fake HTTP source."""

import json
import unittest

from registry import Package, Registry, index_path
from versions import satisfies


class VersionTests(unittest.TestCase):
    def test_cargo_requirements(self):
        for release, requirement, expected in (
            ("1.9.0", "^1.2.3", True), ("2.0.0", "1.2", False),
            ("0.2.9", "^0.2.3", True), ("0.3.0", "^0.2.3", False),
            ("0.0.4", "^0.0.3", False), ("0.0.9", "0.0", True),
            ("1.3.0", "~1.2.3", False), ("1.2.9", "1.2.*", True),
            ("1.5.0", ">=1.0, <2.0", True), ("1.2.3", "=1.2.3", True),
            ("1.2.3-beta.2", "*", False),
            ("1.2.3-beta.2", ">=1.2.3-beta.1, <2.0.0", True),
            ("1.3.0-beta.1", ">=1.2.3-beta.1", False),
            ("1.2.9", "<=1.2", True), ("1.3.0", ">1.2", True),
        ):
            with self.subTest(release=release, requirement=requirement):
                self.assertEqual(satisfies(release, requirement), expected)

    def test_sparse_paths(self):
        for name, expected in (
            ("a", "1/a"), ("ab", "2/ab"), ("ABC", "3/a/abc"),
            ("itoa", "it/oa/itoa"),
        ):
            self.assertEqual(index_path(name), expected)


class RegistryTests(unittest.TestCase):
    def test_version_selection_and_renamed_dependency(self):
        requests = []
        records = {
            "root": [{"vers": "1.0.0", "deps": [
                {"name": "alias", "package": "real", "req": "^1",
                 "kind": "normal", "optional": False},
                {"name": "skip", "req": "*", "optional": True},
                {"name": "skip", "req": "*", "kind": "dev"},
            ]}],
            "real": [
                {"vers": "1.0.0", "deps": []},
                {"vers": "1.1.0", "deps": []},
                {"vers": "1.2.0", "deps": [], "yanked": True},
                {"vers": "2.0.0", "deps": []},
            ],
        }

        def fetch(url):
            requests.append(url)
            name = url.rsplit("/", 1)[1]
            return "\n".join(json.dumps(r) for r in records[name])

        registry = Registry("https://example.test", fetch)
        root = registry.root("root@1.0.0")
        self.assertEqual(registry.dependencies(root),
                         [Package("real", "1.1.0")])
        registry.dependencies(root)
        self.assertEqual(len(requests), 2)
        with self.assertRaises(ValueError):
            registry.resolve("real", "=3.0.0")

    def test_invalid_json(self):
        registry = Registry("https://example.test", lambda url: "{invalid")
        with self.assertRaises(ValueError):
            registry.root("a")


if __name__ == "__main__":
    unittest.main()
