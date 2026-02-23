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

**Full run** (real hardware):

```bash
python run_benchmark.py
```

**Custom config**:

```bash
python run_benchmark.py --config path/to/llm.json
```

## Output

- `results/benchmark_results.json` – Full results with metadata and aggregates
- `results/raw_runs.jsonl` – One JSON object per run
- `results/backend_properties/` – Backend property snapshots (when enabled)

## Files

| File | Purpose |
|------|---------|
| `llm.json` | Benchmark specification |
| `config.py` | Config loader |
| `circuit_builders.py` | QFT roundtrip circuits (Qiskit, PyTket) |
| `metrics.py` | Population, Hellinger fidelity, 2Q breakdown |
| `run_benchmark.py` | Main entry point |
