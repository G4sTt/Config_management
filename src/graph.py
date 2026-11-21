"""Recursive breadth-first traversal with a shared visited set."""

from dataclasses import dataclass, field


@dataclass
class Graph:
    """A root, shortest-path depths and collected adjacency lists."""

    root: object
    limit: int
    depths: dict = field(default_factory=dict)
    edges: dict = field(default_factory=dict)

    def as_dict(self):
        """Serialize identities to strings without losing their versions."""
        return {str(node): [str(child) for child in children]
                for node, children in self.edges.items()}


def visit_level(graph, frontier, neighbors, level):
    """Expand one complete BFS layer before recursing to the next."""
    if not frontier or level >= graph.limit:
        return
    following = []
    for parent in frontier:
        children = tuple(sorted(set(neighbors(parent)), key=str))
        graph.edges[parent] = children
        for child in children:
            if child not in graph.depths:
                graph.depths[child] = level + 1
                graph.edges[child] = ()
                following.append(child)
    visit_level(graph, following, neighbors, level + 1)


def build_graph(root, neighbors, max_depth):
    """Build a depth-bounded graph, preserving back edges and shared nodes."""
    if max_depth < 0:
        raise ValueError("Depth must be nonnegative")
    graph = Graph(root, max_depth, {root: 0}, {root: ()})
    visit_level(graph, [root], neighbors, 0)
    return graph
