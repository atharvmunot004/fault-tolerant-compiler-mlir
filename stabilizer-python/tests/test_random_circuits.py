import random
from typing import List, Tuple

from stabilizer_python.circuit import Circuit
from stabilizer_python.linear_algebra import rank_gf2
from stabilizer_python.tableau import StabilizerState


Gate = Tuple[str, Tuple[int, ...]]


def _random_clifford_gates(rng: random.Random, n_qubits: int, depth: int) -> List[Gate]:
    gates: List[Gate] = []
    for _ in range(depth):
        name = rng.choice(["H", "S", "X", "Z", "CNOT"])
        if name == "CNOT":
            control, target = rng.sample(range(n_qubits), 2)
            gates.append((name, (control, target)))
        else:
            gates.append((name, (rng.randrange(n_qubits),)))
    return gates


def _append_gate(circuit: Circuit, gate: Gate) -> None:
    name, targets = gate
    if name == "H":
        circuit.h(targets[0])
    elif name == "S":
        circuit.s(targets[0])
    elif name == "X":
        circuit.x(targets[0])
    elif name == "Z":
        circuit.z(targets[0])
    elif name == "CNOT":
        circuit.cnot(targets[0], targets[1])
    elif name == "MZ":
        circuit.mz(targets[0])
    else:
        raise ValueError(f"unknown random gate {name}")


def _circuit_from_gates(n_qubits: int, gates: List[Gate]) -> Circuit:
    circuit = Circuit(n_qubits)
    for gate in gates:
        _append_gate(circuit, gate)
    return circuit


def _inverse_gates(gates: List[Gate]) -> List[Gate]:
    inverse: List[Gate] = []
    for gate in reversed(gates):
        name, targets = gate
        if name == "S":
            inverse.extend([gate, gate, gate])
        else:
            inverse.append((name, targets))
    return inverse


def _assert_same_tableau(left: StabilizerState, right: StabilizerState) -> None:
    assert left.n == right.n
    assert left.x_mat == right.x_mat
    assert left.z_mat == right.z_mat
    assert left.r_phase == right.r_phase


def _symplectic_product(state: StabilizerState, row_a: int, row_b: int) -> int:
    total = 0
    for q in range(state.n):
        total ^= state.x_mat[row_a][q] & state.z_mat[row_b][q]
        total ^= state.z_mat[row_a][q] & state.x_mat[row_b][q]
    return total


def _assert_valid_stabilizer_tableau(state: StabilizerState) -> None:
    assert len(state.x_mat) == 2 * state.n
    assert len(state.z_mat) == 2 * state.n
    assert len(state.r_phase) == 2 * state.n

    for row in state.x_mat + state.z_mat:
        assert len(row) == state.n
        assert all(bit in (0, 1) for bit in row)
    assert all(phase in (0, 1) for phase in state.r_phase)

    stabilizer_rows = range(state.n, 2 * state.n)
    stabilizer_matrix: List[List[int]] = []
    for row_a in stabilizer_rows:
        stabilizer_matrix.append(state.x_mat[row_a] + state.z_mat[row_a])
        assert any(state.x_mat[row_a] + state.z_mat[row_a])
        for row_b in range(row_a + 1, 2 * state.n):
            assert _symplectic_product(state, row_a, row_b) == 0

    assert rank_gf2(stabilizer_matrix) == state.n


def test_random_clifford_circuits_round_trip_to_zero_state():
    seeds = range(20)
    for seed in range(20):
        rng = random.Random(seed)
        n_qubits = rng.randint(2, 6)
        gates = _random_clifford_gates(rng, n_qubits=n_qubits, depth=80)
        circuit = _circuit_from_gates(n_qubits, gates + _inverse_gates(gates))

        state = StabilizerState.zero(n_qubits)
        circuit.run(state)

        _assert_same_tableau(state, StabilizerState.zero(n_qubits))

    print(f"random Clifford inverse check passed for {len(seeds)} circuits")


def test_random_clifford_circuits_generate_valid_stabilizers():
    seeds = range(40, 60)
    for seed in seeds:
        rng = random.Random(seed)
        n_qubits = rng.randint(2, 6)
        gates = _random_clifford_gates(rng, n_qubits=n_qubits, depth=80)

        state = StabilizerState.zero(n_qubits)
        _circuit_from_gates(n_qubits, gates).run(state)

        _assert_valid_stabilizer_tableau(state)

    print(f"valid stabilizer generator check passed for {len(seeds)} random circuits")


def test_random_measurement_circuits_keep_valid_tableau():
    seeds = range(20, 40)
    for seed in seeds:
        rng = random.Random(seed)
        random.seed(seed)
        n_qubits = rng.randint(2, 6)
        gates = _random_clifford_gates(rng, n_qubits=n_qubits, depth=60)
        measure_targets = [rng.randrange(n_qubits) for _ in range(10)]
        gates.extend(("MZ", (target,)) for target in measure_targets)

        state = StabilizerState.zero(n_qubits)
        measurements = _circuit_from_gates(n_qubits, gates).run(state)

        assert len(measurements) == len(measure_targets)
        assert all(bit in (0, 1) for bit in measurements)
        _assert_valid_stabilizer_tableau(state)

    print(f"random measurement tableau check passed for {len(seeds)} circuits")
