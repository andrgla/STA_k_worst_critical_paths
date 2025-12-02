import networkx as nx
import matplotlib.pyplot as plt
import os
import sys
import time
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
k = 5  # adjust as needed

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
    # Main entry point: Build DAG from Verilog and run STA analysis
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    
    # Add project root to path for imports when running as script
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    
    # Try relative import first, fall back to absolute
    try:
        from .verilog_parcer import build_graph_from_verilog
    except ImportError:
        try:
            from verilog_parcer import build_graph_from_verilog
        except ImportError:
            from sta.verilog_parcer import build_graph_from_verilog

    # Load Verilog netlist and build timing DAG
    netlist_path = os.path.join(project_root, "benches", "Test_circuit_priority.v")
    G, startpoints, endpoints = build_graph_from_verilog(netlist_path)

    delays = [G[u][v]["delay"] for u, v in G.edges()]
    unique_delays = sorted(set(delays))
    delay_counts = {d: delays.count(d) for d in unique_delays}
    
    print("Min edge delay:", min(delays))
    print("Max edge delay:", max(delays))
    print("Number of edges with nonzero delay:", sum(1 for d in delays if d != 0.0))
    print(f"Unique delays found: {len(unique_delays)}")
    print("Delay distribution:")
    for delay in sorted(delay_counts.keys()):
        count = delay_counts[delay]
        pct = 100 * count / len(delays) if delays else 0
        print(f"  {delay:.3f} ns: {count:5d} edges ({pct:.1f}%)")

    print(f"Loaded DAG from {netlist_path}")
    print(f"Nodes: {len(G.nodes())}, Edges: {len(G.edges())}")

    # Timing parameters
    Tclk = 3
    setup = 0.05
    clock_to_q = 0.06

    # Run STA analysis
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

    # Time the critical path finding
    print("\n=== Finding critical paths ===")
    start_time = time.time()
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
    elapsed_time = time.time() - start_time
    print(f"Critical path calculation took {elapsed_time:.4f} seconds ({elapsed_time*1000:.2f} ms)")

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

    # Visualize the timing graph with critical paths highlighted
    if critical_paths:
        pos = nx.spring_layout(G, seed=42)

        nx.draw_networkx_nodes(G, pos, node_size=30, node_color="lightgray")
        nx.draw_networkx_edges(
            G, pos, arrows=True, arrowsize=5, edge_color="#e5e5e5", alpha=0.15
        )

        num_paths = len(critical_paths)
        # Use a colormap that spans the full spectrum (red → yellow → green → blue → purple)
        colormap = plt.cm.get_cmap('hsv')
        
        for i in range(num_paths - 1, -1, -1):
            path_info = critical_paths[i]
            path_nodes = path_info["nodes"]
            path_edges = path_info["edges"]

            # Map path index to color in the spectrum
            # Most critical path (i=num_paths-1) gets red, least critical gets purple/blue
            if num_paths == 1:
                color_value = 0.0  # Red for single path
            else:
                # Distribute colors across the spectrum (0.0 = red, 0.17 = yellow, 0.33 = green, 0.5 = cyan, 0.67 = blue, 0.83 = purple)
                # Reverse the mapping: most critical (high i) → red (0.0), least critical (low i) → purple (0.8)
                color_value = (1.0 - i / (num_paths - 1)) * 0.8  # Use 0.8 to avoid wrapping back to red
            
            color = colormap(color_value)

            nx.draw_networkx_nodes(
                G, pos, nodelist=path_nodes, node_size=50, node_color=color
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

        plt.title(f"Timing DAG with {len(critical_paths)} Critical Path(s)")
        plt.show()

    # # Khan's algorithm animation
    # order_plain = Khan_topological_sort(G)
    # order_states, _ = Khan_with_states(G)

    # print("\nTopological order length (Khan_topological_sort):", len(order_plain))
    # print("Topological order length (states):", len(order_states))

    # # Animate Khan's algorithm
    # animate_khan(G, interval=20)
