"""
Circuit builders for QFT roundtrip benchmark.

Builds circuits per spec: X_ALL, QFT, IQFT, MEASURE_ALL.
Expected ideal output: all-ones bitstring.
"""

from typing import Any

# Qiskit
from qiskit import QuantumCircuit
from qiskit.circuit.library import QFT, IQFT

# PyTket (optional - import only when needed)
try:
    from pytket import Circuit as TketCircuit
    from pytket.extensions.qiskit import qiskit_to_tk
    PYTKET_AVAILABLE = True
except ImportError:
    PYTKET_AVAILABLE = False
    TketCircuit = None  # type: ignore


def build_qiskit_qft_roundtrip(n_qubits: int) -> QuantumCircuit:
    """Build QFT roundtrip circuit: X on all, QFT, IQFT, measure all."""
    qc = QuantumCircuit(n_qubits, n_qubits)
    # X_ALL
    for q in range(n_qubits):
        qc.x(q)
    # QFT
    qc.append(QFT(n_qubits, do_swaps=True), range(n_qubits))
    # IQFT
    qc.append(IQFT(n_qubits, do_swaps=True), range(n_qubits))
    # MEASURE_ALL
    qc.measure(range(n_qubits), range(n_qubits))
    return qc


def build_pytket_qft_roundtrip(n_qubits: int) -> "TketCircuit":
    """Build QFT roundtrip circuit in PyTket via conversion from Qiskit for semantic equivalence."""
    if not PYTKET_AVAILABLE:
        raise ImportError("pytket and pytket-qiskit required. Install with: pip install pytket pytket-qiskit")
    qc = build_qiskit_qft_roundtrip(n_qubits)
    return qiskit_to_tk(qc)


def get_circuit_builder(framework: str):
    """Return the circuit builder function for the given framework."""
    if framework == "qiskit":
        return build_qiskit_qft_roundtrip
    if framework == "pytket":
        return build_pytket_qft_roundtrip
    raise ValueError(f"Unknown framework: {framework}")
