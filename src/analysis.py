"""Connect configuration, repository access and recursive graph traversal."""

from graph import build_graph
from repositories import open_repository


def analyze(settings, reverse=False):
    """Build the forward or reverse graph from a validated configuration."""
    repository = open_repository(settings)
    root = repository.root(settings.package)
    neighbors = repository.dependents if reverse else repository.dependencies
    return build_graph(root, neighbors, settings.max_depth)
