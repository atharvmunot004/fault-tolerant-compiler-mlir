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


GATE_BENCH_N_QUBITS = 10
GATE_BENCH_Q = 5  # qubit index used for single-qubit gates


def _write_gate_chp_circuits(assets_dir: Path) -> Dict[str, Path]:
    """
    CHP natively supports H, P (S), CNOT, M. X and Z use standard Clifford decompositions:
    Z = P^2,  X = H P^2 H.
    """
    gate_dir = assets_dir / "circuits_gates"
    gate_dir.mkdir(parents=True, exist_ok=True)
    q = GATE_BENCH_Q
    specs = {
        "H": [f"h {q}"],
        "S": [f"p {q}"],
        "X": [f"h {q}", f"p {q}", f"p {q}", f"h {q}"],
        "Z": [f"p {q}", f"p {q}"],
        "CNOT": [f"c {q} {q + 1}"],
        "MZ": [f"m {q}"],
        "Mixed (no meas)": [
            "h 0",
            "p 1",
            "h 2",
            "p 2",
            "p 2",
            "h 2",
            "p 3",
            "p 3",
            "c 4 5",
            "h 6",
            "p 7",
            "c 8 9",
        ],
    }
    paths: Dict[str, Path] = {}
    for name, lines in specs.items():
        body = "\n".join(lines)
        text = f"Gate benchmark: {name} on {GATE_BENCH_N_QUBITS} qubits (no measurement except MZ).\n#\n{body}\n"
        path = gate_dir / f"{name.lower().replace(' ', '_').replace('(', '').replace(')', '')}.chp"
        path.write_text(text, encoding="utf-8")
        paths[name] = path
    return paths


def _import_python_impl():
    # Local import to keep script usable even if package isn't importable in some contexts.
    root = _repo_root()
    pkg_root = root / "stabilizer-python"
    if str(pkg_root) not in sys.path:
        sys.path.insert(0, str(pkg_root))

    from stabilizer_python.circuit import Circuit
    from stabilizer_python.tableau import StabilizerState

    n = GATE_BENCH_N_QUBITS
    q = GATE_BENCH_Q

    def _gate_h() -> None:
        StabilizerState.zero(n).h(q)

    def _gate_s() -> None:
        StabilizerState.zero(n).s(q)

    def _gate_x() -> None:
        StabilizerState.zero(n).x(q)

    def _gate_z() -> None:
        StabilizerState.zero(n).z(q)

    def _gate_cnot() -> None:
        StabilizerState.zero(n).cnot(q, q + 1)

    def _gate_mz() -> None:
        StabilizerState.zero(n).measure_z(q)

    def _mixed_circuit() -> None:
        st = StabilizerState.zero(n)
        Circuit(n).h(0).s(1).x(2).z(3).cnot(4, 5).h(6).s(7).cnot(8, 9).run(st)

    gate_fns = {
        "H": _gate_h,
        "S": _gate_s,
        "X": _gate_x,
        "Z": _gate_z,
        "CNOT": _gate_cnot,
        "MZ": _gate_mz,
        "Mixed (no meas)": _mixed_circuit,
    }

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

    py_impl = {"EPR": epr, "GHZ": ghz_like_chp, "Teleport (z)": teleport_z_like_chp_input_char_z}
    return py_impl, gate_fns


def run_python_gate(fn: Callable[[], None]) -> Tuple[Tuple[int, ...], float, float]:
    tracemalloc.start()
    t0 = time.perf_counter()
    fn()
    dt_ms = (time.perf_counter() - t0) * 1000.0
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return tuple(), dt_ms, peak / 1024.0


