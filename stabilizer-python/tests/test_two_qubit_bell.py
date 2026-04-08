from stabilizer_python.circuit import Circuit
from stabilizer_python.tableau import StabilizerState


def test_bell_has_zz_parity_plus():
    st = StabilizerState.zero(3)  # ancilla q2 for parity readout
    Circuit(3).h(0).cnot(0, 1).run(st)
    # Measure Z0Z1 using ancilla q2 (CNOTs into ancilla then measure Z on ancilla).
    out = Circuit(3).cnot(0, 2).cnot(1, 2).mz(2).run(st)
    assert out == [0]


def test_bell_has_xx_parity_plus():
    st = StabilizerState.zero(3)  # ancilla q2 for parity readout
    Circuit(3).h(0).cnot(0, 1).run(st)
    # Measure X0X1 by rotating both with H, then measuring Z0Z1.
    Circuit(3).h(0).h(1).run(st)
    out = Circuit(3).cnot(0, 2).cnot(1, 2).mz(2).run(st)
    assert out == [0]

