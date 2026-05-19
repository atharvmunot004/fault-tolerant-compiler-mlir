from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple

from .circuit import Circuit
from .tableau import StabilizerState


@dataclass(frozen=True)
class BitFlip3Code:
    """
    3-qubit repetition code for correcting a single X (bit-flip) error.

    - Logical |0_L> = |000>, |1_L> = |111>
    - Stabilizers: Z0Z1, Z1Z2
    """

    @staticmethod
    def encoder_circuit() -> Circuit:
        # Input: |psi> on q0, |0> on q1,q2
        c = Circuit(3)
        c.cnot(0, 1).cnot(0, 2)
        return c

    @staticmethod
    def syndrome_circuit() -> Circuit:
        """
        Measures Z0Z1 and Z1Z2 using two ancillas (q3,q4), returning two bits.
        Total qubits: 5.
        """
        c = Circuit(5)
        # ancilla q3 measures Z0Z1
        c.cnot(0, 3).cnot(1, 3).mz(3, key="s01")
        # ancilla q4 measures Z1Z2
        c.cnot(1, 4).cnot(2, 4).mz(4, key="s12")
        return c

    @staticmethod
    def read_syndrome(state: StabilizerState) -> Tuple[int, int]:
        """
        Read (Z0Z1, Z1Z2) eigenvalue bits from stabilizer phases on the 3 data qubits.
        No ancillas required. Returns (s01, s12) where 0 => +1 and 1 => -1.
        """
        if state.n < 3:
            raise ValueError("need at least 3 qubits")

        def _phase_for_z(zpat: Tuple[int, ...]) -> int:
            for p, x, z in state.stabilizer_generators():
                if all(xb == 0 for xb in x) and tuple(z[:3]) == zpat:
                    return p
            raise ValueError(f"no stabilizer with Z pattern {zpat}")

        s01 = _phase_for_z((1, 1, 0))
        s12 = _phase_for_z((1, 1, 0)) ^ _phase_for_z((1, 0, 1))
        return s01, s12

    @staticmethod
    def measure_syndrome(state: StabilizerState, *, ancilla_01: int = 3, ancilla_12: int = 4) -> Tuple[int, int]:
        """
        Measures (Z0Z1, Z1Z2) into two ancillas and resets those ancillas back to |0>.
        Returns syndrome bits (s01, s12) where 0 => +1 and 1 => -1.
        """
        # Z0Z1 parity
        state.cnot(0, ancilla_01)
        state.cnot(1, ancilla_01)
        s01 = state.measure_z(ancilla_01)
        state.reset_z(ancilla_01)

        # Z1Z2 parity
        state.cnot(1, ancilla_12)
        state.cnot(2, ancilla_12)
        s12 = state.measure_z(ancilla_12)
        state.reset_z(ancilla_12)

        return s01, s12

    @staticmethod
    def correct_x_from_syndrome(state: StabilizerState, s01: int, s12: int) -> None:
        """
        For syndrome bits (0 => +1, 1 => -1):
        - 00: no error
        - 10: error on q0
        - 11: error on q1
        - 01: error on q2
        """
        if (s01, s12) == (1, 0):
            state.x(0)
        elif (s01, s12) == (1, 1):
            state.x(1)
        elif (s01, s12) == (0, 1):
            state.x(2)


@dataclass(frozen=True)
class Shor9Code:
    """
    9-qubit Shor code (corrects any single-qubit error) encoder circuit.

    Qubit layout:
    - Phase protection across roots: q0, q3, q6
    - Bit-flip repetition in each block: (q0,q1,q2), (q3,q4,q5), (q6,q7,q8)
    """

    @staticmethod
    def encoder_circuit() -> Circuit:
        # Input: |psi> on q0, others |0>
        c = Circuit(9)
        # Spread amplitude to three blocks (bit-flip blocks roots).
        c.cnot(0, 3).cnot(0, 6)
        # Protect against phase flips by switching to X basis on block roots.
        c.h(0).h(3).h(6)
        # Bit-flip encoding within each block.
        c.cnot(0, 1).cnot(0, 2)
        c.cnot(3, 4).cnot(3, 5)
        c.cnot(6, 7).cnot(6, 8)
        return c

    # Syndrome bit patterns (stabilizer row phases) for single X errors on q0..q8.
    _X_SYNDROME: Tuple[Tuple[int, ...], ...] = (
        (0, 1, 1, 0, 0, 0, 0, 0, 0),
        (0, 1, 0, 0, 0, 0, 0, 0, 0),
        (0, 0, 1, 0, 0, 0, 0, 0, 0),
        (0, 0, 0, 0, 1, 1, 0, 0, 0),
        (0, 0, 0, 0, 1, 0, 0, 0, 0),
        (0, 0, 0, 0, 0, 1, 0, 0, 0),
        (0, 0, 0, 0, 0, 0, 0, 1, 1),
        (0, 0, 0, 0, 0, 0, 0, 1, 0),
        (0, 0, 0, 0, 0, 0, 0, 0, 1),
    )

    @staticmethod
    def read_syndrome(state: StabilizerState) -> Tuple[int, ...]:
        """Stabilizer-row phase bits (0 => +1, 1 => -1) for all 9 generators."""
        return tuple(g[0] for g in state.stabilizer_generators())

    @staticmethod
    def correct_x_from_syndrome(state: StabilizerState, syndrome: Tuple[int, ...]) -> None:
        """Apply X on the data qubit matching a single-X-error syndrome, if recognized."""
        for q, pattern in enumerate(Shor9Code._X_SYNDROME):
            if syndrome == pattern:
                state.x(q)
                return


def run_2qubit_bell() -> Tuple[StabilizerState, List[int]]:
    """
    Convenience helper: prepares Bell state |Phi+> on 2 qubits.
    """
    st = StabilizerState.zero(2)
    c = Circuit(2).h(0).cnot(0, 1)
    c.run(st)
    return st, []


def bitflip3_encode_zero_state() -> StabilizerState:
    """
    Returns encoded |0_L> (starting from |000> and applying encoder; stays |000>).
    """
    st = StabilizerState.zero(3)
    BitFlip3Code.encoder_circuit().run(st)
    return st

