"""Independent comparison with cargo tree; not used by the analyzer."""

import json
import os
import re
import shutil
import subprocess
from pathlib import Path

from analysis import analyze
from demo import PROJECT, REAL_CASES
from file_io import write_text
from settings import load_settings


def parse_cargo_tree(text):
    """Convert cargo tree --prefix depth output to versioned nodes and edges."""
    nodes, edges, stack = set(), set(), []
    for line in text.splitlines():
        match = re.fullmatch(r"(\d+)\s*([A-Za-z0-9_-]+) v([^\s]+).*", line)
        if match is None:
            if line.strip():
                raise ValueError(f"Unexpected cargo tree line: {line}")
            continue
        depth, name, release = match.groups()
        depth = int(depth)
        node = f"{name}@{release}"
        nodes.add(node)
        if depth > len(stack):
            raise ValueError("Missing parent in cargo tree output")
        stack = stack[:depth]
        if stack:
            edges.add((stack[-1], node))
        stack.append(node)
    return nodes, edges


def cargo_output(name, root):
    """Create a tiny consumer manifest and run the native display tool."""
    cargo = os.environ.get("CARGO") or shutil.which("cargo")
    if not cargo:
        raise ValueError(
            "Install Rust/Cargo to run this independent comparison"
        )
    folder = PROJECT / "build/comparison" / name
    manifest = folder / "Cargo.toml"
    consumer_name = name.replace("_", "-")
    write_text(manifest, (
        f'[package]\nname="compare-{consumer_name}"\n'
        'version="0.1.0"\nedition="2021"\n\n[dependencies]\n'
        f'{root.name}={{ version="={root.release}", '
        'default-features=false }\n'
    ))
    write_text(folder / "src/lib.rs", "// Manifest-only comparison target.\n")
    environment = os.environ.copy()
    environment.setdefault("CARGO_HOME", str(PROJECT / "build/cargo-home"))
    environment["CARGO_REGISTRIES_CRATES_IO_PROTOCOL"] = "sparse"
    result = subprocess.run(
        [cargo, "tree", "--manifest-path", str(manifest), "-p", str(root),
         "--edges", "normal", "--target", "all", "--prefix", "depth",
         "--charset", "ascii", "--no-dedupe"],
        capture_output=True, text=True, timeout=180, env=environment,
    )
    if result.returncode:
        raise ValueError(result.stderr.strip())
    write_text(folder / "cargo-tree.txt", result.stdout)
    return result.stdout


def compare_case(name):
    """Compare resolved identities and edges for one complete small graph."""
    settings = load_settings(PROJECT / "configs" / f"{name}.ini")
    graph = analyze(settings)
    native_nodes, native_edges = parse_cargo_tree(
        cargo_output(name, graph.root)
    )
    nodes = {str(node) for node in graph.edges}
    edges = {(str(parent), str(child))
             for parent, children in graph.edges.items() for child in children}
    result = {
        "case": name, "root": str(graph.root), "nodes": sorted(nodes),
        "edges": sorted(edges), "cargo_nodes": sorted(native_nodes),
        "cargo_edges": sorted(native_edges),
        "match": nodes == native_nodes and edges == native_edges,
    }
    print(f"{name}: {'MATCH' if result['match'] else 'DIFFERENCE'}")
    return result


def main():
    """Save an auditable comparison and return nonzero for a difference."""
    try:
        results = [compare_case(name) for name in REAL_CASES]
        write_text(PROJECT / "build/comparison/results.json",
                   json.dumps(results, indent=2) + "\n")
        return 0 if all(result["match"] for result in results) else 1
    except (OSError, ValueError, subprocess.TimeoutExpired) as error:
        print(f"Comparison error: {error}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
