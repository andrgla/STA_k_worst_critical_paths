"""
Utilities to visualize startpoints and endpoints in a DAG in a
"circuit-style" left-to-right layout.

The main entry point is:

    visualize_start_and_endpoints(G, startpoints, endpoints, critical_paths=None, ...)

This will:
- Place startpoints on the left, endpoints on the right.
- Place internal nodes roughly according to their topological "level"
  (distance from any startpoint), so the graph reads left-to-right.
- Optionally, if `critical_paths` is provided (as produced by run_sta),
  group nodes that belong to the same path into vertical "bands"
  to make path clusters visually clearer.
"""

from typing import Iterable, Hashable, Dict, List, Optional, Any

import matplotlib.pyplot as plt
import networkx as nx


def _compute_levels(G: nx.DiGraph, startpoints: Iterable[Hashable]) -> Dict[Hashable, int]:
    """
    Compute a left-to-right "level" for each node based on max distance
    from any startpoint in the DAG.

    startpoints: iterable of source-like nodes (e.g. PIs and FF Qs).
    Returns:
        level dict mapping node -> non-negative integer.
    """
    start_set = set(startpoints)
    # Default all nodes to level 0
    level: Dict[Hashable, int] = {n: 0 for n in G.nodes()}

    # Use a topological order so predecessors are visited before successors
    try:
        topo = list(nx.topological_sort(G))
    except nx.NetworkXUnfeasible:
        # Graph has cycles; fall back to arbitrary ordering
        topo = list(G.nodes())

    for n in topo:
        if n in start_set or G.in_degree(n) == 0:
            # treat as a source
            level[n] = 0
        else:
            preds = list(G.predecessors(n))
            if preds:
                level[n] = max(level[p] + 1 for p in preds)
            else:
                level[n] = 0

    return level


def _build_positions(
    G: nx.DiGraph,
    startpoints: Iterable[Hashable],
    endpoints: Iterable[Hashable],
    critical_paths: Optional[List[Dict[str, Any]]] = None,
) -> Dict[Hashable, tuple]:
    """
    Build a 2D position dictionary for nodes so that:

    - X axis = "time"/logic level from left (sources) to right (sinks).
    - Y axis = used to separate different critical paths into clusters.
    """
    start_set = set(startpoints)
    end_set = set(endpoints)

    levels = _compute_levels(G, startpoints)
    if not levels:
        return {}

    # Normalize x-coordinates so they span [0, 1]
    max_level = max(levels.values()) or 1
    x_scale = 1.0 / max_level

    # If we have critical paths, build a mapping node -> list of path indices
    node_to_paths: Dict[Hashable, List[int]] = {}
    if critical_paths:
        for pi, path in enumerate(critical_paths):
            for n in path.get("nodes", []):
                node_to_paths.setdefault(n, []).append(pi)

    # Y coordinates:
    # - If node belongs to at least one critical path, place it in a band for that path.
    # - Otherwise, place it in a "background" band near y=0.
    positions: Dict[Hashable, tuple] = {}

    # Compute how many vertical bands we need
    num_paths = len(critical_paths) if critical_paths is not None else 0
    # Reserve central band for non-path nodes
    total_bands = max(num_paths, 1) + 1

    for n in G.nodes():
        x = levels.get(n, 0) * x_scale

        if n in node_to_paths and num_paths > 0:
            # Place according to the first path it participates in
            pidx = node_to_paths[n][0]
            # bands are spread in (0, 1]; band 0 is reserved for non-critical
            band_y_center = (pidx + 1) / (total_bands)
            # small jitter based on level to avoid perfect straight lines
            y = band_y_center + 0.02 * ((levels[n] % 5) - 2)
        else:
            # background band near bottom
            band_y_center = 0.0
            y = band_y_center + 0.02 * ((levels[n] % 5) - 2)

        positions[n] = (x, y)

    return positions


def visualize_start_and_endpoints(
    G: nx.DiGraph,
    startpoints: Iterable[Hashable],
    endpoints: Iterable[Hashable],
    critical_paths: Optional[List[Dict[str, Any]]] = None,
    figsize=(14, 6),
    title: str = "Circuit-style DAG view (startpoints → endpoints)",
    show_labels: bool = True,
) -> None:
    """
    Visualize the DAG in a "circuit-style" left-to-right layout.

    - Startpoints / earliest nodes appear on the left.
    - Endpoints / latest nodes appear on the right.
    - Internal nodes are placed according to their topological level.
    - If `critical_paths` is provided (list of dicts with a "nodes" and "edges"
      key, as returned by run_sta), nodes on the same path are visually grouped
      into horizontal clusters and edges on those paths are highlighted.

    Args:
        G: networkx.DiGraph representing the circuit DAG.
        startpoints: iterable of startpoint node IDs.
        endpoints: iterable of endpoint node IDs.
        critical_paths: optional list of path dicts:
            {
                "nodes": [n0, n1, ...],
                "edges": [(u, v), ...],
                "delay": float,
                "WNS": float,
                "TNS": float,
                ...
            }
        figsize: matplotlib figure size.
        title: plot title.
        show_labels: whether to draw node labels.
    """
    if G.number_of_nodes() == 0:
        print("Graph is empty, nothing to visualize.")
        return

    start_set = set(startpoints)
    end_set = set(endpoints)

    pos = _build_positions(G, startpoints, endpoints, critical_paths)

    fig, ax = plt.subplots(figsize=figsize)
    ax.set_title(title)
    ax.axis("off")

    # Draw all edges in light grey
    nx.draw_networkx_edges(
        G,
        pos,
        ax=ax,
        arrows=True,
        arrowsize=10,
        alpha=0.2,
        edge_color="lightgray",
    )

    # Highlight critical paths if provided
    if critical_paths:
        # Color map per path
        cmap = plt.cm.get_cmap("tab10")
        for idx, path in enumerate(critical_paths):
            color = cmap(idx % 10)
            edges = path.get("edges", [])
            if edges:
                nx.draw_networkx_edges(
                    G,
                    pos,
                    edgelist=edges,
                    ax=ax,
                    arrows=True,
                    arrowsize=14,
                    width=2.0,
                    edge_color=[color],
                    alpha=0.9,
                )

    # Prepare node colors and sizes:
    node_colors = []
    node_sizes = []

    for n in G.nodes():
        if n in start_set and n in end_set:
            # degenerate case: both start and end
            node_colors.append("#ffcc00")  # yellow
            node_sizes.append(250)
        elif n in start_set:
            node_colors.append("#4daf4a")  # green
            node_sizes.append(220)
        elif n in end_set:
            node_colors.append("#e41a1c")  # red
            node_sizes.append(220)
        else:
            node_colors.append("#377eb8")  # blue for internal nodes
            node_sizes.append(120)

    # Draw nodes
    nx.draw_networkx_nodes(
        G,
        pos,
        ax=ax,
        node_color=node_colors,
        node_size=node_sizes,
        linewidths=0.5,
        edgecolors="black",
        alpha=0.9,
    )

    # Labels
    if show_labels and G.number_of_nodes() <= 200:
        nx.draw_networkx_labels(
            G,
            pos,
            ax=ax,
            font_size=6,
            font_color="black",
        )

    # Add a simple legend-like text
    legend_y = 1.02
    ax.text(
        0.0,
        legend_y,
        "Green = startpoints   Red = endpoints   Blue = internal   Colored edges = critical paths",
        transform=ax.transAxes,
        fontsize=8,
        ha="left",
        va="bottom",
    )

    plt.tight_layout()
    plt.show()
