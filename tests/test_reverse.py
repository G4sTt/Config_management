"""Check reverse traversal, cycles and version-filtered API responses."""

import json
import unittest
from pathlib import Path

from graph import build_graph
from registry import Package, Registry
from repositories import LocalRepository

FIXTURES = Path(__file__).with_name("repositories")


class ReverseTests(unittest.TestCase):
    """Check reverse graph traversal and paginated API results."""
    def test_direct_and_transitive_dependents(self):
        """Verify direct and transitive dependents."""
        repository = LocalRepository(FIXTURES / "reverse.json")
        graph = build_graph("B", repository.dependents, 3)
        self.assertEqual(graph.as_dict(), {
            "B": ["A", "C"], "A": [], "C": ["D"], "D": ["E"], "E": [],
        })
        self.assertNotIn("F", graph.edges)

    def test_reverse_depth_limit(self):
        """Verify reverse depth limit."""
        repository = LocalRepository(FIXTURES / "reverse.json")
        graph = build_graph("B", repository.dependents, 1)
        self.assertEqual(set(graph.edges), {"A", "B", "C"})
        self.assertEqual(graph.edges["C"], ())

    def test_reverse_cycle(self):
        """Verify reverse cycle."""
        repository = LocalRepository(FIXTURES / "cycle.json")
        graph = build_graph("A", repository.dependents, 10)
        self.assertEqual(graph.edges["A"], ("C",))
        self.assertEqual(graph.edges["B"], ("A",))
        self.assertEqual(len(graph.edges), 3)

    def test_reverse_api_pagination_and_version_filter(self):
        """Verify reverse api pagination and version filter."""
        calls = []

        def fetch(url):
            """Return fixture metadata for the requested URL."""
            calls.append(url)
            if url.endswith("config.json"):
                return json.dumps({"api": "https://api.test"})
            first = "page=1&" in url
            return json.dumps({
                "dependencies": [
                    {"version_id": 1, "req": "^1", "kind": None},
                    {"version_id": 2, "req": "^2", "kind": "normal"},
                ] if first else [],
                "versions": [
                    {"id": 1, "crate": "consumer", "num": "1.0.0"},
                    {"id": 2, "crate": "skip", "num": "1.0.0"},
                ],
                "meta": {"total": 101},
            })

        registry = Registry("https://index.test", fetch)
        self.assertEqual(registry.dependents(Package("root", "1.2.0")),
                         [Package("consumer", "1.0.0")])
        self.assertEqual(len(calls), 3)


if __name__ == "__main__":
    unittest.main()
