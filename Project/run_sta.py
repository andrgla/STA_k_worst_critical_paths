# run_sta.py (optional helper)
import networkx as nx
from typing import Iterable, Hashable, Optional, Dict
import matplotlib.pyplot as plt
import os

from Kahn import kahn_topological_sort
from Forwards import forward_arrival_times
from Backwards import backward_required_times
from SlackComputation import compute_slacks

# Number of critical paths to find
k = 150  # Change this to find more or fewer paths 

def run_sta(
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
    topo = kahn_topological_sort(G)
    AT, backpred = forward_arrival_times(
        G, topo, startpoints,
        clock_to_q=clock_to_q,
        startpoint_overrides=startpoint_overrides,
        delay_attr=delay_attr,
        eps=eps,
    )
    RT = backward_required_times(
        G, topo, endpoints,
        Tclk=Tclk, setup=setup,
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
if __name__ == "__main__":
    """Run STA on the Test_circuit_adder.v netlist using the Verilog_Parcer."""
    # Import your Verilog parser. Adjust the import and function name
    # to match the actual API of your Verilog_Parcer module.
    from Verilog_Parcer import build_graph_from_verilog  # TODO: adapt to your parser

    # Path to the Verilog netlist you want to analyze
    script_dir = os.path.dirname(os.path.abspath(__file__))
    netlist_path = os.path.join(script_dir, "Test_circuit_adder.v")

    # The parser is expected to return:
    #   - G: nx.DiGraph with a "delay" attribute on each edge
    #   - startpoints: iterable of startpoint nodes (e.g., FF/Q pins or primary inputs)
    #   - endpoints: iterable of endpoint nodes (e.g., FF/D pins or primary outputs)
    G, startpoints, endpoints = build_graph_from_verilog(netlist_path)

    # Define clock and timing parameters (adjust these to your testbench)
    Tclk = 2.0
    setup = 0.05
    clock_to_q = 0.08

    # Run STA
    res = run_sta(
        G,
        startpoints=startpoints,
        endpoints=endpoints,
        Tclk=Tclk,
        setup=setup,
        clock_to_q=clock_to_q,
    )

    print("=== STA results for", netlist_path, "===")
    print("WNS =", res["WNS"], "TNS =", res["TNS"])
    
    # Find k most critical paths
    def find_critical_paths(G, node_slack, edge_slack, backpred, endpoints, startpoints, k):
        """Find the k most critical distinct paths."""
        # Get endpoints sorted by worst slack
        endpoint_slacks = [(endpoint, node_slack.get(endpoint, float('inf'))) 
                           for endpoint in endpoints if endpoint in node_slack]
        endpoint_slacks.sort(key=lambda x: x[1])  # Sort by slack (worst first)
        
        all_paths = []
        
        def trace_single_path(endpoint):
            """Trace back a single critical path from endpoint to startpoint."""
            path_nodes = []
            path_edges = []
            current = endpoint
            
            # Trace back following backpred
            while current is not None:
                path_nodes.append(current)
                
                # Check if we've reached a startpoint
                if current in startpoints or (current not in backpred or not backpred[current]):
                    break
                
                # Follow the first critical predecessor
                if backpred[current]:
                    pred = backpred[current][0]  # Take first predecessor
                    edge = (pred, current)
                    path_edges.append(edge)
                    current = pred
                else:
                    break
            
            if len(path_nodes) > 1:  # Valid path has at least 2 nodes
                path_nodes_set = set(path_nodes)
                path_edges_set = set(path_edges)
                # Calculate worst slack in this path
                path_node_slacks = [node_slack.get(n, float('inf')) for n in path_nodes_set]
                path_edge_slacks = [edge_slack.get(e, float('inf')) for e in path_edges_set]
                path_worst_slack = min(path_node_slacks + path_edge_slacks)
                return (path_nodes_set, path_edges_set, path_worst_slack)
            return None
        
        # Find paths from worst-slack endpoints
        for endpoint, _ in endpoint_slacks:
            path = trace_single_path(endpoint)
            if path:
                all_paths.append(path)
        
        # Remove duplicate paths and ensure distinctness
        unique_paths = []
        seen_paths = set()
        
        for path_nodes, path_edges, path_worst_slack in all_paths:
            # Check if this path is significantly different from already seen paths
            path_key = tuple(sorted(path_nodes))
            is_duplicate = False
            
            for seen_key_tuple in seen_paths:
                # Convert tuple back to set for intersection
                seen_key_set = set(seen_key_tuple)
                # Check overlap - if paths share >80% nodes, consider them duplicates
                if len(path_nodes & seen_key_set) / max(len(path_nodes), len(seen_key_set)) > 0.8:
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                seen_paths.add(path_key)
                unique_paths.append((path_nodes, path_edges, path_worst_slack))
        
        # Sort by worst slack (most critical first)
        unique_paths.sort(key=lambda x: x[2])
        
        # Return k most critical distinct paths
        return unique_paths[:k]
    
    critical_paths = find_critical_paths(
        G, res["node_slack"], res["edge_slack"], res["backpred"], endpoints, startpoints, k
    )
    
    print(f"\nFound {len(critical_paths)} critical path(s)")
    
    # Print WNS and TNS for each critical path
    for i, (path_nodes, path_edges, path_worst_slack) in enumerate(critical_paths, 1):
        # Calculate TNS for this path (sum of negative slacks)
        path_node_slacks = [res["node_slack"].get(n, 0.0) for n in path_nodes]
        path_edge_slacks = [res["edge_slack"].get(e, 0.0) for e in path_edges]
        all_path_slacks = path_node_slacks + path_edge_slacks
        path_tns = sum(s for s in all_path_slacks if s < 0.0)
        
        print(f"\nPath {i}:")
        print(f"  WNS = {path_worst_slack:.6f} ns")
        print(f"  TNS = {path_tns:.6f} ns")
        print(f"  Nodes: {len(path_nodes)}, Edges: {len(path_edges)}")
    
    # Optional: draw the timing graph with critical paths highlighted
    pos = nx.spring_layout(G, seed=42)
    
    # Draw all nodes and edges in default color
    nx.draw_networkx_nodes(G, pos, node_size=100, node_color='lightgray')
    nx.draw_networkx_edges(G, pos, arrows=True, arrowsize=5, edge_color='lightgray', alpha=0.3)
    
    # Draw critical paths with gradient red colors
    # Draw less critical paths first so most critical appears on top
    if critical_paths:
        num_paths = len(critical_paths)
        # Draw paths in reverse order (least critical first) so most critical is on top
        for i in range(len(critical_paths) - 1, -1, -1):
            path_nodes, path_edges, path_slack = critical_paths[i]
            # Most critical (i=0) gets brightest red, less critical gets lighter
            if num_paths == 1:
                red_intensity = 1.0
            else:
                # Gradient from 1.0 (bright red) to 0.4 (lighter red/pink)
                red_intensity = 1.0 - (i / (num_paths - 1)) * 0.6
            # Use RGB tuple format for matplotlib
            color = (red_intensity, 0.0, 0.0)
            
            # Draw nodes for this path
            nx.draw_networkx_nodes(G, pos, nodelist=list(path_nodes), 
                                   node_size=100, node_color=color)
            # Draw edges for this path
            nx.draw_networkx_edges(G, pos, edgelist=list(path_edges), 
                                  arrows=True, arrowsize=5, edge_color=color, width=2)
    
    # Draw labels
    nx.draw_networkx_labels(G, pos, font_size=5)
    
    plt.title(f"Timing DAG for Test_circuit_adder ({len(critical_paths)} Critical Paths in Red Gradient)")
    plt.show()
