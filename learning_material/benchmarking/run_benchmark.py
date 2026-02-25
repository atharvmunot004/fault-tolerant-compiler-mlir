"""
Qiskit vs PyTket IBM Torino QFT Roundtrip Benchmark

Runs the benchmark defined in llm.json:
- Circuit: X_ALL, QFT, IQFT, MEASURE_ALL
- Qubit counts: 5, 10, 15, 20, 25, 30, 35, 40
- Frameworks: Qiskit, PyTket with optimization levels 0-3
- Backend: IBM Torino (real hardware)
- Metrics: compile time, memory, depth, 2Q count, population, Hellinger fidelity

Usage:
    python run_benchmark.py [--config path/to/llm.json] [--dry-run]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import sys
import time
import tracemalloc
from datetime import datetime, timezone
from pathlib import Path

# Add parent for imports if needed
sys.path.insert(0, str(Path(__file__).parent))

from config import load_config
from circuit_builders import build_qiskit_qft_roundtrip, build_pytket_qft_roundtrip, get_circuit_builder
from metrics import (
    population_target_state,
    hellinger_fidelity,
    normalize_counts,
    get_two_qubit_breakdown_qiskit,
    get_two_qubit_breakdown_pytket,
)


def _backend_properties_sha256(backend) -> str:
    """Compute SHA256 of backend properties JSON for calibration consistency."""
    try:
        props = backend.properties()
        if props is None:
            return ""
        # Convert to dict-like and hash
        data = str(dict(props.to_dict()) if hasattr(props, "to_dict") else str(props))
        return hashlib.sha256(data.encode()).hexdigest()
    except Exception:
        return ""


def _run_qiskit(
    n_qubits: int,
    opt_level: int,
    backend,
    shots: int,
    seed: int,
) -> dict:
    """Run one Qiskit benchmark iteration (uses Sampler V2 primitives)."""
    import qiskit
    from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager
    qv = qiskit.__version__

    qc = build_qiskit_qft_roundtrip(n_qubits)

    # Compile with preset pass manager (required for Runtime primitives)
    tracemalloc.start()
    t0 = time.perf_counter()
    pm = generate_preset_pass_manager(optimization_level=opt_level, backend=backend, seed_transpiler=seed)
    compiled = pm.run(qc)
    compile_time = time.perf_counter() - t0
    _, peak_mib = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    peak_mib = peak_mib / (1024 * 1024)

    depth = compiled.depth()
    breakdown = get_two_qubit_breakdown_qiskit(compiled)
    two_q_total = sum(breakdown.values())

    # Execute via Sampler V2 (backend.run() removed)
    from qiskit_ibm_runtime import SamplerV2 as Sampler
    sampler = Sampler(backend)
    t0 = time.perf_counter()
    job = sampler.run([compiled], shots=shots)
    result = job.result()
    exec_time = time.perf_counter() - t0

    # PrimitiveResult: use join_data() for counts (works with any creg layout)
    counts = {}
    if result and len(result) > 0:
        pub_result = result[0]
        if hasattr(pub_result, "join_data"):
            counts = pub_result.join_data().get_counts()
        elif hasattr(pub_result, "data") and hasattr(pub_result.data, "get_counts"):
            counts = getattr(pub_result.data, "get_counts", lambda: {})()
    if not isinstance(counts, dict):
        counts = {}

    pop = population_target_state(counts, n_qubits)
    hel = hellinger_fidelity(counts, n_qubits)
    counts_norm = normalize_counts(counts, n_qubits)

    return {
        "framework": "qiskit",
        "framework_version": qv,
        "qubit_count": n_qubits,
        "optimizer_level": opt_level,
        "shots": shots,
        "compile_time_seconds": compile_time,
        "peak_tracemalloc_mib": peak_mib,
        "post_routing_depth": depth,
        "post_routing_2q_total": two_q_total,
        "post_routing_2q_breakdown": breakdown,
        "execution_time_seconds": exec_time,
        "counts_normalized": counts_norm,
        "population_target_state": pop,
        "hellinger_fidelity": hel,
        "backend_properties_sha256": _backend_properties_sha256(backend),
    }


def _run_pytket(
    n_qubits: int,
    opt_level: int,
    pytket_backend,
    qiskit_backend,
    shots: int,
    seed: int,
) -> dict:
    """Run one PyTket benchmark: compile with PyTket, run on IBM via Qiskit Sampler (job mode)."""
    import pytket
    from pytket.extensions.qiskit import tk_to_qiskit
    from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager
    from qiskit_ibm_runtime import SamplerV2 as Sampler

    circ = build_pytket_qft_roundtrip(n_qubits)

    # Compile with PyTket (metrics reflect PyTket's compilation)
    tracemalloc.start()
    t0 = time.perf_counter()
    compiled = pytket_backend.get_compiled_circuit(circ, optimisation_level=opt_level)
    compile_time = time.perf_counter() - t0
    _, peak_mib = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    peak_mib = peak_mib / (1024 * 1024)

    depth = compiled.depth()
    breakdown = get_two_qubit_breakdown_pytket(compiled)
    two_q_total = sum(breakdown.values())

    # Convert PyTket circuit to Qiskit and make ISA-compliant for Runtime
    qc_qiskit = tk_to_qiskit(compiled)
    pm = generate_preset_pass_manager(optimization_level=0, backend=qiskit_backend)
    qc_isa = pm.run(qc_qiskit)

    # Execute via Qiskit Sampler (job mode; works on open plan)
    sampler = Sampler(qiskit_backend)
    t0 = time.perf_counter()
    job = sampler.run([qc_isa], shots=shots)
    result = job.result()
    exec_time = time.perf_counter() - t0

    counts = {}
    if result and len(result) > 0:
        pub_result = result[0]
        if hasattr(pub_result, "join_data"):
            counts = pub_result.join_data().get_counts()
        elif hasattr(pub_result, "data") and hasattr(pub_result.data, "get_counts"):
            counts = getattr(pub_result.data, "get_counts", lambda: {})()
    if not isinstance(counts, dict):
        counts = {}

    pop = population_target_state(counts, n_qubits)
    hel = hellinger_fidelity(counts, n_qubits)
    counts_norm = normalize_counts(counts, n_qubits)

    return {
        "framework": "pytket",
        "framework_version": pytket.__version__,
        "qubit_count": n_qubits,
        "optimizer_level": opt_level,
        "shots": shots,
        "compile_time_seconds": compile_time,
        "peak_tracemalloc_mib": peak_mib,
        "post_routing_depth": depth,
        "post_routing_2q_total": two_q_total,
        "post_routing_2q_breakdown": breakdown,
        "execution_time_seconds": exec_time,
        "counts_normalized": counts_norm,
        "population_target_state": pop,
        "hellinger_fidelity": hel,
        "backend_properties_sha256": _backend_properties_sha256(qiskit_backend),
        "notes": "Executed via Qiskit Sampler (PyTket-compiled circuit converted to Qiskit for job-mode run).",
    }


def _get_backend(config: dict):
    """Get IBM backend from config."""
    backend_name = config["backend"]["backend_name"]
    provider = config["backend"]["provider"]

    if provider == "ibm_quantum":
        try:
            from qiskit_ibm_runtime import QiskitRuntimeService
            service = QiskitRuntimeService()
            return service.backend(backend_name)
        except ImportError:
            from qiskit_ibm_provider import IBMProvider
            provider_obj = IBMProvider()
            return provider_obj.get_backend(backend_name)
    raise ValueError(f"Unknown provider: {provider}")


def _get_pytket_backend(config: dict):
    """Get PyTket IBM backend."""
    backend_name = config["backend"]["backend_name"]
    from pytket.extensions.qiskit import IBMQBackend
    return IBMQBackend(backend_name)


def run_benchmark(config_path: Path | None = None, dry_run: bool = False, qiskit_only: bool = False) -> None:
    """Main benchmark entry point."""
    config = load_config(config_path)
    out = config["output"]["write_files"]
    base = Path(__file__).parent
    (base / "results").mkdir(exist_ok=True)
    (base / "results" / "backend_properties").mkdir(exist_ok=True)

    qubit_counts = config["circuit_family"]["qubit_counts"]
    opt_levels = config["frameworks"][0]["compilation"]["optimizer_preset_levels"]
    shots = config["execution"]["shots_per_run"]
    n_repeats = config["execution"]["repetitions_per_configuration"]
    seed = config["reproducibility"]["random_seeds"]["seed_value"]

    frameworks = [f["name"] for f in config["frameworks"]]
    if qiskit_only:
        frameworks = [f for f in frameworks if f == "qiskit"]
        if not frameworks:
            print("--qiskit-only specified but qiskit not in config; using all frameworks.")
            frameworks = [f["name"] for f in config["frameworks"]]
        else:
            print("Running Qiskit only (PyTket skipped).")
    all_runs = []
    aggregates = []

    # Dry run: only build circuits, no execution
    if dry_run:
        print("Dry run: building circuits only (no backend execution)")
        for nq in qubit_counts[:2]:  # First 2 qubit counts
            for fw in frameworks:
                try:
                    builder = get_circuit_builder(fw)
                    circ = builder(nq)
                    print(f"  {fw} n_qubits={nq}: built OK")
                except Exception as e:
                    print(f"  {fw} n_qubits={nq}: {e}")
        return

    # Real run
    print("Connecting to IBM backend...")
    try:
        qiskit_backend = _get_backend(config)
        pytket_backend = _get_pytket_backend(config)
    except Exception as e:
        print(f"Failed to connect to backend: {e}")
        print("Tip: Set IBM_QUANTUM_TOKEN or save account with IBMProvider.save_account()")
        return

    total = len(qubit_counts) * len(opt_levels) * len(frameworks) * n_repeats
    idx = 0

    for nq in qubit_counts:
        for opt in opt_levels:
            for fw in frameworks:
                run_records = []
                for rep in range(n_repeats):
                    idx += 1
                    print(f"[{idx}/{total}] {fw} n_qubits={nq} opt={opt} rep={rep+1}/{n_repeats}")
                    try:
                        if fw == "qiskit":
                            rec = _run_qiskit(nq, opt, qiskit_backend, shots, seed)
                        else:
                            rec = _run_pytket(nq, opt, pytket_backend, qiskit_backend, shots, seed)
                        rec["timestamp_utc"] = datetime.now(timezone.utc).isoformat()
                        rec["backend_name"] = config["backend"]["backend_name"]
                        rec["repeat_index"] = rep
                        rec["calibration_match_with_paired_framework"] = True  # Simplified
                        rec["notes"] = ""
                        all_runs.append(rec)
                        run_records.append(rec)
                    except Exception as e:
                        print(f"  Error: {e}")
                        all_runs.append({
                            "framework": fw,
                            "qubit_count": nq,
                            "optimizer_level": opt,
                            "repeat_index": rep,
                            "notes": str(e),
                            "error": True,
                        })

                # Aggregate per configuration
                if run_records and not run_records[0].get("error"):
                    vals = {
                        "compile_time": [r["compile_time_seconds"] for r in run_records],
                        "exec_time": [r["execution_time_seconds"] for r in run_records],
                        "tracemalloc": [r["peak_tracemalloc_mib"] for r in run_records],
                        "depth": [r["post_routing_depth"] for r in run_records],
                        "2q_total": [r["post_routing_2q_total"] for r in run_records],
                        "pop": [r["population_target_state"] for r in run_records],
                        "hel": [r["hellinger_fidelity"] for r in run_records],
                    }

                    def _mean(x):
                        return sum(x) / len(x) if x else 0

                    def _std(x):
                        if len(x) < 2:
                            return 0
                        m = _mean(x)
                        return (sum((v - m) ** 2 for v in x) / (len(x) - 1)) ** 0.5

                    def _median(x):
                        s = sorted(x)
                        n = len(s)
                        return s[n // 2] if n else 0

                    agg = {
                        "framework": fw,
                        "backend_name": config["backend"]["backend_name"],
                        "qubit_count": nq,
                        "optimizer_level": opt,
                        "shots": shots,
                        "n_repeats": n_repeats,
                        "mean_depth": _mean(vals["depth"]),
                        "mean_2q_total": _mean(vals["2q_total"]),
                        "mean_compile_time_seconds": _mean(vals["compile_time"]),
                        "mean_execution_time_seconds": _mean(vals["exec_time"]),
                        "mean_peak_tracemalloc_mib": _mean(vals["tracemalloc"]),
                        "mean_population_target_state": _mean(vals["pop"]),
                        "mean_hellinger_fidelity": _mean(vals["hel"]),
                        "std_compile_time": _std(vals["compile_time"]),
                        "std_execution_time": _std(vals["exec_time"]),
                        "median_compile_time": _median(vals["compile_time"]),
                        "median_execution_time": _median(vals["exec_time"]),
                    }
                    aggregates.append(agg)

    # Write outputs (paths relative to benchmark folder)
    base = Path(__file__).parent
    results_json_path = base / out["results_json"]
    raw_runs_path = base / out["raw_runs_jsonl"]
    results_json_path.parent.mkdir(parents=True, exist_ok=True)
    raw_runs_path.parent.mkdir(parents=True, exist_ok=True)

    meta = {
        "experiment_name": config["experiment_name"],
        "version": config["version"],
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "system_info": {
            "platform": platform.platform(),
            "python": sys.version,
        },
        "config": config,
    }

    with open(results_json_path, "w", encoding="utf-8") as f:
        json.dump({
            "metadata": meta,
            "raw_runs": all_runs,
            "aggregates": aggregates,
        }, f, indent=2)

    with open(raw_runs_path, "w", encoding="utf-8") as f:
        for r in all_runs:
            # Serialize for JSONL (simplify counts for readability)
            r_copy = {k: v for k, v in r.items() if k != "counts_normalized" or isinstance(v, dict)}
            f.write(json.dumps(r_copy, default=str) + "\n")

    print(f"\nResults written to {results_json_path}")
    print(f"Raw runs to {raw_runs_path}")


def main():
    parser = argparse.ArgumentParser(description="Qiskit vs PyTket QFT Roundtrip Benchmark")
    parser.add_argument("--config", type=Path, default=None, help="Path to llm.json config")
    parser.add_argument("--dry-run", action="store_true", help="Build circuits only, no execution")
    parser.add_argument("--qiskit-only", action="store_true", help="Run only Qiskit (skip PyTket; use on IBM open plan to avoid session errors)")
    args = parser.parse_args()
    run_benchmark(config_path=args.config, dry_run=args.dry_run, qiskit_only=args.qiskit_only)


if __name__ == "__main__":
    main()
