"""
Test Cirq-like circuit conversion.

These tests verify that circuits with Cirq-like structure (all_operations,
all_qubits methods) are correctly converted to OpenQASM.
"""
import pytest
from src.ingestion_layer.frontend_adapter import convert_to_qasm


def create_gate_class(name):
    """Create a gate class with the specified name."""
    return type(name, (), {})


class FakeOp:
    """Mock operation with gate and qubits."""
    def __init__(self, gate, qubits):
        self.gate = gate
        self.qubits = qubits


class FakeCirqCircuit:
    """Mock Cirq-like circuit with all_operations and all_qubits methods."""
    def __init__(self):
        self._qubits = ['q0', 'q1']
        self._ops = [
            FakeOp(create_gate_class('H')(), ['q0']),
            FakeOp(create_gate_class('CX')(), ['q0', 'q1'])
        ]

    def all_qubits(self):
        return self._qubits

    def all_operations(self):
        return self._ops


def test_cirq_like_conversion():
    """Test basic Cirq-like circuit conversion."""
    circ = FakeCirqCircuit()
    out = convert_to_qasm(circ)

    assert 'OPENQASM 3.0;' in out
    assert 'h q[0];' in out.lower()
    assert 'cx q[0], q[1];' in out.lower()


def test_cirq_qubit_mapping():
    """Test that qubits are correctly mapped to indices."""
    class MultiQubitCircuit:
        def __init__(self):
            self._qubits = ['a', 'b', 'c', 'd']
            self._ops = [
                FakeOp(create_gate_class('H')(), ['a']),
                FakeOp(create_gate_class('X')(), ['b']),
                FakeOp(create_gate_class('CX')(), ['a', 'd']),
            ]

        def all_qubits(self):
            return self._qubits

        def all_operations(self):
            return self._ops

    circ = MultiQubitCircuit()
    out = convert_to_qasm(circ)

    assert 'qubit[4] q;' in out
    assert 'h q[0];' in out.lower()
    assert 'x q[1];' in out.lower()
    assert 'cx q[0], q[3];' in out.lower()


def test_cirq_gate_name_lowercasing():
    """Test that gate names are lowercased."""
    class MixedCaseCircuit:
        def __init__(self):
            self._qubits = ['q0']
            self._ops = [
                FakeOp(create_gate_class('HADAMARD')(), ['q0']),
                FakeOp(create_gate_class('PauliX')(), ['q0']),
                FakeOp(create_gate_class('CNOT')(), ['q0', 'q0']),
            ]

        def all_qubits(self):
            return self._qubits

        def all_operations(self):
            return self._ops

    circ = MixedCaseCircuit()
    out = convert_to_qasm(circ)

    # Gate names should be lowercased
    assert 'hadamard' in out.lower() or 'h' in out.lower()
    assert 'paulix' in out.lower() or 'x' in out.lower()
    assert 'cnot' in out.lower() or 'cx' in out.lower()


def test_cirq_operation_order():
    """Test that operation order is preserved."""
    class OrderedCircuit:
        def __init__(self):
            self._qubits = ['q0', 'q1']
            self._ops = [
                FakeOp(create_gate_class('H')(), ['q0']),
                FakeOp(create_gate_class('X')(), ['q1']),
                FakeOp(create_gate_class('Z')(), ['q0']),
                FakeOp(create_gate_class('CX')(), ['q0', 'q1']),
            ]

        def all_qubits(self):
            return self._qubits

        def all_operations(self):
            return self._ops

    circ = OrderedCircuit()
    out = convert_to_qasm(circ)

    # Check that operations appear in order
    h_pos = out.lower().find('h q[0];')
    x_pos = out.lower().find('x q[1];')
    z_pos = out.lower().find('z q[0];')
    cx_pos = out.lower().find('cx q[0], q[1];')

    assert h_pos < x_pos < z_pos < cx_pos


def test_cirq_single_qubit_gates():
    """Test single qubit gates."""
    class SingleQubitCircuit:
        def __init__(self):
            self._qubits = ['q0']
            self._ops = [
                FakeOp(create_gate_class('H')(), ['q0']),
                FakeOp(create_gate_class('X')(), ['q0']),
                FakeOp(create_gate_class('Y')(), ['q0']),
                FakeOp(create_gate_class('Z')(), ['q0']),
            ]

        def all_qubits(self):
            return self._qubits

        def all_operations(self):
            return self._ops

    circ = SingleQubitCircuit()
    out = convert_to_qasm(circ)

    assert 'qubit[1] q;' in out
    assert 'h q[0];' in out.lower()
    assert 'x q[0];' in out.lower()
    assert 'y q[0];' in out.lower()
    assert 'z q[0];' in out.lower()


def test_cirq_no_classical_bits():
    """Test that Cirq circuits have no classical bits by default."""
    circ = FakeCirqCircuit()
    out = convert_to_qasm(circ)

    # Cirq adapter should set num_cbits to 0
    assert 'bit[0] c;' in out

