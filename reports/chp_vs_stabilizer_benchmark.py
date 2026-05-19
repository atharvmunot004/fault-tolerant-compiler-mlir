from __future__ import annotations

import argparse
import json
import re
import sys
import statistics
import subprocess
import time
import tracemalloc
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, List, Optional, Sequence, Tuple


@dataclass(frozen=True)
class RunSamples:
    outcomes: List[Tuple[int, ...]]
    wall_ms: List[float]
    py_peak_kib: Optional[List[float]] = None


MEAS_RE = re.compile(r"Outcome of measuring qubit\s+(?P<q>\d+):\s+(?P<bit>[01])")


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def run_chp(
    chp_exe: Path,
    circuit_file: Path,
    *,
    input_state: Optional[str],
    silent: bool,
    capture_outcomes: bool,
) -> Tuple[Tuple[int, ...], float]:
    args = [str(chp_exe)]
    if silent:
        args.append("-s")
    args.append(str(circuit_file))
    if input_state is not None:
        args.append(input_state)

    t0 = time.perf_counter()
    cp = subprocess.run(args, capture_output=True, text=True, check=True)
    dt_ms = (time.perf_counter() - t0) * 1000.0

    if not capture_outcomes:
        return tuple(), dt_ms

    bits: List[int] = []
    for m in MEAS_RE.finditer(cp.stdout):
        bits.append(int(m.group("bit")))
    return tuple(bits), dt_ms


def run_python(measure_fn: Callable[[], Tuple[int, ...]]) -> Tuple[Tuple[int, ...], float, float]:
    tracemalloc.start()
    t0 = time.perf_counter()
    out = measure_fn()
    dt_ms = (time.perf_counter() - t0) * 1000.0
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return out, dt_ms, peak / 1024.0


def summarize(samples: Sequence[float]) -> Dict[str, float]:
    s = list(samples)
    s_sorted = sorted(s)
    return {
        "n": float(len(s_sorted)),
        "min_ms": float(s_sorted[0]),
        "p50_ms": float(statistics.median(s_sorted)),
        "p95_ms": float(s_sorted[int(0.95 * (len(s_sorted) - 1))]),
        "max_ms": float(s_sorted[-1]),
        "mean_ms": float(statistics.mean(s_sorted)),
        "stdev_ms": float(statistics.pstdev(s_sorted)),
    }


def freq_table(outcomes: Sequence[Tuple[int, ...]]) -> Dict[str, int]:
    out: Dict[str, int] = {}
    for tup in outcomes:
        k = "".join(str(b) for b in tup) if tup else ""
        out[k] = out.get(k, 0) + 1
    return out


def ensure_matplotlib():
    import matplotlib  # noqa: F401


def plot_outcome_comparison(
    *,
    title: str,
    circuit_names: Sequence[str],
    py_freqs: Sequence[Dict[str, int]],
    chp_freqs: Sequence[Dict[str, int]],
    out_path: Path,
):
    ensure_matplotlib()
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, len(circuit_names), figsize=(6 * len(circuit_names), 4), tight_layout=True)
    if len(circuit_names) == 1:
        axes = [axes]

    for ax, name, f_py, f_chp in zip(axes, circuit_names, py_freqs, chp_freqs):
        keys = sorted(set(f_py.keys()) | set(f_chp.keys()))
        py_vals = [f_py.get(k, 0) for k in keys]
        chp_vals = [f_chp.get(k, 0) for k in keys]

        x = list(range(len(keys)))
        w = 0.42
        ax.bar([i - w / 2 for i in x], py_vals, width=w, label="Python")
        ax.bar([i + w / 2 for i in x], chp_vals, width=w, label="CHP")
        ax.set_title(name)
        ax.set_xticks(x)
        ax.set_xticklabels([k if k else "(none)" for k in keys])
        ax.set_ylabel("count")
        ax.grid(axis="y", alpha=0.25)
        ax.legend()

    fig.suptitle(title)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=180)
    plt.close(fig)


def plot_runtime_boxplots(
    *,
    title: str,
    circuit_names: Sequence[str],
    py_ms: Sequence[Sequence[float]],
    chp_ms: Sequence[Sequence[float]],
    out_path: Path,
):
    ensure_matplotlib()
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(2 + 2.2 * len(circuit_names), 5), tight_layout=True)

    data: List[Sequence[float]] = []
    labels: List[str] = []
    for name, a, b in zip(circuit_names, py_ms, chp_ms):
        data.append(a)
        labels.append(f"{name}\nPython")
        data.append(b)
        labels.append(f"{name}\nCHP")

    try:
        ax.boxplot(data, tick_labels=labels, showfliers=False)
    except TypeError:
        # Matplotlib < 3.9
        ax.boxplot(data, labels=labels, showfliers=False)
    ax.set_title(title)
    ax.set_ylabel("wall time (ms)")
    ax.grid(axis="y", alpha=0.25)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=180)
    plt.close(fig)


