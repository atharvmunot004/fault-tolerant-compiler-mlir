"""
Frontend Adapter Module (Language → OpenQASM)

Purpose:
---------
Convert circuits from various SDKs (Qiskit, Cirq, PennyLane, raw QASM)
into an equivalent OpenQASM representation.

This module:
- Removes language-specific quirks
- Preserves circuit order and structure
- Performs NO semantic validation
- Performs NO contract enforcement
- Performs NO canonicalization beyond syntax normalization

Grammar checking, circuit contracts, canonical IR, and MLIR lowering
happen in later stages.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Tuple
import re


# =============================================================================
# Lightweight Instruction Model (Syntax-Level Only)
# =============================================================================

@dataclass
class QASMInstruction:
    name: str
    qubits: Tuple[int, ...]
    cbits: Tuple[int, ...] = ()
    params: Tuple[str, ...] = ()  # symbolic allowed here


@dataclass
class QASMCircuit:
    num_qubits: int
    num_cbits: int
    instructions: List[QASMInstruction]


# =============================================================================
# Errors
# =============================================================================

class FrontendAdapterError(Exception):
    pass


class UnsupportedCircuitTypeError(FrontendAdapterError):
    pass


# =============================================================================
# Adapter Interface
# =============================================================================

class BaseAdapter(ABC):
    """Translate a circuit into a QASMCircuit (syntax-level only)."""

    @abstractmethod
    def can_handle(self, circuit) -> bool:
        pass

    @abstractmethod
    def to_qasm_circuit(self, circuit) -> QASMCircuit:
        pass


# =============================================================================
# QASM Adapter (Pass-through + light normalization)
# =============================================================================

class QASMAdapter(BaseAdapter):
    def can_handle(self, circuit) -> bool:
        return isinstance(circuit, str) and ("qreg" in circuit.lower() or "qubit" in circuit.lower())

    def to_qasm_circuit(self, circuit: str) -> QASMCircuit:
        lines = [l.strip() for l in circuit.splitlines() if l.strip()]

        num_qubits = 0
        num_cbits = 0
        instructions = []

        for line in lines:
            if "qubit[" in line:
                num_qubits = int(re.search(r"qubit\[(\d+)\]", line).group(1))
            elif "qreg" in line:
                num_qubits = int(re.search(r"qreg\s+\w+\[(\d+)\]", line).group(1))
            elif "bit[" in line:
                num_cbits = int(re.search(r"bit\[(\d+)\]", line).group(1))
            elif "creg" in line:
                num_cbits = int(re.search(r"creg\s+\w+\[(\d+)\]", line).group(1))

            elif "measure" in line:
                # Handle QASM 2.0: measure q[0] -> c[0]
                m = re.search(r"measure\s+q\[(\d+)\]\s*->\s*c\[(\d+)\]", line)
                if m:
                    instructions.append(
                        QASMInstruction("measure", (int(m.group(1)),), (int(m.group(2)),))
                    )
                else:
                    # Handle QASM 3.0: c[0] = measure q[0]
                    m = re.search(r"c\[(\d+)\]\s*=\s*measure\s+q\[(\d+)\]", line)
                    if m:
                        instructions.append(
                            QASMInstruction("measure", (int(m.group(2)),), (int(m.group(1)),))
                        )
            elif "cx" in line or "cnot" in line:
                m = re.search(r"q\[(\d+)\],\s*q\[(\d+)\]", line)
                if m:
                    instructions.append(
                        QASMInstruction("cx", (int(m.group(1)), int(m.group(2))))
                    )
            else:
                m = re.search(r"(\w+)\s+q\[(\d+)\]", line)
                if m:
                    instructions.append(
                        QASMInstruction(m.group(1), (int(m.group(2)),))
                    )

        return QASMCircuit(num_qubits, num_cbits, instructions)


# =============================================================================
# Qiskit Adapter
# =============================================================================

class QiskitAdapter(BaseAdapter):
    def can_handle(self, circuit) -> bool:
        return hasattr(circuit, "data") and hasattr(circuit, "num_qubits")

    def to_qasm_circuit(self, circuit) -> QASMCircuit:
        instructions = []

        for inst, qargs, cargs in circuit.data:
            instructions.append(
                QASMInstruction(
                    name=inst.name,
                    qubits=tuple(q.index for q in qargs),
                    cbits=tuple(c.index for c in cargs),
                )
            )

        return QASMCircuit(
            num_qubits=circuit.num_qubits,
            num_cbits=getattr(circuit, "num_clbits", 0),
            instructions=instructions,
        )


# =============================================================================
# Cirq Adapter
# =============================================================================

class CirqAdapter(BaseAdapter):
    def can_handle(self, circuit) -> bool:
        return hasattr(circuit, "all_operations")

    def to_qasm_circuit(self, circuit) -> QASMCircuit:
        qubit_map = {q: i for i, q in enumerate(sorted(circuit.all_qubits()))}
        instructions = []

        for op in circuit.all_operations():
            name = op.gate.__class__.__name__.lower()
            qubits = tuple(qubit_map[q] for q in op.qubits)
            instructions.append(QASMInstruction(name, qubits))

        return QASMCircuit(len(qubit_map), 0, instructions)


# =============================================================================
# PennyLane Adapter
# =============================================================================

class PennyLaneAdapter(BaseAdapter):
    def can_handle(self, circuit) -> bool:
        return hasattr(circuit, "operations")

    def to_qasm_circuit(self, circuit) -> QASMCircuit:
        instructions = []

        for op in circuit.operations:
            instructions.append(
                QASMInstruction(
                    name=op.name.lower(),
                    qubits=tuple(op.wires),
                )
            )

        return QASMCircuit(circuit.num_wires, 0, instructions)


# =============================================================================
# OpenQASM Emitter
# =============================================================================

class OpenQASMEmitter:
    @staticmethod
    def emit(circuit: QASMCircuit) -> str:
        lines = [
            "OPENQASM 3.0;",
            f"qubit[{circuit.num_qubits}] q;",
            f"bit[{circuit.num_cbits}] c;",
            "",
        ]

        for inst in circuit.instructions:
            if inst.name == "measure":
                lines.append(f"c[{inst.cbits[0]}] = measure q[{inst.qubits[0]}];")
            elif len(inst.qubits) == 2:
                lines.append(f"{inst.name} q[{inst.qubits[0]}], q[{inst.qubits[1]}];")
            else:
                lines.append(f"{inst.name} q[{inst.qubits[0]}];")

        return "\n".join(lines)


# =============================================================================
# Frontend Adapter Orchestrator
# =============================================================================

class FrontendAdapter:
    def __init__(self):
        self.adapters = [
            QASMAdapter(),
            QiskitAdapter(),
            CirqAdapter(),
            PennyLaneAdapter(),
        ]

    def convert(self, circuit) -> str:
        for adapter in self.adapters:
            if adapter.can_handle(circuit):
                qasm_circuit = adapter.to_qasm_circuit(circuit)
                return OpenQASMEmitter.emit(qasm_circuit)

        raise UnsupportedCircuitTypeError(
            f"No frontend adapter for circuit type {type(circuit)}"
        )


# =============================================================================
# Convenience API
# =============================================================================

def convert_to_qasm(circuit) -> str:
    return FrontendAdapter().convert(circuit)
