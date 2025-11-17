import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from collections import deque
import os
import sys
from typing import Iterable, Hashable, Optional, Dict
from visualize_start_and_end_points import visualize_start_and_endpoints


# Handle imports for both module and direct script execution
# When run as a script, add the sta directory to path first
# Check if we're being run directly (not imported as a module)
if __name__ == "__main__" or not __package__:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    if script_dir not in sys.path:
        sys.path.insert(0, script_dir)

try:
    from .animate_khan import animate_khan
    from .animate_khan import Khan_with_states
    from .Khan import Khan_topological_sort
    from .forwards import forward_arrival_times
    from .backwards import backward_required_times
    from .slack_computation import compute_slacks
except ImportError:
    # When run directly as a script, use absolute imports
    from animate_khan import animate_khan
    from animate_khan import Khan_with_states
    from Khan import Khan_topological_sort
    from forwards import forward_arrival_times
    from backwards import backward_required_times
    from slack_computation import compute_slacks

# Number of critical paths to find when plotting
k = 1  # adjust as needed

def run_sta(
    G: nx.DiGraph,
    startpoints: Iterable[Hashable],
    endpoints: Iterable[Hashable],
    Tclk: float,
    *,
    setup: float = 0.05,
    clock_to_q: float = 0.05,
    startpoint_overrides: Optional[Dict[Hashable, float]] = None,
    endpoint_overrides: Optional[Dict[Hashable, float]] = None,
    delay_attr: str = "delay",
    eps: float = 1e-12,
):
    topo = Khan_topological_sort(G)
    AT, backpred = forward_arrival_times(
        G,
        topo,
        startpoints,
        clock_to_q=clock_to_q,
        startpoint_overrides=startpoint_overrides,
        delay_attr=delay_attr,
        eps=eps,
    )
    RT = backward_required_times(
        G,
        topo,
        endpoints,
        Tclk=Tclk,
        setup=setup,
        endpoint_overrides=endpoint_overrides,
        delay_attr=delay_attr,
    )
    node_slack, edge_slack, WNS, TNS = compute_slacks(G, AT, RT, delay_attr)
    return {
        "AT": AT,
        "RT": RT,
        "backpred": backpred,
        "node_slack": node_slack,
        "edge_slack": edge_slack,
        "WNS": WNS,
        "TNS": TNS,
        "topo": topo,
    }


def extract_single_critical_path(
    G: nx.DiGraph,
    startpoints: Iterable[Hashable],
    endpoints: Iterable[Hashable],
    Tclk: float,
    *,
    setup: float = 0.0,
    clock_to_q: float = 0.0,
    startpoint_overrides: Optional[Dict[Hashable, float]] = None,
    endpoint_overrides: Optional[Dict[Hashable, float]] = None,
    delay_attr: str = "delay",
    eps: float = 1e-12,
):
    """Run STA once and extract a single most critical path."""
    res = run_sta(
        G,
        startpoints=startpoints,
        endpoints=endpoints,
        Tclk=Tclk,
        setup=setup,
        clock_to_q=clock_to_q,
        startpoint_overrides=startpoint_overrides,
        endpoint_overrides=endpoint_overrides,
        delay_attr=delay_attr,
        eps=eps,
    )

    node_slack = res["node_slack"]
    edge_slack = res["edge_slack"]
    backpred = res["backpred"]

    valid_endpoints = [e for e in endpoints if e in node_slack]
    if not valid_endpoints:
        return None

    worst_endpoint = min(valid_endpoints, key=lambda e: node_slack[e])

    path_nodes = []
    path_edges = []
    current = worst_endpoint

    while True:
        path_nodes.append(current)
        if current in startpoints or current not in backpred or not backpred[current]:
            break
        pred = backpred[current][0]  # follow the most critical predecessor
        path_edges.append((pred, current))
        current = pred

    if len(path_nodes) < 2:
        return None

    # Reverse so that nodes/edges go from startpoint -> endpoint
    path_nodes = list(reversed(path_nodes))
    path_edges = list(reversed(path_edges))

    # Compute total delay along the path
    total_delay = 0.0
    for (u, v) in path_edges:
        if G.has_edge(u, v):
            total_delay += float(G[u][v].get(delay_attr, 0.0))

    # Compute WNS/TNS restricted to this path
    node_slacks = [node_slack.get(n, float("inf")) for n in path_nodes]
    edge_slacks = [edge_slack.get(e, float("inf")) for e in path_edges]
    all_slacks = node_slacks + edge_slacks

    if all_slacks:
        path_WNS = min(all_slacks)
        path_TNS = sum(s for s in all_slacks if s < 0.0)
    else:
        path_WNS = float("inf")
        path_TNS = 0.0

    return {
        "nodes": path_nodes,
        "edges": path_edges,
        "delay": total_delay,
        "WNS": path_WNS,
        "TNS": path_TNS,
        "sta": res,
    }


