"""Generate Graphviz DOT and an ASCII tree from an already collected graph."""

import json


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


def ascii_tree(graph):
    """Display branches, marking cycles, shared nodes and the depth limit."""
    lines = [str(graph.root)]
    seen = {graph.root}
    stack = [(graph.root, "", True, (), 0)]
    while stack:
        node, prefix, last, ancestors, depth = stack.pop()
        cycle = node in ancestors
        repeated = node in seen and depth > 0
        marker = " [cycle]" if cycle else " [seen]" if repeated else ""
        if depth:
            lines.append(prefix + ("\\-- " if last else "+-- ")
                         + str(node) + marker)
        if cycle or repeated:
            continue
        seen.add(node)
        if depth >= graph.limit:
            lines[-1] += " [depth limit]"
            continue
        children = graph.edges.get(node, ())
        child_prefix = prefix + ("    " if last else "|   ") if depth else ""
        for index in reversed(range(len(children))):
            stack.append((children[index], child_prefix,
                          index == len(children) - 1,
                          (*ancestors, node), depth + 1))
    return "\n".join(lines) + "\n"
