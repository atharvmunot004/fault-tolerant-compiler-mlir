"""
Fuzz-style randomized testing to catch edge cases.

These tests use randomized inputs to discover edge cases and ensure
the frontend adapter handles various inputs robustly.
"""
import random
import pytest
from src.ingestion_layer.frontend_adapter import convert_to_qasm


def random_qasm(n_qubits=5, depth=20):
    """Generate random OpenQASM circuit."""
    lines = ['OPENQASM 3.0;', f'qubit[{n_qubits}] q;']
    
    gates = ['h', 'x', 'z', 'y']
    for _ in range(depth):
        gate = random.choice(gates)
        q = random.randint(0, n_qubits - 1)
        lines.append(f'{gate} q[{q}];')
    
    return '\n'.join(lines)


def test_random_qasm_fuzz():
    """Test random QASM circuits."""
    for _ in range(50):
        qasm = random_qasm()
        out = convert_to_qasm(qasm)
        assert 'OPENQASM 3.0;' in out


def test_random_qasm_varying_sizes():
    """Test random circuits of varying sizes."""
    for n_qubits in [1, 5, 10, 20, 50]:
        for depth in [1, 10, 50, 100]:
            qasm = random_qasm(n_qubits=n_qubits, depth=depth)
            out = convert_to_qasm(qasm)
            
            assert 'OPENQASM 3.0;' in out
            assert f'qubit[{n_qubits}] q;' in out


def test_random_two_qubit_gates():
    """Test random circuits with two-qubit gates."""
    random.seed(42)  # For reproducibility
    
    for _ in range(20):
        n_qubits = random.randint(2, 10)
        lines = ['OPENQASM 3.0;', f'qubit[{n_qubits}] q;']
        
        for _ in range(30):
            if random.random() < 0.5:
                # Single qubit gate
                gate = random.choice(['h', 'x', 'z'])
                q = random.randint(0, n_qubits - 1)
                lines.append(f'{gate} q[{q}];')
            else:
                # Two qubit gate
                q1 = random.randint(0, n_qubits - 1)
                q2 = random.randint(0, n_qubits - 1)
                if q1 != q2:
                    lines.append(f'cx q[{q1}], q[{q2}];')
        
        qasm = '\n'.join(lines)
        out = convert_to_qasm(qasm)
        
        assert 'OPENQASM 3.0;' in out


def test_fuzz_qasm_2_0_variants():
    """Fuzz test with QASM 2.0 syntax variants."""
    random.seed(123)
    
    for _ in range(30):
        n_qubits = random.randint(1, 20)
        n_cbits = random.randint(0, 10)
        
        lines = [
            'OPENQASM 2.0;',
            f'qreg q[{n_qubits}];',
        ]
        
        if n_cbits > 0:
            lines.append(f'creg c[{n_cbits}];')
        
        # Add random gates
        for _ in range(random.randint(1, 50)):
            gate = random.choice(['h', 'x', 'z'])
            q = random.randint(0, n_qubits - 1)
            lines.append(f'{gate} q[{q}];')
        
        # Add random measurements
        if n_cbits > 0:
            for _ in range(random.randint(0, min(n_cbits, 5))):
                q = random.randint(0, n_qubits - 1)
                c = random.randint(0, n_cbits - 1)
                lines.append(f'measure q[{q}] -> c[{c}];')
        
        qasm = '\n'.join(lines)
        out = convert_to_qasm(qasm)
        
        assert 'OPENQASM 3.0;' in out


def test_fuzz_gate_name_variations():
    """Fuzz test with various gate name formats."""
    gates_to_test = ['h', 'H', 'x', 'X', 'z', 'Z', 'cx', 'CX', 'cnot', 'CNOT']
    
    for gate_name in gates_to_test:
        if gate_name.lower() in ['cx', 'cnot']:
            qasm = f'''
            OPENQASM 3.0;
            qubit[2] q;
            {gate_name} q[0], q[1];
            '''
        else:
            qasm = f'''
            OPENQASM 3.0;
            qubit[1] q;
            {gate_name} q[0];
            '''
        
        out = convert_to_qasm(qasm)
        assert 'OPENQASM 3.0;' in out


def test_fuzz_whitespace_variations():
    """Fuzz test with various whitespace patterns."""
    variations = [
        'OPENQASM 3.0;\nqubit[2] q;\nh q[0];',
        'OPENQASM 3.0;   \nqubit[2] q;   \nh q[0];',
        'OPENQASM 3.0;\n\nqubit[2] q;\n\nh q[0];',
        '  OPENQASM 3.0;\n  qubit[2] q;\n  h q[0];',
    ]
    
    for qasm in variations:
        out = convert_to_qasm(qasm)
        assert 'OPENQASM 3.0;' in out
        assert 'h q[0];' in out.lower()


def test_fuzz_empty_and_minimal():
    """Fuzz test with empty and minimal circuits."""
    minimal_circuits = [
        'OPENQASM 3.0;\nqubit[1] q;',
        'OPENQASM 3.0;\nqubit[1] q;\nbit[0] c;',
        'OPENQASM 3.0;\nqubit[1] q;\nh q[0];',
    ]
    
    for qasm in minimal_circuits:
        out = convert_to_qasm(qasm)
        assert 'OPENQASM 3.0;' in out