def find_k_critical_paths(
    G: nx.DiGraph,
    startpoints: Iterable[Hashable],
    endpoints: Iterable[Hashable],
    Tclk: float,
    *,
    setup: float = 0.0,
    clock_to_q: float = 0.0,
    startpoint_overrides: Optional[Dict[Hashable, float]] = None,
    endpoint_overrides: Optional[Dict[Hashable, float]] = None,
    delay_attr: str = "delay",
    eps: float = 1e-12,
    k: int = 1,
):
    """Extract up to k edge-disjoint critical paths."""
    work_graph = G.copy()
    critical_paths = []

    for _ in range(k):
        path_info = extract_single_critical_path(
            work_graph,
            startpoints=startpoints,
            endpoints=endpoints,
            Tclk=Tclk,
            setup=setup,
            clock_to_q=clock_to_q,
            startpoint_overrides=startpoint_overrides,
            endpoint_overrides=endpoint_overrides,
            delay_attr=delay_attr,
            eps=eps,
        )
        if not path_info:
            break

        critical_paths.append(path_info)

        # Block this path for the next iteration by removing its edges
        for (u, v) in path_info["edges"]:
            if work_graph.has_edge(u, v):
                work_graph.remove_edge(u, v)

    return critical_paths

if __name__ == "__main__":
    # Build DAG from the adder circuit and run both STA and animation
    import sys
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    
    # Add project root to path for imports when running as script
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    
    # Try relative import first, fall back to absolute
    try:
        from .verilog_parcer import build_graph_from_verilog
    except ImportError:
        # When run directly as a script, sta/ is already in sys.path
        try:
            from verilog_parcer import build_graph_from_verilog
        except ImportError:
            from sta.verilog_parcer import build_graph_from_verilog

    # Go up one level from sta/ to STA_k_worst_critical_paths/, then into benches/
    netlist_path = os.path.join(project_root, "benches", "Test_circuit_adder.v")

    # The parser is expected to return:
    #   - G: nx.DiGraph representing the timing/circuit DAG
    #   - startpoints: iterable of startpoint nodes
    #   - endpoints: iterable of endpoint nodes
    G, startpoints, endpoints = build_graph_from_verilog(netlist_path)

    print(f"Loaded DAG from {netlist_path}")
    print(f"Nodes: {len(G.nodes())}, Edges: {len(G.edges())}")

    # Define simple timing parameters (adjust to your testbench)
    Tclk = 2.0
    setup = 0.05
    clock_to_q = 0.08

    # ---- Part 1: STA and k worst critical paths ----
    sta_res = run_sta(
        G,
        startpoints=startpoints,
        endpoints=endpoints,
        Tclk=Tclk,
        setup=setup,
        clock_to_q=clock_to_q,
    )
    print("=== STA results ===")
    print("WNS =", sta_res["WNS"], "TNS =", sta_res["TNS"])

    critical_paths = find_k_critical_paths(
        G,
        startpoints=startpoints,
        endpoints=endpoints,
        Tclk=Tclk,
        setup=setup,
        clock_to_q=clock_to_q,
        delay_attr="delay",
        k=k,
    )

    print(f"\nFound {len(critical_paths)} critical path(s)")
    for i, path_info in enumerate(critical_paths, 1):
        path_nodes = path_info["nodes"]
        path_edges = path_info["edges"]
        path_delay = path_info["delay"]
        path_WNS = path_info["WNS"]
        path_TNS = path_info["TNS"]

        print(f"\nPath {i}:")
        print(f"  Total delay = {path_delay:.6f} ns")
        print(f"  Path WNS    = {path_WNS:.6f} ns")
        print(f"  Path TNS    = {path_TNS:.6f} ns")
        print(f"  Nodes: {len(path_nodes)}, Edges: {len(path_edges)}")

    # Optional: visualize the timing graph with critical paths highlighted
    if critical_paths:
        pos = nx.spring_layout(G, seed=32)

        nx.draw_networkx_nodes(G, pos, node_size=100, node_color="lightgray")
        nx.draw_networkx_edges(
            G, pos, arrows=True, arrowsize=5, edge_color="lightgray", alpha=0.3
        )

        num_paths = len(critical_paths)
        for i in range(num_paths - 1, -1, -1):
            path_info = critical_paths[i]
            path_nodes = path_info["nodes"]
            path_edges = path_info["edges"]

            if num_paths == 1:
                red_intensity = 1.0
            else:
                red_intensity = 1.0 - (i / (num_paths - 1)) * 0.6
            color = (red_intensity, 0.0, 0.0)

            nx.draw_networkx_nodes(
                G, pos, nodelist=path_nodes, node_size=100, node_color=color
            )
            nx.draw_networkx_edges(
                G,
                pos,
                edgelist=path_edges,
                arrows=True,
                arrowsize=5,
                edge_color=color,
                width=2,
            )

        nx.draw_networkx_labels(G, pos, font_size=5)
        plt.title(f"Timing DAG with {len(critical_paths)} Critical Path(s)")
        plt.show()

    # ---- Part 2: Khan animation on the same DAG ----
    # Sanity check: instrumented version matches your original implementation
    order_plain = Khan_topological_sort(G)
    order_states, _ = Khan_with_states(G)

    print("Topological order length (Khan_topological_sort):", len(order_plain))
    print("Topological order length (states):", len(order_states))

    # Finally, animate Khan's algorithm
    animate_khan(G, interval=100)

# ... after you have G, startpoints, endpoints, and maybe critical_paths
visualize_start_and_endpoints(
    G,
    startpoints=startpoints,
    endpoints=endpoints,
    critical_paths=critical_paths,  # or None if you just want the circuit view
    title="Vending machine circuit DAG"
)
