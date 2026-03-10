"""
Generate figures for the opt-level and qubit-sweep section of the benchmark report.
If benchmark_results_opt_qubit_sweep.json exists, plots real data; otherwise creates placeholder PDFs.
Run from results/: python plot_sweep_figures.py
"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

RESULTS_DIR = Path(__file__).parent
JSON_PATH = RESULTS_DIR / "benchmark_results_opt_qubit_sweep.json"

plt.rcParams.update({
    "font.family": "serif",
    "axes.labelsize": 10,
    "axes.titlesize": 11,
    "figure.dpi": 150,
})

FRAMEWORKS = ["Qiskit", "PyTket"]
COLORS = ["#1f77b4", "#ff7f0e"]


def load_aggregates():
    if not JSON_PATH.exists():
        return None
    with open(JSON_PATH, encoding="utf-8") as f:
        data = json.load(f)
    return data.get("aggregates", [])


def fig_sweep_opt_levels(agg):
    """Opt-level comparison at a fixed qubit count (e.g. n_qubits=10)."""
    fig, ax = plt.subplots(figsize=(4.5, 3))
    if agg:
        # Use n_qubits=10 if present, else first qubit count
        nq_vals = sorted(set(a["qubit_count"] for a in agg))
        nq = 10 if 10 in nq_vals else (nq_vals[0] if nq_vals else 10)
        subset = [a for a in agg if a["qubit_count"] == nq]
        opt_levels = sorted(set(a["optimizer_level"] for a in subset))
        x = range(len(opt_levels))
        width = 0.35
        for i, fw in enumerate(FRAMEWORKS):
            fw_data = [a for a in subset if a["framework"] == fw.lower()]
            fw_data = sorted(fw_data, key=lambda a: a["optimizer_level"])
            depths = [a["mean_depth"] for a in fw_data]
            off = (i - 0.5) * width
            ax.bar([xi + off for xi in x], depths, width, label=fw, color=COLORS[i], edgecolor="black", linewidth=0.5)
        ax.set_xticks(x)
        ax.set_xticklabels(opt_levels)
        ax.set_xlabel("Optimization level")
        ax.set_ylabel("Mean depth")
        ax.set_title(f"Opt-level comparison (n_qubits={nq})")
    else:
        ax.text(0.5, 0.5, "Run llm_opt_qubit_sweep.json\nand re-run this script.", ha="center", va="center",
                transform=ax.transAxes, fontsize=11)
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.set_axis_off()
        ax.set_title("Opt-level comparison (placeholder)")
    if agg:
        ax.legend(loc="upper right", frameon=True)
    fig.tight_layout()
    fig.savefig(RESULTS_DIR / "fig_sweep_opt_levels.pdf", bbox_inches="tight")
    plt.close(fig)


def fig_sweep_qubits(agg):
    """Qubit sweep at opt_level=3. Use two subplots so PyTket (often depth=2) is visible alongside Qiskit."""
    fig, axes = plt.subplots(1, 2, figsize=(7, 3), sharex=True)
    if agg:
        opt3 = [a for a in agg if a["optimizer_level"] == 3]
        if not opt3:
            opt3 = agg
        nq_vals = sorted(set(a["qubit_count"] for a in opt3))
        x = range(len(nq_vals))
        width = 0.5
        for ax, (fw, color) in zip(axes, [("qiskit", COLORS[0]), ("pytket", COLORS[1])]):
            fw_data = [a for a in opt3 if a["framework"] == fw]
            fw_data = sorted(fw_data, key=lambda a: a["qubit_count"])
            if not fw_data:
                ax.text(0.5, 0.5, f"No {fw} data", ha="center", va="center", transform=ax.transAxes)
                ax.set_xticks(x)
                ax.set_xticklabels(nq_vals)
                continue
            depths = [a["mean_depth"] for a in fw_data]
            ax.bar(x, depths, width, color=color, edgecolor="black", linewidth=0.5)
            ax.set_xticks(x)
            ax.set_xticklabels(nq_vals)
            ax.set_xlabel("Qubit count")
            ax.set_ylabel("Mean depth")
            ax.set_title(fw.capitalize())
        fig.suptitle("Opt level 3: scaling with qubit count", y=1.02)
        # If PyTket depths are all 2 (artifact), add a note
        pytket_depths = [a["mean_depth"] for a in opt3 if a["framework"] == "pytket"]
        if pytket_depths and max(pytket_depths) <= 2 and min(pytket_depths) >= 0:
            fig.text(0.5, -0.02, "Note: PyTket opt=3 reports depth=2 for all n_qubits (possible compiler artifact).",
                     ha="center", fontsize=8, style="italic")
    else:
        for ax in axes:
            ax.text(0.5, 0.5, "Run llm_opt_qubit_sweep.json\nand re-run this script.", ha="center", va="center",
                    transform=ax.transAxes, fontsize=10)
            ax.set_axis_off()
        axes[0].set_title("Qiskit")
        axes[1].set_title("PyTket")
        fig.suptitle("Qubit sweep at opt=3 (placeholder)", y=1.02)
    fig.tight_layout()
    fig.savefig(RESULTS_DIR / "fig_sweep_qubits.pdf", bbox_inches="tight")
    plt.close(fig)


def main():
    agg = load_aggregates()
    fig_sweep_opt_levels(agg)
    fig_sweep_qubits(agg)
    print("Sweep figures written: fig_sweep_opt_levels.pdf, fig_sweep_qubits.pdf")


if __name__ == "__main__":
    main()
