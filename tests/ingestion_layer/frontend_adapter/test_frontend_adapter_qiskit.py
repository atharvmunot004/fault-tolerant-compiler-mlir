"""
Test Qiskit-like Python circuit conversion.

These tests verify that circuits with Qiskit-like structure (data attribute,
num_qubits, num_clbits) are correctly converted to OpenQASM.
"""
import pytest
from src.ingestion_layer.frontend_adapter import convert_to_qasm


class FakeQubit:
    """Mock qubit object with index attribute."""
    def __init__(self, index):
        self.index = index


class FakeCbit:
    """Mock classical bit object with index attribute."""
    def __init__(self, index):
        self.index = index


class FakeInst:
    """Mock instruction object with name attribute."""
    def __init__(self, name):
        self.name = name


class FakeQiskitCircuit:
    """Mock Qiskit-like circuit with data, num_qubits, num_clbits."""
    def __init__(self):
        self.num_qubits = 2
        self.num_clbits = 1
        self.data = [
            (FakeInst('h'), [FakeQubit(0)], []),
            (FakeInst('cx'), [FakeQubit(0), FakeQubit(1)], []),
            (FakeInst('measure'), [FakeQubit(0)], [FakeCbit(0)]),
        ]


def test_qiskit_like_conversion():
    """Test basic Qiskit-like circuit conversion."""
    circ = FakeQiskitCircuit()
    out = convert_to_qasm(circ)

    assert 'OPENQASM 3.0;' in out
    assert 'h q[0];' in out
    assert 'cx q[0], q[1];' in out
    assert 'c[0] = measure q[0];' in out


def test_qiskit_instruction_order():
    """Test that instruction order from data attribute is preserved."""
    circ = FakeQiskitCircuit()
    out = convert_to_qasm(circ)

    # Find positions to verify order
    h_pos = out.find('h q[0];')
    cx_pos = out.find('cx q[0], q[1];')
    measure_pos = out.find('c[0] = measure q[0];')

    assert h_pos < cx_pos < measure_pos


def test_qiskit_multiple_qubits():
    """Test circuit with multiple qubits."""
    class LargeCircuit:
        def __init__(self):
            self.num_qubits = 5
            self.num_clbits = 0
            self.data = [
                (FakeInst('h'), [FakeQubit(i)], []) for i in range(5)
            ]

    circ = LargeCircuit()
    out = convert_to_qasm(circ)

    assert 'qubit[5] q;' in out
    for i in range(5):
        assert f'h q[{i}];' in out


def test_qiskit_no_classical_bits():
    """Test circuit with no classical bits."""
    class NoCbitsCircuit:
        def __init__(self):
            self.num_qubits = 2
            self.num_clbits = 0
            self.data = [
                (FakeInst('h'), [FakeQubit(0)], []),
                (FakeInst('cx'), [FakeQubit(0), FakeQubit(1)], []),
            ]

    circ = NoCbitsCircuit()
    out = convert_to_qasm(circ)

    assert 'bit[0] c;' in out
    assert 'h q[0];' in out
    assert 'cx q[0], q[1];' in out


def test_qiskit_multiple_measurements():
    """Test circuit with multiple measurements."""
    class MultiMeasureCircuit:
        def __init__(self):
            self.num_qubits = 3
            self.num_clbits = 3
            self.data = [
                (FakeInst('measure'), [FakeQubit(i)], [FakeCbit(i)]) 
                for i in range(3)
            ]

    circ = MultiMeasureCircuit()
    out = convert_to_qasm(circ)

    for i in range(3):
        assert f'c[{i}] = measure q[{i}];' in out


def test_qiskit_gate_names_preserved():
    """Test that gate names are preserved as-is."""
    class CustomGateCircuit:
        def __init__(self):
            self.num_qubits = 2
            self.num_clbits = 0
            self.data = [
                (FakeInst('custom_gate'), [FakeQubit(0)], []),
                (FakeInst('another_gate'), [FakeQubit(1)], []),
            ]

    circ = CustomGateCircuit()
    out = convert_to_qasm(circ)

    # Gate names should be preserved (no semantic validation)
    assert 'custom_gate q[0];' in out
    assert 'another_gate q[1];' in out


def test_qiskit_qubit_indices_preserved():
    """Test that qubit indices are correctly extracted and preserved."""
    class SparseCircuit:
        def __init__(self):
            self.num_qubits = 10
            self.num_clbits = 0
            self.data = [
                (FakeInst('h'), [FakeQubit(0)], []),
                (FakeInst('x'), [FakeQubit(5)], []),
                (FakeInst('z'), [FakeQubit(9)], []),
            ]

    circ = SparseCircuit()
    out = convert_to_qasm(circ)

    assert 'qubit[10] q;' in out
    assert 'h q[0];' in out
    assert 'x q[5];' in out
    assert 'z q[9];' in out

