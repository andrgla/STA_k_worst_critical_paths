import re
import networkx as nx

#added delay between edges to simulate the delay of the gates
GATE_DELAY = {
    "ASSIGN": 0.001,   # fake "wire/assign" delay (simple pass-through)
    "COMB_ALWAYS": 0.02,
    "NOT": 0.01,
    "AND": 0.02,
    "OR": 0.04,
    "XOR": 0.03,
    "NAND": 0.025,    # Slightly more than AND due to inversion
    "NOR": 0.045,     # Slightly more than OR due to inversion
    "MUX2_NOT": 0.05,
    "MUX2_AND": 0.07,
    "MUX2_OR": 0.08,
}

def detect_gate_type(expression):
    """
    Analyze a Verilog expression to determine the gate type.
    
    Args:
        expression: String containing the RHS of an assignment
        
    Returns:
        Gate type string (e.g., "NOT", "AND", "OR", "XOR", "NAND", "NOR", "ASSIGN")
    """
    expr = expression.strip()
    
    # Count operators to understand expression complexity
    and_count = expr.count('&')
    or_count = expr.count('|')
    xor_count = expr.count('^')
    not_count = expr.count('~')
    
    # Check for simple NOT: ~signal (no operators except ~)
    # Pattern: starts with ~, no &, |, ^ operators
    if expr.startswith('~') and and_count == 0 and or_count == 0 and xor_count == 0:
        return "NOT"
    
    # Pattern to match negated signals (handles escaped identifiers like \signal[0])
    # Matches: ~signal, ~\signal[0], etc.
    negated_signal_pattern = r'~\s*(?:\\[^\s&|^]+|[A-Za-z_]\w*(?:\[\d+\])?)'
    
    # Check for NOR pattern: ~a & ~b (De Morgan: ~(a | b))
    # Pattern: multiple negated terms ANDed together, no OR operators
    if and_count > 0 and or_count == 0 and xor_count == 0 and not_count >= 2:
        # Find all negated signals
        negated_signals = re.findall(negated_signal_pattern, expr)
        # If we have 2+ negated signals and they're all connected by AND operators
        # (not mixed with non-negated signals), it's likely a NOR
        if len(negated_signals) >= 2:
            # Count total signals (negated and non-negated)
            # Pattern for any signal (negated or not)
            all_signals_pattern = r'(?:~\s*)?(?:\\[^\s&|^]+|[A-Za-z_]\w*(?:\[\d+\])?)'
            all_signals = re.findall(all_signals_pattern, expr)
            # If all signals are negated, it's a NOR
            if len(negated_signals) == len(all_signals):
                return "NOR"
    
    # Check for NAND pattern: ~a | ~b (De Morgan: ~(a & b))
    # Pattern: multiple negated terms ORed together, no AND operators
    if or_count > 0 and and_count == 0 and xor_count == 0 and not_count >= 2:
        negated_signals = re.findall(negated_signal_pattern, expr)
        if len(negated_signals) >= 2:
            all_signals_pattern = r'(?:~\s*)?(?:\\[^\s&|^]+|[A-Za-z_]\w*(?:\[\d+\])?)'
            all_signals = re.findall(all_signals_pattern, expr)
            # If all signals are negated, it's a NAND
            if len(negated_signals) == len(all_signals):
                return "NAND"
    
    # Check for XOR: a ^ b (no AND, no OR)
    if xor_count > 0 and and_count == 0 and or_count == 0:
        return "XOR"
    
    # Check for AND: a & b (no OR, no XOR)
    # This includes cases like a & ~b (AND with one inverted input)
    if and_count > 0 and or_count == 0 and xor_count == 0:
        return "AND"
    
    # Check for OR: a | b (no AND, no XOR)
    # This includes cases like a | ~b (OR with one inverted input)
    if or_count > 0 and and_count == 0 and xor_count == 0:
        return "OR"
    
    # Mixed operators or complex expression - default to ASSIGN
    # This handles cases like (a & b) | c which would need multiple gates
    return "ASSIGN"

