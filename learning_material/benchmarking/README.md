# Qiskit vs PyTket IBM Torino QFT Roundtrip Benchmark

Benchmark implementation based on `llm.json` specification.

## Overview

- **Circuit**: X on all qubits → QFT → inverse QFT → measure all
- **Expected output**: All-ones bitstring (|1...1⟩)
- **Qubit counts**: 5, 10, 15, 20, 25, 30, 35, 40
- **Frameworks**: Qiskit, PyTket (optimization levels 0–3)
- **Backend**: IBM Torino (real hardware)
- **Metrics**: Compile time, peak tracemalloc memory, depth, 2Q gate count, population, Hellinger fidelity

## Setup

```bash
pip install -r requirements.txt
```

Or install from project root:

```bash
pip install qiskit qiskit-ibm-runtime pytket pytket-qiskit
```

Configure IBM Quantum access (one of):

- Set `IBM_QUANTUM_TOKEN` environment variable
- Or: `IBMProvider.save_account(token="...")` (qiskit-ibm-provider)
- Or: `QiskitRuntimeService.save_account(channel="ibm_quantum", token="...")`

## Usage

**Dry run** (build circuits only, no backend):

```bash
python run_benchmark.py --dry-run
```

**Full run** (real hardware, default config):

```bash
python run_benchmark.py
```

**Opt-level comparison and opt_level=3 qubit sweep** (real hardware):

Compare optimization levels 0, 1, 2, 3 and measure opt_level=3 performance across qubit counts 10, 20, 30, 40, 50. Total: 5 qubit counts × 4 opt levels × 2 frameworks = 40 runs.

```bash
python run_benchmark.py --config llm_opt_qubit_sweep.json
```

Results: `results/benchmark_results_opt_qubit_sweep.json`, `results/raw_runs_opt_qubit_sweep.jsonl`.

**Quick run** (fewer runs, e.g. 5 qubits, opt 0 only):

```bash
python run_benchmark.py --config llm_quick.json
```

**Custom config**:

```bash
python run_benchmark.py --config path/to/llm.json
```

**Qiskit only** (skip PyTket; useful on IBM open plan):

```bash
python run_benchmark.py --config llm_quick.json --qiskit-only
```

## Output

- `results/benchmark_results.json` – Full results with metadata and aggregates
- `results/raw_runs.jsonl` – One JSON object per run
- `results/backend_properties/` – Backend property snapshots (when enabled)

## Files

| File | Purpose |
|------|---------|
| `llm.json` | Full benchmark specification |
| `llm_quick.json` | Quick run: 5 qubits, opt 0, 1 rep |
| `llm_opt_qubit_sweep.json` | Opt levels 0–3 and opt_level=3 qubit sweep (10–50 qubits) on real hardware |
| `config.py` | Config loader |
| `circuit_builders.py` | QFT roundtrip circuits (Qiskit, PyTket) |
| `metrics.py` | Population, Hellinger fidelity, 2Q breakdown |
| `run_benchmark.py` | Main entry point |
