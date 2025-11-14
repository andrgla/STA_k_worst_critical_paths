import re
import networkx as nx

def parse_verilog_to_dag(verilog_text):
    # Graph where nodes are net names (strings), edges are data dependencies
    G = nx.DiGraph()

    # Regex for "assign lhs = rhs;"
    assign_re = re.compile(r'\s*assign\s+(.+?)\s*=\s*(.+?);')

    # Regex for signal names:
    #  - escaped identifiers: \something_until_whitespace  (e.g. "\a[0]")
    #  - normal identifiers:   a123, n386, f[0], etc.
    signal_re = re.compile(r'(\\\S+|[A-Za-z_]\w*(?:\[\d+\])?)')

    for line in verilog_text.splitlines():
        m = assign_re.match(line)
        if not m:
            continue

        lhs_raw, rhs_raw = m.groups()
        lhs_raw = lhs_raw.strip()

        # canonicalize LHS: for escaped identifiers, strip trailing whitespace
        lhs = lhs_raw

        # find all signal tokens on RHS
        rhs_signals = signal_re.findall(rhs_raw)

        # filter out things that are obviously not nets if needed
        # (here we assume every match is a net, since we only have &, |, ~, etc.)
        for s in rhs_signals:
            # add nodes just in case
            G.add_node(s)
            G.add_node(lhs)
            # edge from source net to destination net
            G.add_edge(s, lhs)

    return G

# Example usage:
if __name__ == "__main__":
    with open("top.v", "r") as f:
        verilog_text = f.read()

    G = parse_verilog_to_dag(verilog_text)

    print("Number of nodes:", G.number_of_nodes())
    print("Number of edges:", G.number_of_edges())

    # Primary inputs = nodes with no predecessors
    primary_inputs = [n for n in G.nodes if G.in_degree(n) == 0]
    # Primary outputs = nodes with no successors (often \f[*] and cOut)
    primary_outputs = [n for n in G.nodes if G.out_degree(n) == 0]

    print("Primary inputs (first 10):", primary_inputs[:10])
    print("Primary outputs:", primary_outputs)


def build_graph_from_verilog(netlist_path: str):
    """
    Parse a Verilog netlist file and return a graph with startpoints and endpoints.
    
    Args:
        netlist_path: Path to the Verilog file
        
    Returns:
        G: nx.DiGraph with delay attributes on edges (defaults to 0.0 if not specified)
        startpoints: List of nodes with no predecessors (primary inputs)
        endpoints: List of nodes with no successors (primary outputs)
    """
    with open(netlist_path, "r") as f:
        verilog_text = f.read()
    
    G = parse_verilog_to_dag(verilog_text)
    
    # Add default delay of 0.0 to all edges if not present
    for u, v in G.edges():
        if "delay" not in G[u][v]:
            G[u][v]["delay"] = 0.0
    
    # Primary inputs = nodes with no predecessors (startpoints)
    startpoints = [n for n in G.nodes() if G.in_degree(n) == 0]
    # Primary outputs = nodes with no successors (endpoints)
    endpoints = [n for n in G.nodes() if G.out_degree(n) == 0]
    
    return G, startpoints, endpoints
