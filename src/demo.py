"""Demonstrate local graph cases or three real Cargo crates."""

import argparse
from pathlib import Path

from analysis import analyze
from file_io import write_text
from settings import load_settings
from visualize import ascii_tree, dot_graph

PROJECT = Path(__file__).resolve().parents[1]
REAL_CASES = ("itoa", "num_integer", "itertools")


def run_case(name, reverse=False):
    """Save both graph representations for one demonstrative configuration."""
    settings = load_settings(PROJECT / "configs" / f"{name}.ini")
    graph = analyze(settings, reverse)
    label = name + ("_reverse" if reverse else "")
    write_text(PROJECT / "build" / f"{label}.dot", dot_graph(graph, reverse))
    write_text(PROJECT / "build" / f"{label}.txt", ascii_tree(graph))
    print(f"{label}: {len(graph.edges)} nodes, "
          f"{sum(map(len, graph.edges.values()))} edges")
    print(ascii_tree(graph), end="")
    return graph


def main():
    """Run deterministic local examples or the three HTTP-backed examples."""
    parser = argparse.ArgumentParser(description="Dependency graph examples")
    parser.add_argument("--live", action="store_true")
    options = parser.parse_args()
    try:
        names = REAL_CASES if options.live else (
            "simple", "cycle", "isolated", "depth_one",
        )
        for name in names:
            run_case(name)
        if not options.live:
            run_case("reverse", reverse=True)
    except (OSError, ValueError, RecursionError) as error:
        parser.exit(2, f"Error: {error}\n")


if __name__ == "__main__":
    main()
