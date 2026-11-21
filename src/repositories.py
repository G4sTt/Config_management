"""Validate local graph fixtures and select a data source."""

import json
import re
from pathlib import Path

from registry import Registry


class LocalRepository:
    """A complete local repository with uppercase package names."""

    def __init__(self, path):
        try:
            data = json.loads(path.read_text(encoding="utf-8-sig"))
        except json.JSONDecodeError as error:
            raise ValueError(
                f"Invalid test repository JSON: {error}"
            ) from error
        if not isinstance(data, dict):
            raise ValueError("Test repository must be a JSON object")
        for name, dependencies in data.items():
            if re.fullmatch(r"[A-Z]+", name) is None:
                raise ValueError("Test names must be uppercase Latin letters")
            if not isinstance(dependencies, list) or not all(
                isinstance(item, str) and item in data for item in dependencies
            ):
                raise ValueError(f"Invalid or undefined dependency of {name}")
        self.graph = {name: tuple(sorted(set(items)))
                      for name, items in data.items()}

    def root(self, name):
        """Check that the configured package exists in the repository."""
        if name not in self.graph:
            raise ValueError(f"Package {name} is absent from the repository")
        return name

    def dependencies(self, package):
        """Return the direct outgoing dependencies of a package."""
        return self.graph[package]

    def dependents(self, package):
        """Find all local packages that directly depend on the given one."""
        return tuple(sorted(name for name, items in self.graph.items()
                            if package in items))


def open_repository(settings):
    """Construct the selected repository implementation."""
    if settings.test_mode:
        return LocalRepository(Path(settings.repository))
    return Registry(settings.repository)
