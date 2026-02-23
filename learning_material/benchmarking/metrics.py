"""
Metrics for the QFT roundtrip benchmark.

- population_target_state: probability of all-ones outcome
- hellinger_fidelity: Hellinger fidelity between observed and ideal (delta at all-ones)
"""

import math
from typing import Dict


def normalize_counts(counts: Dict[str, int], n_qubits: int, msb_left: bool = True) -> Dict[str, float]:
    """
    Normalize counts to probabilities.
    Optionally normalize bitstring convention to msb_left for consistency.
    """
    total = sum(counts.values())
    if total == 0:
        return {}
    result = {}
    for bitstring, count in counts.items():
        # Pad or truncate to n_qubits for consistency
        if len(bitstring) != n_qubits:
            if msb_left:
                bitstring = bitstring.zfill(n_qubits)[:n_qubits]
            else:
                bitstring = bitstring.zfill(n_qubits)[-n_qubits:]
        result[bitstring] = count / total
    return result


def population_target_state(counts: Dict[str, int], n_qubits: int, target: str | None = None) -> float:
    """
    Probability mass of the expected all-ones bitstring.
    Target is "1" * n_qubits when msb_left.
    """
    if target is None:
        target = "1" * n_qubits
    total = sum(counts.values())
    if total == 0:
        return 0.0
    # Handle both possible bitstring formats (Qiskit vs PyTket may differ)
    count = 0
    for k, v in counts.items():
        # Normalize: pad to n_qubits, msb_left
        k_norm = k.zfill(n_qubits)[:n_qubits]
        if k_norm == target:
            count += v
    return count / total


def hellinger_fidelity(
    counts: Dict[str, int],
    n_qubits: int,
    target: str | None = None,
) -> float:
    """
    Hellinger fidelity between observed distribution p and ideal distribution q.
    q is delta at all-ones: q[target]=1, else 0.
    Formula: F_H = 1 - (1/sqrt(2)) * sqrt( sum_i (sqrt(p_i) - sqrt(q_i))^2 )
    """
    if target is None:
        target = "1" * n_qubits
    total = sum(counts.values())
    if total == 0:
        return 0.0
    p = normalize_counts(counts, n_qubits, msb_left=True)
    # Ideal q: q[target]=1, else 0
    sum_sq = 0.0
    for bitstring, prob in p.items():
        q_i = 1.0 if bitstring == target else 0.0
        sum_sq += (math.sqrt(prob) - math.sqrt(q_i)) ** 2
    return 1.0 - (1.0 / math.sqrt(2)) * math.sqrt(sum_sq)


def get_two_qubit_breakdown_qiskit(circuit) -> Dict[str, int]:
    """Count 2-qubit gates by type from a Qiskit QuantumCircuit."""
    from collections import defaultdict
    breakdown = defaultdict(int)
    for instr in circuit.data:
        if len(instr.qubits) == 2:
            name = instr.operation.name.lower()
            breakdown[name] += 1
    return dict(breakdown)


def get_two_qubit_breakdown_pytket(circuit) -> Dict[str, int]:
    """Count 2-qubit gates by type from a PyTket Circuit (excludes Measure, Barrier)."""
    from collections import defaultdict
    skip = {"Measure", "Barrier"}
    breakdown = defaultdict(int)
    for cmd in circuit.get_commands():
        name = cmd.op.type.name
        if name in skip:
            continue
        if len(cmd.args) >= 2:
            breakdown[name] += 1
    return dict(breakdown)
