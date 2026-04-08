from stabilizer_python.circuit import Circuit
from stabilizer_python.tableau import StabilizerState


def main() -> None:
    # Use a 3rd qubit as an ancilla to verify correlations.
    st = StabilizerState.zero(3)
    Circuit(3).h(0).cnot(0, 1).run(st)

    # Verify ZZ parity is +1 by measuring Z0Z1 with ancilla q2.
    out = Circuit(3).cnot(0, 2).cnot(1, 2).mz(2).run(st)
    print("Bell |Phi+> prepared.")
    print("Measured Z0Z1 parity (0 => +1):", out[0])


if __name__ == "__main__":
    main()