def benchmark_gates(
    *,
    chp_exe: Path,
    gate_chp_files: Dict[str, Path],
    gate_fns: Dict[str, Callable[[], None]],
    n: int,
    warmup: int,
) -> Dict[str, Dict[str, object]]:
    chp_native = {"H", "S", "CNOT", "MZ"}
    chp_decompose = {"X": "H P² H", "Z": "P²", "Mixed (no meas)": "H,P,CNOT (+ X/Z decomps)"}
    out: Dict[str, Dict[str, object]] = {}

    for name, chp_path in gate_chp_files.items():
        py_fn = gate_fns[name]
        for _ in range(warmup):
            run_chp(chp_exe, chp_path, input_state=None, silent=True, capture_outcomes=False)
            run_python_gate(py_fn)

        py_ms: List[float] = []
        chp_ms: List[float] = []
        py_peak: List[float] = []
        for _ in range(n):
            _, t_ms, peak_kib = run_python_gate(py_fn)
            py_ms.append(t_ms)
            py_peak.append(peak_kib)
            _, t_chp = run_chp(
                chp_exe, chp_path, input_state=None, silent=True, capture_outcomes=False
            )
            chp_ms.append(t_chp)

        entry: Dict[str, object] = {
            "n_qubits": GATE_BENCH_N_QUBITS,
            "python": {
                "timing_ms": summarize(py_ms),
                "peak_alloc_kib": {
                    "p50_kib": float(statistics.median(py_peak)),
                    "mean_kib": float(statistics.mean(py_peak)),
                },
            },
            "chp": {"timing_ms": summarize(chp_ms)},
        }
        if name in chp_native:
            entry["chp_mapping"] = "native"
        else:
            entry["chp_mapping"] = chp_decompose.get(name, "decomposed")
        out[name] = entry
    return out


