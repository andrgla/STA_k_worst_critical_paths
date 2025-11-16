import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from collections import deque

def kahn_with_states(G: nx.DiGraph, skip_intermediate=True):
    """Run Kahn's algorithm but record all intermediate states.

    Each state dictionary contains:
      - "step": step index
      - "processed": list of nodes that have been output so far
      - "queue": nodes currently in the zero-indegree queue
      - "current": node being processed at this step (or None)
    
    Args:
        skip_intermediate: If True, only record states when a node is processed
                          (skips the "after updating" states to reduce frames)
    """
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
        }
    )

    step = 0
    while q:
        u = q.popleft()
        order.append(u)
        step += 1

        # State when processing node u
        states.append(
            {
                "step": step,
                "processed": list(order),
                "queue": list(q),
                "current": u,
            }
        )

        for v in G.successors(u):
            indeg[v] -= 1
            if indeg[v] == 0:
                q.append(v)

        # Only record intermediate state if requested (for smoother animation)
        if not skip_intermediate:
            states.append(
                {
                    "step": step,
                    "processed": list(order),
                    "queue": list(q),
                    "current": None,
                }
            )

    if len(order) != len(G):
        raise nx.NetworkXUnfeasible(
            "Graph contains a cycle; topological sort not possible."
        )

    return order, states


def animate_kahn(G: nx.DiGraph, interval: int = 1000, max_nodes: int = 100, 
                 show_labels: bool = True):
    """Create an animation of Kahn's algorithm on graph G.

    Args:
        interval: Time between frames in milliseconds
        max_nodes: If graph has more nodes, subsample or use simpler visualization
        show_labels: Whether to show node labels (slower if True)
    """
    # For very large graphs, warn user
    if len(G) > max_nodes:
        print(f"Warning: Graph has {len(G)} nodes. Consider using a smaller subgraph for animation.")
    
    order, states = kahn_with_states(G, skip_intermediate=True)

    cmap = plt.cm.get_cmap('plasma')
    num_frames = len(states) if len(states) > 1 else 1

    # Use spring layout but with reduced iterations for speed
    pos = nx.spring_layout(G, seed=42, iterations=20)

    fig, ax = plt.subplots(figsize=(8, 6))
    plt.tight_layout()

    # Pre-compute all colors for all states (faster than computing each frame)
    all_colors = []
    processed_sets = []
    queue_sets = []
    current_nodes = []
    
    for frame_idx, state in enumerate(states):
        processed = set(state["processed"])
        queue = set(state["queue"])
        current = state["current"]
        
        processed_sets.append(processed)
        queue_sets.append(queue)
        current_nodes.append(current)
        
        # Pre-compute colors for this state
        t = frame_idx / (num_frames - 1) if num_frames > 1 else 0.0
        step_color = cmap(t)
        
        colors = []
        for n in G.nodes():
            if n == current:
                colors.append(step_color)
            elif n in processed:
                colors.append((step_color[0], step_color[1], step_color[2], 0.8))
            elif n in queue:
                colors.append((step_color[0], step_color[1], step_color[2], 0.5))
            else:
                colors.append("lightgray")
        all_colors.append(colors)

    def get_node_colors(state, frame_idx):
        # Use pre-computed colors
        return all_colors[frame_idx]

    def init():
        ax.clear()
        ax.set_title("Kahn's Algorithm: Topological Sort")
        ax.axis("off")

        colors = all_colors[0]
        # Draw edges once (static)
        nx.draw_networkx_edges(G, pos, ax=ax, arrows=True, arrowsize=8, 
                              alpha=0.3, edge_color='gray')
        nodes = nx.draw_networkx_nodes(G, pos, ax=ax, node_color=colors, 
                                      node_size=300 if len(G) < 50 else 100)
        if show_labels and len(G) < 100:
            nx.draw_networkx_labels(G, pos, ax=ax, font_size=6, font_color="dimgray")

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
        state = states[frame]
        ax.clear()
        ax.set_title("Kahn's Algorithm: Topological Sort")
        ax.axis("off")

        # Draw edges (static, don't change)
        nx.draw_networkx_edges(G, pos, ax=ax, arrows=True, arrowsize=8, 
                              alpha=0.3, edge_color='gray')

        # Draw nodes with pre-computed colors
        colors = all_colors[frame]
        node_size = 300 if len(G) < 50 else 100
        node_collection = nx.draw_networkx_nodes(
            G, pos, ax=ax, node_color=colors, node_size=node_size
        )
        
        # Only draw labels for smaller graphs
        if show_labels and len(G) < 100:
            nx.draw_networkx_labels(G, pos, ax=ax, font_size=6, font_color="dimgray")

        # Simplified text (don't show full queue/processed for large graphs)
        if len(G) < 50:
            queue_str = ", ".join(str(x) for x in state["queue"][:10]) or "(empty)"
            if len(state["queue"]) > 10:
                queue_str += f", ... ({len(state['queue'])} total)"
            processed_str = f"{len(state['processed'])} nodes"
        else:
            queue_str = f"{len(state['queue'])} nodes"
            processed_str = f"{len(state['processed'])} nodes"
        
        current_str = state["current"] if state["current"] is not None else "None"

        text = (
            f"Step: {state['step']}/{len(order)}\n"
            f"Current: {current_str}\n"
            f"Queue: {queue_str}\n"
            f"Processed: {processed_str}"
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
