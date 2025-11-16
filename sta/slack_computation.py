# slack_computation.py
import math
import networkx as nx
from typing import Dict, Hashable, Tuple

def compute_slacks(
    G: nx.DiGraph,
    AT: Dict[Hashable, float],
    RT: Dict[Hashable, float],
    delay_attr: str = "delay",
) -> Tuple[Dict[Hashable, float], Dict[tuple, float], float, float]:
    """
    Compute node and edge slacks, plus WNS and TNS.

    Node slack: S[n] = RT[n] - AT[n]
    Edge slack: S[(u,v)] = RT[v] - AT[u] - d(u,v)

    Returns:
        node_slack, edge_slack, WNS, TNS
    """
    # Node slacks
    node_slack: Dict[Hashable, float] = {}
    for n in G.nodes():
        at = AT.get(n, -math.inf)
        rt = RT.get(n, math.inf)
        s = rt - at
        node_slack[n] = s

    # Edge slacks
    edge_slack: Dict[tuple, float] = {}
    for u, v, data in G.edges(data=True):
        d = float(data.get(delay_attr, 0.0))
        at_u = AT.get(u, -math.inf)
        rt_v = RT.get(v, math.inf)
        edge_slack[(u, v)] = rt_v - at_u - d

    # WNS/TNS over *finite* slacks only (ignore ±inf islands)
    finite_node_slacks = [s for s in node_slack.values() if math.isfinite(s)]
    WNS = min(finite_node_slacks) if finite_node_slacks else math.inf
    TNS = sum(s for s in finite_node_slacks if s < 0.0)

    return node_slack, edge_slack, WNS, TNS
