# STA (Static Timing Analysis) Tool

A Python package for performing static timing analysis on Verilog netlists, including finding k worst critical paths.

## Structure

```
STA_k_worst_critical_paths/
├── sta/                    # Python package
│   ├── __init__.py
│   ├── run_sta.py          # Main STA functions
│   ├── animate_khan.py       # Khan's algorithm animation
│   ├── backwards.py         # Backward required time computation
│   ├── forwards.py          # Forward arrival time computation
│   ├── Khan.py              # Topological sort implementation
│   ├── slack_computation.py  # Slack calculation
│   └── Verilog_Parcer.py    # Verilog parser
├── benches/                 # Verilog benchmarks
│   ├── Test_circuit_adder.v
│   └── Test_circuit_sequential.v
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
from sta.Verilog_Parcer import build_graph_from_verilog
from sta.run_sta import run_sta, find_k_critical_paths

# Load a Verilog netlist
G, startpoints, endpoints = build_graph_from_verilog("benches/Test_circuit_sequential.v")

# Run STA
Tclk = 2.0
setup = 0.05
clock_to_q = 0.08

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

- Verilog netlist parsing with gate-level MUX2 expansion
- Forward arrival time (AT) computation
- Backward required time (RT) computation
- Slack calculation (WNS, TNS)
- K worst critical path extraction
- Khan's algorithm visualization

## Gate Delays

The parser supports configurable gate delays defined in `Verilog_Parcer.py`:

- `ASSIGN`: 0.03 ns (wire/assign delay)
- `NOT`: 0.03 ns
- `AND`: 0.06 ns
- `OR`: 0.07 ns
- `MUX2_NOT`: 0.02 ns
- `MUX2_AND`: 0.09 ns
- `MUX2_OR`: 0.08 ns

