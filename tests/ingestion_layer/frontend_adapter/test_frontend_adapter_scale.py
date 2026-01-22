"""
Stress test large circuits for performance and ordering.

These tests verify that the frontend adapter can handle large circuits
without slowdown and preserves instruction ordering.
"""
import pytest
import time
from src.ingestion_layer.frontend_adapter import convert_to_qasm


def test_large_circuit_scale():
    """Test large circuit with many gates."""
    qasm = ['OPENQASM 3.0;', 'qubit[100] q;']
    for i in range(99):
        qasm.append(f'cx q[{i}], q[{i+1}];')

    qasm = '\n'.join(qasm)
    out = convert_to_qasm(qasm)

    # Must preserve all gates
    assert out.count('cx') == 99
    assert 'qubit[100] q;' in out


def test_large_circuit_performance():
    """Test that large circuits are processed in reasonable time."""
    qasm = ['OPENQASM 3.0;', 'qubit[1000] q;']
    for i in range(999):
        qasm.append(f'h q[{i % 1000}];')

    qasm = '\n'.join(qasm)

    start = time.time()
    out = convert_to_qasm(qasm)
    elapsed = time.time() - start

    # Should complete in under 5 seconds
    assert elapsed < 5.0
    assert 'qubit[1000] q;' in out
    assert out.count('h') == 999


def test_large_circuit_instruction_order():
    """Test that instruction order is preserved in large circuits."""
    qasm = ['OPENQASM 3.0;', 'qubit[50] q;']
    
    # Create a pattern: H gates on even indices, X gates on odd indices
    for i in range(50):
        if i % 2 == 0:
            qasm.append(f'h q[{i}];')
        else:
            qasm.append(f'x q[{i}];')

    qasm = '\n'.join(qasm)
    out = convert_to_qasm(qasm)

    # Verify order by checking positions
    h_positions = []
    x_positions = []
    lines = out.split('\n')
    
    for idx, line in enumerate(lines):
        if 'h q[' in line.lower():
            h_positions.append(idx)
        if 'x q[' in line.lower():
            x_positions.append(idx)

    # Should have 25 H gates and 25 X gates
    assert len(h_positions) == 25
    assert len(x_positions) == 25

    # First gate should be H (index 0)
    assert h_positions[0] < x_positions[0]


def test_large_circuit_with_measurements():
    """Test large circuit with many measurements."""
    qasm = ['OPENQASM 3.0;', 'qubit[100] q;', 'bit[100] c;']
    
    for i in range(100):
        qasm.append(f'c[{i}] = measure q[{i}];')

    qasm = '\n'.join(qasm)
    out = convert_to_qasm(qasm)

    assert 'qubit[100] q;' in out
    assert 'bit[100] c;' in out
    assert out.count('measure') == 100


def test_very_large_qubit_count():
    """Test circuit with very large qubit count."""
    qasm = f'''
    OPENQASM 3.0;
    qubit[10000] q;
    h q[0];
    '''

    out = convert_to_qasm(qasm)

    assert 'qubit[10000] q;' in out
    assert 'h q[0];' in out


def test_deep_circuit_depth():
    """Test circuit with very deep depth (many sequential gates)."""
    qasm = ['OPENQASM 3.0;', 'qubit[10] q;']
    
    # Create 1000 sequential gates
    for _ in range(1000):
        qasm.append('h q[0];')

    qasm = '\n'.join(qasm)
    out = convert_to_qasm(qasm)

    # All gates should be preserved
    assert out.count('h q[0];') == 1000


def test_mixed_large_circuit():
    """Test large circuit with mixed gate types."""
    qasm = ['OPENQASM 3.0;', 'qubit[50] q;']
    
    gates = ['h', 'x', 'z', 'y']
    for i in range(200):
        gate = gates[i % len(gates)]
        qubit_idx = i % 50
        qasm.append(f'{gate} q[{qubit_idx}];')

    qasm = '\n'.join(qasm)
    out = convert_to_qasm(qasm)

    # Count each gate type
    assert out.count('h q[') == 50
    assert out.count('x q[') == 50
    assert out.count('z q[') == 50
    assert out.count('y q[') == 50