def parse_verilog_to_dag(verilog_text):
    """
    Build a combinational DAG from a (possibly sequential) Verilog description.

    - Continuous assignments (`assign lhs = rhs;`) are treated as combinational edges.
    - Combinational always blocks (`always @(*)` or `always @*`) are treated similarly:
      assignments inside them create edges from RHS signals to LHS.
    - Clocked always blocks (`always @(posedge ...)` / `negedge`) are used to detect
      state registers:
        * The LHS of non-blocking assignments (<=) in such blocks are treated as
          registered outputs (Q signals).
        * The RHS signals of those assignments are treated as D-input nets.
      We intentionally do NOT add edges from RHS to LHS for these assignments, because
      they represent a cycle-to-cycle transfer (flops), not combinational logic.

    Returns:
        G: nx.DiGraph
        ff_q_nets: set of signals that are clocked registers (Q nets)
        d_nets: set of signals that drive those registers (D nets)
    """
    # Graph where nodes are net names (strings), edges are data dependencies
    G = nx.DiGraph()

    # Regex for "assign lhs = rhs;"
    assign_re = re.compile(r'\s*assign\s+(.+?)\s*=\s*(.+?);')

    # Regex for signal names:
    #  - escaped identifiers: \something_until_whitespace  (e.g. "\a[0]")
    #  - normal identifiers:   a123, n386, f[0], etc.
    signal_re = re.compile(
        r'(\\[^\s,;]+|[A-Za-z_]\w*(?:\[\d+\])?)'
    )

    # Procedural assignments inside always blocks: "lhs = rhs;" or "lhs <= rhs;"
    proc_assign_re = re.compile(
        r'\s*([A-Za-z_]\w*(?:\[\d+\])?)\s*(<=|=)\s*(.+?);'
    )

    # Regex for MUX2 module instantiation: "MUX2 instance_name ( .A(signalA), .B(signalB), .S(signalS), .Y(outputY) );"
    # This matches patterns like: MUX2 mux_acc0 ( .A(\acc[0] ), .B(\total[0] ), .S(n0), .Y(n10) );
    # Also handles: MUX2 mux_rst0 ( .A(n10), .B(1'b0), .S(reset_acc), .Y(\acc_next[0] ) );
    mux2_re = re.compile(
        r'\s*MUX2\s+\w+\s*\(\s*\.A\s*\(\s*([^)]+)\s*\)\s*,\s*\.B\s*\(\s*([^)]+)\s*\)\s*,\s*\.S\s*\(\s*([^)]+)\s*\)\s*,\s*\.Y\s*\(\s*([^)]+)\s*\)\s*\);'
    )

    ff_q_nets = set()  # registers updated in clocked always blocks
    d_nets = set()     # nets that drive those registers (D inputs)

    in_seq_always = False   # always @(posedge/negedge ...)
    in_comb_always = False  # always @(*) or always @*
    
    # Counter for generating unique intermediate signal names for MUX2 expansions
    mux2_counter = 0

    for line in verilog_text.splitlines():
        stripped = line.strip()

        # Detect entry into always blocks
        if stripped.startswith("always"):
            # Very simple heuristic: clocked vs combinational
            if "posedge" in stripped or "negedge" in stripped:
                in_seq_always = True
                in_comb_always = False
            else:
                # e.g. "always @(*)" or "always @*"
                in_comb_always = True
                in_seq_always = False
            continue

        # Detect end of an always block
        if in_seq_always or in_comb_always:
            if stripped.startswith("end"):
                in_seq_always = False
                in_comb_always = False
                continue

        # Inside a clocked always block: detect state registers
        if in_seq_always:
            m = proc_assign_re.match(line)
            if m:
                lhs, op, rhs_raw = m.groups()
                lhs = lhs.strip()
                # Treat LHS as a registered signal (Q net)
                ff_q_nets.add(lhs)
                G.add_node(lhs)

                # RHS signals are the D-inputs that feed the reg
                rhs_signals = signal_re.findall(rhs_raw)
                for s in rhs_signals:
                    s = s.strip()
                    if not s:
                        continue
                    d_nets.add(s)
                    G.add_node(s)
            # Do NOT add combinational edges from rhs -> lhs here
            # (they are across clock cycles)
            continue

        # Inside a combinational always block: build combinational edges
        if in_comb_always:
            m = proc_assign_re.match(line)
            if m:
                lhs, op, rhs_raw = m.groups()
                lhs = lhs.strip()
                rhs_raw = rhs_raw.strip()
                
                # Detect gate type from expression
                gate_type = detect_gate_type(rhs_raw)
                delay = GATE_DELAY.get(gate_type, GATE_DELAY["COMB_ALWAYS"])
                
                rhs_signals = signal_re.findall(rhs_raw)
                for s in rhs_signals:
                    s = s.strip()
                    if not s:
                        continue
                    G.add_node(s)
                    G.add_node(lhs)
                    G.add_edge(s, lhs, delay=delay)
            continue

        # Handle MUX2 module instantiations: expand to gate-level logic
        # MUX2 logic: Y = S ? B : A
        # Gate-level: nS = ~S, t0 = A & nS, t1 = B & S, Y = t0 | t1
        m = mux2_re.match(line)
        if m:
            signal_a, signal_b, signal_s, signal_y = m.groups()
            signal_a = signal_a.strip()
            signal_b = signal_b.strip()
            signal_s = signal_s.strip()
            signal_y = signal_y.strip()
            
            # Generate unique intermediate signal names for this MUX2 instance
            mux2_counter += 1
            nS_name = f"mux2_nS_{mux2_counter}"
            t0_name = f"mux2_t0_{mux2_counter}"
            t1_name = f"mux2_t1_{mux2_counter}"
            
            # Add all nodes
            G.add_node(signal_a)
            G.add_node(signal_b)
            G.add_node(signal_s)
            G.add_node(nS_name)
            G.add_node(t0_name)
            G.add_node(t1_name)
            G.add_node(signal_y)
            
            # NOT gate: S -> nS
            G.add_edge(signal_s, nS_name, delay=GATE_DELAY["MUX2_NOT"])
            
            # AND gate: A, nS -> t0
            G.add_edge(signal_a, t0_name, delay=GATE_DELAY["MUX2_AND"])
            G.add_edge(nS_name, t0_name, delay=GATE_DELAY["MUX2_AND"])
            
            # AND gate: B, S -> t1
            G.add_edge(signal_b, t1_name, delay=GATE_DELAY["MUX2_AND"])
            G.add_edge(signal_s, t1_name, delay=GATE_DELAY["MUX2_AND"])
            
            # OR gate: t0, t1 -> Y
            G.add_edge(t0_name, signal_y, delay=GATE_DELAY["MUX2_OR"])
            G.add_edge(t1_name, signal_y, delay=GATE_DELAY["MUX2_OR"])
            
            continue

        # Outside any always-block: handle continuous assignments
        m = assign_re.match(line)
        if m:
            lhs_raw, rhs_raw = m.groups()
            lhs = lhs_raw.strip()
            rhs_raw = rhs_raw.strip()

            # Detect gate type from expression
            gate_type = detect_gate_type(rhs_raw)
            delay = GATE_DELAY.get(gate_type, GATE_DELAY["ASSIGN"])

            rhs_signals = signal_re.findall(rhs_raw)
            for s in rhs_signals:
                s = s.strip()
                if not s:
                    continue
                G.add_node(s)
                G.add_node(lhs)
                G.add_edge(s, lhs, delay=delay)

    return G, ff_q_nets, d_nets