def plot_gate_runtime_bars(
    *,
    gate_names: Sequence[str],
    py_p50: Sequence[float],
    chp_p50: Sequence[float],
    n: int,
    out_path: Path,
):
    ensure_matplotlib()
    import matplotlib.pyplot as plt

    x = list(range(len(gate_names)))
    w = 0.38
    fig, ax = plt.subplots(figsize=(2 + 1.4 * len(gate_names), 5), tight_layout=True)
    ax.bar([i - w / 2 for i in x], py_p50, width=w, label="Python p50")
    ax.bar([i + w / 2 for i in x], chp_p50, width=w, label="CHP p50")
    ax.set_xticks(x)
    ax.set_xticklabels(gate_names, rotation=25, ha="right")
    ax.set_ylabel("wall time (ms)")
    ax.set_title(f"Pure gate / mixed-circuit timing (n={n} runs, {GATE_BENCH_N_QUBITS} qubits)")
    ax.grid(axis="y", alpha=0.25)
    ax.legend()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=180)
    plt.close(fig)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=200, help="number of runs per circuit/implementation")
    ap.add_argument("--warmup", type=int, default=10, help="warmup runs per circuit/implementation")
    ap.add_argument(
        "--skip-circuits",
        action="store_true",
        help="only run gate / mixed-circuit benchmarks",
    )
    ap.add_argument(
        "--skip-gates",
        action="store_true",
        help="only run EPR/GHZ/Teleport circuit benchmarks",
    )
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

    py_impl, gate_fns = _import_python_impl()

    results: Dict[str, Dict[str, object]] = {}
    py_out_freqs: List[Dict[str, int]] = []
    chp_out_freqs: List[Dict[str, int]] = []
    py_times: List[List[float]] = []
    chp_times: List[List[float]] = []
    py_peaks: List[List[float]] = []

    if not args.skip_circuits:
        # Warmup (reduce one-time costs).
        for name, file, inp in circuits:
            for _ in range(args.warmup):
                run_chp(chp_exe, file, input_state=inp, silent=True, capture_outcomes=False)
                run_python(py_impl[name])

    if not args.skip_circuits:
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

                o2, t2_ms = run_chp(
                    chp_exe, file, input_state=inp, silent=True, capture_outcomes=False
                )
                chp_out.append(o2)  # empty tuples in silent mode
                chp_ms.append(t2_ms)

            # Separate pass for CHP outcomes (non-silent, but fewer runs to keep IO manageable).
            chp_outcomes: List[Tuple[int, ...]] = []
            for _ in range(max(50, args.n // 4)):
                o3, _t3 = run_chp(
                    chp_exe, file, input_state=inp, silent=False, capture_outcomes=True
                )
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

    gate_results: Dict[str, Dict[str, object]] = {}
    gate_chp_files: Dict[str, Path] = {}
    if not args.skip_gates:
        gate_chp_files = _write_gate_chp_circuits(assets_dir)
        gate_results = benchmark_gates(
            chp_exe=chp_exe,
            gate_chp_files=gate_chp_files,
            gate_fns=gate_fns,
            n=args.n,
            warmup=args.warmup,
        )

    assets_dir.mkdir(parents=True, exist_ok=True)
    metrics_payload: Dict[str, object] = {
        "runs_per_benchmark": args.n,
        "gate_benchmark_n_qubits": GATE_BENCH_N_QUBITS,
        "circuits": results,
        "gates": gate_results,
    }
    (assets_dir / "metrics.json").write_text(json.dumps(metrics_payload, indent=2), encoding="utf-8")

    if not args.skip_circuits and py_out_freqs:
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

    if gate_results:
        gate_order = list(gate_chp_files.keys())
        plot_gate_runtime_bars(
            gate_names=gate_order,
            py_p50=[
                float(gate_results[g]["python"]["timing_ms"]["p50_ms"])  # type: ignore[index]
                for g in gate_order
            ],
            chp_p50=[
                float(gate_results[g]["chp"]["timing_ms"]["p50_ms"])  # type: ignore[index]
                for g in gate_order
            ],
            n=args.n,
            out_path=assets_dir / "performance_gate_runtime.png",
        )

    # Write a small markdown summary that can be embedded or linked.
    lines: List[str] = []
    lines.append("## Benchmark summary (auto-generated)\n")
    lines.append(f"- Runs per benchmark (timing): **{args.n}**\n")
    if not args.skip_circuits:
        lines.append(f"- Runs per circuit (CHP outcomes): **{max(50, args.n // 4)}**\n")
    if gate_results:
        lines.append(f"- Gate benchmarks: **{GATE_BENCH_N_QUBITS} qubits**, fresh `|0…0⟩` + one gate (or mixed circuit) per run\n")
    lines.append("- Date/time: generated at runtime\n\n")

    if not args.skip_circuits:
        lines.append("### Full circuits (EPR / GHZ / Teleport)\n\n")
        for name in results:
            r = results[name]
            py_t = r["python"]["timing_ms"]  # type: ignore[index]
            chp_t = r["chp"]["timing_ms"]  # type: ignore[index]
            ratio = float(py_t["p50_ms"]) / float(chp_t["p50_ms"]) if float(chp_t["p50_ms"]) > 0 else float("inf")
            lines.append(f"#### {name}\n")
            lines.append(f"- Python p50: **{py_t['p50_ms']:.3f} ms** (p95 {py_t['p95_ms']:.3f} ms)\n")
            lines.append(f"- CHP p50: **{chp_t['p50_ms']:.3f} ms** (p95 {chp_t['p95_ms']:.3f} ms)\n")
            lines.append(f"- Python/CHP p50 ratio: **{ratio:.4f}×**\n\n")

    if gate_results:
        lines.append("### Pure gates and mixed Clifford circuit\n\n")
        lines.append("| Gate / circuit | CHP mapping | Python p50 (ms) | CHP p50 (ms) | Python/CHP p50 |\n")
        lines.append("|----------------|-------------|-----------------|--------------|----------------|\n")
        for name, r in gate_results.items():
            py_t = r["python"]["timing_ms"]  # type: ignore[index]
            chp_t = r["chp"]["timing_ms"]  # type: ignore[index]
            mapping = str(r.get("chp_mapping", ""))
            ratio = float(py_t["p50_ms"]) / float(chp_t["p50_ms"]) if float(chp_t["p50_ms"]) > 0 else float("inf")
            lines.append(
                f"| {name} | {mapping} | {py_t['p50_ms']:.4f} | {chp_t['p50_ms']:.3f} | {ratio:.4f}× |\n"
            )
        lines.append("\n")
    (assets_dir / "metrics_summary.md").write_text("".join(lines), encoding="utf-8")

    print(f"Wrote assets to: {assets_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

