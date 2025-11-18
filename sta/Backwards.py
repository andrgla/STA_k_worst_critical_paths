import math
import networkx as nx
from typing import Dict, Iterable, Hashable, List, Optional

try:
    from .Khan import Khan_topological_sort
except ImportError:
    from Khan import Khan_topological_sort

def backward_required_times(
    G: nx.DiGraph,
    topo_order: List[Hashable],
    endpoints: Iterable[Hashable],
    Tclk: float,
    setup: float = 0.05,
    endpoint_overrides: Optional[Dict[Hashable, float]] = None,
    delay_attr: str = "delay",
) -> Dict[Hashable, float]:
    """
    Compute required times (RT) on a DAG timing graph.

    RT[u] = min_{(u->v) in E} ( RT[v] - d(u,v) )

    Args:
        G: nx.DiGraph where each edge (u,v) has a `delay_attr` (seconds).
        topo_order: topological order of G (sources→sinks).
        endpoints: nodes to seed as timing endpoints (e.g., FF D pins).
        Tclk: clock period (seconds).
        setup: setup time (seconds). Endpoint seeds default to Tclk - setup.
        endpoint_overrides: optional dict {endpoint: RT_value} to override seeds.
        delay_attr: edge attribute name carrying arc delay.

    Returns:
        RT: dict mapping node -> required time (seconds).
    """
    # Initialize all nodes with +inf (least constraining)
    RT: Dict[Hashable, float] = {n: math.inf for n in G.nodes()}

    # Seed endpoints with default RT
    for e in endpoints:
        if e in RT:
            RT[e] = Tclk - setup

    # Apply any explicit overrides (e.g., I/O constraints)
    if endpoint_overrides:
        for e, val in endpoint_overrides.items():
            if e in RT:
                RT[e] = float(val)

    # Backward sweep in reverse topological order
    # for u in reversed(topo_order):
    #     # For each fanout (u->v), tighten RT[u]
    #     for _, v, data in G.out_edges(u, data=True):
    #         d = float(data.get(delay_attr, 0.0))
    #         cand = RT[v] - d
    #         if cand < RT[u]:
    #             RT[u] = cand

    return RT


def backward_required_times_autotopo(
    G: nx.DiGraph,
    endpoints: Iterable[Hashable],
    Tclk: float,
    setup: float = 0.0,
    endpoint_overrides: Optional[Dict[Hashable, float]] = None,
    delay_attr: str = "delay",
) -> Dict[Hashable, float]:
    """
    Convenience wrapper that computes Khan topo order internally.
    """
    topo = Khan_topological_sort(G)
    return backward_required_times(
        G, topo, endpoints, Tclk, setup, endpoint_overrides, delay_attr
    )
