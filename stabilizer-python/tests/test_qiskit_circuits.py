from typing import List, Set

from qiskit import QuantumCircuit

from stabilizer_python.circuit import Circuit
from stabilizer_python.linear_algebra import rank_gf2
from stabilizer_python.tableau import StabilizerState


def _from_qiskit(circuit: QuantumCircuit) -> Circuit:
    """Convert supported Qiskit Clifford instructions into this package's circuit."""
    out = Circuit(circuit.num_qubits)

    for instruction in circuit.data:
        name = instruction.operation.name
        qubits = [circuit.find_bit(qubit).index for qubit in instruction.qubits]

        if name == "h":
            out.h(qubits[0])
        elif name == "s":
            out.s(qubits[0])
        elif name == "x":
            out.x(qubits[0])
        elif name == "z":
            out.z(qubits[0])
        elif name in ("cx", "cnot"):
            out.cnot(qubits[0], qubits[1])
        elif name == "measure":
            out.mz(qubits[0])
        elif name == "barrier":
            continue
        else:
            raise ValueError(f"unsupported Qiskit instruction: {name}")

    return out


def _pauli_string(x_row: List[int], z_row: List[int]) -> str:
    chars = []
    for x_bit, z_bit in zip(x_row, z_row):
        if x_bit == 0 and z_bit == 0:
            chars.append("I")
        elif x_bit == 1 and z_bit == 0:
            chars.append("X")
        elif x_bit == 0 and z_bit == 1:
            chars.append("Z")
        else:
            chars.append("Y")
    return "".join(chars)


def _stabilizers_from_qiskit(circuit: QuantumCircuit) -> Set[str]:
    state = StabilizerState.zero(circuit.num_qubits)
    _from_qiskit(circuit).run(state)

    stabilizers = set()
    stabilizer_matrix: List[List[int]] = []
    for phase, x_row, z_row in state.stabilizer_generators():
        sign = "-" if phase else "+"
        stabilizers.add(sign + _pauli_string(x_row, z_row))
        stabilizer_matrix.append(x_row + z_row)

    assert rank_gf2(stabilizer_matrix) == circuit.num_qubits
    return stabilizers


def test_qiskit_bell_circuit_stabilizers():
    circuit = QuantumCircuit(2)
    circuit.h(0)
    circuit.cx(0, 1)

    stabilizers = _stabilizers_from_qiskit(circuit)
    print(f"Qiskit Bell circuit stabilizers from stabilizer_python: {sorted(stabilizers)}")
    assert stabilizers == {"+XX", "+ZZ"}


def test_qiskit_ghz_circuit_stabilizers():
    circuit = QuantumCircuit(3)
    circuit.h(0)
    circuit.cx(0, 1)
    circuit.cx(0, 2)

    stabilizers = _stabilizers_from_qiskit(circuit)
    print(f"Qiskit GHZ circuit stabilizers from stabilizer_python: {sorted(stabilizers)}")
    assert stabilizers == {"+XXX", "+ZZI", "+ZIZ"}


def test_qiskit_circuit_with_pauli_updates_stabilizer_signs():
    circuit = QuantumCircuit(2)
    circuit.h(0)
    circuit.cx(0, 1)
    circuit.z(0)

    stabilizers = _stabilizers_from_qiskit(circuit)
    print(f"Qiskit Bell+Z circuit stabilizers from stabilizer_python: {sorted(stabilizers)}")
    assert stabilizers == {"-XX", "+ZZ"}
