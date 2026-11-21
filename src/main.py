"""Command-line dependency graph tool for Cargo packages."""

import argparse
import sys
from dataclasses import asdict
from pathlib import Path

from analysis import analyze
from file_io import write_text
from repositories import open_repository
from settings import load_settings
from visualize import ascii_tree, dot_graph


def validate_output(options, settings):
    """Check output-stage compatibility and protect input files."""
    protected = {options.config.resolve()}
    if settings.test_mode:
        protected.add(Path(settings.repository).resolve())
    if options.output and options.output.resolve() in protected:
        raise ValueError("Output must differ from the INI and repository files")
    if options.stage in {"config", "direct"} and options.output:
        raise ValueError("--output is supported for graph and reverse stages")


def print_graph(options, settings):
    """Print DOT and optionally save the diagram and display the tree."""
    reverse = options.stage == "reverse"
    graph = analyze(settings, reverse)
    diagram = dot_graph(graph, reverse)
    if options.output:
        write_text(options.output, diagram)
    print(diagram, end="")
    if settings.ascii_tree:
        print(ascii_tree(graph), file=sys.stderr, end="")


def execute(options):
    """Execute a selected stage while keeping DOT separate from the tree."""
    settings = load_settings(options.config)
    validate_output(options, settings)
    if options.stage == "config":
        for key, value in asdict(settings).items():
            print(f"{key}={value}")
    elif options.stage == "direct":
        repository = open_repository(settings)
        root = repository.root(settings.package)
        print(root)
        for package in repository.dependencies(root):
            print(package)
    else:
        print_graph(options, settings)


def main():
    """Load the configuration and report validation errors consistently."""
    parser = argparse.ArgumentParser(description="Cargo dependency graph")
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output", type=Path, help="Optional DOT output")
    parser.add_argument(
        "--stage", choices=("config", "direct", "graph", "reverse"),
        default="graph",
    )
    options = parser.parse_args()
    try:
        execute(options)
    except (OSError, ValueError, RecursionError) as error:
        parser.exit(2, f"Error: {error}\n")


if __name__ == "__main__":
    main()
