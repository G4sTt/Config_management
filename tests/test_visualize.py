"""Check cycle-safe representations and root-only graphs."""

import unittest

from graph import build_graph
from visualize import ascii_tree, dot_graph


class VisualizationTests(unittest.TestCase):
    """Check DOT and ASCII graph representations."""
    def test_dot_contains_cycle_and_isolated_root(self):
        """Verify dot contains cycle and isolated root."""
        graph = build_graph("A", {"A": ["B"], "B": ["A"]}.__getitem__, 3)
        text = dot_graph(graph)
        self.assertIn('"A" -> "B";', text)
        self.assertIn('"B" -> "A";', text)
        self.assertIn('"A" [penwidth=2];',
                      dot_graph(build_graph("A", lambda _: (), 2)))

    def test_ascii_cycle_and_shared_dependency(self):
        """Verify ascii cycle and shared dependency."""
        graph = build_graph("A", {
            "A": ["B", "C"], "B": ["A", "D"], "C": ["D"], "D": [],
        }.__getitem__, 4)
        text = ascii_tree(graph)
        self.assertIn("A [cycle]", text)
        self.assertIn("D [seen]", text)
        self.assertIn("+-- B", text)
        self.assertIn("\\-- C", text)

    def test_depth_marker(self):
        """Verify depth marker."""
        graph = build_graph("A", lambda _: ["B"], 1)
        self.assertIn("B [depth limit]", ascii_tree(graph))
        self.assertNotIn('"B" ->', dot_graph(graph))


if __name__ == "__main__":
    unittest.main()
