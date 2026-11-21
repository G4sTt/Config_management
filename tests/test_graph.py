"""Exercise recursive BFS, bounded depths and graph validation."""

import tempfile
import unittest
from pathlib import Path

from graph import build_graph
from repositories import LocalRepository

FIXTURES = Path(__file__).with_name("repositories")


class GraphTests(unittest.TestCase):
    def test_breadth_first_order_and_shared_dependency(self):
        repository = LocalRepository(FIXTURES / "simple.json")
        calls = []

        def neighbors(package):
            calls.append(package)
            return repository.dependencies(package)

        graph = build_graph("A", neighbors, 3)
        self.assertEqual(calls, ["A", "B", "C", "D"])
        self.assertEqual(graph.depths, {"A": 0, "B": 1, "C": 1, "D": 2})
        self.assertEqual(graph.edges["B"], ("D",))
        self.assertEqual(graph.edges["C"], ("D",))

    def test_depth_zero_and_one(self):
        repository = LocalRepository(FIXTURES / "simple.json")
        for depth, nodes in ((0, {"A"}), (1, {"A", "B", "C"})):
            graph = build_graph("A", repository.dependencies, depth)
            self.assertEqual(set(graph.edges), nodes)
            self.assertLessEqual(max(graph.depths.values()), depth)
        self.assertEqual(build_graph("A", lambda _: (), 0).as_dict(), {"A": []})

    def test_cycle_terminates_and_keeps_back_edge(self):
        repository = LocalRepository(FIXTURES / "cycle.json")
        graph = build_graph("A", repository.dependencies, 20)
        self.assertEqual(len(graph.edges), 4)
        self.assertEqual(graph.edges["C"], ("A", "D"))
        self.assertEqual(graph.depths["A"], 0)

    def test_isolated_package(self):
        repository = LocalRepository(FIXTURES / "isolated.json")
        self.assertEqual(
            build_graph("A", repository.dependencies, 3).as_dict(), {"A": []}
        )
        with self.assertRaises(ValueError):
            repository.root("Z")

    def test_invalid_repository(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "bad.json"
            for text in ('{bad', '[]', '{"a":[]}', '{"A":["B"]}', '{"A":{}}'):
                with self.subTest(text=text):
                    path.write_text(text)
                    with self.assertRaises(ValueError):
                        LocalRepository(path)


if __name__ == "__main__":
    unittest.main()
