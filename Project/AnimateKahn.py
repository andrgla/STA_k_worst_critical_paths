import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from collections import deque

from Kahn import kahn_topological_sort


def generate_example_graph() -> nx.DiGraph:
    """Create a small example DAG to visualize Kahn's algorithm."""
    G = nx.DiGraph()
    edges = [
        ("A", "B"),
        ("A", "C"),
        ("B", "D"),
        ("B", "E"),
        ("C", "D"),
        ("D", "F"),
        ("E", "F"),
    ]
    G.add_edges_from(edges)
    return G


def kahn_with_states(G: nx.DiGraph):
    """Run Kahn's algorithm but record all intermediate states."""
    if not G.is_directed():
        raise TypeError("Graph must be a directed graph (DiGraph).")

    indeg = {u: G.in_degree(u) for u in G.nodes()}
    q = deque([u for u, d in indeg.items() if d == 0])

    order = []
    states = []

    # Initial state (before any node is removed)
    states.append(
        {
            "step": 0,
            "processed": list(order),
            "queue": list(q),
            "current": None,
            "indeg": dict(indeg),
        }
    )

    step = 0
    while q:
        u = q.popleft()
        order.append(u)
        step += 1

        # After choosing `u` but before relaxing its outgoing edges
        states.append(
            {
                "step": step,
                "processed": list(order),
                "queue": list(q),
                "current": u,
                "indeg": dict(indeg),
            }
        )

        for v in G.successors(u):
            indeg[v] -= 1
            if indeg[v] == 0:
                q.append(v)

        # After updating indegrees and queue
        states.append(
            {
                "step": step,
                "processed": list(order),
                "queue": list(q),
                "current": None,
                "indeg": dict(indeg),
            }
        )

    if len(order) != len(G):
        raise nx.NetworkXUnfeasible(
            "Graph contains a cycle; topological sort not possible."
        )

    return order, states


def animate_kahn(G: nx.DiGraph, interval: int = 1000):
    """Create an animation of Kahn's algorithm on graph G."""
    order, states = kahn_with_states(G)

    pos = nx.spring_layout(G, seed=42)

    fig, ax = plt.subplots(figsize=(6, 4))
    plt.tight_layout()

    node_collection = None
    text_annotation = None

    def get_node_colors(state):
        processed = set(state["processed"])
        queue = set(state["queue"])
        current = state["current"]

        colors = []
        for n in G.nodes():
            if n == current:
                colors.append("tab:orange")      # node being processed
            elif n in processed:
                colors.append("tab:green")       # already output
            elif n in queue:
                colors.append("tab:blue")        # in zero-indegree queue
            else:
                colors.append("lightgray")       # not yet reachable
        return colors

    def init():
        ax.clear()
        ax.set_title("Kahn's Algorithm: Topological Sort")
        ax.axis("off")

        colors = get_node_colors(states[0])
        nx.draw_networkx_edges(G, pos, ax=ax, arrows=True, arrowsize=10)
        nodes = nx.draw_networkx_nodes(G, pos, ax=ax, node_color=colors, node_size=500)
        nx.draw_networkx_labels(G, pos, ax=ax, font_size=10, font_weight="bold")

        txt = ax.text(
            0.02,
            0.02,
            "",
            transform=ax.transAxes,
            fontsize=9,
            verticalalignment="bottom",
        )

        return nodes, txt

    def update(frame):
        nonlocal node_collection, text_annotation

        state = states[frame]
        ax.clear()
        ax.set_title("Kahn's Algorithm: Topological Sort")
        ax.axis("off")

        nx.draw_networkx_edges(G, pos, ax=ax, arrows=True, arrowsize=10)

        colors = get_node_colors(state)
        node_collection = nx.draw_networkx_nodes(
            G, pos, ax=ax, node_color=colors, node_size=500
        )
        nx.draw_networkx_labels(G, pos, ax=ax, font_size=10, font_weight="bold")

        queue_str = ", ".join(str(x) for x in state["queue"]) or "(empty)"
        processed_str = ", ".join(str(x) for x in state["processed"]) or "(none)"
        current_str = state["current"] if state["current"] is not None else "None"

        text = (
            f"Step: {state['step']}\n"
            f"Current: {current_str}\n"
            f"Queue: [{queue_str}]\n"
            f"Processed: [{processed_str}]"
        )

        text_annotation = ax.text(
            0.02,
            0.02,
            text,
            transform=ax.transAxes,
            fontsize=9,
            verticalalignment="bottom",
        )

        return node_collection, text_annotation

    anim = FuncAnimation(
        fig,
        update,
        frames=len(states),
        init_func=init,
        interval=interval,
        blit=False,
        repeat=False,
    )

    plt.show()

    return anim


if __name__ == "__main__":
    G = generate_example_graph()

    # Sanity check: instrumented version matches your original implementation
    order_plain = kahn_topological_sort(G)
    order_states, _ = kahn_with_states(G)

    print("Topological order (kahn_topological_sort):", order_plain)
    print("Topological order (states):", order_states)

    animate_kahn(G, interval=1000)