def plot_python_peak_memory(
    *,
    title: str,
    circuit_names: Sequence[str],
    py_peak_kib: Sequence[Sequence[float]],
    out_path: Path,
):
    ensure_matplotlib()
    import matplotlib.pyplot as plt

    means = [statistics.mean(x) for x in py_peak_kib]
    p95s = [sorted(x)[int(0.95 * (len(x) - 1))] for x in py_peak_kib]

    fig, ax = plt.subplots(figsize=(2 + 2.0 * len(circuit_names), 5), tight_layout=True)
    x = list(range(len(circuit_names)))
    ax.bar(x, means, label="mean peak KiB")
    ax.plot(x, p95s, marker="o", linestyle="--", label="p95 peak KiB")
    ax.set_xticks(x)
    ax.set_xticklabels(list(circuit_names))
    ax.set_title(title)
    ax.set_ylabel("Python peak allocated memory (KiB, tracemalloc)")
    ax.grid(axis="y", alpha=0.25)
    ax.legend()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=180)
    plt.close(fig)


def _import_python_impl():
    # Local import to keep script usable even if package isn't importable in some contexts.
    root = _repo_root()
    pkg_root = root / "stabilizer-python"
    if str(pkg_root) not in sys.path:
        sys.path.insert(0, str(pkg_root))

    from stabilizer_python.circuit import Circuit
    from stabilizer_python.tableau import StabilizerState

    def epr() -> Tuple[int, ...]:
        st = StabilizerState.zero(2)
        out = Circuit(2).h(0).cnot(0, 1).mz(1).run(st)
        return (out[0],)

    def ghz_like_chp() -> Tuple[int, ...]:
        st = StabilizerState.zero(3)
        out = (
            Circuit(3)
            .h(0)
            .h(1)
            .cnot(0, 2)
            .cnot(1, 2)
            .s(0)
            .s(1)
            .s(2)
            .h(0)
            .mz(0)
            .h(1)
            .mz(1)
            .mz(2)
            .run(st)
        )
        return (out[0], out[1], out[2])

    def teleport_z_like_chp_input_char_z() -> Tuple[int, ...]:
        # Empirically, the repo's CHP `teleport.chp z` yields deterministic final MZ(q2)=0.
        # We model the same circuit with a minimal "input prep" on q0 that matches that behavior.
        st = StabilizerState.zero(5)
        circ = Circuit(5)

        # Input character 'z' in CHP historically varies by fork; we align with observed behavior
        # by not applying any extra prep here.
        circ.h(1).cnot(1, 2).cnot(0, 1).h(0).mz(0).mz(1).cnot(0, 3).cnot(1, 4).cnot(4, 2).h(2).cnot(
            3, 2
        ).h(2).mz(2)
        out = circ.run(st)
        return (out[0], out[1], out[2])

    return {"EPR": epr, "GHZ": ghz_like_chp, "Teleport (z)": teleport_z_like_chp_input_char_z}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=200, help="number of runs per circuit/implementation")
    ap.add_argument("--warmup", type=int, default=10, help="warmup runs per circuit/implementation")
    args = ap.parse_args()

    root = _repo_root()
    assets_dir = root / "reports" / "chp_vs_stabilizer_assets"

    chp_exe = root / "learning_material" / "CHP" / "chp.exe"
    if not chp_exe.exists():
        raise FileNotFoundError(f"Missing CHP executable: {chp_exe}")

    chp_examples = root / "learning_material" / "CHP" / "examples"
    circuits = [
        ("EPR", chp_examples / "epr.chp", None),
        ("GHZ", chp_examples / "ghz.chp", None),
        ("Teleport (z)", chp_examples / "teleport.chp", "z"),
    ]

    py_impl = _import_python_impl()

    # Warmup (reduce one-time costs).
    for name, file, inp in circuits:
        for _ in range(args.warmup):
            run_chp(chp_exe, file, input_state=inp, silent=True, capture_outcomes=False)
            run_python(py_impl[name])

    results: Dict[str, Dict[str, object]] = {}
    py_out_freqs: List[Dict[str, int]] = []
    chp_out_freqs: List[Dict[str, int]] = []
    py_times: List[List[float]] = []
    chp_times: List[List[float]] = []
    py_peaks: List[List[float]] = []

    for name, file, inp in circuits:
        py_out: List[Tuple[int, ...]] = []
        chp_out: List[Tuple[int, ...]] = []
        py_ms: List[float] = []
        chp_ms: List[float] = []
        py_peak: List[float] = []

        for _ in range(args.n):
            o, t_ms, peak_kib = run_python(py_impl[name])
            py_out.append(o)
            py_ms.append(t_ms)
            py_peak.append(peak_kib)

            o2, t2_ms = run_chp(chp_exe, file, input_state=inp, silent=True, capture_outcomes=False)
            chp_out.append(o2)  # empty tuples in silent mode
            chp_ms.append(t2_ms)

        # Separate pass for CHP outcomes (non-silent, but fewer runs to keep IO manageable).
        # Still "multiple times" and enough to show the distribution.
        chp_outcomes: List[Tuple[int, ...]] = []
        for _ in range(max(50, args.n // 4)):
            o3, _t3 = run_chp(chp_exe, file, input_state=inp, silent=False, capture_outcomes=True)
            chp_outcomes.append(o3)

        results[name] = {
            "python": {
                "timing_ms": summarize(py_ms),
                "peak_alloc_kib": {
                    "n": float(len(py_peak)),
                    "min_kib": float(min(py_peak)),
                    "p50_kib": float(statistics.median(py_peak)),
                    "p95_kib": float(sorted(py_peak)[int(0.95 * (len(py_peak) - 1))]),
                    "max_kib": float(max(py_peak)),
                    "mean_kib": float(statistics.mean(py_peak)),
                },
                "outcome_freq": freq_table(py_out),
            },
            "chp": {
                "timing_ms": summarize(chp_ms),
                "outcome_freq": freq_table(chp_outcomes),
            },
        }

        py_out_freqs.append(freq_table(py_out))
        chp_out_freqs.append(freq_table(chp_outcomes))
        py_times.append(py_ms)
        chp_times.append(chp_ms)
        py_peaks.append(py_peak)

    assets_dir.mkdir(parents=True, exist_ok=True)
    (assets_dir / "metrics.json").write_text(json.dumps(results, indent=2), encoding="utf-8")

    plot_outcome_comparison(
        title="Outcome distributions (multiple runs)",
        circuit_names=[c[0] for c in circuits],
        py_freqs=py_out_freqs,
        chp_freqs=chp_out_freqs,
        out_path=assets_dir / "comparison_outcomes.png",
    )
    plot_runtime_boxplots(
        title=f"Runtime distributions (n={args.n}, silent CHP, Python no prints)",
        circuit_names=[c[0] for c in circuits],
        py_ms=py_times,
        chp_ms=chp_times,
        out_path=assets_dir / "performance_runtime_boxplot.png",
    )
    plot_python_peak_memory(
        title=f"Python peak allocated memory (n={args.n}, tracemalloc)",
        circuit_names=[c[0] for c in circuits],
        py_peak_kib=py_peaks,
        out_path=assets_dir / "performance_python_peak_memory.png",
    )

    # Write a small markdown summary that can be embedded or linked.
    lines: List[str] = []
    lines.append("## Benchmark summary (auto-generated)\n")
    lines.append(f"- Runs per circuit (timing): **{args.n}**\n")
    lines.append(f"- Runs per circuit (CHP outcomes): **{max(50, args.n // 4)}**\n")
    lines.append(f"- Date/time: generated at runtime\n")
    lines.append("\n")
    for name in results:
        r = results[name]
        py_t = r["python"]["timing_ms"]  # type: ignore[index]
        chp_t = r["chp"]["timing_ms"]  # type: ignore[index]
        speedup = float(py_t["p50_ms"]) / float(chp_t["p50_ms"]) if float(chp_t["p50_ms"]) > 0 else float("inf")
        lines.append(f"### {name}\n")
        lines.append(f"- Python p50: **{py_t['p50_ms']:.3f} ms** (p95 {py_t['p95_ms']:.3f} ms)\n")
        lines.append(f"- CHP p50: **{chp_t['p50_ms']:.3f} ms** (p95 {chp_t['p95_ms']:.3f} ms)\n")
        lines.append(f"- Speedup (Python p50 / CHP p50): **{speedup:.2f}×**\n")
        lines.append("\n")
    (assets_dir / "metrics_summary.md").write_text("".join(lines), encoding="utf-8")

    print(f"Wrote assets to: {assets_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

