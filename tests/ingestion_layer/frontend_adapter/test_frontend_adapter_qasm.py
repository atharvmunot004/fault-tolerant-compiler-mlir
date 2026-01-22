"""
Test OpenQASM input pass-through and normalization.

These tests verify that raw OpenQASM input is correctly converted to OpenQASM 3.0,
preserving circuit structure and instruction ordering.
"""
import pytest
from src.ingestion_layer.frontend_adapter import convert_to_qasm


def normalize(qasm):
    """Normalize whitespace for comparison."""
    return '\n'.join(l.strip() for l in qasm.strip().splitlines() if l.strip())


def test_qasm_round_trip_simple():
    """Test simple QASM 2.0 to 3.0 conversion."""
    qasm = '''
    OPENQASM 2.0;
    qreg q[2];
    creg c[1];
    h q[0];
    cx q[0], q[1];
    measure q[0] -> c[0];
    '''

    out = convert_to_qasm(qasm)

    assert 'OPENQASM 3.0;' in out
    assert 'h q[0];' in out
    assert 'cx q[0], q[1];' in out
    assert 'c[0] = measure q[0];' in out


def test_qasm_3_0_passthrough():
    """Test that OpenQASM 3.0 input passes through correctly."""
    qasm = '''
    OPENQASM 3.0;
    qubit[2] q;
    bit[1] c;
    h q[0];
    cx q[0], q[1];
    c[0] = measure q[0];
    '''

    out = convert_to_qasm(qasm)

    assert 'OPENQASM 3.0;' in out
    assert 'h q[0];' in out
    assert 'cx q[0], q[1];' in out
    assert 'c[0] = measure q[0];' in out


def test_qasm_instruction_order_preserved():
    """Test that instruction order is preserved."""
    qasm = '''
    OPENQASM 3.0;
    qubit[3] q;
    h q[0];
    x q[1];
    z q[2];
    cx q[0], q[1];
    '''

    out = convert_to_qasm(qasm)

    # Check that all instructions are present
    assert 'h q[0];' in out
    assert 'x q[1];' in out
    assert 'z q[2];' in out
    assert 'cx q[0], q[1];' in out

    # Check order by finding positions
    h_pos = out.find('h q[0];')
    x_pos = out.find('x q[1];')
    z_pos = out.find('z q[2];')
    cx_pos = out.find('cx q[0], q[1];')

    assert h_pos < x_pos < z_pos < cx_pos


def test_qasm_cnot_variants():
    """Test that both 'cx' and 'cnot' are handled."""
    qasm_cx = '''
    OPENQASM 3.0;
    qubit[2] q;
    cx q[0], q[1];
    '''

    qasm_cnot = '''
    OPENQASM 3.0;
    qubit[2] q;
    cnot q[0], q[1];
    '''

    out_cx = convert_to_qasm(qasm_cx)
    out_cnot = convert_to_qasm(qasm_cnot)

    # Both should produce valid output
    assert 'OPENQASM 3.0;' in out_cx
    assert 'OPENQASM 3.0;' in out_cnot
    # At least one should have the gate
    assert ('cx q[0], q[1];' in out_cx) or ('cnot q[0], q[1];' in out_cx)
    assert ('cx q[0], q[1];' in out_cnot) or ('cnot q[0], q[1];' in out_cnot)


def test_qasm_multiple_measurements():
    """Test multiple measurement operations."""
    qasm = '''
    OPENQASM 2.0;
    qreg q[3];
    creg c[3];
    measure q[0] -> c[0];
    measure q[1] -> c[1];
    measure q[2] -> c[2];
    '''

    out = convert_to_qasm(qasm)

    assert 'c[0] = measure q[0];' in out
    assert 'c[1] = measure q[1];' in out
    assert 'c[2] = measure q[2];' in out


def test_qasm_qubit_count_preserved():
    """Test that qubit count is correctly extracted and preserved."""
    qasm = '''
    OPENQASM 3.0;
    qubit[10] q;
    h q[0];
    '''

    out = convert_to_qasm(qasm)

    assert 'qubit[10] q;' in out


def test_qasm_cbit_count_preserved():
    """Test that classical bit count is correctly extracted and preserved."""
    qasm = '''
    OPENQASM 2.0;
    qreg q[2];
    creg c[5];
    measure q[0] -> c[0];
    '''

    out = convert_to_qasm(qasm)

    assert 'bit[5] c;' in out

