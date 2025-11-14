import math
import networkx as nx
from typing import Dict, Iterable, Hashable, List, Optional, Tuple

from Kahn import kahn_topological_sort  # your Kahn.py

def forward_arrival_times(
    G: nx.DiGraph,
    topo_order: List[Hashable],
    startpoints: Iterable[Hashable],
    clock_to_q: float = 0.0,
    startpoint_overrides: Optional[Dict[Hashable, float]] = None,
    delay_attr: str = "delay",
    eps: float = 1e-12,
) -> Tuple[Dict[Hashable, float], Dict[Hashable, List[Hashable]]]:
    """
    Late-mode arrival time (AT) propagation on a DAG timing graph.

    AT[v] = max_{(u->v)} ( AT[u] + d(u,v) )
    Startpoints are seeded with clock_to_q (or per-node overrides).

    Args:
        G: nx.DiGraph where each edge (u,v) has a `delay_attr` (seconds).
        topo_order: topological order of G (sources -> sinks).
        startpoints: nodes to seed as timing startpoints (e.g., FF Q pins).
        clock_to_q: default seed value for all startpoints (seconds).
        startpoint_overrides: optional dict {startpoint: AT_value} to override seeds.
        delay_attr: edge attribute name carrying arc delay.
        eps: tolerance for tie-handling when recording back-predecessors.

    Returns:
        AT: dict(node -> arrival time in seconds)
        backpred: dict(node -> list of predecessors that achieve AT[node])
                  (used for critical path back-tracing)
    """
    # Initialize AT to -inf (unreached)
    AT: Dict[Hashable, float] = {n: -math.inf for n in G.nodes()}
    backpred: Dict[Hashable, List[Hashable]] = {n: [] for n in G.nodes()}

    # Seed startpoints
    for s in startpoints:
        if s in AT:
            AT[s] = clock_to_q
    if startpoint_overrides:
        for s, val in startpoint_overrides.items():
            if s in AT:
                AT[s] = float(val)

    # Forward sweep along topo order
    for u in topo_order:
        au = AT[u]
        if au == -math.inf:
            # unreachable; skip pushing to fanouts
            continue
        for _, v, data in G.out_edges(u, data=True):
            d = float(data.get(delay_attr, 0.0))
            cand = au + d
            if cand > AT[v] + eps:
                AT[v] = cand
                backpred[v] = [u]
            elif abs(cand - AT[v]) <= eps:
                # Tie: keep all predecessors that realize the max (for path enumeration)
                backpred[v].append(u)

    return AT, backpred


def forward_arrival_times_autotopo(
    G: nx.DiGraph,
    startpoints: Iterable[Hashable],
    clock_to_q: float = 0.0,
    startpoint_overrides: Optional[Dict[Hashable, float]] = None,
    delay_attr: str = "delay",
    eps: float = 1e-12,
) -> Tuple[Dict[Hashable, float], Dict[Hashable, List[Hashable]]]:
    """
    Convenience wrapper that computes Kahn topo order internally.
    """
    topo = kahn_topological_sort(G)
    return forward_arrival_times(
        G,
        topo,
        startpoints,
        clock_to_q=clock_to_q,
        startpoint_overrides=startpoint_overrides,
        delay_attr=delay_attr,
        eps=eps,
    )
