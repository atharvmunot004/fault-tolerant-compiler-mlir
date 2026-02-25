"""
Generate benchmark figures for LaTeX report.
Reads benchmark_results_quick.json and writes PDFs to the same directory.
"""
import json
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib
matplotlib.use("Agg")

RESULTS_DIR = Path(__file__).parent
JSON_PATH = RESULTS_DIR / "benchmark_results_quick.json"

# LaTeX-friendly style
plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["DejaVu Serif"],
    "axes.labelsize": 10,
    "axes.titlesize": 11,
    "xtick.labelsize": 9,
    "ytick.labelsize": 9,
    "legend.fontsize": 9,
    "figure.dpi": 150,
})

FRAMEWORKS = ["Qiskit", "PyTket"]
COLORS = ["#1f77b4", "#ff7f0e"]  # blue, orange


def load_aggregates():
    with open(JSON_PATH, encoding="utf-8") as f:
        data = json.load(f)
    return data["aggregates"]


def main():
    agg = load_aggregates()
    if len(agg) != 2:
        raise SystemExit("Expected exactly 2 aggregates (Qiskit, PyTket).")
    qiskit = next(a for a in agg if a["framework"] == "qiskit")
    pytket = next(a for a in agg if a["framework"] == "pytket")

    x = [0, 1]
    width = 0.35

    # --- Figure 1: Runtime metrics (compile time, execution time) ---
    fig1, ax1 = plt.subplots(figsize=(4.2, 2.8))
    compile_vals = [qiskit["mean_compile_time_seconds"], pytket["mean_compile_time_seconds"]]
    exec_vals = [qiskit["mean_execution_time_seconds"], pytket["mean_execution_time_seconds"]]
    ax1.bar([x[0] - width/2, x[1] - width/2], compile_vals, width, label="Compile (s)", color=COLORS[0], edgecolor="black", linewidth=0.5)
    ax1.bar([x[0] + width/2, x[1] + width/2], exec_vals, width, label="Execution (s)", color=COLORS[1], edgecolor="black", linewidth=0.5)
    ax1.set_ylabel("Time (s)")
    ax1.set_xticks(x)
    ax1.set_xticklabels(FRAMEWORKS)
    ax1.set_title("Runtime metrics (mean)")
    ax1.legend(loc="upper right", frameon=True)
    ax1.set_ylim(0, None)
    fig1.tight_layout()
    fig1.savefig(RESULTS_DIR / "fig_runtime.pdf", bbox_inches="tight")
    plt.close(fig1)

    # --- Figure 2: Post-routing circuit metrics (depth, 2Q count) ---
    fig2, ax2 = plt.subplots(figsize=(4.2, 2.8))
    depth_vals = [qiskit["mean_depth"], pytket["mean_depth"]]
    twoq_vals = [qiskit["mean_2q_total"], pytket["mean_2q_total"]]
    ax2.bar([x[0] - width/2, x[1] - width/2], depth_vals, width, label="Depth", color=COLORS[0], edgecolor="black", linewidth=0.5)
    ax2.bar([x[0] + width/2, x[1] + width/2], twoq_vals, width, label="2Q gate count", color=COLORS[1], edgecolor="black", linewidth=0.5)
    ax2.set_ylabel("Count")
    ax2.set_xticks(x)
    ax2.set_xticklabels(FRAMEWORKS)
    ax2.set_title("Post-routing circuit metrics (mean)")
    ax2.legend(loc="upper right", frameon=True)
    ax2.set_ylim(0, None)
    fig2.tight_layout()
    fig2.savefig(RESULTS_DIR / "fig_circuit.pdf", bbox_inches="tight")
    plt.close(fig2)

    # --- Figure 3: Peak tracemalloc (MiB) ---
    fig3, ax3 = plt.subplots(figsize=(3.5, 2.5))
    mem_vals = [qiskit["mean_peak_tracemalloc_mib"], pytket["mean_peak_tracemalloc_mib"]]
    bars = ax3.bar(FRAMEWORKS, mem_vals, color=COLORS, edgecolor="black", linewidth=0.5)
    ax3.set_ylabel("Peak tracemalloc (MiB)")
    ax3.set_title("Compilation memory (mean)")
    ax3.set_ylim(0, None)
    for b in bars:
        h = b.get_height()
        ax3.annotate(f"{h:.2f}", xy=(b.get_x() + b.get_width()/2, h), xytext=(0, 4), textcoords="offset points", ha="center", fontsize=9)
    fig3.tight_layout()
    fig3.savefig(RESULTS_DIR / "fig_memory.pdf", bbox_inches="tight")
    plt.close(fig3)

    # --- Figure 4: Hardware result metrics (population target, Hellinger fidelity) ---
    fig4, ax4 = plt.subplots(figsize=(4.2, 2.8))
    pop_vals = [qiskit["mean_population_target_state"], pytket["mean_population_target_state"]]
    hel_vals = [qiskit["mean_hellinger_fidelity"], pytket["mean_hellinger_fidelity"]]
    ax4.bar([x[0] - width/2, x[1] - width/2], pop_vals, width, label="Population target state", color=COLORS[0], edgecolor="black", linewidth=0.5)
    ax4.bar([x[0] + width/2, x[1] + width/2], hel_vals, width, label="Hellinger fidelity", color=COLORS[1], edgecolor="black", linewidth=0.5)
    ax4.set_ylabel("Probability / Fidelity")
    ax4.set_xticks(x)
    ax4.set_xticklabels(FRAMEWORKS)
    ax4.set_title("Hardware result metrics (mean)")
    ax4.set_ylim(0, 1)
    ax4.legend(loc="upper right", frameon=True)
    fig4.tight_layout()
    fig4.savefig(RESULTS_DIR / "fig_hardware.pdf", bbox_inches="tight")
    plt.close(fig4)

    print("Figures written:", list(RESULTS_DIR.glob("fig_*.pdf")))


if __name__ == "__main__":
    main()
