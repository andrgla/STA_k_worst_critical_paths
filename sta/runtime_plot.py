import os
import sys
import time
from typing import List, Dict

import matplotlib.pyplot as plt

# Handle imports for both module and direct script execution
if __name__ == "__main__" or not __package__:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    if script_dir not in sys.path:
        sys.path.insert(0, script_dir)

# Import STA utilities
try:
    # When used as a module inside the sta package
    from .run_sta import find_k_critical_paths
except ImportError:
    # When run directly as a script
    from run_sta import find_k_critical_paths

# Import Verilog parser
try:
    from .verilog_parcer import build_graph_from_verilog
except ImportError:
    try:
        from verilog_parcer import build_graph_from_verilog
    except ImportError:
        from sta.verilog_parcer import build_graph_from_verilog


# Values of k to test
K_VALUES: List[int] = list(range(1, 6)) + list(range(7, 50, 5))

# Benchmarks to test (Verilog filenames without extension)
BENCHMARKS: Dict[str, str] = {
    "Test_circuit_adder": "Test_circuit_adder.v",
    "Test_circuit_priority": "Test_circuit_priority.v",
    "Test_circuit_sqrt": "Test_circuit_sqrt.v",
    "Test_circuit_ctrl": "Test_circuit_ctrl.v",
    "Test_circuit_bar": "Test_circuit_bar.v",
}

# Timing parameters (same as in run_sta main)
TCLK_DEFAULT = 2.5
SETUP_DEFAULT = 0.05
CLOCK_TO_Q_DEFAULT = 0.06


def measure_runtime_for_circuit(
    netlist_path: str,
    k_values: List[int],
    Tclk: float = TCLK_DEFAULT,
    setup: float = SETUP_DEFAULT,
    clock_to_q: float = CLOCK_TO_Q_DEFAULT,
) -> Dict[int, float]:
    """
    For a given Verilog netlist, measure runtime of find_k_critical_paths
    for different values of k.

    Returns a dict: k -> runtime_seconds.
    """
    G, startpoints, endpoints = build_graph_from_verilog(netlist_path)

    runtimes: Dict[int, float] = {}

    print(f"\n=== {os.path.basename(netlist_path)} ===")
    print(f"Nodes: {len(G.nodes())}, Edges: {len(G.edges())}")

    for k in k_values:
        start = time.perf_counter()
        _ = find_k_critical_paths(
            G,
            startpoints=startpoints,
            endpoints=endpoints,
            Tclk=Tclk,
            setup=setup,
            clock_to_q=clock_to_q,
            delay_attr="delay",
            k=k,
        )
        elapsed = time.perf_counter() - start
        runtimes[k] = elapsed
        print(f"k = {k:3d}: {elapsed:.6f} s")

    return runtimes


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    benches_dir = os.path.join(project_root, "benches")

    all_results: Dict[str, Dict[int, float]] = {}

    # Measure runtimes
    for bench_name, filename in BENCHMARKS.items():
        netlist_path = os.path.join(benches_dir, filename)

        if not os.path.isfile(netlist_path):
            print(f"Warning: netlist not found: {netlist_path}, skipping.")
            continue

        runtimes = measure_runtime_for_circuit(
            netlist_path,
            K_VALUES,
            Tclk=TCLK_DEFAULT,
            setup=SETUP_DEFAULT,
            clock_to_q=CLOCK_TO_Q_DEFAULT,
        )
        all_results[bench_name] = runtimes

    if not all_results:
        print("No benchmarks were successfully measured. Exiting.")
        return

    # Plot runtime vs k for each benchmark
    plt.figure()
    for bench_name, runtimes in all_results.items():
        ks = sorted(runtimes.keys())
        ys = [runtimes[k] for k in ks]
        plt.plot(ks, ys, marker="o", label=bench_name)

    plt.xlabel("k (number of critical paths)")
    plt.ylabel("Runtime (seconds)")
    plt.title("Runtime of critical path extraction vs k")
    plt.legend()
    plt.grid(True)

    # Save and show
    out_path = os.path.join(project_root, "runtime_vs_k.png")
    plt.savefig(out_path, dpi=300, bbox_inches="tight")
    print(f"\nSaved plot to {out_path}")

    plt.show()


if __name__ == "__main__":
    main()