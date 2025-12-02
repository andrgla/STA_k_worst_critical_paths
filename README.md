# STA (Static Timing Analysis) Tool 🌅

A Python package for performing static timing analysis on Verilog netlists, including finding k worst critical paths with gate-level delay modeling.

## Structure

```
STA_k_worst_critical_paths/
├── sta/                          # Python package
│   ├── __init__.py
│   ├── run_sta.py                # Main STA functions and visualization
│   ├── animate_khan.py           # Khan's algorithm animation
│   ├── backwards.py              # Backward required time computation
│   ├── forwards.py               # Forward arrival time computation
│   ├── Khan.py                   # Topological sort implementation
│   ├── slack_computation.py      # Slack calculation
│   ├── verilog_parcer.py         # Verilog parser with gate type detection
│   ├── visualize_start_and_end_points.py  # Circuit-style visualization
│   ├── runtime_plot.py           # Runtime analysis plotting
│   └── plot_relative.py          # Normalized runtime plotting
├── benches/                      # Verilog benchmarks
│   ├── Test_circuit_adder.v
│   ├── Test_circuit_bar.v
│   ├── Test_circuit_ctrl.v
│   ├── Test_circuit_priority.v
│   ├── Test_circuit_sequential.v
│   └── Test_circuit_sqrt.v
├── requirements.txt
└── README.md
```

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### As a package

```python
from sta.verilog_parcer import build_graph_from_verilog
from sta.run_sta import run_sta, find_k_critical_paths

# Load a Verilog netlist
G, startpoints, endpoints = build_graph_from_verilog("benches/Test_circuit_adder.v")

# Run STA
Tclk = 2.5
setup = 0.05
clock_to_q = 0.06

sta_res = run_sta(
    G,
    startpoints=startpoints,
    endpoints=endpoints,
    Tclk=Tclk,
    setup=setup,
    clock_to_q=clock_to_q,
)

print(f"WNS = {sta_res['WNS']}, TNS = {sta_res['TNS']}")

# Find k worst critical paths
critical_paths = find_k_critical_paths(
    G,
    startpoints=startpoints,
    endpoints=endpoints,
    Tclk=Tclk,
    setup=setup,
    clock_to_q=clock_to_q,
    k=5,
)
```

### As a script

```bash
python -m sta.run_sta
```

## Features

- **Verilog netlist parsing** with automatic gate type detection
- **Gate-level delay modeling** with realistic delays for different gate types
- **Forward arrival time (AT)** computation
- **Backward required time (RT)** computation
- **Slack calculation** (WNS, TNS)
- **K worst critical path extraction** (edge-disjoint paths)
- **Interactive visualization** with full spectrum color coding
- **Khan's algorithm animation** for topological sorting
- **Runtime analysis** tools for performance benchmarking

## Gate Type Detection

The parser automatically detects gate types from Verilog expressions and assigns appropriate delays:

- **NOT gates**: `~signal`
- **AND gates**: `a & b`, `a & ~b`
- **OR gates**: `a | b`, `a | ~b`
- **XOR gates**: `a ^ b`
- **NOR gates**: `~a & ~b` (De Morgan's law)
- **NAND gates**: `~a | ~b` (De Morgan's law)
- **MUX2 modules**: Expanded to gate-level logic (NOT, AND, OR)

## Gate Delays

The parser uses configurable gate delays defined in `verilog_parcer.py`:

- `ASSIGN`: 0.001 ns (wire/assign delay)
- `COMB_ALWAYS`: 0.03 ns
- `NOT`: 0.01 ns
- `AND`: 0.02 ns
- `OR`: 0.04 ns
- `XOR`: 0.03 ns
- `NAND`: 0.025 ns
- `NOR`: 0.045 ns
- `MUX2_NOT`: 0.05 ns
- `MUX2_AND`: 0.09 ns
- `MUX2_OR`: 0.08 ns

## Visualization

The tool provides several visualization options:

1. **Critical Path Visualization**: Shows k worst critical paths with full spectrum colors (red → yellow → green → cyan → blue → purple)
2. **Khan's Algorithm Animation**: Animated visualization of topological sorting
3. **Circuit-style Layout**: Left-to-right layout with startpoints and endpoints clearly marked

## Runtime Analysis

The project includes tools for analyzing algorithm performance:

- `runtime_plot.py`: Plots runtime vs. k for different benchmarks
- `plot_relative.py`: Normalized runtime analysis (runtime per graph element)

