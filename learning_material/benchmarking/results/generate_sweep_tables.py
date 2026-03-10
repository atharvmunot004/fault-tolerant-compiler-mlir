"""
Generate sweep results table for benchmark_report.tex.
Reads benchmark_results_opt_qubit_sweep.json and writes results/sweep_tables.tex.
Run after: python run_benchmark.py --config llm_opt_qubit_sweep.json
"""
import json
from pathlib import Path

RESULTS_DIR = Path(__file__).parent
JSON_PATH = RESULTS_DIR / "benchmark_results_opt_qubit_sweep.json"
OUT_PATH = RESULTS_DIR / "sweep_tables.tex"


def main():
    if not JSON_PATH.exists():
        print(f"Not found: {JSON_PATH}")
        print("Run: python run_benchmark.py --config llm_opt_qubit_sweep.json")
        return
    with open(JSON_PATH, encoding="utf-8") as f:
        data = json.load(f)
    aggregates = data.get("aggregates", [])
    if not aggregates:
        print("No aggregates in JSON.")
        return

    lines = [
        r"\begin{table}[htbp]",
        r"\centering",
        r"\caption{Aggregates: opt-level comparison and opt\_level=3 qubit sweep (mean).}",
        r"\label{tab:opt-qubit-sweep}",
        r"\resizebox{\textwidth}{!}{%",
        r"\begin{tabular}{llccccccc}",
        r"\toprule",
        r"Framework & \(n_{\mathrm{qubits}}\) & opt & mean depth & mean 2Q & mean compile (s) & mean exec (s) & mean pop. & mean \(F_H\) \\",
        r"\midrule",
    ]
    for a in aggregates:
        fw = a.get("framework", "")
        nq = a.get("qubit_count", "")
        opt = a.get("optimizer_level", "")
        depth = a.get("mean_depth", 0)
        twoq = a.get("mean_2q_total", 0)
        comp = a.get("mean_compile_time_seconds", 0)
        exec_t = a.get("mean_execution_time_seconds", 0)
        pop = a.get("mean_population_target_state", 0)
        fh = a.get("mean_hellinger_fidelity", 0)
        if isinstance(comp, float):
            comp = f"{comp:.3f}"
        if isinstance(exec_t, float):
            exec_t = f"{exec_t:.3f}"
        if isinstance(pop, float):
            pop = f"{pop:.4f}"
        if isinstance(fh, float):
            fh = f"{fh:.4f}"
        lines.append(f"{fw} & {nq} & {opt} & {depth} & {twoq} & {comp} & {exec_t} & {pop} & {fh} \\\\")
    lines.extend([
        r"\bottomrule",
        r"\end{tabular}%",
        r"}",
        r"\end{table}",
    ])
    OUT_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {OUT_PATH}")


if __name__ == "__main__":
    main()
