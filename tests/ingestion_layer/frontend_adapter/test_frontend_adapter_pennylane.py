"""
Test PennyLane-like circuit conversion.

These tests verify that circuits with PennyLane-like structure (operations
attribute, num_wires) are correctly converted to OpenQASM.
"""
import pytest
from src.ingestion_layer.frontend_adapter import convert_to_qasm


class FakePLGate:
    """Mock PennyLane gate with name and wires."""
    def __init__(self, name, wires):
        self.name = name
        self.wires = wires


class FakePennyLaneCircuit:
    """Mock PennyLane-like circuit with operations and num_wires."""
    def __init__(self):
        self.num_wires = 2
        self.operations = [
            FakePLGate('H', [0]),
            FakePLGate('CNOT', [0, 1])
        ]


def test_pennylane_like_conversion():
    """Test basic PennyLane-like circuit conversion."""
    circ = FakePennyLaneCircuit()
    out = convert_to_qasm(circ)

    assert 'OPENQASM 3.0;' in out
    assert 'h q[0];' in out.lower()
    assert 'cnot q[0], q[1];' in out.lower() or 'cx q[0], q[1];' in out.lower()


def test_pennylane_wire_count():
    """Test that num_wires is correctly converted to qubit count."""
    class LargeCircuit:
        def __init__(self):
            self.num_wires = 10
            self.operations = [
                FakePLGate('H', [i]) for i in range(10)
            ]

    circ = LargeCircuit()
    out = convert_to_qasm(circ)

    assert 'qubit[10] q;' in out
    for i in range(10):
        assert f'h q[{i}];' in out.lower()


def test_pennylane_gate_name_preservation():
    """Test that gate names are preserved (lowercased)."""
    class CustomGateCircuit:
        def __init__(self):
            self.num_wires = 2
            self.operations = [
                FakePLGate('CustomGate', [0]),
                FakePLGate('AnotherGate', [1]),
            ]

    circ = CustomGateCircuit()
    out = convert_to_qasm(circ)

    # Gate names should be lowercased but preserved
    assert 'customgate' in out.lower()
    assert 'anothergate' in out.lower()


def test_pennylane_wire_indices():
    """Test that wire indices are correctly preserved."""
    class SparseCircuit:
        def __init__(self):
            self.num_wires = 10
            self.operations = [
                FakePLGate('H', [0]),
                FakePLGate('X', [5]),
                FakePLGate('Z', [9]),
            ]

    circ = SparseCircuit()
    out = convert_to_qasm(circ)

    assert 'qubit[10] q;' in out
    assert 'h q[0];' in out.lower()
    assert 'x q[5];' in out.lower()
    assert 'z q[9];' in out.lower()


def test_pennylane_two_qubit_gates():
    """Test two-qubit gates."""
    class TwoQubitCircuit:
        def __init__(self):
            self.num_wires = 4
            self.operations = [
                FakePLGate('CNOT', [0, 1]),
                FakePLGate('CZ', [2, 3]),
                FakePLGate('SWAP', [0, 3]),
            ]

        def all_qubits(self):
            return list(range(self.num_wires))

    circ = TwoQubitCircuit()
    out = convert_to_qasm(circ)

    assert 'qubit[4] q;' in out
    assert ('cnot q[0], q[1];' in out.lower() or 'cx q[0], q[1];' in out.lower())
    assert 'cz q[2], q[3];' in out.lower()
    assert 'swap q[0], q[3];' in out.lower()


def test_pennylane_operation_order():
    """Test that operation order is preserved."""
    class OrderedCircuit:
        def __init__(self):
            self.num_wires = 2
            self.operations = [
                FakePLGate('H', [0]),
                FakePLGate('X', [1]),
                FakePLGate('CNOT', [0, 1]),
            ]

    circ = OrderedCircuit()
    out = convert_to_qasm(circ)

    # Check order
    h_pos = out.lower().find('h q[0];')
    x_pos = out.lower().find('x q[1];')
    cnot_pos = out.lower().find('cnot') or out.lower().find('cx')

    assert h_pos < x_pos < cnot_pos


def test_pennylane_no_classical_bits():
    """Test that PennyLane circuits have no classical bits by default."""
    circ = FakePennyLaneCircuit()
    out = convert_to_qasm(circ)

    # PennyLane adapter should set num_cbits to 0
    assert 'bit[0] c;' in out