# Example usage:
if __name__ == "__main__":
    with open("top.v", "r") as f:
        verilog_text = f.read()

    G, ff_q_nets, d_nets = parse_verilog_to_dag(verilog_text)

    print("Number of nodes:", G.number_of_nodes())
    print("Number of edges:", G.number_of_edges())

    # Primary inputs = nodes with no predecessors
    primary_inputs = [n for n in G.nodes if G.in_degree(n) == 0]
    # Primary outputs = nodes with no successors
    primary_outputs = [n for n in G.nodes if G.out_degree(n) == 0]

    print("Primary inputs (first 10):", primary_inputs[:10])
    print("Primary outputs:", primary_outputs)
    print("Detected FF Q nets (state registers):", sorted(ff_q_nets))
    print("Detected FF D nets:", sorted(d_nets))


def build_graph_from_verilog(netlist_path: str):
    """
    Parse a Verilog netlist file and return a graph with startpoints and endpoints.

    Args:
        netlist_path: Path to the Verilog file

    Returns:
        G: nx.DiGraph with delay attributes on edges
        startpoints: List of nodes treated as timing startpoints
        endpoints: List of nodes treated as timing endpoints
    """
    with open(netlist_path, "r") as f:
        verilog_text = f.read()

    G, ff_q_nets, d_nets = parse_verilog_to_dag(verilog_text)

    # Ensure every edge has a delay attribute
    for u, v in G.edges():
        if "delay" not in G[u][v]:
            G[u][v]["delay"] = GATE_DELAY["ASSIGN"]

    # Combinational start/end based on graph structure
    comb_start = {n for n in G.nodes() if G.in_degree(n) == 0}
    comb_end = {n for n in G.nodes() if G.out_degree(n) == 0}

    # Final startpoints/endpoints:
    #  - Startpoints: primary-like sources + FF Q nets (state registers)
    #  - Endpoints: primary-like sinks + FF D nets (inputs to registers)
    startpoints = sorted(comb_start.union(ff_q_nets))
    endpoints = sorted(comb_end.union(d_nets))

    return G, startpoints, endpoints
