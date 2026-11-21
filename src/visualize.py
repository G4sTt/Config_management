"""Generate Graphviz DOT and an ASCII tree from an already collected graph."""

import json

from graph import ROOT_DEPTH


def quoted(value):
    """Escape a node identity as a Graphviz string."""
    return json.dumps(str(value), ensure_ascii=True)


def dot_graph(graph, reverse=False):
    """Describe all collected edges, including cycles and isolated roots."""
    lines = ["digraph dependencies {", "  rankdir=LR;", "  node [shape=box];"]
    if reverse:
        lines.append('  label="Reverse dependencies: required by";')
    for node in sorted(graph.edges, key=str):
        attributes = " [penwidth=2]" if node == graph.root else ""
        lines.append(f"  {quoted(node)}{attributes};")
    for parent in sorted(graph.edges, key=str):
        for child in graph.edges[parent]:
            lines.append(f"  {quoted(parent)} -> {quoted(child)};")
    return "\n".join([*lines, "}"]) + "\n"


def repetition_marker(node, ancestors, seen):
    """Distinguish a cycle on this path from an already expanded shared node."""
    if node in ancestors:
        return " [cycle]"
    if node in seen:
        return " [seen]"
    return ""


def ascii_tree(graph):
    """Display branches, marking cycles, shared nodes and the depth limit."""
    lines = [str(graph.root)]
    seen = set()
    stack = [(graph.root, "", True, (), ROOT_DEPTH)]
    while stack:
        node, prefix, last, ancestors, depth = stack.pop()
        marker = repetition_marker(node, ancestors, seen)
        if depth:
            lines.append(prefix + ("\\-- " if last else "+-- ")
                         + str(node) + marker)
        if marker:
            continue
        seen.add(node)
        if depth >= graph.limit:
            lines[-1] += " [depth limit]"
            continue
        children = graph.edges.get(node, ())
        child_prefix = prefix + ("    " if last else "|   ") if depth else ""
        last_index = len(children) - 1
        for index in reversed(range(len(children))):
            stack.append((children[index], child_prefix,
                          index == last_index,
                          (*ancestors, node), depth + 1))
    return "\n".join(lines) + "\n"
