import networkx as nx
from collections import deque


def Khan_topological_sort(G: nx.DiGraph):
    """
    Perform topological sort on a directed acyclic graph using Khan's algorithm.
    
    Args:
        G: NetworkX DiGraph to sort
        
    Returns:
        List of nodes in topological order
        
    Raises:
        TypeError: If graph is not directed
        nx.NetworkXUnfeasible: If graph contains cycles
    """
    # Check if DAG
    if not G.is_directed():
        raise TypeError("Graph must be a directed graph (DiGraph).")

    # Initial indegrees
    indeg = {u: G.in_degree(u) for u in G.nodes()}
    # Queue of nodes with no incoming edges
    q = deque([u for u, d in indeg.items() if d == 0])

    order = []
    while q:
        u = q.popleft()
        order.append(u)
        for v in G.successors(u):
            indeg[v] -= 1
            if indeg[v] == 0:
                q.append(v)

    if len(order) != len(G):
        # Not all nodes were output → cycle(s) exist
        raise nx.NetworkXUnfeasible("Graph contains a cycle; topological sort not possible.")
    return order
